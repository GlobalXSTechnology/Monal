# -*- coding: utf-8 -*-

from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)

all_timezones = [('-750', 'Etc/GMT-12:30'), ('-12', 'Etc/GMT-12'), ('-690', 'Etc/GMT-11:30'), ('-11', 'Etc/GMT-11'), ('-630', 'Etc/GMT-10:30'), ('-10', 'Etc/GMT-10'), ('-570', 'Etc/GMT-9:30'), ('-9', 'Etc/GMT-9'), ('-510', 'Etc/GMT-8:30'), ('-8', 'Etc/GMT-8'), ('-450', 'Etc/GMT-7:30'), ('-7', 'Etc/GMT-7'), ('-390', 'Etc/GMT-6:30'), ('-6', 'Etc/GMT-6'), ('-330', 'Etc/GMT-5:30'), ('-5', 'Etc/GMT-5'), ('-270', 'Etc/GMT-4:30'), ('-4', 'Etc/GMT-4'), ('-210', 'Etc/GMT-3:30'), ('-3', 'Etc/GMT-3'), ('-150', 'Etc/GMT-2:30'), ('-2', 'Etc/GMT-2'), ('-90', 'Etc/GMT-1:30'), ('-1', 'Etc/GMT-1'), ('-30', 'Etc/GMT-0:30'), ('0', 'Etc/GMT'), ('30', 'Etc/GMT+0:30'), ('1', 'Etc/GMT+1'), ('90', 'Etc/GMT+1:30'), ('2', 'Etc/GMT+2'), ('3', 'Etc/GMT+3'), ('210', 'Etc/GMT+3:30'), ('4', 'Etc/GMT+4'), ('270', 'Etc/GMT+4:30'), ('5', 'Etc/GMT+5'), ('330', 'Etc/GMT+5:30'), ('6', 'Etc/GMT+6'), ('390', 'Etc/GMT+6:30'), ('7', 'Etc/GMT+7'), ('450', 'Etc/GMT+7:30'), ('8', 'Etc/GMT+8'), ('510', 'Etc/GMT+8:30'), ('9', 'Etc/GMT+9'), ('570', 'Etc/GMT+9:30'), ('10', 'Etc/GMT+10'), ('630', 'Etc/GMT+10:30'), ('11', 'Etc/GMT+11'), ('690', 'Etc/GMT+11:30'), ('12', 'Etc/GMT+12'), ('750', 'Etc/GMT+12:30'), ('13', 'Etc/GMT+13'), ('810', 'Etc/GMT+13:30')]




class SABiometricDeviceUserFPT(models.Model):
    _name = 'sa.biometric.device.user.fpt'
    _description = 'Biometric Device User Fingerprint'

    user_id     = fields.Many2one('sa.biometric.device.user', string='User', required=True, ondelete='cascade')
    device_id   = fields.Many2one('sa.biometric.device',  related='user_id.device_id', string='Device')
    
    pin         = fields.Char(string='User PIN', readonly=True)
    fid         = fields.Char(string='Fingerprint ID')
    size        = fields.Integer(string='Template Size')
    valid       = fields.Boolean(string='Is Valid')
    tmp         = fields.Text(string='Fingerprint Template (Base64)')
    
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

    pin         = fields.Integer(string="PIN", required=True)
    no          = fields.Integer(string="No")
    index       = fields.Integer(string="Index", required=True)
    valid       = fields.Boolean(string="Valid", default=False)
    duress      = fields.Boolean(string="Duress", default=False)
    bio_type    = fields.Integer(string="Bio Type")
    major_ver   = fields.Integer(string="Major Version")
    minor_ver   = fields.Integer(string="Minor Version")
    format      = fields.Integer(string="Format")
    tmp         = fields.Binary(string="Template Data")    
    user_id     = fields.Many2one('sa.biometric.device.user', string='User', required=True, ondelete='cascade')
    device_id   = fields.Many2one('sa.biometric.device', string="Device", related='user_id.device_id', store=True)
    bio_type    = fields.Selection([
        ('0', 'General Template'), ('1', 'Fingerprint'),
        ('2', 'Face'), ('3', 'Voice'), 
        ('4', 'Iris'), ('5', 'Retina'),
        ('6', 'Palm Vein'), ('7', 'Finger Vein'),
        ('8', 'Palm Print'), ('9', 'Visible Light Face')], string="Biometric Type", required=True, default='1')
    
    is_biophoto = fields.Boolean(default=False)
    filename    = fields.Char()
    size        = fields.Integer()
    content     = fields.Binary()
    
    

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
            
            decoded_tmp = str(unified.tmp)[2:-1] if unified.tmp else ''
            decoded_content = str(unified.content)[2:-1] if unified.content else ''
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