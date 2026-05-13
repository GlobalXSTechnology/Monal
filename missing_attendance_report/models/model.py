from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'


    adjustment_id = fields.Many2one(
        'attendance.adjustment',
        compute='_compute_adjustment_id',
        string="Adjustment Reference",
        store=True
    )

    def _compute_adjustment_id(self):
        for res in self:
            # Search mein adjustment model ke SAHI field names use karein
            adjustment = self.env['attendance.adjustment'].search([
                ('name', '=', res.employee_id.id),  # 'employee_id' ki jagah 'name'
                ('att_date', '=', res.check_in.date())  # 'attendance_date' ki jagah 'att_date'
            ], limit=1)
            res.adjustment_id = adjustment if adjustment else False

class AttendanceAdjustment(models.Model):
    _inherit = ['attendance.adjustment']
    _description = 'Attendance Adjustment Request'

    active = fields.Boolean(default=True)

    def revert_button(self):
        for rec in self:

            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', rec.name.id),
                ('check_in', '=', rec.emp_check_in),
                ('check_out', '=', rec.emp_check_out),
                ('adjustment_id', '=', rec.id),  # Behtar hai k adjustment_id se hi search karein
            ], limit=1)

            if not attendance:
                raise ValidationError(f"No matching attendance found for {rec.name.name}")

            if not rec.pre_check_in and not rec.pre_check_out:

                attendance.unlink()
            else:

                attendance.write({
                    'check_in': rec.pre_check_in or False,
                    'check_out': rec.pre_check_out or False,
                    'adjustment_id': False,  # Yeh line field ko khali kar degi
                })

            rec.state = 'draft'

    def create_attendance(self):
        search_attendance = self.env['hr.attendance']
        print("here boi")
        for recc in self:
            start_of_day = datetime.combine(recc.att_date, datetime.min.time())
            end_of_day = datetime.combine(recc.att_date, datetime.max.time())

            search_record = search_attendance.search([
                ('employee_id', '=', recc.name.id),
                ('check_in', '>=', start_of_day),
                ('check_in', '<=', end_of_day),
            ], limit=1)

            # search_record = search_attendance.search(
            #     [('employee_id', '=', self.name.id),('check_in','=',self.emp_check_in)])
            print('My search record', search_record)
            if search_record:
                print('My write')
                search_record.write({
                    'check_in': recc.emp_check_in,
                    'check_out': recc.emp_check_out,
                    'adjustment_id': recc.id,

                })
            else:
                print('My create')
                self.env['hr.attendance'].create({
                    'employee_id': recc.name.id,
                    'check_in': recc.emp_check_in,
                    'check_out': recc.emp_check_out,
                    'adjustment_id': recc.id,
                })
        return self.write({'state': 'done'})



