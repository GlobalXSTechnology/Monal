from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.model
    def create(self, vals):
        leave = super(HrLeave, self).create(vals)
        leave._check_short_leave_constraints()
        return leave

    def _check_short_leave_constraints(self):
        for leave in self:
            leave_type = leave.holiday_status_id
            if leave_type.name != 'Short Leave':
                continue  # Apply only for short leave

            # 1. Check only one short leave allowed per month
            month_start = leave.request_date_from.replace(day=1)
            month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

            existing_leaves = self.search_count([
                ('id', '!=', leave.id),
                ('employee_id', '=', leave.employee_id.id),
                ('holiday_status_id', '=', leave.holiday_status_id.id),
                ('request_date_from', '>=', month_start),
                ('request_date_from', '<=', month_end),
                ('state', 'in', ['draft', 'confirm', 'validate']),  # include current leaves
            ])
            if existing_leaves >= 1 or leave.number_of_days > 1:
                raise ValidationError(_("Only one short leave is allowed per month."))

            # 2. Leave should be only one day
            if leave.request_date_from != leave.request_date_to:
                raise ValidationError(_("Short leave must be for a single day only."))

            # 3. Work hours should be at least 6 on that day
            start_dt = datetime.combine(leave.request_date_from, datetime.min.time())
            end_dt = datetime.combine(leave.request_date_from, datetime.max.time())

            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', leave.employee_id.id),
                ('check_in', '>=', start_dt),
                ('check_in', '<=', end_dt),
            ], limit=1, order='check_in desc')

            if not attendance:
                raise ValidationError(_("No attendance found for this day. Cannot approve short leave."))

            if attendance.check_out:
                if attendance.worked_hours < 6:
                    raise ValidationError(_("Worked hours on this day are less than 6. Cannot approve short leave."))
            else:
                now = fields.Datetime.now()
                worked_duration = (now - attendance.check_in).total_seconds() / 3600.0
                if worked_duration >= 6:
                    attendance.check_out = now
                    attendance._compute_worked_hours()
                else:
                    raise ValidationError(_("You haven't completed 6 working hours yet. Cannot approve short leave."))
