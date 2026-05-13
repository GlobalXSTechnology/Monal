from odoo import models, api, fields
from datetime import date, timedelta, datetime, date
from calendar import monthrange
import calendar
from odoo.exceptions import ValidationError
import math
import logging
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_round


_logger = logging.getLogger(__name__)


class BulkAdvanceLoan(models.Model):
    _name = 'bulk.advance.loan'

    selected_employee_ids = fields.Many2many('hr.employee', compute='_compute_selected_employees')

    @api.depends('employee_ids.employee_id')
    def _compute_selected_employees(self):
        for record in self:
            # Jitni bhi lines hain unke employee_ids nikal kar list bana lo
            record.selected_employee_ids = record.employee_ids.mapped('employee_id')

    amount = fields.Integer('Amount')
    special_approval = fields.Boolean(string="Special Approval")
    request_date = fields.Datetime(string="Request Date", default=datetime.now(), )
    advance_type = fields.Selection([('bank', 'Bank'), ('cash', 'Cash'), ('final_bank_salary', 'Final Bank Salary')],
                                    string='Type', default='bank')
    payment_start_date = fields.Datetime('Payment Start Date', copy=False, )
    payment = fields.Selection([('partially', 'Loan'), ('fully', 'Advance Salary')], string='Advance',
                               default='fully', store=True, readonly=True)

    duration_month = fields.Integer('Payment Duration(month)')

    employee_ids = fields.One2many('bulk.advance.loan.line', 'rec_ids', string='Employee', compute="get_employees",
                                   store=True, readonly=False)

    loan_type = fields.Selection([('dep', 'By Department'), ('company', 'By Company'), ('category', 'By Category')],
                                 string='Payment based on ',
                                 required=False
                                 , store=True, default='dep')

    department_ids = fields.Many2many(
        'hr.department', 'bulk_advance_loan_hr_department_rel', string='Department')

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    category_ids = fields.Many2many('hr.employee.category', string="Employee Tags")

    journal_id = fields.Many2one('account.journal', domain=[('type', 'in', ['bank', 'cash'])], string='Journal',
                                 required=False)
    month = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string="Month",
        required=True,
        tracking=True
    )
    month_start_date = fields.Date(string='Month start Date ', tracking=True)
    month_end_date = fields.Date(string='Month End Date', tracking=True)

    def action_load_employees(self):
        for rec in self:
            if rec.advance_type in ['final_bank_salary', 'bank']:
                employees = self.env['hr.employee'].search([])
                lines = []
                for emp in employees:
                    contract = self.env['hr.contract'].search([
                        ('employee_id', '=', emp.id),
                        ('state', 'in', ['open', 'close'])
                    ], limit=1)
                    if contract and contract.x_studio_bank_salary > 0:
                        lines.append((0, 0, {
                            'employee_id': emp.id,
                            'badge_id': emp.barcode,
                            'amount': 0.0,
                        }))
                _logger.warning("action_load_employees: found %d employees", len(lines))
                rec.write({'employee_ids': [(5, 0, 0)] + lines})

            elif rec.advance_type == 'cash':
                rec.write({'employee_ids': [(5, 0, 0)]})

        # Return the same wizard to keep it open
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.advance.loan',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

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
            self.payment_start_date = self.month_start_date
            last_day = calendar.monthrange(year, month)[1]
            self.month_end_date = f'{year}-{month:02d}-{last_day}'

    @api.onchange('loan_type')
    def set_employees(self):
        for rec in self.employee_ids:
            rec.rec_ids = False

    # @api.onchange('advance_type','month')
    def _onchange_advance_type(self):
        if self.advance_type in ['final_bank_salary', 'bank']:
            employees = self.env['hr.employee'].search([])

            lines = []
            for emp in employees:
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', emp.id),
                    ('state', 'in', ['open', 'close'])
                ], limit=1)

                if contract and contract.x_studio_bank_salary > 0:
                    lines.append((0, 0, {
                        'employee_id': emp.id,
                        'badge_id': emp.barcode,
                        'amount': 0.0,
                    }))

            self.employee_ids = [(5, 0, 0)] + lines
        elif self.advance_type == 'cash':
            self.employee_ids = [(5, 0, 0)]

    @staticmethod
    def _sanitize_o2m_commands(commands):
        clean = []
        for cmd in commands:
            if isinstance(cmd, (list, tuple)) and len(cmd) >= 2:
                cmd_type, cmd_id = cmd[0], cmd[1]
                if isinstance(cmd_id, str) and cmd_id.startswith('virtual_'):
                    if cmd_type == 0:
                        clean.append((0, 0, cmd[2] if len(cmd) > 2 else {}))
                    # skip (1, virtual, ...) and (2, virtual) — never in DB
                    continue
            clean.append(cmd)
        return clean

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'employee_ids' in vals:
                vals['employee_ids'] = self._sanitize_o2m_commands(vals['employee_ids'])
        return super().create(vals_list)

    def write(self, vals):
        if 'employee_ids' in vals:
            vals['employee_ids'] = self._sanitize_o2m_commands(vals['employee_ids'])
        return super().write(vals)

    def bulk_advance_loan(self):
        request_date = self.request_date.date() if self.request_date else fields.Date.today()
        year = request_date.year
        month = request_date.month

        for line in self.employee_ids:
            contract = self.env['hr.contract'].search(
                [('employee_id', '=', line.employee_id.id), ('state', 'in', ['open'])],
                limit=1)
            if not contract:
                raise ValidationError(f'No open contract found for {line.employee_id.name}.')

            bank_salary_limit = contract.x_studio_bank_salary or 0.0

            # already taken bank advances this month
            # state_filter = ['paid', 'done']
            # if rec.advance_type == 'final_bank_salary':
            #     state_filter = ['gm_finance', 'paid', 'done']
            # already_taken_bank = self.env['hr.advance.salary'].search([
            #     ('employee_id', '=', line.employee_id.id),
            #     ('advance_type', 'in', ['bank', 'final_bank_salary']),
            #     ('payment', '=', 'fully'),
            #     ('state', 'in', state_filter),
            #     ('request_date', '>=', date(year, month, 1)),
            #     ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
            # ])
            state_filter = ['paid', 'done']

            already_taken_bank1 = self.env['hr.advance.salary'].search([
                ('employee_id', '=', line.employee_id.id),
                ('id', '!=', line.id),
                ('payment', '=', 'fully'),
                ('advance_type', 'in', ['bank']),
                ('state', 'in', state_filter),
                ('request_date', '>=', date(year, month, 1)),
                ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
            ])

            state_filter = ['gm_finance', 'done', 'paid']

            already_taken_bank2 = self.env['hr.advance.salary'].search([
                ('employee_id', '=', line.employee_id.id),
                ('id', '!=', line.id),
                ('payment', '=', 'fully'),
                ('advance_type', 'in', ['final_bank_salary']),
                ('state', 'in', state_filter),
                ('request_date', '>=', date(year, month, 1)),
                ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
            ])
            already_taken_bank = already_taken_bank2 + already_taken_bank1

            already_taken_bank_amount = sum(already_taken_bank.mapped('amount_to_pay'))
            remaining_bank_amount = bank_salary_limit - already_taken_bank_amount

            # compute per-day wage based on attendances like in action_confirm
            total_days_in_month = [
                d for d in (date(year, month, 1) + timedelta(days=i)
                            for i in range(calendar.monthrange(year, month)[1]))
                if d.weekday() != 6  # exclude Sundays
            ]
            days_in_month = len(total_days_in_month)
            wage_per_day = contract.wage / days_in_month

            start_date = date(year, month, 1)
            # end_date = request_date
            end_date = start_date + relativedelta(months=1, days=-1)

            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', line.employee_id.id),
                ('check_in', '>=', start_date),
                ('check_in', '<=', end_date),
                ('check_out', '!=', False),
            ])

            working_days = set()
            employee_schedule = line.employee_id.resource_calendar_id
            if employee_schedule and employee_schedule.x_studio_is_zero:
                for att in attendances:
                    if att.check_in:
                        working_days.add(att.check_in.date())
            else:
                for att in attendances:
                    if att.check_in and att.worked_hours > 6:
                        working_days.add(att.check_in.date())

            total_working_days = len(working_days)
            if total_working_days > days_in_month:
                total_working_days = days_in_month

            # wage earned so far
            new_wage = wage_per_day * total_working_days

            # allowances – adjust to your actual fields
            allowances = contract.x_studio_resident_allowance or 0.0
            allowance_per_day = allowances / days_in_month
            total_allowance_amount = allowance_per_day * total_working_days

            wage_without_tax = new_wage + total_allowance_amount

            # final eligible advance salary
            adv_salary_wage = wage_without_tax  # minus deductions if needed

            if self.advance_type in ['bank', 'final_bank_salary']:
                if line.amount > remaining_bank_amount:
                    raise ValidationError(
                        f"{line.employee_id.name} Badge ID {line.employee_id.barcode} has already taken {already_taken_bank_amount:.2f} "
                        f"Bank Advance. Remaining eligible amount: {remaining_bank_amount:.2f}. "
                        f"You requested {line.amount:.2f}."
                    )
                if line.amount > bank_salary_limit:
                    raise ValidationError(
                        f"{line.employee_id.name} Badge ID {line.employee_id.barcode} Your eligible Bank advance amount is {bank_salary_limit:.2f}. "
                        f"You cannot request more than this."
                    )
            if self.advance_type == 'cash':  # cash advance
                if line.amount > line.remaining_cash_limit:
                    raise ValidationError(
                        f"{line.employee_id.name} Badge ID {line.employee_id.barcode} can take max Cash Advance {line.remaining_cash_limit:.2f}. "
                        f"You requested {line.amount:.2f}."
                    )

            if line.amount <= 0:
                raise ValidationError('Advance amount must be greater than zero.')
            if line.amount > line.allowed_salary_1:
                raise ValidationError(
                    f" {line.employee_id.name} Badge ID {line.employee_id.barcode} your Amount cannot be greater than Allowed Salary{line.allowed_salary_1}")

            # Create advance salary record
            if not self.month_start_date:
                raise ValidationError(f'Month start date and end date are required.')

            loan = self.env['hr.advance.salary'].create({
                'company_id': self.company_id.id,  # add this
                'employee_id': line.employee_id.id,
                'request_amount': line.amount,
                'month': self.month,
                'month_start_date': self.month_start_date,
                'month_end_date': self.month_end_date,
                'payment_start_date': self.month_start_date,
                'special_approval': self.special_approval,
                'request_date': self.request_date,
                'advance_type': self.advance_type,
                'payment': self.payment,
                'reason': 'Create by bulk action',
                'bulk_adv_loan': True,
            })
            loan.calculate_button_action()
            loan._onchange_month()

            # print('eee')


class BulkAdvanceLoanLine(models.TransientModel):
    _name = 'bulk.advance.loan.line'

    rec_ids = fields.Many2one('bulk.advance.loan', string='Employee')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    badge_id = fields.Char(string='Badge ID')
    amount = fields.Float('Amount', required=True)

    allowed_salary = fields.Float('Earned Salary', compute='_compute_employee_id')
    allowed_salary_1 = fields.Integer('Earned Salary', compute='_compute_employee_id')

    remaining_cash_limit = fields.Float(
        string='Cash Limit',
        compute='_compute_remaining_cash_limit',
        store=False,  # store=True if you want it saved in DB
        readonly=True
    )
    remaining_bank_limit = fields.Float(
        string='Bank Limit',
        compute='_compute_remaining_bank_limit',
        store=False,  # store=True if you want it saved in DB
        readonly=True
    )

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.badge_id = self.employee_id.barcode

    @api.depends('employee_id', 'rec_ids.request_date')
    def _compute_remaining_bank_limit(self):
        for line in self:
            remaining_bank_amount = 0.0
            if line.employee_id and line.rec_ids:
                contract = self.env['hr.contract'].search(
                    [('employee_id', '=', line.employee_id.id), ('state', 'in', ['open', 'close'])],
                    limit=1)
                if contract:
                    request_date = line.rec_ids.request_date.date() if line.rec_ids.request_date else fields.Date.today()
                    year = request_date.year
                    month = request_date.month

                    bank_salary_limit = contract.x_studio_bank_salary or 0.0
                    # state_filter = ['paid', 'done']
                    # if line.rec_ids.advance_type == 'final_bank_salary':
                    #     state_filter = ['gm_finance', 'paid', 'done']
                    #
                    # already_taken_bank = self.env['hr.advance.salary'].search([
                    #     ('employee_id', '=', line.employee_id.id),
                    #     ('advance_type', 'in', ['bank', 'final_bank_salary']),
                    #     ('payment', '=', 'fully'),  # Only full advances, skip loans
                    #     ('state', 'in', state_filter),
                    #     ('request_date', '>=', date(year, month, 1)),
                    #     ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    # ])
                    state_filter = ['paid', 'done']

                    already_taken_bank1 = self.env['hr.advance.salary'].search([
                        ('employee_id', '=', line.employee_id.id),
                        # ('id', '!=', rec.id),
                        ('payment', '=', 'fully'),
                        ('advance_type', 'in', ['bank']),
                        ('state', 'in', state_filter),
                        ('request_date', '>=', date(year, month, 1)),
                        ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    ])

                    state_filter = ['gm_finance', 'done', 'paid']

                    already_taken_bank2 = self.env['hr.advance.salary'].search([
                        ('employee_id', '=', line.employee_id.id),
                        # ('id', '!=', rec.id),
                        ('payment', '=', 'fully'),
                        ('advance_type', 'in', ['final_bank_salary']),
                        ('state', 'in', state_filter),
                        ('request_date', '>=', date(year, month, 1)),
                        ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    ])

                    already_taken_bank = already_taken_bank2 + already_taken_bank1
                    already_taken_bank_amount = sum(already_taken_bank.mapped('amount_to_pay'))

                    remaining_bank_amount = bank_salary_limit - already_taken_bank_amount
            line.remaining_bank_limit = remaining_bank_amount

    # remaining_budget = fields.Float('Remaining Advance Limit', compute='_compute_remaining_budget')

    # @api.depends('employee_id')
    # def _compute_remaining_budget(self):
    #     for rec in self:
    #         rec.remaining_budget = rec.employee_id.get_remaining_advance_budget() if rec.employee_id else 0.0

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.badge_id = self.employee_id.barcode
        else:
            self.badge_id = False

    @api.onchange('badge_id')
    def _onchange_badge_id(self):
        if self.badge_id:
            employee = self.env['hr.employee'].search([('barcode', '=', self.badge_id)], limit=1)
            if employee:
                self.employee_id = employee.id
            else:
                self.employee_id = False

    @api.depends('employee_id', 'rec_ids.request_date')
    def _compute_employee_id(self):
        """When selecting employee, compute allowed salary dynamically."""
        for rec in self:
            if rec.employee_id:
                request_date = rec.rec_ids.request_date or fields.Date.today()
                rec.allowed_salary = rec.employee_id._get_allowed_salary(request_date=request_date,
                                                                         advance_type=rec.rec_ids.advance_type)
                rec.allowed_salary_1 = rec.employee_id._get_allowed_salary(request_date=request_date,
                                                                           advance_type=rec.rec_ids.advance_type)
            else:
                rec.allowed_salary = 0.0
                rec.allowed_salary_1 = 0.0


    @api.depends('allowed_salary','allowed_salary_1', 'remaining_bank_limit', 'employee_id')
    def _compute_remaining_cash_limit(self):
        for line in self:
            if not line.employee_id:
                line.remaining_cash_limit = 0.0
                continue

            today = date.today()
            year, month = today.year, today.month

            # Already taken cash advances this month
            already_taken_cash = self.env['hr.advance.salary'].search([
                ('employee_id', '=', line.employee_id.id),
                ('advance_type', '=', 'cash'),
                ('state', 'in', ['paid', 'done']),
                ('request_date', '>=', date(year, month, 1)),
                ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
            ])
            already_taken_cash_amount = sum(already_taken_cash.mapped('amount_to_pay'))

            line.remaining_cash_limit = (
                    line.allowed_salary_1 - line.remaining_bank_limit
            )

            # remaining cash = allowed salary - remaining bank limit - already taken cash
            # line.remaining_cash_limit = (
            #         line.allowed_salary - line.remaining_bank_limit - already_taken_cash_amount
            # )


#
class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    x_studio_is_zero = fields.Boolean()


class Employee(models.Model):
    _inherit = 'hr.employee'

    def _get_salary_details(self, request_date=False, advance_type=False):
        _logger.info('starttttttttttttttttt bulkkkkkkkk loannnnnnnnnnnnnn')
        _logger.info('starttttttttttttttttt bulkkkkkkkk loannnnnnnnnnnnnn')
        _logger.info('starttttttttttttttttt bulkkkkkkkk loannnnnnnnnnnnnn')
        """
        Compute full salary details for the employee (like calculate_button_action).
        Returns a dict with:
        salary_without_tax, house_allowance_amount, loan_amount, tax_amount,
        eobi_amount, umra_amount, already_taken_adv, remaining_bank_limit, allowed_amount
        """
        self.ensure_one()
        calc_date = request_date or date.today()
        day = calc_date.day
        month = calc_date.month
        year = calc_date.year

        contract = self.env['hr.contract'].search([
            ('employee_id', '=', self.id),
            ('state', 'in', ['open', 'close'])
        ], order='date_start desc', limit=1)

        if not contract:
            return {}

        # Total days except Sunday
        total_days_in_month = [
            d for d in (date(year, month, 1) + timedelta(days=i)
                        for i in range(calendar.monthrange(year, month)[1]))
            if d.weekday() != 6
        ]
        days_in_month = len(total_days_in_month)

        # Wage per day
        total_wage = contract.wage
        # wage_per_day = total_wage / days_in_month

        # Attendance logic
        start_date = date(year, month, 1)
        end_date = start_date + relativedelta(months=1, days=-1)
        # end_date = date(year, month, day)

        attendances = self.env['hr.attendance'].search([
            ('employee_id', '=', self.id),
            ('check_in', '>=', datetime.combine(start_date, datetime.min.time())),
            ('check_in', '<=', datetime.combine(end_date, datetime.max.time())),
            ('check_out', '!=', False),
        ])

        working_days = set()
        employee_schedule = self.resource_calendar_id

        if employee_schedule and employee_schedule.x_studio_is_zero:
            for att in attendances:
                if att.check_in:
                    working_days.add(att.check_in.date())
        else:
            for att in attendances:
                if att.check_in and att.worked_hours > 6:
                    working_days.add(att.check_in.date())

        paid_leaves = self.env['hr.leave'].search([
            ('employee_id', '=', self.id),
            ('state', '=', 'validate'),  # only validated leaves
            ('holiday_status_id.is_leave_unpaid', '!=', True),
            ('leave_encashed_check', '=', False),
            # only paid leaves (you may need to check your leave type field)
            ('request_date_from', '<=', end_date),
            ('request_date_to', '>=', start_date),
        ])
        # sd = datetime.combine(start_date, datetime.min.time())
        # ed = datetime.combine(end_date, datetime.max.time())

        for leave in paid_leaves:
            leave_start = max(leave.request_date_from, start_date)
            leave_end = min(leave.request_date_to, end_date)
            leave_days = (leave_end - leave_start).days + 1
            for n in range(leave_days):
                working_days.add(leave_start + timedelta(days=n))

        if self.resource_calendar_id.x_studio_is_zero:
            attendance_count = self.env['hr.attendance'].search_count([
                ('employee_id', '=', self.id),
                ('check_in', '>=', start_date),
                ('check_in', '<=', end_date),
                ('check_out', '!=', False),
            ])
        else:


            attendance_count = self.env['hr.attendance'].search_count([
                ('employee_id', '=', self.id),
                ('attend_check_in', '>=', start_date),
                ('attend_check_in', '<=', end_date),
                ('worked_hours', '>=', 6),
                ('check_out', '!=', False),

            ])
            # attendances = self.env['hr.attendance'].search([
            #     ('employee_id', '=', rec.employee_id.id),
            #     ('check_in', '>=', datetime.combine(start_date, datetime.min.time())),
            #     ('check_in', '<=', datetime.combine(end_date, datetime.max.time())),
            # ])

            # working_days = set()
            # employee_schedule = rec.employee_id.resource_calendar_id

            # if employee_schedule and employee_schedule.x_studio_is_zero:
            #     for att in attendances:
            #         if att.check_in:
            #             working_days.add(att.check_in.date())
            # else:
            #     for att in attendances:
            #         if att.check_in and att.worked_hours > 6:
            #             working_days.add(att.check_in.date())

        paid_leaves = self.env['hr.leave'].search([
            ('employee_id', '=', self.id),
            ('state', '=', 'validate'),  # only validated leaves
            ('holiday_status_id.is_leave_unpaid', '!=', True),
            ('leave_encashed_check', '=', False),
            # only paid leaves (you may need to check your leave type field)
            ('request_date_from', '<=', end_date),
            ('request_date_to', '>=', start_date),
        ])
        # sd = datetime.combine(start_date, datetime.min.time())
        # ed = datetime.combine(end_date, datetime.max.time())

        # for leave in paid_leaves:
        #     leave_start = max(leave.request_date_from, start_date)
        #     leave_end = min(leave.request_date_to, end_date)
        #     leave_days = (leave_end - leave_start).days + 1
        #     for n in range(leave_days):
        #         working_days.add(leave_start + timedelta(days=n))
        paid_leave_days = sum(
            leave.number_of_days
            for leave in paid_leaves
        )

        # total_working_days = len(working_days)
        total_working_days = attendance_count + paid_leave_days

        if total_working_days > days_in_month:
            total_working_days = days_in_month

        # Salary without tax
        # new_wage = wage_per_day * total_working_days
        is_daily = contract.schedule_pay == 'daily'  # OR contract.is_daily
        if is_daily:
            wage_per_day = total_wage
            new_wage = wage_per_day * total_working_days
        else:
            wage_per_day = total_wage / days_in_month
            new_wage = wage_per_day * total_working_days

        # Allowances (per day)
        house_per_day = contract.x_studio_resident_allowance / days_in_month
        house_allowance_amount = house_per_day * total_working_days

        # Add other allowances here if needed…
        total_allowance_amount = house_allowance_amount
        wage_without_tax = new_wage + total_allowance_amount

        # raise ValidationError(f"{wage_without_tax}------{new_wage}-------{total_working_days}-------{is_daily}")

        # Loan installments (current month)
        loan_installments = self.env['hr.advance.salary'].search([
            ('employee_id', '=', self.id),
            ('payment', '=', 'partially'),
            ('state', '=', 'paid'),
        ])

        loan_deduction = 0.0
        for loan in loan_installments:
            for line in loan.advance_salary_line_ids:
                if line.date.month == month and line.date.year == year and not line.skip:
                    loan_deduction += line.amount

        # Already taken advance (current month)
        # already_taken = self.env['hr.advance.salary'].search([
        #     ('employee_id', '=', self.id),
        #     ('state', 'in', ['paid', 'done']),
        #     ('payment', '=', 'fully'),
        #     ('request_date', '>=', date(year, month, 1)),
        #     ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
        # ])
        already_taken_1 = self.env['hr.advance.salary'].search([
            ('employee_id', '=', self.id),
            # ('id', '!=', rec.id),
            ('payment', '=', 'fully'),
            ('advance_type', 'in', ['bank', 'cash']),
            ('state', 'in', ['paid', 'done']),
            ('request_date', '>=', date(year, month, 1)),
            ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
        ])
        state_filter = ['gm_finance', 'done', 'paid']
        already_taken_2 = self.env['hr.advance.salary'].search([
            ('employee_id', '=', self.id),
            # ('id', '!=', rec.id),
            ('payment', '=', 'fully'),
            ('advance_type', 'in', ['final_bank_salary']),
            ('state', 'in', ['gm_finance', 'paid', 'done']),
            ('request_date', '>=', date(year, month, 1)),
            ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
        ])
        already_taken = already_taken_1 + already_taken_2
        already_taken_amount = sum(already_taken.mapped('amount_to_pay'))

        # Bank limit
        bank_salary = contract.x_studio_bank_salary
        # state_filter = ['paid', 'done']
        # if advance_type == 'final_bank_salary':
        #     state_filter = ['gm_finance', 'paid', 'done']
        # already_taken_bank = self.env['hr.advance.salary'].search([
        #     ('employee_id', '=', self.id),
        #     ('advance_type', 'in', ['bank', 'final_bank_salary']),
        #     ('state', 'in', state_filter),
        #     ('request_date', '>=', date(year, month, 1)),
        #     ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
        # ])
        state_filter = ['paid', 'done']

        already_taken_bank1 = self.env['hr.advance.salary'].search([
            ('employee_id', '=', self.id),
            # ('id', '!=', self.id),
            ('payment', '=', 'fully'),
            ('advance_type', 'in', ['bank']),
            ('state', 'in', state_filter),
            ('request_date', '>=', date(year, month, 1)),
            ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
        ])
        state_filter = ['gm_finance', 'done', 'paid']

        already_taken_bank2 = self.env['hr.advance.salary'].search([
            ('employee_id', '=', self.id),
            # ('id', '!=', self.id),
            ('payment', '=', 'fully'),
            ('advance_type', 'in', ['final_bank_salary']),
            ('state', 'in', state_filter),
            ('request_date', '>=', date(year, month, 1)),
            ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
        ])

        already_taken_bank = already_taken_bank2 + already_taken_bank1
        already_taken_bank_amount = sum(already_taken_bank.mapped('amount_to_pay'))
        remaining_bank_limit = bank_salary - already_taken_bank_amount

        # Other deductions
        if contract.contract_type_id.name != 'Daily Wage':
            umra_amount = contract.wage * 0.03 if contract.x_studio_umra_deduction else 0
        else:
            umra_amount = (contract.wage*attendance_count) * 0.03 if contract.x_studio_umra_deduction else 0
        eobi_amount = 0 if not contract.x_studio_disallow_eobi else self.env.company.x_studio_basic_govt_wage_for_eobi * 0.01
        issi_amount = 0 if not contract.x_studio_disllow_issi else self.env.company.basic_govt_wage * 0.06
        tax_amount = contract.x_studio_income_tax
        uniform_deduction = 0.0

        uniform_records = self.env['employee.uniform'].search([
            ('distribution_date', '>=', date(year, month, 1)),
            ('distribution_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
            ('state', '=', 'done'),
        ])

        for parent in uniform_records:
            for line in parent.line_ids:  # make sure this is correct field name
                if line.employee_id.id == self.id:
                    uniform_deduction += line.charged_price or 0.0

        uniform_amount = uniform_deduction
        fine_deduction = 0.0

        fine_records = self.env['emp.fine.deduction'].search([
            ('employee_id', '=', self.id),
            ('state', '=', 'approve'),
            ('date', '>=', date(year, month, 1)),
            ('date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
        ])

        if fine_records:
            fine_deduction = sum(fine_records.mapped('amount'))

        food_deductions = self.env['food.allowances.line'].search([
            ('employee_id', '=', self.id),
            ('food_template.date', '>=', date(year, month, 1)),
            ('food_template.date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
            ('food_template.state', '=', 'done'),  # ✅ Only lines from "done" wizards
        ])

        total_food_deduction = sum(food_deductions.mapped('food_deduction'))
        # global_input_lines = self.env['employee.global.input'].search([
        #     ('employee_id', '=', self.id),
        #     ('global_input_id.state', 'in', ['approved']),
        #     ('date_from', '>=', date(year, month, 1)),
        #     ('date_to', '<=', date(year, month, calendar.monthrange(year, month)[1])),
        # ])
        #
        # global_input_deductions = sum(global_input_lines.mapped('amount'))
        global_input_lines = self.env['employee.global.input'].search([
            ('employee_id', '=', self.id),
            ('global_input_id.state', 'in', ['approved', 'done']),
            ('global_input_id.date_from', '>=', date(year, month, 1)),  # or 'month' = month
            ('global_input_id.date_to', '<=', date(year, month, calendar.monthrange(year, month)[1])),
        ])
        _logger.info('hammmmmmaaaddd***************d')
        _logger.info(date(year, month, 1))
        _logger.info(date(year, month, calendar.monthrange(year, month)[1]))
        _logger.info(global_input_lines)
        input_lines = global_input_lines.mapped('input_line_ids')  # or 'input_line_ids' - check your model

        global_input_deduction = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Deduction').mapped('amount'))
        global_input_negative_salary_all = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Negative Salary Allowance').mapped(
                'amount'))
        global_input_cutlery = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Cutlery').mapped('amount'))
        global_input_laundry = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Laundry').mapped('amount'))
        global_input_chillar = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Chiller').mapped('amount'))
        global_input_negative_salary = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Negative Salary').mapped('amount'))
        global_input_crockery = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Crockery Manual').mapped('amount'))
        global_input_cashier = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Cashier Debit').mapped('amount'))
        global_input_accomodation = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Accomodation Manual').mapped('amount'))
        global_input_fine = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Fine').mapped('amount'))
        global_input_debit = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Debit').mapped('amount'))
        global_input_service_charges = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Service Charges').mapped('amount'))
        global_input_food_all = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Food Allowance').mapped('amount'))
        global_input_uniform = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Uniform').mapped('amount'))
        global_input_bonus = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Bonus').mapped('amount'))
        global_input_Gratuity = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Gratuity').mapped('amount'))
        global_input_reward_overtime = sum(
            input_lines.filtered(lambda l: l.input_type_id.name == 'Reward/Overtime').mapped('amount'))

        # global_input_deductions = sum(input_lines.mapped('amount'))
        # emp_crockery = self.company_id.x_studio_crockery_deduction
        if self.company_id.x_studio_crockery_deduction > 0:
            crockery = self.company_id.x_studio_crockery_deduction if attendance_count >= 18 else attendance_count * 10
        else:
            crockery = 0
        _logger.info('Check crockery dedyction')
        _logger.info('Check crockery dedyction')
        _logger.info('Check crockery dedyction')
        _logger.info(f"Check crockery dedyction global input{global_input_crockery}")
        _logger.info(f"Check crockery dedyction company{crockery}")
        _logger.info(f"Check crockery dedyction company{self.company_id.name}")
        global_input_crockery += crockery

        accomodation_deduction = 0
        if contract.x_studio_allow_accommodation:
            accomodation_deduction = self.company_id.x_studio_allow_accomodation
        # total_global_input_deduction = global_input_deductions
        # total_global_input_deduction -= (
        #         global_input_negative_salary_all +
        #         global_input_fine +
        #         global_input_service_charges +
        #         global_input_bonus +
        #         global_input_Gratuity +
        #         global_input_food_all +
        #         global_input_reward_overtime
        # )
        total_global_input_deduction = global_input_deduction + global_input_cutlery + global_input_laundry + global_input_chillar + global_input_negative_salary + global_input_cashier + global_input_accomodation + global_input_debit + global_input_uniform

        _logger.info(f"totalllllllllll global inputtttttttttttttt{total_global_input_deduction}")
        _logger.info(f"wage without texxxxxxxxxxxxxxxxxxxxxxx{wage_without_tax}")
        _logger.info(f"wage per dayyyyyyyyyyyyyyyyyyyyyyyyyy{wage_per_day}")
        _logger.info(f"income taxxxxxxxxxxxxxxxxx{tax_amount}")
        _logger.info(f"eobiiiiiiiiiiiiiiiiiii{eobi_amount}")
        _logger.info(f"fineeeeeeeeeeeeeeeeeeeeeeee{fine_deduction}")
        _logger.info(f"fooddddddddddddddddddddd{total_food_deduction}")
        _logger.info(f"issiiiiiiiiiiiiiiiiiiiiii{issi_amount}")
        _logger.info(f"loan deductionnnnnnnnnnnnnnn{loan_deduction}")
        _logger.info(f"Umrahhhhhhhhhhhhhhhh{umra_amount}")
        _logger.info(f"alreadyyyyyy takennnnnnnnnnnn{already_taken_amount}")
        n_date = request_date.date()
        _logger.info(n_date)
        _logger.info('n_date')
        _logger.info(self.id)
        deductions = uniform_amount + global_input_crockery + tax_amount + eobi_amount + accomodation_deduction + fine_deduction + total_food_deduction + issi_amount + loan_deduction + umra_amount + already_taken_amount + total_global_input_deduction
        payslip = self.env['hr.payslip'].search(
            [('employee_id', '=', self.id), ('date_from', '<=', n_date), ('date_to', '>=', n_date)], limit=1)
        _logger.info('hammmmadddddd')
        _logger.info(payslip)
        encashment = 0
        home_delivery_all = 0
        if payslip:
            encashment = payslip.line_ids.filtered(lambda x: x.salary_rule_id.code == 'ENCASH').total
            home_delivery_all = payslip.line_ids.filtered(lambda x: x.salary_rule_id.code == 'HD').total
            _logger.info(encashment)
        allowed_amount = (
                                     wage_without_tax + encashment + home_delivery_all + global_input_negative_salary_all + global_input_reward_overtime + global_input_service_charges) - deductions
        _logger.info('allowed_amount')
        _logger.info(allowed_amount)
        _logger.info(deductions)
        _logger.info(already_taken_bank)
        _logger.info(bank_salary)
        _logger.info(tax_amount)
        _logger.info(eobi_amount)
        _logger.info(loan_deduction)
        _logger.info(umra_amount)
        _logger.info(already_taken_amount)

        return {
            'salary_without_tax': new_wage,
            'house_allowance_amount': house_allowance_amount,
            'loan_amount': loan_deduction,
            'tax_amount': tax_amount,
            'eobi_amount': eobi_amount,
            'umra_amount': umra_amount,
            'already_taken_adv': already_taken_amount,
            'remaining_bank_limit': remaining_bank_limit,
            'allowed_amount': float_round(allowed_amount, precision_digits=0),
        }

    def _get_allowed_salary(self, request_date=False, advance_type=False):
        """Return just allowed salary amount (backward compatible)."""
        return self._get_salary_details(request_date, advance_type).get('allowed_amount', 0.0)
