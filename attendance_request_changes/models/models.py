from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AttendanceRequestChanges(models.Model):
    _inherit = 'attendance.adjustment'

    employee_id = fields.Many2one('hr.employee', string='Employee', compute='get_employee',store=True, readonly=False)
    worked_hours = fields.Float(string='Worked Hours', compute='get_worked_hours',store=True)

    @api.depends('emp_check_in','emp_check_out')
    def get_worked_hours(self):
        for rec in self:
            if rec.emp_check_in and rec.emp_check_out:
                duration = rec.emp_check_out - rec.emp_check_in
                rec.worked_hours = duration.total_seconds() / 3600
            else:
                rec.worked_hours = 0


    @api.depends('name')
    def get_employee(self):
        for rec in self:
            rec.employee_id = rec.name


    def revert_button(self):
        for rec in self:
            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', rec.name.id),
                ('check_in', '=', rec.emp_check_in),
                ('check_out', '=', rec.emp_check_out),
            ], limit=1)

            if not attendance:
                raise ValidationError(f"No matching attendance found for {rec.name.name} 🕵️‍♂️")

            if not rec.pre_check_in and not rec.pre_check_out:
                attendance.unlink()
                rec.state = 'draft'
            else:
                attendance.write({
                    'check_in': rec.pre_check_in if rec.pre_check_in else False,
                    'check_out': rec.pre_check_out if rec.pre_check_out else False,
                     })
                rec.state = 'draft'

    # def action_ask_approval(self):
    #     rec = super().action_ask_approval()
    #
    #     for rec in self:
    #         if not rec.emp_check_in:
    #             continue
    #
    #         check_in_date = rec.emp_check_in.date()
    #
    #         year = check_in_date.year
    #         month = check_in_date.month
    #
    #         days_in_month = calendar.monthrange(year, month)[1]
    #
    #         start_date = date(year, month, 1)
    #         end_date = date(year, month, days_in_month)
    #
    #         existing_attendances = self.env['attendance.adjustment'].search([
    #             ('name', '=', rec.employee_id.id),
    #             ('state', '=', 'done'),
    #             ('emp_check_in', '>=', f"{start_date} 00:00:00"),
    #             ('emp_check_in', '<=', f"{end_date} 23:59:59")
    #         ])
    #         print(f"existing: {len(existing_attendances)}")
    #
    #         if len(existing_attendances) >= 3:
    #             raise ValidationError(
    #                 "This employee already has 3 approved attendance adjustments for this month. No more for now 🛑.")
    #
    #         if rec.emp_check_in and rec.emp_check_out:
    #             duration = rec.emp_check_out - rec.emp_check_in
    #             if duration > timedelta(hours=24):
    #                 raise ValidationError(
    #                     "The time between Check In and Check Out cannot exceed 24 hours ⏳."
    #                 )
    #
    #     return rec
