# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import werkzeug.wrappers as wrappers
import logging
import urllib.parse


_logger = logging.getLogger(__name__)

TEX = """OK GET OPTION FROM: {serial_no}
TransFlag=TransData\tAttLog\tOpLog\tAttPhoto\tEnrollFP\tEnrollUser\tFPImag\tChgUser\tChgFP\tFACE\tUserPic\tFVEIN\tBioPhoto
ServerVer=2.4.1
PushProtVer=2.4.1
Encrypt=0
EncryptFlag=1000000000
SupportPing=1
PushOptionsFlag=1
MaxPostSize=1048576
PushOptions=UserCount,TransactionCount,FingerFunOn,FPVersion,FPCount,FaceFunOn,FaceVersion,FaceCount,FvFunOn,FvVersion,FvCount,PvFunOn,PvVersion,PvCount,BioPhotoFun,BioDataFun,PhotoFunOn,~LockFunOn,CardProtFormat,~Platform,MultiBioPhotoSupport,MultiBioDataSupport,MultiBioVersion
MultiBioDataSupport=0:1:1:0:0:0:0:1:1:1:1
MultiBioPhotoSupport=0:0:0:0:0:0:0:0:0:1:1
TimeZone={timezone}
TransTimes=00:00;14:05
TransInterval=1
ErrorDelay=60
Delay=10
Realtime=1
"""

class ZkAttendence(http.Controller):


    @http.route(['/iclock/cdata/','/iclock/cdata.aspx/'], type='http', auth="public", csrf=False)
    def zk_bio_device_cdata(self, **kw):
        d_obj = request.env['sa.biometric.device'].sudo()
        device = d_obj.search([('serial_no','=',kw.get('SN','softatt'))]) #fix me
        _logger.info("Device SN: %s", kw.get('SN'))
        
        if not kw.get('table', False):
            if not device:
                device = d_obj.create({'serial_no': kw.get('SN'), 'state':'pending'})
            text = TEX.format(serial_no=device.serial_no, timezone=device.tz_offset)
            return wrappers.Response(status="200 OK",
                                    headers={
                                        'Date': 'Tue, 07 Nov 2023 17:38:17 GMT',
                                        'Server': 'Apache/2.4.54 (Win64) mod_wsgi/4.7.1 Python/3.7',
                                        'Pragma': 'no-cache',
                                        'Cache-Control': 'no-store',
                                        'Content-Length': '762',
                                        'Content-Type': 'text/plain',
                                        'Connection': 'close'
                                        }, 
                                    response=text)
        
        table = kw.get('table')
        _logger.info('Processing table: %s', table)
        
        # Get raw binary data
        raw_data = request.httprequest.data
        _logger.info('Raw data length: %d bytes', len(raw_data))
        
        # ============= NEW: HANDLE ATTPHOTO (SpeedFace-V5L photo uploads) =============
        if table == 'ATTPHOTO':
            stored = 0
            try:
                # Look for JPEG header to separate text from binary
                jpeg_header = b'\xff\xd8\xff'
                header_pos = raw_data.find(jpeg_header)
                
                if header_pos > 0:
                    # Split text header and binary image
                    text_part = raw_data[:header_pos].decode('utf-8', errors='ignore')
                    binary_data = raw_data[header_pos:]
                    
                    _logger.info('ATTPHOTO text header: %s', text_part)
                    
                    # Parse text header (format: PIN=xxx.jpg\nSN=xxx\nsize=xxx\nCMD=xxx)
                    params = {}
                    for line in text_part.strip().split('\n'):
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            params[key.strip()] = value.strip()
                    
                    pin = params.get('PIN', '').replace('.jpg', '').replace('.jpeg', '')
                    cmd = params.get('CMD', '')
                    size = params.get('size', '0')
                    
                    _logger.info('ATTPHOTO - PIN: %s, CMD: %s, Size: %s', pin, cmd, size)
                    
                    if cmd == 'uploadphoto' and binary_data:
                        # Store photo data
                        photo_data = {
                            'pin': pin,
                            'photo': base64.b64encode(binary_data).decode('utf-8'),
                            'device_id': device.id
                        }
                        stored += self._store_biophoto_data(photo_data, device.id)
                        _logger.info('ATTPHOTO stored for PIN: %s', pin)
                else:
                    _logger.warning('No JPEG header found in ATTPHOTO data')
                    
            except Exception as e:
                _logger.error('Error processing ATTPHOTO: %s', str(e), exc_info=True)
                stored = 0
                
            return wrappers.Response(response='OK: %s' % stored)
        
        # ============= ORIGINAL BIODATA HANDLER =============
        if table == 'BIODATA':
            data = raw_data.decode('utf-8', errors='ignore')
            entries = data.split('\n')
            stored = 0
            if data.startswith('BIODATA'):
                entries = data.split('BIODATA ')[1:]  # Process FP entries
                for entry in entries:                    
                    if entry.strip():  # Make sure to ignore empty entries
                        try:
                            unified_tmp_data = self._parse_data(entry)
                            stored += self._store_unified_data(unified_tmp_data, device.id)
                        except Exception as e:
                            _logger.error(str(e))
                            stored += 1
            return wrappers.Response(response='OK: %s' % stored)
    
        # ============= ORIGINAL OPERLOG HANDLER =============
        if table == 'OPERLOG':
            data = raw_data.decode('utf-8', errors='ignore')
            entries = data.split('\n')
            stored = 0
            if data.startswith('USER'):
                entries = data.split('USER ')[1:]  # Process User entries
                for entry in entries:
                    if entry.strip():
                        try:
                            user_data = self._parse_data(entry)
                            stored += self._store_biometric_user(user_data, device.id)
                        except Exception as e:
                            _logger.error(str(e))
                            stored += 1
                            
            if data.startswith('BIOPHOTO'):
                entries = data.split('BIOPHOTO ')[1:]  # Process User entries
                for entry in entries:
                    if entry.strip():
                        try:
                            photo_data = self._parse_data(entry)
                            stored += self._store_biophoto_data(photo_data, device.id)
                        except Exception as e:
                            _logger.error(str(e))
                            stored += 1
            elif data.startswith('FP'):
                entries = data.split('FP ')[1:]  # Process FP entries
                for entry in entries:
                    if entry.strip():  # Make sure to ignore empty entries
                        try:
                            fingerprint_data = self._parse_data(entry)
                            stored += self._store_fingerprint_data(fingerprint_data, device.id)
                        except Exception as e:
                            _logger.error(str(e))
                            stored += 1
            return wrappers.Response(response='OK: %s' % stored)
    
        # ============= ORIGINAL ATTLOG HANDLER =============
        if table == 'ATTLOG':
            data = raw_data.decode('utf-8', errors='ignore')
            device_id = device.id
            query = """
            INSERT INTO sa_biometric_att (device_id, emp_code, punch_time, punch_state, punch_type)
            VALUES (%s, %s, %s::timestamp AT TIME ZONE '{tz}' AT TIME ZONE 'UTC', %s, %s)
            """
            lines = str(data).split('\n')
            values_list = [line.split('\t')[:4] for line in lines if line.strip()]
            flat_values = []
            for values in values_list:
                flat_values.append([device_id] + values)
            if flat_values:
                request.env.cr.executemany(query.format(tz=device.tz), flat_values)
                request.env.cr.commit()
            return wrappers.Response(response='OK')
        
        # Default response for unhandled tables
        return wrappers.Response(response='OK')

    # @http.route(['/iclock/cdata/','/iclock/cdata.aspx/'], type='http', auth="public", csrf=False)
    # def zk_bio_device_cdata(self, **kw):
    #     d_obj=request.env['sa.biometric.device'].sudo()
    #     device = d_obj.search([('serial_no','=',kw.get('SN','softatt'))]) #fix me
    #     _logger.info(kw.get('SN'))
    #     if not kw.get('table', False):
    #         if not device:
    #             device=d_obj.create({'serial_no':kw.get('SN'), 'state':'pending'})
    #         text = TEX.format(serial_no=device.serial_no, timezone=device.tz_offset)
    #         return wrappers.Response(status="200 OK",
    #                                 headers ={
    #                                     'Date': 'Tue, 07 Nov 2023 17:38:17 GMT',
    #                                     'Server': 'Apache/2.4.54 (Win64) mod_wsgi/4.7.1 Python/3.7',
    #                                     'Pragma': 'no-cache',
    #                                     'Cache-Control': 'no-store',
    #                                     'Content-Length': '762',
    #                                     'Content-Type': 'text/plain',
    #                                     'Connection': 'close'
    #                                     }, 
    #                                 response=text)
    #     table = kw.get('table')
    #     data    = request.httprequest.data.decode('utf-8')
    #     if table == 'BIODATA':
    #         data    = request.httprequest.data.decode('utf-8')
    #         entries = data.split('\n')
    #         stored = 0
    #         if data.startswith('BIODATA'):
    #             entries = data.split('BIODATA ')[1:]  # Process FP entries
    #             for entry in entries:                    
    #                 if entry.strip():  # Make sure to ignore empty entries
    #                     try:
    #                         unified_tmp_data = self._parse_data(entry)
    #                         stored += self._store_unified_data(unified_tmp_data, device.id)
    #                     except Exception as e:
    #                         _logger.error(str(e))
    #                         stored += 1

    #     if table == 'OPERLOG':
    #         data    = request.httprequest.data.decode('utf-8')
    #         entries = data.split('\n')
    #         stored = 0
    #         if data.startswith('USER'):
    #             entries = data.split('USER ')[1:]  # Process User entries
    #             for entry in entries:
    #                 if entry.strip():
    #                     try:
    #                         user_data = self._parse_data(entry)
    #                         stored += self._store_biometric_user(user_data, device.id)
    #                     except Exception as e:
    #                         _logger.error(str(e))
    #                         stored += 1
                            
    #         if data.startswith('BIOPHOTO'):
    #             entries = data.split('BIOPHOTO ')[1:]  # Process User entries
    #             for entry in entries:
    #                 if entry.strip():
    #                     try:
    #                         photo_data = self._parse_data(entry)
    #                         stored += self._store_biophoto_data(photo_data, device.id)
    #                     except Exception as e:
    #                         _logger.error(str(e))
    #                         stored += 1
    #         elif data.startswith('FP'):
    #             entries = data.split('FP ')[1:]  # Process FP entries
    #             for entry in entries:
    #                 if entry.strip():  # Make sure to ignore empty entries
    #                     try:
    #                         fingerprint_data = self._parse_data(entry)
    #                         stored += self._store_fingerprint_data(fingerprint_data, device.id)
    #                     except Exception as e:
    #                         _logger.error(str(e))
    #                         stored += 1
    #         return wrappers.Response(response='OK: %s'%stored)

    #     if table == 'ATTLOG':
    #         data = request.httprequest.data.decode('utf-8')
    #         device_id = device.id
    #         query = """
    #         INSERT INTO sa_biometric_att (device_id, emp_code, punch_time, punch_state, punch_type)
    #         VALUES (%s, %s, %s::timestamp AT TIME ZONE '{tz}' AT TIME ZONE 'UTC', %s, %s)
    #         """
    #         lines = str(data).split('\n')
    #         values_list = [line.split('\t')[:4] for line in lines]
    #         values_list.pop()
    #         flat_values = []
    #         for values in values_list:
    #             flat_values.append([device_id] + values)
    #         request.env.cr.executemany(query.format(tz=device.tz), flat_values)
    #         request.env.cr.commit()
    #     return wrappers.Response(response='OK')



    @http.route(['/iclock/devicecmd/','/iclock/devicecmd.aspx/'], type='http', auth="public", csrf=False)
    def zk_devicecmd(self, **kw):
        # Decode the incoming data
        data = request.httprequest.data.decode('utf-8')
        lines = data.split('\n')  # Split into individual lines for multiple records
        accepted_count = 0  # Counter for successfully processed records
        device = request.env['sa.biometric.device'].sudo().search([('serial_no', '=', kw.get('SN', 'softatt'))])
        if not device:
            return wrappers.Response(content_type="text/plain", response=f"OK")
        for line in lines:
            if not line.strip():  # Skip empty lines
                continue
            # Parse each line as a separate record
            parsed_data = urllib.parse.parse_qs(line)
            cmd_id      = parsed_data.get('ID', [None])[0] or 0
            # Find the corresponding command
            command = device.cmd_ids.filtered(lambda x: int(cmd_id) in x.ids)
            if command:
                # Log the received data and command content
                device.message_post(body=f"{line} : {command.content}\n")
                # Remove the command after processing
                command.unlink()
                accepted_count += 1  # Increment accepted record count
        # Return the response with the count of accepted records
        return wrappers.Response(content_type="text/plain", response=f"OK")



    @http.route(['/iclock/getrequest/', '/iclock/getrequest.aspx/'], type='http', auth="public", csrf=False)
    def zk_getrequest(self, **kw):
        d_obj=request.env['sa.biometric.device'].sudo()
        device = d_obj.search([('serial_no','=',kw.get('SN','softatt'))])
        commands= device.mapped('cmd_ids.command')[:5]
        text='OK'
        if device:
            try:
                ip_address = request.httprequest.remote_addr
                log_data = {'device_id': device.id, 'ip_address': ip_address}
                request.env['sa.biometric.log'].sudo().create(log_data)
            except Exception as e:
                _logger.error(str(e))
        if commands:
            text="".join(commands)
        return wrappers.Response(content_type="text/plain", response=text)


    def _parse_user_data(self, entry):
        """Parse the raw user data string into a dictionary."""
        parsed_data = {}
        entry       = entry.replace('USER ','')
        fields      = entry.split('\t')
        for field in fields:
            if '=' in field:
                key_value = field.split('=', 1)  # Ensure only the first '=' is split
                key = key_value[0].strip()  # The key is the first part
                value = key_value[1].strip() if len(key_value) > 1 else ''  # The value is the second part or empty if missing
                parsed_data[key] = value
        return parsed_data
    
    def _store_biometric_user(self, user_data, device):
        """Store the parsed user data into the 'sa.biometric.device.user' model."""
        pin_value = user_data.get('PIN')
        # Define the user data dictionary
        user_data_dict = {
            'device_id'     : device,
            'pin'           : user_data.get('PIN'),
            'name'          : user_data.get('Name'),
            'pri'           : user_data.get('Pri'),
            'passwd'        : user_data.get('Passwd'),
            'card'          : user_data.get('Card'),
            'grp'           : user_data.get('Grp'),
            'tz_info'       : user_data.get('TZ'),
            'verify_mode'   : user_data.get('Verify'),
            'vice_card'     : user_data.get('ViceCard'),
            'note'          : None,
        }
        # Check if the pin exists on the specific device
        user = None
        if pin_value:
            user = request.env['sa.biometric.device.user'].sudo().search([
                ('pin', '=', int(pin_value)),
                ('device_id.id', '=', device)  # Ensure the user exists on the specified device
            ], limit=1)
        if user:
            # Overwrite the existing user's data
            user.write(user_data_dict)
            return 1
        if device:
            # Create a new user if no existing user found for that device
            request.env['sa.biometric.device.user'].sudo().create(user_data_dict)
            return 1

            
            
    def _parse_data(self, entry):
        """Parse the raw fingerprint data string into a dictionary."""
        parsed_data = {}
        fields = entry.split('\t')  # Fields are separated by horizontal tabs        
        for field in fields:
            if '=' in field:
                key_value = field.split('=', 1)  # Ensure only the first '=' is split
                key = key_value[0].strip()
                value = key_value[1].strip() if len(key_value) > 1 else ''
                parsed_data[key] = value
        return parsed_data
    
    def _store_fingerprint_data(self, fingerprint_data, device_id):
        """Store the parsed fingerprint data into the 'sa.biometric.device.user.fpt' model."""
        user = request.env['sa.biometric.device.user'].sudo().search([
            ('pin', '=', int(fingerprint_data.get('PIN'))),
            ('device_id', '=', device_id),], limit=1)
        if user:
            fpt = request.env['sa.biometric.device.user.fpt'].sudo().search([('fid', '=', int(fingerprint_data.get('FID'))),
                                                                             ('pin', '=', int(fingerprint_data.get('PIN'))),
                                                                             ('device_id.id', '=', device_id)], limit=1)
            if fpt:
                fpt.sudo().write({
                    'size': int(fingerprint_data.get('Size')) if fingerprint_data.get('Size').isdigit() else 0,
                    'valid': fingerprint_data.get('Valid') == '1',
                    'tmp': fingerprint_data.get('TMP'),
                })
            else:
                request.env['sa.biometric.device.user.fpt'].sudo().create({
                    'user_id': user.id,
                    'pin': fingerprint_data.get('PIN'),
                    'fid': fingerprint_data.get('FID'),
                    'size': int(fingerprint_data.get('Size')) if fingerprint_data.get('Size').isdigit() else 0,
                    'valid': fingerprint_data.get('Valid') == '1',
                    'tmp': fingerprint_data.get('TMP'),
                })
            return 1
            
    def _store_unified_data(self, unified_tmp_data, device_id):
        """Store the parsed biometric template data into the 'sa.biometric.device.unified_tmp' model."""
        try:            
            # Fetch and validate the 'Pin' value
            pin = unified_tmp_data.get('Pin')
            if not pin or not pin.isdigit():
                return 0            
            pin = int(pin)

            # Check if the user exists by PIN
            user = request.env['sa.biometric.device.user'].sudo().search([
                ('pin', '=', pin),
                ('device_id.id', '=', device_id),
                ], limit=1)
            if not user:
                return 0

            # Prepare the dictionary with all the data
            unified_data = {
                'pin': pin,
                'user_id': user.id,
                'no': int(unified_tmp_data.get('No', 0)),
                'index': int(unified_tmp_data.get('Index', 0)),
                'duress': int(unified_tmp_data.get('Duress', 0)),
                'bio_type': unified_tmp_data.get('Type', 0),
                'major_ver': int(unified_tmp_data.get('MajorVer', 0)),
                'minor_ver': int(unified_tmp_data.get('MinorVer', 0)),
                'format': int(unified_tmp_data.get('Format', 0)),
                'tmp': unified_tmp_data.get('Tmp') or '',
            }
            unified_tmp_obj = request.env['sa.biometric.device.unified_tmp']
            # Search for an existing template based on PIN and Index
            unified_template = unified_tmp_obj.sudo().search(
                [('pin', '=', pin), 
                 ('device_id', '=', device_id),
                 ('index', '=', unified_data['index']),
                 ('is_biophoto', '=', False),
                 ], limit=1
            )
            if unified_template:
                # Update existing template
                unified_template.sudo().write(unified_data)
            else:
                # Create a new template entry
                unified_tmp_obj.sudo().create(unified_data)
            return 1
        except ValueError as ve:
            _logger.error(f"ValueError in '_store_unified_data': {ve}")
            return 0
        except Exception as e:
            _logger.error(f"Unexpected error in '_store_unified_data': {e}")
            return 0

    def _store_biophoto_data(self, biophoto_data, device_id):
        """Store the parsed biometric photo data into the 'sa.biometric.device.biophoto' model."""
        try:
            # Fetch and validate the 'Pin' value
            pin = biophoto_data.get('PIN')
            if not pin or not pin.isdigit():
                return 0
            pin = int(pin)

            # Check if the user exists by PIN
            user = request.env['sa.biometric.device.user'].sudo().search([
                ('pin', '=', pin),
                ('device_id', '=', device_id),
                ], limit=1)
            if not user:
                return 0

            # Prepare the dictionary with all the data
            biophoto_record_data = {
                'pin': pin,
                'user_id': user.id,
                'no': int(biophoto_data.get('No', 0)),
                'index': int(biophoto_data.get('Index')),
                'content': biophoto_data.get('Content'),
                'filename': biophoto_data.get('FileName'),
                'bio_type': biophoto_data.get('Type'),
                'size': int(biophoto_data.get('Size', 0)),
                'is_biophoto': True,
                
            }
            biophoto_obj = request.env['sa.biometric.device.unified_tmp']
            # Search for an existing biophoto entry based on PIN
            existing_biophoto = biophoto_obj.sudo().search([
                ('pin', '=', pin),
                ('device_id', '=', device_id),
                ('index', '=', biophoto_data['Index']),
                ('is_biophoto', '=', True)], limit=1)
            if existing_biophoto:
                # Update existing biophoto entry
                existing_biophoto.sudo().write(biophoto_record_data)
                _logger.info(f"Updated biophoto for PIN {pin}.")
            else:
                # Create a new biophoto entry
                biophoto_obj.sudo().create(biophoto_record_data)
                _logger.info(f"Created new biophoto entry for PIN {pin}.")
            return 1
        except ValueError as ve:
            _logger.error(f"ValueError in '_store_biophoto_data': {ve}")
            return 0
        except Exception as e:
            _logger.error(f"Unexpected error in '_store_biophoto_data': {e}")
            return 0
