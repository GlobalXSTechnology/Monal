from odoo import models, fields, api
from datetime import datetime, time
import pytz


class MissingAttendanceWizard(models.TransientModel):
    _name = 'missing.attendance.wizard'
    _description = 'Missing Attendance Report Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    filter_status = fields.Selection([
        ('all', 'All'),
        ('missed', 'Missed'),
    ], default='all', required=True, string="Filter Status")

    attendance_ids = fields.Many2many(
        'hr.attendance',
        compute='_compute_attendance_ids'
    )

    @api.depends('date_from', 'date_to', 'filter_status')
    def _compute_attendance_ids(self):
        tz = pytz.timezone(self.env.user.tz or 'Asia/Karachi')

        for rec in self:
            if not rec.date_from or not rec.date_to:
                rec.attendance_ids = False
                continue

            start_utc = tz.localize(datetime.combine(rec.date_from, time.min)).astimezone(pytz.UTC).replace(tzinfo=None)
            end_utc = tz.localize(datetime.combine(rec.date_to, time.max)).astimezone(pytz.UTC).replace(tzinfo=None)

            domain = [
                ('check_in', '>=', start_utc),
                ('check_in', '<=', end_utc),
            ]

            all_records = self.env['hr.attendance'].search(domain, order='check_in asc')

            if rec.filter_status == 'missed':
                # Sirf wo records jo adjustment se pehle missed thay (pre_check_out empty tha)
                # Ya phir jo abhi bhi missed hain (check_out empty hai)
                rec.attendance_ids = all_records.filtered(lambda a:
                                                          (a.adjustment_id and not a.adjustment_id.pre_check_out) or
                                                          (not a.adjustment_id and not a.check_out)
                                                          )
            else:
                # All records
                rec.attendance_ids = all_records

    def action_print_report(self):
        return self.env.ref(
            'missing_attendance_report.action_report_missing_attendance'
        ).report_action(self)
