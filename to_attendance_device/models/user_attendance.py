from odoo import models, fields, api, _
from datetime import datetime, time, timedelta, date


class UserAttendance(models.Model):
    _name = 'user.attendance'
    _description = 'User Attendance'
    _order = 'timestamp DESC, user_id, status, attendance_state_id, device_id'

    date = fields.Date('Today Date', compute="_get_new_date",store=True)
    device_id = fields.Many2one('attendance.device', string='Attendance Device', required=True, ondelete='restrict',
                                index=True)
    user_id = fields.Many2one('attendance.device.user', string='Device User', required=True, ondelete='cascade',
                              index=True)
    timestamp = fields.Datetime(string='Timestamp', required=True, index=True)
    status = fields.Integer(string='Device Attendance State', required=True,
                            help='The state which is the unique number stored in the device to'
                                 ' indicate type of attendance (e.g. 0: Checkin, 1: Checkout, etc)')
    attendance_state_id = fields.Many2one('attendance.state', string='Odoo Attendance State',
                                          help='This technical field is to map the attendance'
                                               ' status stored in the device and the attendance status in Odoo',
                                          required=True, index=True)
    activity_id = fields.Many2one('attendance.activity', related='attendance_state_id.activity_id', store=True,
                                  index=True)
    hr_attendance_id = fields.Many2one('hr.attendance', string='HR Attendance', ondelete='set null',
                                       help='The technical field to link Device Attendance Data with Odoo\' Attendance Data',
                                       index=True)

    type = fields.Selection([('checkin', 'Check-in'),
                             ('checkout', 'Check-out')], string='Activity Type', related='attendance_state_id.type',
                            store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', related='user_id.employee_id', store=True,
                                  index=True)
    valid = fields.Boolean(string='Valid Attendance', index=True, readonly=False, default=False,
                           help="This field is to indicate if this attendance record is valid for HR Attendance Synchronization."
                                " E.g. The Attendances with Check out prior to Check in or the Attendances for users without employee"
                                " mapped will not be valid.")

    _sql_constraints = [
        ('unique_user_id_device_id_timestamp',
         'UNIQUE(user_id, device_id, timestamp)',
         "The Timestamp and User must be unique per Device"),
    ]

    @api.constrains('status', 'attendance_state_id')
    def constrains_status_attendance_state_id(self):
        for r in self:
            if r.status != r.attendance_state_id.code:
                raise (
                    _('Attendance Status conflict! The status number from device must match the attendance status defined in Odoo.'))

    @api.depends('timestamp')
    def _get_new_date(self):
        for rec in self:
            if rec.timestamp:
                date = datetime.strftime(rec.timestamp, '%Y-%m-%d %H:%M:%S')
                new_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()
                rec.date = new_date

    def is_valid(self):
        self.ensure_one()
        prev_att = self.search([('employee_id', '=', self.employee_id.id),
                                ('timestamp', '<', self.timestamp),
                                ('activity_id', '=', self.activity_id.id)], limit=1, order='timestamp DESC')
        next_att = self.search([('employee_id', '=', self.employee_id.id),
                                ('timestamp', '>', self.timestamp),('type', '=', 'checkout'),
                                ('activity_id', '=', self.activity_id.id)], limit=1, order='timestamp DESC')
        if not prev_att:
            valid = self.type == 'checkin' and True or False
        elif not next_att:
            valid = self.type == 'checkout' and True or False
        # if prev_att.status == 0 and next_att.status == 1 and self.status == 1:
        #     valid = True
        # if prev_att.status == 1 and next_att.status == 1 and self.status == 0:
        #     valid = True
        # if prev_att.status == 0 and next_att.status == 0 and self.status == 1:
        #     valid = True
        # if prev_att.status == 1 and next_att.status == 1:
        #     valid = False
        # if prev_att.status == 1 and next_att.status == 0:
        #     valid = True
        else:
            valid = prev_att.type != self.attendance_state_id.type and True or False
        return valid

    @api.model_create_multi
    def create(self, vals_list):
        attendances = super(UserAttendance, self).create(vals_list)
        valid_attendances = attendances.filtered(lambda att: att.is_valid())
        if valid_attendances:
            valid_attendances.write({'valid': True})
        return attendances
