from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.constrains('employee_id', 'request_date_from', 'request_date_to', 'holiday_status_id')
    def _check_paid_leave_attendance(self):
        for leave in self:
            if leave.holiday_status_id and leave.holiday_status_id.leave_encash:
                continue
            if not leave.employee_id or not leave.request_date_from:
                continue

            if leave.holiday_status_id.name and leave.holiday_status_id.name.lower() == 'unpaid':
                continue

            date_from = leave.request_date_from
            date_to = leave.request_date_to
            if isinstance(date_from, datetime):
                date_from = date_from.date()
            if isinstance(date_to, datetime):
                date_to = date_to.date()

            current_date = date_from
            while current_date <= date_to:
                start_day = datetime.combine(current_date, datetime.min.time())
                end_day = datetime.combine(current_date + timedelta(days=1), datetime.min.time())

                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', leave.employee_id.id),
                    ('check_in', '>=', start_day),
                    ('check_in', '<', end_day),
                ])

                total_work_hours = sum(a.worked_hours for a in attendances)

                if attendances and total_work_hours > 6:
                    raise ValidationError(_(
                        "Employee %s has worked %.2f hours on %s.\n"
                        "Paid leave cannot be taken for a day with more than 6 working hours.\n"
                        "Please use Unpaid Leave."
                    ) % (leave.employee_id.name, total_work_hours, current_date.strftime('%Y-%m-%d')))

                current_date += timedelta(days=1)
