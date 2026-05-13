from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import calendar
from odoo.addons.stock.report.stock_traceability import autoIncrement

_logger = logging.getLogger(__name__)


class LeaveCashment(models.Model):
    _name = "leave.encashment"
    _rec_name = "em_p"

    em_p = fields.Many2one('hr.employee', string="Employee", required=True)
    total_leave = fields.Float(string="Total Leave")
    re_leave = fields.Float(string="Remaining leaves")
    amount = fields.Float(string="Amount")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit_to_approve', 'Submit To Approve'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ], default='draft', string="State")
    tree_line = fields.One2many('leave.encashment.tree', 'connecting_field', string='Allocations')
    attendance_lines = fields.One2many('attendance.encashment.tree', 'connecting_field', string='Attendances')
    notice_date = fields.Date(string='Notice Date')
    # period = fields.Many2one('monal.evaluation.period', string='Period', required=False)
    encashed_amount = fields.Float(string="Encashed Amount", compute="_compute_encashed_amount")
    populate = fields.Boolean(string="Populate")
    duration_display = fields.Float(string='Available Leaves')
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        readonly=True
    )
    month = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string="Month",
        required=True,
        tracking=True
    )
    month_start_date = fields.Date(string='Month Start Date', tracking=True)
    month_end_date = fields.Date(string='Month end Date', tracking=True)

    def _get_month_selection(self):
        months = [
            ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
            ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        month_selection = []
        for year in range(2025, 2041):
            for code, name in months:
                month_selection.append((f'{year}-{code}', f'{name} {year}'))
        return month_selection

    @api.onchange('month')
    def _onchange_month(self):
        if self.month:
            year, month = map(int, self.month.split('-'))
            self.month_start_date = f'{year}-{month:02d}-01'
            last_day = calendar.monthrange(year, month)[1]
            self.month_end_date = f'{year}-{month:02d}-{last_day}'

    @api.depends('tree_line.encash_leaves', 'em_p.contract_ids', 'month')
    def _compute_encashed_amount(self):
        for rec in self:
            contract_id = rec.em_p.contract_ids.filtered(lambda x: x.state in ['open','close'])
            wage = contract_id.wage if contract_id else 0.0
            daily_wage = wage / 30 if wage else 0.0

            leave_total = sum(line.encash_leaves for line in rec.tree_line)
            attendance_total = sum(line.encash_2 for line in rec.attendance_lines)

            rec.encashed_amount = daily_wage * (leave_total + attendance_total)

    # def _get_leave_end_date(self, start_date, days_to_encash):
    #     days_counted = 0
    #     current_date = start_date
    #
    #     while days_counted < days_to_encash:
    #         if current_date.weekday() != 6:  # 6 = Sunday
    #             days_counted += 1
    #         if days_counted < days_to_encash:
    #             current_date += timedelta(days=1)
    #
    #     return current_date
    def _get_leave_end_date(self, start_date, days):
        return start_date + timedelta(days=days - 1)

    def action_approve_encashment(self):
        _logger.info('startttttttttttttttttt approveeeeeeeeeeeeeeeeeee')
        for rec in self:

            if not rec.month_start_date:
                raise ValidationError(_("Month start date is missing."))

            # 1️⃣ Find last encashed leave of this month
            last_leave = self.env['hr.leave'].search([
                ('employee_id', '=', rec.em_p.id),
                ('state', '=', 'validate'),
                ('leave_encashed_check', '=', True),
                ('month', '=', rec.month),
            ], order='request_date_to desc', limit=1)

            # 2️⃣ Determine start date
            if last_leave:
                current_start_date = last_leave.request_date_to + timedelta(days=1)
            else:
                current_start_date = rec.month_start_date

            for line in rec.tree_line:
                if not line.encash_leaves:
                    continue

                if line.encash_leaves > line.duration_display:
                    raise ValidationError(_("Not enough leaves available to encash."))

                # 3️⃣ Calculate leave range
                # date_from = current_start_date
                date_from = current_start_date +  relativedelta(months=1)
                date_to = self._get_leave_end_date(date_from, line.encash_leaves)
                allocationnnnnnnn = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', rec.em_p.id),
                    ('holiday_status_id', 'in', rec.tree_line.mapped('holiday_status_id').ids),
                    ('state', '=', 'validate'),
                    ('month', '=', rec.month),
                ], order="id desc", limit=1)
                _logger.info(f"dateeeeeeeeeeeeeeeeee frommmmmmmmmmmmmm{date_from}")
                _logger.info(f"dateeeeeeeeeeeeeeeeee toooooooooo{date_to}")
                _logger.info('Allocationnnnnnnnnnnnnnnnnnn')
                _logger.info('Allocationnnnnnnnnnnnnnnnnnn')
                _logger.info('Allocationnnnnnnnnnnnnnnnnnn')
                _logger.info('Allocationnnnnnnnnnnnnnnnnnn')
                _logger.info(allocationnnnnnnn)
                _logger.info(allocationnnnnnnn.employee_id.name)
                _logger.info(allocationnnnnnnn.number_of_days_display)
                _logger.info(allocationnnnnnnn.month_start_date)
                _logger.info(allocationnnnnnnn.month_end_date)

                _logger.info(rec.em_p.id)
                _logger.info(rec.em_p.name)
                _logger.info(line.holiday_status_id.id)
                _logger.info(date_from)
                _logger.info(date_to)
                _logger.info(line.encash_leaves)
                _logger.info(rec.month)
                
                if date_from < date.today():
                    date_from = date.today()
                    date_to = date.today() + timedelta(days=line.encash_leaves-1)
                _logger.info(f"DDDDDDDDDDDDDFFFFFFFFFFFFFF{date_from}")
                _logger.info(f"DDDDDDDDTTTTTTTTTTT{date_to}")
                # 4️⃣ Create leave (Odoo calendar handles Sundays)
                leave = self.env['hr.leave'].create({
                    'name': 'Leaves Encashed',
                    'employee_id': rec.em_p.id,
                    'holiday_status_id': line.holiday_status_id.id,
                    'request_date_from': date_from,
                    'request_date_to': date_to,
                    'number_of_days': line.encash_leaves,
                    'state': 'confirm',
                    'month': rec.month,
                    'leave_encashed_check': True,
                })
                _logger.info(leave)

                leave.action_approve()
                leave.action_validate()

                # 5️⃣ Move pointer forward
                current_start_date = date_to + timedelta(days=1)

                # Deduct balance
                line.duration_display -= line.encash_leaves

            rec.state = 'approve'
        # for rec in self:
        #     total_encashed_leaves = 0.0
        #
        #     # Find the latest encashed leave for this employee & month
        #     last_encashed_leave = self.env['hr.leave'].search([
        #         ('employee_id', '=', rec.em_p.id),
        #         ('holiday_status_id', 'in', rec.tree_line.mapped('holiday_status_id').ids),
        #         ('state', '=', 'validate'),
        #         ('leave_encashed_check', '=', True),
        #         ('month', '=', rec.month),
        #     ], order="request_date_to desc", limit=1)
        #     _logger.info(f"Last encasged leaveeeeeeeeeeeeee{last_encashed_leave}")
        #
        #     if last_encashed_leave:
        #         current_start_date = last_encashed_leave.request_date_to + timedelta(days=1)
        #         _logger.info(f"current 11111111111111{current_start_date}")
        #     else:
        #         psd = rec.month_start_date
        #         current_start_date = (psd + relativedelta(months=1)).replace(day=1)
        #         _logger.info(f"current 22222222222222222{current_start_date}")
        #
        #     for line in rec.tree_line:
        #         if line.encash_leaves:
        #             # Deduct from balance
        #             if current_start_date.weekday() == 6:
        #                 current_start_date += timedelta(days=1)
        #                 _logger.info(f"current start date if its sundayyyyyyyyyyyy{current_start_date}")
        #             line.duration_display -= line.encash_leaves
        #             total_encashed_leaves += line.encash_leaves
        #             allocationnnnnnnn = self.env['hr.leave.allocation'].search([
        #                 ('employee_id', '=', rec.em_p.id),
        #                 ('holiday_status_id', 'in', rec.tree_line.mapped('holiday_status_id').ids),
        #                 ('state', '=', 'validate'),
        #                 ('month', '=', rec.month),
        #             ], order="id desc", limit=1)
        #             _logger.info('Allocationnnnnnnnnnnnnnnnnnn')
        #             _logger.info('Allocationnnnnnnnnnnnnnnnnnn')
        #             _logger.info('Allocationnnnnnnnnnnnnnnnnnn')
        #             _logger.info(allocationnnnnnnn)
        #             _logger.info(allocationnnnnnnn.employee_id.name)
        #             _logger.info(allocationnnnnnnn.number_of_days_display)
        #             _logger.info(allocationnnnnnnn.month_start_date)
        #             _logger.info(allocationnnnnnnn.month_end_date)
        #             leave = ''
        #             _logger.info(rec.em_p.id)
        #
        #             _logger.info(line.encash_leaves)
        #
        #
        #             # Calculate end date for this leave encashment
        #             date_from = current_start_date
        #             date_to = self._get_leave_end_date(rec.month_end_date, line.encash_leaves)
        #             _logger.info(rec.month_start_date)
        #             _logger.info(rec.month_end_date)
        #
        #             # Create leave record
        #             leave = self.env['hr.leave'].create({
        #                 'name': 'Leaves Encashed',
        #                 'employee_id': rec.em_p.id,
        #                 'holiday_status_id': line.holiday_status_id.id,
        #                 'request_date_from': date_from,
        #                 'request_date_to': date_to,
        #                 'number_of_days': line.encash_leaves,
        #                 'state': 'confirm',
        #                 'month': rec.month,
        #             })
        #             _logger.info(f"LEaveeeeeeeeeeeeeeeee{leave}")
        #             _logger.info(f"LEaveeeeeeeeeeeeeeeee{leave}")
        #             _logger.info
        #             leave.action_approve()
        #             leave.action_validate()
        #             # current_start_date = rec.month_end_date + timedelta(days=1)
        #
        #             # Move forward correctly (skip Sunday if needed)
        #             current_start_date = date_to + timedelta(days=1)
        #             if current_start_date.weekday() == 6:
        #                 current_start_date += timedelta(days=1)
        #
        #
        #             _logger.info(';;;;;;;;;;;;;;;;;;;;')
        #             _logger.info(current_start_date)
        #
        #     rec.state = 'approve'

    def action_reject_encashment(self):
        self.state = 'reject'

    def action_sumbit_to_encashment(self):
        for rec in self:

            leave_used = any(line.encash_leaves > 0 for line in rec.tree_line)
            att_used = any(line.encash_2 > 0 for line in rec.attendance_lines)

            # No type selected
            if not leave_used and not att_used:
                raise ValidationError(
                    _("Please enter encash amount in either Leave Encashment or Attendance Encashment."))

            # Both selected → not allowed
            # if leave_used and att_used:
            #     raise ValidationError(_("You cannot encash both Leaves and Attendance Days at the same time."))

            # Validate Leave Encashment
            if leave_used:
                for line in rec.tree_line:
                    if line.encash_leaves < 0:
                        raise ValidationError(_("Encash Leave cannot be negative"))
                    if line.encash_leaves > 0 and line.encash_leaves > line.duration_display:
                        raise ValidationError(_(
                            "You cannot encash more than available leaves. Demand %s. Available: %s"
                        ) % (line.encash_leaves, line.duration_display))

            # Validate Attendance Encashment
            if att_used:
                for att_line in rec.attendance_lines:
                    if att_line.encash_2 < 0:
                        raise ValidationError(_("Encash Days cannot be negative"))
                    if att_line.encash_2 > 0 and att_line.encash_2 > att_line.duration_display_2:
                        raise ValidationError(_(
                            "You cannot encash more than available attendance days. Demand %s. Available: %s"
                        ) % (att_line.encash_2, att_line.duration_display_2))

        self.state = 'submit_to_approve'

    def action_post(self):
        _logger.info('111111111111111111111111111111')
        """Populate leave or attendance encashment lines"""
        for rec in self:
            if not rec.em_p or not rec.month:
                raise ValidationError(_("Please select Employee and month first."))

            # start_date = rec.period.period_start_date
            # end_date = rec.period.period_end_date
            start_date = rec.month_start_date
            end_date = rec.month_end_date

            # if not start_date or not end_date:
            #     raise ValidationError(_("Selected month does not have valid dates."))

            # ------------------------
            #  Attendance Count Logic
            # ------------------------
            if rec.em_p.resource_calendar_id.x_studio_is_zero:
                present_days = self.env['hr.attendance'].search_count([
                    ('employee_id', '=', rec.em_p.id),
                    ('check_in', '>=', start_date),
                    ('check_in', '<=', end_date),
                ])
            else:
                present_days = self.env['hr.attendance'].search_count([
                    ('employee_id', '=', rec.em_p.id),
                    ('check_in', '>=', start_date),
                    ('check_in', '<=', end_date),
                    ('worked_hours', '>=', 6),
                ])

            if present_days <= 0:
                raise ValidationError(
                    _("Employee %s has no attendance records in this month.") % rec.em_p.name
                )

            # Clear previous lines
            rec.tree_line = [(5, 0, 0)]
            rec.attendance_lines = [(5, 0, 0)]

            leave_types = self.env['hr.leave.type'].search([('leave_encash', '=', True)])
            vals = []
            leave_found = False
            total_available_leaves = 0

            previous_enc = self.env['leave.encashment'].search([
                ('em_p', '=', rec.em_p.id),
                ('month', '=', rec.month),
                ('state', 'in', ['draft','submit_to_approve','approve']),
                ('id', '!=', rec.id)
            ])

            previous_leave_used = sum(previous_enc.mapped('tree_line.encash_leaves'))
            rec.duration_display = previous_leave_used

            previous_days_used = sum(previous_enc.mapped('attendance_lines.encash_2'))

            # -----------------------------------------
            #  Leave Encashment (Existing logic)
            # -----------------------------------------
            for leave_type in leave_types:

                allocations = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', rec.em_p.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', '=', 'validate'),
                    ('month', '=', rec.month),
                ]).mapped('number_of_days')

                used = self.env['hr.leave'].search([
                    ('employee_id', '=', rec.em_p.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', '=', 'validate'),
                    ('month', '=', rec.month),
                ]).mapped('number_of_days')
                # duration_display = sum(allocations) - sum(used)
                duration_display = sum(allocations)
                _logger.info(duration_display)
                _logger.info(used)

                if duration_display > 0:
                    leave_found = True
                    total_available_leaves += duration_display

                    vals.append((0, 0, {
                        'employee_id': rec.em_p.id,
                        'holiday_status_id': leave_type.id,
                        'name': present_days,
                        'duration_display': duration_display,
                    }))

            # If leaves found → create leave lines
            if leave_found:
                _logger.info('222222222222222222222222222')
                rec.tree_line = vals
                rec.populate = True
                contract_id = rec.em_p.contract_ids.filtered(lambda x: x.state in ['open','close'])
                daily_wage = (contract_id.wage / 30) if contract_id else 0.0
                rec.amount = total_available_leaves * daily_wage

                total_month_days = (end_date - start_date).days + 1

                sundays_in_month = 0
                day = start_date
                while day <= end_date:
                    if day.weekday() == 6:
                        sundays_in_month += 1
                    day += timedelta(days=1)

                working_days = total_month_days - sundays_in_month
                extra_days = present_days - working_days
                _logger.info(extra_days)
                extra_after_leave = extra_days - total_available_leaves - previous_leave_used - previous_days_used
                _logger.info(total_available_leaves)
                _logger.info(previous_leave_used)
                _logger.info(previous_days_used)
                # extra_after_leave should never be negative
                extra_after_leave = max(extra_after_leave, 0)
                # extra_after_leave = extra_days - previous_days_used
                if extra_after_leave > 0:
                    contract_id = rec.em_p.contract_ids.filtered(lambda x: x.state in ['open','close'])
                    daily_wage = (contract_id.wage / 30) if contract_id else 0.0
                    total_amount = (extra_after_leave + total_available_leaves) * daily_wage

                    rec.attendance_lines = [(0, 0, {
                        'employee_id_2': rec.em_p.id,
                        'name_2': str(present_days),
                        'duration_display_2': extra_after_leave,
                        'encash_2': 0.0,
                    })]

                    rec.amount = total_amount

                return  # IMPORTANT: Do NOT go into next logic if leaves exist

            # ------------------------------------------------
            #   If NO LEAVES FOUND → Attendance Encashment
            # ------------------------------------------------
            total_month_days = (end_date - start_date).days + 1

            sundays_in_month = 0
            day = start_date
            while day <= end_date:
                if day.weekday() == 6:
                    sundays_in_month += 1
                day += timedelta(days=1)

            working_days = total_month_days - sundays_in_month

            _logger.info(f"Present Days: {present_days}")
            _logger.info(f"Working Days: {working_days}")
            # extra_days = present_days - 26
            extra_days = present_days - working_days
            _logger.info(extra_days)

            if extra_days <= 0:
                raise ValidationError(
                    _("Employee %s has %s present days, which is not enough for attendance-based encashment (minimum 27).") %
                    (rec.em_p.name, present_days)
                )

            # remaining_days = extra_days - previous_days_used
            remaining_days = extra_days - total_available_leaves - previous_leave_used - previous_days_used

            if remaining_days <= 0:
                raise ValidationError(
                    _("Employee %s has already encashed all available Leaves or attendance days for this month.") %
                    rec.em_p.name
                )

            contract_id = rec.em_p.contract_ids.filtered(lambda x: x.state in ['open','close'])
            daily_wage = (contract_id.wage / 30) if contract_id else 0.0

            rec.attendance_lines = [(0, 0, {
                'employee_id_2': rec.em_p.id,
                'name_2': str(present_days),
                'duration_display_2': remaining_days,
                'encash_2': 0.0,
            })]

            rec.amount = remaining_days * daily_wage
            rec.populate = True
            _logger.info('finalllllllllllllllllllllllll')

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise ValidationError(_("You cannot Delete Record if state is not draft"))
        return super().unlink()


class LeaveEncashmentTree(models.Model):
    _name = "leave.encashment.tree"

    connecting_field = fields.Many2one('leave.encashment', string='Connecting Field')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    holiday_status_id = fields.Many2one('hr.leave.type', string='Time Off Type')
    name = fields.Char(string='Work Days')
    duration_display = fields.Float(string='Available Leaves')
    encash_leaves = fields.Float(string='Leaves to Encash')
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        readonly=True
    )


class AttendanceEncashmentTree(models.Model):
    _name = "attendance.encashment.tree"

    connecting_field = fields.Many2one('leave.encashment', string='Connecting Field')
    employee_id_2 = fields.Many2one('hr.employee', string='Employee')
    name_2 = fields.Char(string='Work Days')
    duration_display_2 = fields.Float(string='Available Days To Encash')
    encash_2 = fields.Float(string='Days to Encash')
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        readonly=True
    )


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    leave_encash = fields.Boolean(string="Leave Encashment", store=True, trackuing=True)


class HRLeave(models.Model):
    _inherit = "hr.leave"

    leave_encashed_check = fields.Boolean(string="Leave Encashed", store=True, trackuing=True)
    monal_evaluation_period_id = fields.Many2one(
        'monal.evaluation.period',
        string="Evaluation Period",
        help="The evaluation period for which this allocation was created."
    )

    month = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string="Month",
        required=True,
        tracking=True
    )
    month_start_date = fields.Date(string='Month start Date ', tracking=True)
    month_end_date = fields.Date(string='Month End Date', tracking=True)

    def _get_month_selection(self):
        months = [
            ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
            ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        month_selection = []
        for year in range(2025, 2041):
            for code, name in months:
                month_selection.append((f'{year}-{code}', f'{name} {year}'))
        return month_selection

    @api.onchange('month')
    def _onchange_month(self):
        if self.month:
            year, month = map(int, self.month.split('-'))
            self.month_start_date = f'{year}-{month:02d}-01'
            last_day = calendar.monthrange(year, month)[1]
            self.month_end_date = f'{year}-{month:02d}-{last_day}'
