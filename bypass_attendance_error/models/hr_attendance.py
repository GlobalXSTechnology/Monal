from odoo import models, _
from odoo.exceptions import AccessError


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    def write(self, vals):
        result = True
        
        for rec in self:
            if vals.get('employee_id') and \
                    vals['employee_id'] not in self.env.user.employee_ids.ids and \
                    not self.env.user.has_group('hr_attendance.group_hr_attendance_officer'):
                raise AccessError(_("Do not have access, user cannot edit the attendances that are not his own."))

            attendances_dates = self._get_attendances_dates()

            if vals.get('check_out') and rec.out_mode == 'technical':
                vals.update({'out_mode': 'manual'})
            if vals.get('check_in') and rec.in_mode == 'technical':
                vals.update({'in_mode': 'manual'})
            result = super(HrAttendance, rec).write(vals)
            if any(field in vals for field in ['employee_id', 'check_in', 'check_out']):
                for emp, dates in self._get_attendances_dates().items():
                    attendances_dates[emp] |= dates
                self._update_overtime(attendances_dates)

        return result
