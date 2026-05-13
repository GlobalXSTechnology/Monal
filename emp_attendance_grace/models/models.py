from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from pytz import timezone
import logging

_logger = logging.getLogger(__name__)


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    allowed_grace = fields.Boolean(string="Allowed Grace")


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    grace_hours = fields.Float(string="Grace Hours")


class ResCompany(models.Model):
    _inherit = 'res.company'

    basic_govt_wage = fields.Float(string="Basic Govt Wage")


class HRAttendance(models.Model):
    _inherit = 'hr.attendance'


    def _convert_gatepass_time(self, float_value):
        if not float_value:
            return 0.0
        hours = int(float_value)
        minutes = round((float_value - hours) * 100)
        return hours + (minutes / 60.0)

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        super(HRAttendance, self)._compute_worked_hours()

        for attendance in self:
            if attendance.worked_hours and attendance.employee_id:
                employee = attendance.employee_id
                shift = employee.resource_calendar_id
                if employee.allowed_grace and shift and shift.grace_hours > 0:
                    attendance.worked_hours += shift.grace_hours

            if attendance.employee_id and attendance.check_in and attendance.check_out:
                gatepasses = self.env['employee.gatepass'].search([
                    ('name', '=', attendance.employee_id.id),
                    ('time_in', '<=', attendance.check_out),
                    ('time_out', '>=', attendance.check_in),
                    ('gate_pass_type', 'in', ['personal']),
                ])
                _logger.info("Gatepassssssssssssssssss")
                _logger.info("Gatepassssssssssssssssss")
                _logger.info(gatepasses)

                if gatepasses:
                    total_gatepass_time = sum(self._convert_gatepass_time(gp.total_time) for gp in gatepasses)
                    _logger.info(attendance.worked_hours)
                    _logger.info(total_gatepass_time)
                    attendance.worked_hours = max(0.0, attendance.worked_hours - total_gatepass_time)
