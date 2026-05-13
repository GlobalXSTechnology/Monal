from odoo.tools import date_utils

import pytz

from calendar import monthrange
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from operator import itemgetter
from pytz import timezone
from random import randint

from odoo.http import request
from odoo import models, fields, api, exceptions, _
from odoo.addons.resource.models.utils import Intervals
from odoo.osv.expression import AND, OR
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError
from odoo.tools import convert, format_duration, format_time, format_datetime
from odoo.tools.float_utils import float_compare
class SaAttendance(models.Model):
    _inherit = "hr.attendance"
    
    location_id         = fields.Many2one('hr.work.location', pre_compute=True,compute="_compute_location", string="Location", tracking=True, store=True)
    resource_calendar_id= fields.Many2one('resource.calendar', string="Assigned Shift", compute="_compute_assigned_shift", store=True, tracking=True)
    department_id       = fields.Many2one(related="employee_id.department_id", readonly=True, store=True, tracking=True)
    late_minutes        = fields.Integer(readonly=False, pre_compute=True,  store=True, compute="_compute_late_minutes", tracking=True)
    device_code = fields.Integer('Device ID',store=True)
    @api.depends("employee_id")
    def _compute_location(self):
        for r in self:
            r.location_id           =r.employee_id.work_location_id.id      if r.employee_id.work_location_id\
                else None
            
    @api.depends("employee_id")
    def _compute_assigned_shift(self):
        for r in self:
            r.resource_calendar_id  =r.employee_id.resource_calendar_id.id  if r.employee_id.resource_calendar_id\
                else None

    @api.model_create_multi
    def create(self, vals_list):
        result = super(SaAttendance, self).create(vals_list)
        result._compute_late_minutes()
        return result

    @api.depends("employee_id", "check_in")
    def _compute_late_minutes(self):
        for r in self:
            r.late_minutes = 0
            if not r.resource_calendar_id or not r.check_in or not r.employee_id:
                r.late_minutes = 0
                continue
            if not r.employee_id.tz:
                r.late_minutes = 0
                continue
            working_hours   = r.resource_calendar_id
            check_in        = date_utils._softatt_localize(r.check_in, r.employee_id.tz)
            current_day     = check_in.weekday()
            result          = working_hours._softatt_get_shift_start_and_end_bot(current_day, check_in)
            if not result:
                r.late_minutes = 0
                return
            shift_start_datetime    = result[0]
            time_difference         = check_in - shift_start_datetime 
            difference_in_minutes   = time_difference.total_seconds() / 60
            r.late_minutes          = difference_in_minutes

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            pass
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            # last_attendance_before_check_in = self.env['hr.attendance'].search([
            #     ('employee_id', '=', attendance.employee_id.id),
            #     ('check_in', '<=', attendance.check_in),
            #     ('id', '!=', attendance.id),
            # ], order='check_in desc', limit=1)
            # if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
            #     raise exceptions.ValidationError(
            #         _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s",
            #           empl_name=attendance.employee_id.name,
            #           datetime=format_datetime(self.env, attendance.check_in, dt_format=False)))
            #
            # if not attendance.check_out:
            #     # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
            #     no_check_out_attendances = self.env['hr.attendance'].search([
            #         ('employee_id', '=', attendance.employee_id.id),
            #         ('check_out', '=', False),
            #         ('id', '!=', attendance.id),
            #     ], order='check_in desc', limit=1)
            #     if no_check_out_attendances:
            #         raise exceptions.ValidationError(
            #             _("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s",
            #               empl_name=attendance.employee_id.name,
            #               datetime=format_datetime(self.env, no_check_out_attendances.check_in, dt_format=False)))
            # else:
            #     # we verify that the latest attendance with check_in time before our check_out time
            #     # is the same as the one before our check_in time computed before, otherwise it overlaps
            #     last_attendance_before_check_out = self.env['hr.attendance'].search([
            #         ('employee_id', '=', attendance.employee_id.id),
            #         ('check_in', '<', attendance.check_out),
            #         ('id', '!=', attendance.id),
            #     ], order='check_in desc', limit=1)
            #     if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
            #         raise exceptions.ValidationError(
            #             _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s",
            #               empl_name=attendance.employee_id.name,
            #               datetime=format_datetime(self.env, last_attendance_before_check_out.check_in,
            #                                        dt_format=False)))


