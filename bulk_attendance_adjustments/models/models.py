from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime, time


class MultiEntryLine(models.TransientModel):
    _name = 'adjustment.lines'
    _description = 'Multiple Adjustment Lines'

    wizard_id = fields.Many2one('bulk.attendance.adjustments', string="Wizard Reference")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    badge_id = fields.Char(related='employee_id.barcode', string="Badge Id")
    dept_id = fields.Many2one(related='employee_id.department_id', string="Department")
    att_date = fields.Date(string="Date", required=True)
    check_in = fields.Datetime(string="Check In", required=True)
    check_out = fields.Datetime(string="Check Out", required=True)
    pre_check_in = fields.Datetime(string="Previous Check In", compute='get_pre_checks')
    pre_check_out = fields.Datetime(string="Previous Check Out", compute='get_pre_checks')
    remarks = fields.Char(string="Remarks")

    worked_hours = fields.Float(string='Worked Hours', compute='get_worked_hours')

    @api.depends('check_in','check_out')
    def get_worked_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                duration = rec.check_out - rec.check_in
                rec.worked_hours = duration.total_seconds() / 3600
            else:
                rec.worked_hours = 0

    @api.onchange('employee_id','att_date')
    def get_pre_checks(self):
        for rec in self:
            if rec.employee_id and rec.att_date:
                start_dt = datetime.combine(rec.att_date, time.min)
                end_dt = datetime.combine(rec.att_date, time.max)

                attendance = self.env['hr.attendance'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('check_in', '>=', start_dt),
                    ('check_in', '<=', end_dt),
                ], limit=1, order="check_in asc")

                if attendance:
                    rec.pre_check_in = attendance.check_in
                    rec.pre_check_out = attendance.check_out
                else:
                    rec.pre_check_in = False
                    rec.pre_check_out = False
            else:
                rec.pre_check_in = False
                rec.pre_check_out = False



class BulkAttendanceAdjustments(models.TransientModel):
    _name = 'bulk.attendance.adjustments'

    line_ids = fields.One2many('adjustment.lines', 'wizard_id', string=" ")

    apply_to_all = fields.Boolean(string="Apply to All Employees", default=False)
    employee_ids = fields.Many2many('hr.employee', string="Employees",
                                    help="Select multiple employees when using Apply to All")
    global_check_in = fields.Datetime(string="Global Check In")
    global_check_out = fields.Datetime(string="Global Check Out")

    def action_submit(self):
        Adjustment = self.env['attendance.adjustment']
        employee_entry_counts = {}

        if self.apply_to_all:
            if not self.global_check_in or not self.global_check_out:
                raise ValidationError("Please provide both check-in and check-out times!")

            if self.global_check_in > self.global_check_out:
                raise ValidationError("Check-in cannot be after check-out!")

            if not self.employee_ids:
                raise ValidationError("Please select at least one employee!")

            start_date = self.global_check_in.date()
            end_date = self.global_check_out.date()
            num_days = (end_date - start_date).days + 1

            for emp in self.employee_ids:
                # existing_count = Adjustment.search_count([('name', '=', emp.id)])
                # if existing_count + num_days > 3:
                #     raise ValidationError(
                #         f"Oops! Employee '{emp.name}' already has {existing_count} adjustments. "
                #         f"Adding {num_days} more would exceed the limit of 3 😤"
                #     )

                for i in range(num_days):
                    current_day = start_date + timedelta(days=i)
                    check_in = self.global_check_in.replace(
                        year=current_day.year, month=current_day.month, day=current_day.day
                    )
                    check_out = self.global_check_out.replace(
                        year=current_day.year, month=current_day.month, day=current_day.day
                    )

                    search_record = self.env['hr.attendance'].search([
                        ('employee_id', '=', emp.id),
                        ('check_in', '>=', check_in.replace(hour=0, minute=0, second=0)),
                        ('check_in', '<=', check_out.replace(hour=23, minute=59, second=59)),
                    ], limit=1)


                    Adjustment.create({
                        'name': emp.id,
                        'employee_id':emp.id,
                        'att_date': current_day,
                        'emp_check_in': check_in,
                        'emp_check_out': check_out,
                        'pre_check_in': search_record.check_in if search_record else False,
                        'pre_check_out': search_record.check_out if search_record else False,
                        'notes': f"Bulk entry for {current_day.strftime('%Y-%m-%d')}",
                    })

        else:
            for line in self.line_ids:
                emp_id = line.employee_id.id

                if (line.check_in.date() != line.att_date) and (line.check_out.date() != line.att_date):
                    raise ValidationError(
                        f"⚠️ Employee '{line.employee_id.name}' must have either check-in or check-out on the attendance date ({line.att_date})."
                    )

                # if line.check_in.date != line.att_date and line.check_out.date == line.att_date:
                #     print('I am here')
                #     raise ValidationError('You have to adjust the attendance in the same date.')
                # elif  line.check_out.date != line.att_date and line.check_in.date == line.att_date:
                #     print('I am not there')
                #     raise ValidationError('You have to adjust the attendance in the same date.')
                # else:
                #     pass


                # if emp_id not in employee_entry_counts:
                #     existing_count = self.env['attendance.adjustment'].search_count([('name', '=', emp_id)])
                #     employee_entry_counts[emp_id] = existing_count
                #
                # employee_entry_counts[emp_id] += 1
                #
                # if employee_entry_counts[emp_id] > 3:
                #     raise ValidationError(
                #         f"Oops! Employee '{line.employee_id.name}' already has 3 or more attendance adjustments. "
                #         "No more entries allowed 😤"
                #     )

            for line in self.line_ids:
                pre_att = self.env['hr.attendance'].search([
                    ('employee_id', '=', line.employee_id.id),
                    ('check_in', '>=', line.check_in.replace(hour=0, minute=0, second=0)),
                    ('check_in', '<=', line.check_in.replace(hour=23, minute=59, second=59)),
                ], limit=1)

                self.env['attendance.adjustment'].create({
                    'name': line.employee_id.id,
                    'employee_id': line.employee_id.id,
                    'att_date': line.att_date,
                    'emp_check_in': line.check_in,
                    'emp_check_out': line.check_out,
                    'pre_check_in': pre_att.check_in if pre_att else False,
                    'pre_check_out': pre_att.check_out if pre_att else False,
                    'notes': line.remarks,
                    'worked_hours': line.worked_hours,
                })
