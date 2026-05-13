from odoo import models, fields

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    active = fields.Boolean(
        string='Active',
        default=True,
        copy=False,  #No duplicate
    )

    def _unlink_related_work_entries(self, attendance):
        """Helper method to unlink related work entries"""
        if not (attendance.check_in and attendance.check_out):
            return

        try:
            work_entries = self.env['hr.work.entry'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('date_start', '=', attendance.check_in),
                ('date_stop', '=', attendance.check_out),
            ])

            if work_entries:
                validated = work_entries.filtered(lambda w: w.state == 'validated')
                if validated:
                    validated._reset_conflicting_state()
                work_entries.unlink()
        except Exception as e:
            # Log error but don't raise to prevent blocking archive operation
            pass

    def action_archive(self):
        """Archive selected records and delete related work entries"""
        for attendance in self:
            self._unlink_related_work_entries(attendance)

        return super(HrAttendance, self).action_archive()

    def write(self, vals):
        # Prevent recursion when archiving through action_archive
        if 'active' in vals and not vals['active']:
            # Only process if not coming from action_archive
            if not self.env.context.get('from_action_archive'):
                for attendance in self.filtered(lambda a: a.active):
                    self._unlink_related_work_entries(attendance)

        return super(HrAttendance, self).write(vals)