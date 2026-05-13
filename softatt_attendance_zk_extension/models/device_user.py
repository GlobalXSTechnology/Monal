
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

all_timezones = [('-750', 'Etc/GMT-12:30'), ('-12', 'Etc/GMT-12'), ('-690', 'Etc/GMT-11:30'), ('-11', 'Etc/GMT-11'), ('-630', 'Etc/GMT-10:30'), ('-10', 'Etc/GMT-10'), ('-570', 'Etc/GMT-9:30'), ('-9', 'Etc/GMT-9'), ('-510', 'Etc/GMT-8:30'), ('-8', 'Etc/GMT-8'), ('-450', 'Etc/GMT-7:30'), ('-7', 'Etc/GMT-7'), ('-390', 'Etc/GMT-6:30'), ('-6', 'Etc/GMT-6'), ('-330', 'Etc/GMT-5:30'), ('-5', 'Etc/GMT-5'), ('-270', 'Etc/GMT-4:30'), ('-4', 'Etc/GMT-4'), ('-210', 'Etc/GMT-3:30'), ('-3', 'Etc/GMT-3'), ('-150', 'Etc/GMT-2:30'), ('-2', 'Etc/GMT-2'), ('-90', 'Etc/GMT-1:30'), ('-1', 'Etc/GMT-1'), ('-30', 'Etc/GMT-0:30'), ('0', 'Etc/GMT'), ('30', 'Etc/GMT+0:30'), ('1', 'Etc/GMT+1'), ('90', 'Etc/GMT+1:30'), ('2', 'Etc/GMT+2'), ('3', 'Etc/GMT+3'), ('210', 'Etc/GMT+3:30'), ('4', 'Etc/GMT+4'), ('270', 'Etc/GMT+4:30'), ('5', 'Etc/GMT+5'), ('330', 'Etc/GMT+5:30'), ('6', 'Etc/GMT+6'), ('390', 'Etc/GMT+6:30'), ('7', 'Etc/GMT+7'), ('450', 'Etc/GMT+7:30'), ('8', 'Etc/GMT+8'), ('510', 'Etc/GMT+8:30'), ('9', 'Etc/GMT+9'), ('570', 'Etc/GMT+9:30'), ('10', 'Etc/GMT+10'), ('630', 'Etc/GMT+10:30'), ('11', 'Etc/GMT+11'), ('690', 'Etc/GMT+11:30'), ('12', 'Etc/GMT+12'), ('750', 'Etc/GMT+12:30'), ('13', 'Etc/GMT+13'), ('810', 'Etc/GMT+13:30')]




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