# -*- coding: utf-8 -*-

import base64
from datetime import datetime, timedelta
from odoo import models, fields, api
import pytz
import logging
_logger = logging.getLogger(__name__)

all_timezones = [('-750', 'Etc/GMT-12:30'), ('-12', 'Etc/GMT-12'), ('-690', 'Etc/GMT-11:30'), ('-11', 'Etc/GMT-11'), ('-630', 'Etc/GMT-10:30'), ('-10', 'Etc/GMT-10'), ('-570', 'Etc/GMT-9:30'), ('-9', 'Etc/GMT-9'), ('-510', 'Etc/GMT-8:30'), ('-8', 'Etc/GMT-8'), ('-450', 'Etc/GMT-7:30'), ('-7', 'Etc/GMT-7'), ('-390', 'Etc/GMT-6:30'), ('-6', 'Etc/GMT-6'), ('-330', 'Etc/GMT-5:30'), ('-5', 'Etc/GMT-5'), ('-270', 'Etc/GMT-4:30'), ('-4', 'Etc/GMT-4'), ('-210', 'Etc/GMT-3:30'), ('-3', 'Etc/GMT-3'), ('-150', 'Etc/GMT-2:30'), ('-2', 'Etc/GMT-2'), ('-90', 'Etc/GMT-1:30'), ('-1', 'Etc/GMT-1'), ('-30', 'Etc/GMT-0:30'), ('0', 'Etc/GMT'), ('30', 'Etc/GMT+0:30'), ('1', 'Etc/GMT+1'), ('90', 'Etc/GMT+1:30'), ('2', 'Etc/GMT+2'), ('3', 'Etc/GMT+3'), ('210', 'Etc/GMT+3:30'), ('4', 'Etc/GMT+4'), ('270', 'Etc/GMT+4:30'), ('5', 'Etc/GMT+5'), ('330', 'Etc/GMT+5:30'), ('6', 'Etc/GMT+6'), ('390', 'Etc/GMT+6:30'), ('7', 'Etc/GMT+7'), ('450', 'Etc/GMT+7:30'), ('8', 'Etc/GMT+8'), ('510', 'Etc/GMT+8:30'), ('9', 'Etc/GMT+9'), ('570', 'Etc/GMT+9:30'), ('10', 'Etc/GMT+10'), ('630', 'Etc/GMT+10:30'), ('11', 'Etc/GMT+11'), ('690', 'Etc/GMT+11:30'), ('12', 'Etc/GMT+12'), ('750', 'Etc/GMT+12:30'), ('13', 'Etc/GMT+13'), ('810', 'Etc/GMT+13:30')]


_tzs = [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]
def _tz_get(self):
    return _tzs


def _softatt_localize(utc_time, timezone):
    old_tz  = pytz.timezone('UTC')
    new_tz  = pytz.timezone(timezone)
    dt      = old_tz.localize(utc_time).astimezone(new_tz).replace(tzinfo=None)
    return dt




class SaBiometricCmd(models.Model):
    _name           = 'sa.biometric.cmd'
    _description    = 'Biometric commands'

    device_id       = fields.Many2one('sa.biometric.device')
    content         = fields.Char(string='Content', required=True)
    command         = fields.Char(compute='_compute_command', store=True)
    transfare_time  = fields.Datetime(string='Transfare Time')

    @api.depends('content')
    def _compute_command(self):
        for r in self:
            r.command = None
            if r.id and r.content:
                r.command = "".join(("C:",str(r.id),":",r.content,"\n"))
                
                


class SaBiometricDevice(models.Model):
    _name           = 'sa.biometric.area'
    _description    = 'Biometric Location'
    
    name            = fields.Char()
    
class SaBiometricDeviceLog(models.Model):
    _name = 'sa.biometric.log'
    _description = 'Biometric log'
    _order = 'create_date desc'

    ip_address      = fields.Char(required=True)
    device_id       = fields.Many2one('sa.biometric.device')
    
    @api.model
    def delete_old_signals(self):
        # Define the logic to delete old signals here
        threshold_days = 3
        threshold_date = fields.Datetime.now() - timedelta(days=threshold_days)
        old_logs = self.search([('create_date', '<', threshold_date)])
        old_logs.unlink()
        
        
class UserDevices(models.Model):
    _inherit = 'res.users'
    device_ids = fields.Many2many('sa.biometric.device')
    

    
class SaBiometricDevice(models.Model):
    _inherit = ['sa.biometric.device']

    name            = fields.Char(tracking=1)
    serial_no       = fields.Char(required=True)
    area_id         = fields.Many2one('sa.biometric.area',tracking=1)
    cmd_ids         = fields.One2many('sa.biometric.cmd', 'device_id', string='Commands')
    att_ids         = fields.One2many('sa.biometric.att', 'device_id', string='Log')
    timezone        = fields.Selection(all_timezones, default="3", tracking=1, required=True)
    tz              = fields.Selection(_tz_get,'timezone')
    tz_offset       = fields.Char(compute='_compute_tz_offset', string='Timezone offset', invisible=True)
    state           = fields.Selection([('active','Active'),('inactive','Inactive'), ('pending','Pending')], tracking=1, compute='_compute_device_state', store=True)
    last_connection = fields.Datetime()
    log_ids         = fields.One2many('sa.biometric.log', 'device_id')
    device_user_ids = fields.One2many('sa.biometric.device.user', 'device_id')
    device_user_count = fields.Integer(compute='_compute_device_user_count', string='User Count')
    last_check_time = fields.Datetime()
    _sql_constraints= [('unique_serial_no', 'unique(serial_no)', 'Serial Number must be unique!')]
    attendance_count = fields.Integer(string='Attendance Records', compute='_compute_attendance_count')

    def _compute_attendance_count(self):
        for device in self:
            device.attendance_count = self.env['sa.biometric.att'].search_count([('device_id', '=', device.id)])

    def _compute_device_user_count(self):
        for device in self:
            device.device_user_count = len(device.device_user_ids)
            
    def _compute_device_state(self):
        for record in self:
            most_recent_log = record.log_ids[:1]
            if most_recent_log:
                record.last_connection = most_recent_log.create_date
                if most_recent_log.create_date >= fields.Datetime.now() - timedelta(minutes=5):
                    record.state = 'active'
                else:
                    record.state = 'inactive'
            else:
                record.state = 'inactive'
                record.last_connection = False
            record.last_check_time = fields.Datetime.now()
            
                
    @api.model
    def _cron_update_device_state(self, batch_size=20):
        records             = self.search(['|',('last_check_time','=',False), ('last_check_time','<=',fields.Datetime.now() - timedelta(minutes=5))], limit=batch_size+1)
        next_cron_trigger   = False
        if len(records) > batch_size:
            next_cron_trigger= True
        for rec in records[:batch_size]:
            try:
                rec._compute_device_state()
            except Exception as e:
                rec.env.cr.rollback()
                rec.message_post(body=str(e))
                rec.env.cr.commit() 
                continue
            rec.env.cr.commit()
        if  next_cron_trigger:
            _logger.info(f"Trigger Next 'Update device state' Cron - {len(records)}")
            self.env.ref('softatt_attendance_zk_extension.ir_cron_update_device_state')._trigger()
        return

    def update_device_state(self):
        self._compute_device_state()
        
 
    @api.depends('tz')
    def _compute_tz_offset(self):
        for device in self:
            device.tz_offset = datetime.now(pytz.timezone(device.tz or 'GMT')).strftime('%z')

    
    def action_info(self):
        for r in self:
            if not r.cmd_ids.filtered(lambda x: x.content=="INFO"):
                r.cmd_ids.create({'device_id':r.id,'content':"INFO"})
            
    def action_reboot(self):
        for r in self:
            if not r.cmd_ids.filtered(lambda x: x.content=="REBOOT"):
                r.cmd_ids.create({'device_id':r.id,'content':"REBOOT"})
                
    def action_check(self):
        for r in self:
            if not r.cmd_ids.filtered(lambda x: x.content=="CHECK"):
                r.cmd_ids.create({'device_id':r.id,'content':"CHECK"})
                

    def action_download_users(self):
        for r in self:
            if not r.cmd_ids.filtered(lambda x: x.content.startswith(f"DATA QUERY USERINFO")):
                command_content = f"DATA QUERY USERINFO"
                r.cmd_ids.create({'device_id': r.id, 'content': command_content})
                _logger.info(f"Command sent to device --------- {command_content}")

    def _custom_log(self, start_time=fields.datetime.now() - timedelta(days=1), end_time=fields.datetime.now() + timedelta(days=1)):
        for r in self:
            # Format the start and end times
            formatted_start_time = _softatt_localize(start_time,r.tz).strftime("%Y-%m-%d %H: %M: %S")
            formatted_end_time = _softatt_localize(end_time,r.tz).strftime("%Y-%m-%d %H: %M: %S")
            # Create the ATTLOG command if it doesn't already exist
            if not r.cmd_ids.filtered(lambda x: x.content.startswith(f"DATA QUERY ATTLOG StartTime")):
                command_content = f"DATA QUERY ATTLOG StartTime={formatted_start_time}\tEndTime={formatted_end_time}"
                r.cmd_ids.create({'device_id': r.id, 'content': command_content})
                
class SABiometricDeviceUser(models.Model):
    _name = 'sa.biometric.device.user'
    _description = 'Biometric Device User'

    device_id = fields.Many2one('sa.biometric.device', string='Device', required=True, ondelete='cascade')
    pin = fields.Char(string='PIN')
    name = fields.Char(string='Name')
    pri = fields.Selection([('0',"Normal User"), ('14',"Super Admin")], string='Role', required=True, default='0')
    passwd = fields.Char(string='Password')
    card = fields.Char(string='Card Number')
    grp = fields.Char(string='Group', default='1')
    tz_info = fields.Char(string='Timezone Information', default='0000000100000000')
    verify_mode = fields.Char(string='Verification Mode', default='-1')
    vice_card = fields.Char(string='Vice Card')
    employee_id = fields.Many2one('hr.employee', string='Employee', compute='_compute_employee_id')
    
    fpt_ids     = fields.One2many('sa.biometric.device.user.fpt', 'user_id', string='Registered Fingerprints')
    face_ids    = fields.One2many('sa.biometric.device.user.face', 'user_id', string='Registered Faces')
    biodata_ids    = fields.One2many('sa.biometric.device.unified_tmp', 'user_id', string='Registered Bio Info')
    note        = fields.Char()
    
    
    def write(self, vals):
        if 'note' not in vals:
            vals['note'] = "There's unsynced data. Please update the user in the device."
        return super(SABiometricDeviceUser, self).write(vals)
    
    
    def _compute_employee_id(self):
        for user in self:
            user.employee_id = self.env['sa.attendance.employee.code'].search([('code', '=', user.pin), ('device_id.id', '=', user.device_id.id)], limit=1).employee_id
        
        

    def open_users_lookup_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Similar Users',
            'res_model': 'sa.biometric.device.user',
            'view_mode': 'list,form',
            'target': 'new',
            'context': {'search_default_pin': self.pin}
        }

    def open_biometric_enrollment_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Biometric Enrollment',
            'res_model': 'biometric.enrollment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_user_id': self.id,
            }
        }
    
    def open_sync_user_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sync Biometric Users',
            'res_model': 'sync.biometric.user.device.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_user_ids': self.ids,
            }
        }
    def enroll_userbio_command(self, bio_type='1', fid=6):
        SP = ' '  # Space
        HT = '\t'  # Horizontal Tab
        for user in self:
            if user.pin:
                if bio_type == '1':
                    command_content = f"ENROLL_FP{HT}PIN={user.pin}{HT}FID={fid}{HT}CardNo={HT}RETRY=3{HT}OVERWRITE=1"
                else:
                    command_content = f"ENROLL_BIO{HT}TYPE={bio_type}{HT}PIN={user.pin}{HT}FID={fid}{HT}CardNo={HT}RETRY=3{HT}OVERWRITE=1"
                # Create the command for the device
                user.device_id.cmd_ids.create({
                    'device_id': user.device_id.id,
                    'content': command_content
                })
                _logger.info(f"Command {command_content} {user.pin} issued to device {user.device_id.name}")

    def get_userinfo_command(self, device_id=False):
        SP = ' '  # Space
        HT = '\t'  # Horizontal Tab
        for user in self:
            device_id = device_id or user.device_id
            if user.pin:
                command_content = f"DATA QUERY USERINFO{HT}PIN={user.pin}"
                # Create the command for the device
                device_id.cmd_ids.create({
                    'device_id': device_id.id,
                    'content': command_content
                })
                _logger.info(f"Command {command_content} {user.pin} issued to device {device_id.name}")
                
    def delete_userinfo_command(self):
        for user in self:
            if user.pin:
                # Create the DELETE command for the user
                command_content = f"DATA DELETE USERINFO PIN={user.pin}"
                # Create the command for the device
                user.device_id.cmd_ids.create({
                    'device_id': user.device_id.id,
                    'content': command_content
                })
                _logger.info(f"Command {command_content} {user.pin} issued to device {user.device_id.name}")
                user.unlink()
                
    def update_userinfo_command(self, device_id=False):
        SP = ' '  # Space
        HT = '\t'  # Horizontal Tab
        for user in self:
            command = f"DATA{SP}UPDATE{SP}USERINFO{SP}"
            command += f"PIN={user.pin}{HT}Name={user.name}{HT}"
            command += f"Pri={user.pri}{HT}Passwd={user.passwd}{HT}"
            command += f"Card={user.card}{HT}Grp={user.grp}{HT}"
            command += f"TZ={user.tz_info}{HT}Verify={user.verify_mode}{HT}"
            command += f"ViceCard={user.vice_card}"
            device_id = device_id or user.device_id
            user.note = None
            user.device_id.cmd_ids.create({'device_id': device_id.id, 'content': command})
            
            user.fpt_ids.update_fingerprint_command(device_id)
            user.biodata_ids.update_unified_tmp_command(device_id)
            user.get_userinfo_command(device_id)


class SyncBiometricUserDeviceWizard(models.TransientModel):
    _name = 'sync.biometric.user.device.wizard'
    _description = 'Sync Biometric User Info Across Devices'

    device_ids = fields.Many2many(
        'sa.biometric.device',
        string='Devices',
        required=True
    )
    user_ids = fields.Many2many(
        'sa.biometric.device.user',
        string='Users',
        required=True
    )

    def action_confirm(self):
        """Loop through the selected devices and users, and call the update_userinfo_command method."""
        for device in self.device_ids:
            self.user_ids.update_userinfo_command(device_id=device)
        return {'type': 'ir.actions.act_window_close'}



class BiometricGetUserWizard(models.TransientModel):
    _name = 'biometric.enrollment.wizard'
    _description = 'Biometric Enrollment Wizard'



class BiometricEnrollmentWizard(models.TransientModel):
    _name = 'biometric.enrollment.wizard'
    _description = 'Biometric Enrollment Wizard'

    bio_type = fields.Selection([
        ('0', 'General Template'),
        ('1', 'Fingerprint'),
        ('2', 'Face'),
        ('3', 'Voice'),
        ('4', 'Iris'),
        ('5', 'Retina'),
        ('6', 'Palm Vein'),
        ('7', 'Finger Vein'),
        ('8', 'Palm Print'),
        ('9', 'Visible Light Face'),
    ], string="Biometric Type", required=True, default='1')

    finger_id = fields.Selection([
        ('0', '0 - Left Thumb'),
        ('1', '1 - Left Index Finger'),
        ('2', '2 - Left Middle Finger'),
        ('3', '3 - Left Ring Finger'),
        ('4', '4 - Left Little Finger'),
        ('5', '5 - Right Thumb'),
        ('6', '6 - Right Index Finger'),
        ('7', '7 - Right Middle Finger'),
        ('8', '8 - Right Ring Finger'),
        ('9', '9 - Right Little Finger'),
    ], string="Finger", help="Select the finger for fingerprint enrollment")

    user_id = fields.Many2one('sa.biometric.device.user', string="User", required=True)
    device_id = fields.Many2one(related='user_id.device_id', string="Device", readonly=True)

    def action_confirm(self):
        """Run the enrollment command based on user selection."""
        for wizard in self:
            fid = wizard.finger_id if wizard.bio_type == '1' else 6  # Default FID is 6 unless fingerprint
            wizard.user_id.enroll_userbio_command(bio_type=wizard.bio_type, fid=fid)

    
class SABiometricDeviceUserFPT(models.Model):
    _name = 'sa.biometric.device.user.fpt'
    _description = 'Biometric Device User Fingerprint'

    user_id = fields.Many2one('sa.biometric.device.user', string='User', required=True, ondelete='cascade')
    device_id = fields.Many2one('sa.biometric.device',  related='user_id.device_id', string='Device')
    
    pin = fields.Char(string='User PIN', readonly=True)
    fid = fields.Char(string='Fingerprint ID')
    size = fields.Integer(string='Template Size')
    valid = fields.Boolean(string='Is Valid')
    tmp = fields.Text(string='Fingerprint Template (Base64)')
    
    def update_fingerprint_command(self, device_id=False):
        """Create command string for updating fingerprint template."""
        SP = ' '  # Space
        HT = '\t'  # Horizontal Tab
        for fingerprint in self:
            device_id = device_id or fingerprint.device_id
            command = f"DATA{SP}UPDATE{SP}FINGERTMP{SP}"
            command += f"PIN={fingerprint.pin}{HT}FID={fingerprint.fid}{HT}"
            command += f"Size={fingerprint.size}{HT}Valid={1 if fingerprint.valid else 0}{HT}"
            command += f"TMP={fingerprint.tmp}"
            fingerprint.device_id.cmd_ids.create({'device_id': device_id.id, 'content': command})
            
    def delete_fingerprint_command(self):
        """Create command string for deleting fingerprint and then unlink it."""
        SP = ' '  # Space
        HT = '\t'  # Horizontal Tab
        for fingerprint in self:
            # Create DELETE command for the fingerprint
            command = f"DATA{SP}DELETE{SP}FINGERTMP{SP}FID={fingerprint.fid}"
            fingerprint.device_id.cmd_ids.create({'device_id': fingerprint.device_id.id, 'content': command})
            _logger.info(f"Fingerprint with PIN {fingerprint.pin} and FID {fingerprint.fid} deleted from the device.")
            # Unlink the fingerprint record
            fingerprint.unlink()
            
            


class SABiometricDeviceUnifiedTmp(models.Model):
    _name = 'sa.biometric.device.unified_tmp'
    _description = 'Unified Biometric Template Data'

    pin = fields.Integer(string="PIN", required=True)
    no = fields.Integer(string="No")
    index = fields.Integer(string="Index", required=True)
    valid = fields.Boolean(string="Valid", default=False)
    duress = fields.Boolean(string="Duress", default=False)
    bio_type = fields.Integer(string="Bio Type")
    major_ver = fields.Integer(string="Major Version")
    minor_ver = fields.Integer(string="Minor Version")
    format = fields.Integer(string="Format")
    tmp = fields.Binary(string="Template Data")    
    user_id = fields.Many2one('sa.biometric.device.user', string='User', required=True, ondelete='cascade')
    device_id = fields.Many2one('sa.biometric.device', string="Device", related='user_id.device_id', store=True)
    bio_type = fields.Selection([
        ('0', 'General Template'),
        ('1', 'Fingerprint'),
        ('2', 'Face'),
        ('3', 'Voice'),
        ('4', 'Iris'),
        ('5', 'Retina'),
        ('6', 'Palm Vein'),
        ('7', 'Finger Vein'),
        ('8', 'Palm Print'),
        ('9', 'Visible Light Face'),
    ], string="Biometric Type", required=True, default='1')
    is_biophoto  = fields.Boolean(default=False)
    filename = fields.Char()
    size  = fields.Integer()
    content  = fields.Binary()
    
    

    def update_unified_tmp_command(self, device_id=False):
        """Create command string for updating unified template."""
        SP = ' '  # Space
        HT = '\t'  # Horizontal Tab
        for unified in self:
            # Use provided device_id or the record's device_id
            device_id = device_id or unified.device_id
            command = f"DATA{SP}UPDATE{SP}BIODATA{SP}" if not unified.is_biophoto else  f"DATA{SP}UPDATE{SP}BIOPHOTO{SP}"
            pin= 'PIN'if unified.is_biophoto else "Pin"
            command += f"{pin}={unified.pin}{HT}" 
            command += f"No={unified.no}{HT}" if not unified.is_biophoto else ""
            command += f"Index={unified.index}{HT}"
            command += f"Valid=1{HT}" if not unified.is_biophoto else ""
            command += f"Size={unified.size}{HT}" if unified.is_biophoto else ""
            command += f"Duress={unified.duress}{HT}" if not unified.is_biophoto else ""
            command += f"Type={unified.bio_type}{HT}"
            command += f"MajorVer={unified.major_ver}{HT}" if not unified.is_biophoto else ""
            command += f"MinorVer={unified.minor_ver}{HT}" if not unified.is_biophoto else ""
            _format = unified.format if unified.format else ""
            command += f"Format={_format}{HT}" if not unified.is_biophoto else ""
            command += f"FileName={unified.filename}{HT}" if unified.is_biophoto else ""
            
            # Decode binary data to a string and trim
            decoded_tmp = str(unified.tmp)[2:-1] if unified.tmp else ''
            decoded_content = str(unified.content)[2:-1] if unified.content else ''

            # Add the trimmed string to the command
            command += f"Tmp={decoded_tmp}" if not unified.is_biophoto else f"Content={decoded_content}"
            
            
            # Create the command for the device
            device_id.cmd_ids.create({
                'device_id': device_id.id,
                'content': command
            })
            _logger.info(f"Update unified template command created for PIN {unified.pin} on device {device_id.name}.")


    def delete_unified_tmp_command(self):
        """Create command string for deleting unified template and then unlink it."""
        SP = ' '  # Space
        HT = '\t'  # Horizontal Tab
        for unified in self:
            # Create DELETE command for the unified template
            command = f"DATA{SP}DELETE{SP}BIODATA{SP}FID={unified.index}"
            unified.device_id.cmd_ids.create({
                'device_id': unified.device_id.id,
                'content': command
            })
            _logger.info(f"Unified template with PIN {unified.pin} and FID {unified.index} deleted from the device.")
            # Unlink the unified template record
            unified.unlink()



class SABiometricDeviceUserFace(models.Model):
    _name = 'sa.biometric.device.user.face'
    _description = 'Biometric Device User face'

    user_id = fields.Many2one('sa.biometric.device.user', string='User', required=True, ondelete='cascade')
    device_id = fields.Many2one('sa.biometric.device',  related='user_id.device_id', string='Device')
    
    pin = fields.Char(string='User PIN', readonly=True)
    fid = fields.Char(string='Face ID')
    size = fields.Integer(string='Template Size')
    valid = fields.Boolean(string='Is Valid')
    tmp = fields.Text(string='Face Template (Base64)')
    
    def update_face_command(self, device_id=False):
        """Create command string for updating fingerprint template."""
        SP = ' '  # Space
        HT = '\t'  # Horizontal Tab
        for face in self:
            device_id = device_id or face.device_id
            command = f"DATA{SP}UPDATE{SP}FACETMP{SP}"
            command += f"PIN={face.pin}{HT}FID={face.fid}{HT}"
            command += f"Size={face.size}{HT}Valid={1 if face.valid else 0}{HT}"
            command += f"TMP={face.tmp}"
            face.device_id.cmd_ids.create({'device_id': device_id.id, 'content': command})
            
    def delete_face_command(self):
        """Create command string for deleting face and then unlink it."""
        SP = ' '  # Space
        HT = '\t'  # Horizontal Tab
        for face in self:
            # Create DELETE command for the face
            command = f"DATA{SP}DELETE{SP}FACETMP{SP}FID={face.fid}"
            face.device_id.cmd_ids.create({'device_id': face.device_id.id, 'content': command})
            _logger.info(f"Face template with PIN {face.pin} and FID {face.fid} deleted from the device.")
            # Unlink the face record
            face.unlink()
            