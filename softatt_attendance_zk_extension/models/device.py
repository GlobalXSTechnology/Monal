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
            if device.tz:
                timezone = pytz.timezone(device.tz)
                offset_seconds = timezone.utcoffset(datetime.now()).total_seconds()
                offset_minutes = int(offset_seconds / 60)  # Convert seconds to minutes
                
                # Convert to the required format
                if offset_minutes % 60 == 0:
                    formatted_offset = f"{offset_minutes // 60}"
                else:
                    formatted_offset = f"{offset_minutes}"

                device.tz_offset = formatted_offset
            else:
                device.tz_offset = "0"

    
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
                
                


class SaBiometricCmd(models.Model):
    _name           = 'sa.biometric.cmd'
    _description    = 'Biometric Commands'

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
    _description    = 'Device Location'
    
    name            = fields.Char()

class SaBiometricDeviceLog(models.Model):
    _name = 'sa.biometric.log'
    _description = 'Device Signal log'
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
