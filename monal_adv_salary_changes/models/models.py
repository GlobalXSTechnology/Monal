from odoo import models, fields, api
from odoo.exceptions import ValidationError
import calendar
from datetime import datetime, date, timedelta
import logging
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_round




_logger = logging.getLogger(__name__)


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'
    
    x_studio_is_zero = fields.Boolean(string="Zeroooo")


class HrSkipInstallment(models.Model):
    _inherit = 'hr.skip.installment'
    
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
            self.date = self.month_start_date
            last_day = calendar.monthrange(year, month)[1]
            self.month_end_date = f'{year}-{month:02d}-{last_day}'


class HrAdvanceSalaryChanges(models.Model):
    _inherit = 'hr.advance.salary'
    
    advance_type = fields.Selection([('bank', 'Bank'), ('cash', 'Cash'), ('final_bank_salary', 'Final Bank Salary')],
                                    string='Type', default='bank')
    bulk_adv_loan = fields.Boolean(string="Bulk Adv Loan/Sal")
    
    salary_without_tax = fields.Float(string='Basic Salary', readonly=True)
    resident_allowance_amount = fields.Float(string="Resident Allowance", readonly=True)
    # realocation_allowance_amount = fields.Float(string="Realocation Allowance", readonly=True)
    # bike_allowance_amount = fields.Float(string="Bike Allowance", readonly=True)
    # car_maintence_allowance_amount = fields.Float(string="Car Maintenance Allowance", readonly=True)
    house_allowance_amount = fields.Float(string="House Allowance", readonly=True)
    # car_allowance_amount = fields.Float(string="Car Allowance", readonly=True)
    # mobile_allowance_amount = fields.Float(string="Mobile Allowance", readonly=True)
    # miscellaneous_allowance_amount = fields.Float(string="Misc Allowance", readonly=True)
    # fuel_allowance_cash_amount = fields.Float(string="Fuel Cash Allowance", readonly=True)
    # food_allowance_amount = fields.Float(string="Food Allowance", readonly=True)
    # gun_allowance_amount = fields.Float(string="Gun Allowance", readonly=True)
    # hill_allowance_amount = fields.Float(string="Hill Allowance", readonly=True)
    loan_amount = fields.Float(string='Loan Amount', readonly=True)
    tax_amount = fields.Float(string='Tax Amount', readonly=True)
    eobi_amount = fields.Float(string='EOBI Amount', readonly=True)
    issi_amount = fields.Float(string='ISSI Amount', readonly=True)
    umra_amount = fields.Float(string='Umrah Deduction', readonly=True)
    fine_amount = fields.Float(string='Fine Deduction', readonly=True)
    uniform_amount = fields.Float(string='Uniform Deduction', readonly=True)
    accommodation_amount = fields.Float(string='Accommodation Deduction', readonly=True)
    food_amount = fields.Float(string='Food Deduction', readonly=True)
    total_global_input_deduction = fields.Float(string='Total Global Input', readonly=True)
    global_input_deduction = fields.Float(string='Global Input Deduction', readonly=True)
    global_input_negative_salary_all = fields.Float(string='Global Input Negative Salary Alowance', readonly=True)
    global_input_cutlery = fields.Float(string='Global Input Cutlery', readonly=True)
    global_input_laundry = fields.Float(string='Global Input Laundry', readonly=True)
    global_input_chillar = fields.Float(string='Global Input Chillar', readonly=True)
    global_input_negative_salary = fields.Float(string='Global Input Negative Salary', readonly=True)
    global_input_crockery = fields.Float(string='Global Input Crockery', readonly=True)
    global_input_cashier = fields.Float(string='Global Input Cashier', readonly=True)
    global_input_accomodation = fields.Float(string='Global Input Accomodation', readonly=True)
    global_input_fine = fields.Float(string='Global Input Fine', readonly=True)
    global_input_debit = fields.Float(string='Global Input Debit', readonly=True)
    global_input_service_charges = fields.Float(string='Global Input Service Charges', readonly=True)
    global_input_food_all = fields.Float(string='Global Input Food Allowance', readonly=True)
    global_input_uniform = fields.Float(string='Global Input Uniform', readonly=True)
    global_input_bonus = fields.Float(string='Global Input Bonus', readonly=True)
    global_input_Gratuity = fields.Float(string='Global Input Gratuity', readonly=True)
    global_input_reward_overtime = fields.Float(string='Global Input Reward Overtime', readonly=True)
    already_taken_adv = fields.Float(string='Advance Already Taken', readonly=True)
    allowed_amount = fields.Float(string='Earned Salary', readonly=True)
    allowed_amount_1 = fields.Integer(string='Earned Salary', readonly=True)

    remaining_bank_limit = fields.Float(string='Bank Limit', readonly=True)
    remaining_cash_limit = fields.Float(string='Cash Limit', readonly=True, compute='_compute_remaining_cash_limit')
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
            self.payment_start_date = self.month_start_date
            last_day = calendar.monthrange(year, month)[1]
            self.month_end_date = f'{year}-{month:02d}-{last_day}'
    
    
    @api.depends('allowed_amount','allowed_amount_1', 'remaining_bank_limit', 'employee_id')
    def _compute_remaining_cash_limit(self):
        for rec in self:
            if not rec.employee_id:
                rec.remaining_cash_limit = 0.0
                continue
            
            today = date.today()
            
            year, month = today.year, today.month
            
            # Already taken cash advances this month
            already_taken_cash = self.env['hr.advance.salary'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('advance_type', '=', 'cash'),
                ('state', 'in', ['paid', 'done']),
                ('request_date', '>=', date(year, month, 1)),
                ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
            ])
            already_taken_cash_amount = sum(already_taken_cash.mapped('amount_to_pay'))
            
            # remaining cash = allowed salary - remaining bank limit - already taken cash
            # rec.remaining_cash_limit = (
            #         rec.allowed_amount - rec.remaining_bank_limit - already_taken_cash_amount
            # )
            rec.remaining_cash_limit = (
                    rec.allowed_amount_1 - rec.remaining_bank_limit
            )
    
    
    def calculate_button_action(self):
        res = super().calculate_button_action()
        
        for rec in self:
            if rec.payment == 'fully':
                if rec.request_date:
                    day = rec.request_date.day
                    
                    # if not rec.special_approval and day != 24:
                    #     rec.allowed_amount = 0
                    # else:
                    month = rec.request_date.month
                    year = rec.request_date.year
                    
                    total_days_in_month = [
                        d for d in (date(year, month, 1) + timedelta(days=i)
                                    for i in range(calendar.monthrange(year, month)[1]))
                        if d.weekday() != 6
                    ]
                    days_in_month = len(total_days_in_month)
                    
                    # total_wage = rec.employee_id.contract_id.wage
                    # wage_per_day = total_wage / days_in_month
                    if rec.employee_id.contract_id.schedule_pay == 'daily':
                        wage_per_day = rec.employee_id.contract_id.wage
                    else:
                        wage_per_day = rec.employee_id.contract_id.wage / days_in_month
                    
                    start_date = date(year, month, 1)
                    # end_date = start_date + timedelta(months=1, days=-1)
                    end_date = start_date + relativedelta(months=1, days=-1)

                    # end_date = date(year, month, day)


                    if rec.employee_id.resource_calendar_id.x_studio_is_zero:
                        attendance_count = self.env['hr.attendance'].search_count([
                            ('employee_id', '=', rec.employee_id.id),
                            ('check_in', '>=', start_date),
                            ('check_in', '<=', end_date),
                            ('check_out', '!=', False),
                        ])
                    else:
                        attendance_count = self.env['hr.attendance'].search_count([
                            ('employee_id', '=', rec.employee_id.id),
                            ('check_in', '>=', datetime.combine(start_date, datetime.min.time())),
                            ('check_in', '<=', datetime.combine(end_date, datetime.max.time())),
                            ('check_out', '!=', False),
                            ('worked_hours', '>=', 6),
    
                        ])

                        attendance_count = self.env['hr.attendance'].search_count([
                            ('employee_id', '=', rec.employee_id.id),
                            ('attend_check_in', '>=', start_date),
                            ('attend_check_in', '<=', end_date),
                            ('worked_hours', '>=', 6),
                            ('check_out', '!=', False)

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
                        ('employee_id', '=', rec.employee_id.id),
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
                    
                    # working_days = set(a.check_in.date() for a in attendances if a.check_in)
                    # total_working_days = len(working_days)
                    
                    
                    new_wage = wage_per_day * total_working_days
                    # raise ValidationError(f"{new_wage}----{wage_per_day}----{total_working_days}---{attendance_count}---{paid_leave_days}----{start_date}----{end_date}")
                    rec.salary_without_tax = new_wage
                    
                    contract = self.env['hr.contract'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('state', 'in', ['open','close'])
                    ], order='date_start desc', limit=1)
                    
                    resident_per_day = contract.x_studio_resident_allowance / days_in_month
                    # house_per_day = contract.x_studio_house / days_in_month
                    # realocation_per_day = contract.x_studio_realocation / days_in_month
                    # bike_per_day = contract.x_studio_bike / days_in_month
                    # car_maintence_per_day = contract.x_studio_car_maintence / days_in_month
                    # car_allowance_per_day = contract.x_studio_car_allowance / days_in_month
                    # mobile_per_day = contract.x_studio_mobile_allowance / days_in_month
                    # miscellaneous_per_day = contract.x_studio_miscellaneous_allowance / days_in_month
                    # fuel_cash_per_day = contract.x_studio_fuel_allowance_cash_1 / days_in_month
                    # food_per_day = contract.x_studio_food_allowance / days_in_month
                    # gun_per_day = contract.x_studio_gun_allowance / days_in_month
                    # hill_per_day = contract.x_studio_hill / days_in_month
                    
                    rec.resident_allowance_amount = resident_per_day * total_working_days
                    # rec.house_allowance_amount = house_per_day * total_working_days
                    # rec.realocation_allowance_amount = realocation_per_day * total_working_days
                    # rec.bike_allowance_amount = bike_per_day * total_working_days
                    # rec.car_maintence_allowance_amount = car_maintence_per_day * total_working_days
                    # rec.car_allowance_amount = car_allowance_per_day * total_working_days
                    # rec.mobile_allowance_amount = mobile_per_day * total_working_days
                    # rec.miscellaneous_allowance_amount = miscellaneous_per_day * total_working_days
                    # rec.fuel_allowance_cash_amount = fuel_cash_per_day * total_working_days
                    # rec.food_allowance_amount = food_per_day * total_working_days
                    # rec.gun_allowance_amount = gun_per_day * total_working_days
                    # rec.hill_allowance_amount = hill_per_day * total_working_days
                    
                    allowances = contract.x_studio_resident_allowance
                    
                    # allowances = (
                    #         contract.x_studio_resident_allowance + contract.x_studio_realocation + contract.x_studio_bike + contract.x_studio_car_maintence +
                    #         contract.x_studio_house + contract.x_studio_car_allowance + contract.x_studio_mobile_allowance + contract.x_studio_miscellaneous_allowance +
                    #         contract.x_studio_fuel_allowance_cash_1 + contract.x_studio_gun_allowance + contract.x_studio_hill)
                    
                    allowance_per_day = allowances / days_in_month
                    
                    total_allowance_amount = allowance_per_day * total_working_days
                    
                    wage_without_tax = new_wage + total_allowance_amount
                    
                    loan_installments = self.env['hr.advance.salary'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('id', '!=', rec.id),
                        ('payment', '=', 'partially'),
                        ('state', '=', 'paid'),
                    ])
                    
                    loan_deduction = 0.0
                    
                    for loan in loan_installments:
                        for line in loan.advance_salary_line_ids:
                            line_month = line.date.month
                            line_year = line.date.year
                            
                            if line_month == month and line_year == year and line.skip != True:
                                loan_deduction += line.amount
                    state_filter = ['paid', 'done']
                    
                    already_taken_1 = self.env['hr.advance.salary'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('id', '!=', rec.id),
                        ('payment', '=', 'fully'),
                        ('advance_type', 'in', ['bank','cash']),
                        ('state', 'in', ['paid', 'done']),
                        ('request_date', '>=', date(year, month, 1)),
                        ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    ])
                    state_filter = ['gm_finance', 'done', 'paid']
                    already_taken_2 = self.env['hr.advance.salary'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('id', '!=', rec.id),
                        ('payment', '=', 'fully'),
                        ('advance_type', 'in', ['final_bank_salary']),
                        ('state', 'in', ['gm_finance', 'paid', 'done']),
                        ('request_date', '>=', date(year, month, 1)),
                        ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    ])
                    already_taken = already_taken_1 + already_taken_2
                    
                    already_taken_amount = sum(already_taken.mapped('amount_to_pay'))
                    
                    rec.already_taken_adv = already_taken_amount
                    
                    bank_salary = contract.x_studio_bank_salary
                    
                    max_bank_amount = bank_salary
                    state_filter = ['paid', 'done']
                    
                    already_taken_bank1 = self.env['hr.advance.salary'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('id', '!=', rec.id),
                        ('payment', '=', 'fully'),
                        ('advance_type', 'in', ['bank']),
                        ('state', 'in', state_filter),
                        ('request_date', '>=', date(year, month, 1)),
                        ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    ])
                    
                    state_filter = ['gm_finance', 'done', 'paid']
                    
                    already_taken_bank2 = self.env['hr.advance.salary'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('id', '!=', rec.id),
                        ('payment', '=', 'fully'),
                        ('advance_type', 'in', ['final_bank_salary']),
                        ('state', 'in', state_filter),
                        ('request_date', '>=', date(year, month, 1)),
                        ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    ])
                    
                    already_taken_bank = already_taken_bank2 + already_taken_bank1
                    
                    if already_taken_bank:
                        already_taken_bank_amount = sum(already_taken_bank.mapped('amount_to_pay'))
                        rec.remaining_bank_limit = max_bank_amount - already_taken_bank_amount
                    else:
                        rec.remaining_bank_limit = max_bank_amount
                    
                    umrah_deduction = 0
                    
                    if contract.x_studio_umra_deduction:
                        if contract.contract_type_id.name != 'Daily Wage':
                            umrah_deduction += contract.wage * 0.03
                        else:
                            umrah_deduction += (contract.wage*attendance_count) * 0.03
                    
                    rec.umra_amount = umrah_deduction
                    
                    rec.loan_amount = loan_deduction
                    
                    eobi_deduc = 0
                    issi_deduc = 0
                    
                    if contract.x_studio_disallow_eobi:
                        # pass
                        eobi_deduc += self.env.company.x_studio_basic_govt_wage_for_eobi * 0.01
                    if contract.x_studio_disllow_issi:
                        # pass
                        issi_deduc += self.env.company.basic_govt_wage * 0.06
                    
                    rec.tax_amount = contract.x_studio_income_tax
                    rec.eobi_amount = eobi_deduc
                    rec.issi_amount = issi_deduc
                    uniform_deduction = 0.0

                    uniform_records = self.env['employee.uniform'].search([
                        ('distribution_date', '>=', date(year, month, 1)),
                        ('distribution_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                        ('state', '=', 'done'),
                    ])

                    for parent in uniform_records:
                        for line in parent.line_ids:  # make sure this is correct field name
                            if line.employee_id.id == rec.employee_id.id:
                                uniform_deduction += line.charged_price or 0.0

                    rec.uniform_amount = uniform_deduction
                    fine_deduction = 0.0
                    
                    fine_records = self.env['emp.fine.deduction'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('state', '=', 'approve'),
                        ('date', '>=', date(year, month, 1)),
                        ('date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    ])
                    
                    if fine_records:
                        fine_deduction = sum(fine_records.mapped('amount'))
                    rec.fine_amount = fine_deduction
                    food_deductions = self.env['food.allowances.line'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('food_template.date', '>=', date(year, month, 1)),
                        ('food_template.date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                        ('food_template.state', '=', 'done'),  # ✅ Only lines from "done" wizards
                    ])
                    
                    total_food_deduction = sum(food_deductions.mapped('food_deduction'))
                    rec.food_amount = total_food_deduction
                    global_input_lines = self.env['employee.global.input'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('global_input_id.state', 'in', ['approved','done']),
                        ('global_input_id.date_from', '>=', date(year, month, 1)),  # or 'month' = month
                        ('global_input_id.date_to', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    ])
                    input_lines = global_input_lines.mapped('input_line_ids')  # or 'input_line_ids' - check your model
                    
                    rec.global_input_deduction = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Deduction').mapped('amount'))
                    rec.global_input_negative_salary_all = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Negative Salary Allowance').mapped(
                            'amount'))
                    rec.global_input_cutlery = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Cutlery').mapped('amount'))
                    rec.global_input_laundry = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Laundry').mapped('amount'))
                    rec.global_input_chillar = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Chiller').mapped('amount'))
                    rec.global_input_negative_salary = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Negative Salary').mapped('amount'))
                    rec.global_input_crockery = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Crockery Manual').mapped('amount'))
                    rec.global_input_cashier = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Cashier Debit').mapped('amount'))
                    rec.global_input_accomodation = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Accomodation Manual').mapped('amount'))
                    rec.global_input_fine = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Fine').mapped('amount'))
                    rec.global_input_debit = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Debit').mapped('amount'))
                    rec.global_input_service_charges = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Service Charges').mapped('amount'))
                    rec.global_input_food_all = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Food Allowance').mapped('amount'))
                    rec.global_input_uniform = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Uniform').mapped('amount'))
                    rec.global_input_bonus = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Bonus').mapped('amount'))
                    rec.global_input_Gratuity = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Gratuity').mapped('amount'))
                    rec.global_input_reward_overtime = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Reward/Overtime').mapped('amount'))
                    
                    # global_input_deductions = sum(input_lines.mapped('amount'))
                    # rec.total_global_input_deduction = global_input_deductions
                    # rec.total_global_input_deduction -= (
                    #         rec.global_input_negative_salary_all +
                    #         rec.global_input_fine +
                    #         rec.global_input_service_charges +
                    #         rec.global_input_bonus +
                    #         rec.global_input_Gratuity +
                    #         rec.global_input_food_all +
                    #         rec.global_input_reward_overtime
                    # )
                    rec.total_global_input_deduction = rec.global_input_deduction + rec.global_input_cutlery+ rec.global_input_laundry+ rec.global_input_chillar + rec.global_input_negative_salary + rec.global_input_cashier + rec.global_input_accomodation  + rec.global_input_debit + rec.global_input_uniform

                    # rec.global_input_crockery = self.company_id.x_studio_crockery_deduction
                    if self.company_id.x_studio_crockery_deduction > 0:
                        crockery = self.company_id.x_studio_crockery_deduction if attendance_count >= 18 else attendance_count * 10
                    else:
                        crockery = 0
                    rec.global_input_crockery += crockery
                    accomodation_deduction = 0
                    if contract.x_studio_allow_accommodation:
                        accomodation_deduction = self.company_id.x_studio_allow_accomodation
                        rec.accommodation_amount = accomodation_deduction

                    deductions = contract.x_studio_income_tax  + rec.uniform_amount + rec.accommodation_amount + rec.global_input_crockery + eobi_deduc + issi_deduc + loan_deduction + umrah_deduction + already_taken_amount + fine_deduction + total_food_deduction + rec.total_global_input_deduction
                    
                    n_date = rec.request_date.date()
                    payslip = self.env['hr.payslip'].search([('employee_id','=',rec.employee_id.id),('date_from','<=', n_date),('date_to','>=', n_date)], limit=1)
                    encashment = 0
                    home_delivery_all = 0
                    if payslip:
                        encashment = payslip.line_ids.filtered(lambda x:x.salary_rule_id.code == 'ENCASH').total
                        home_delivery_all = payslip.line_ids.filtered(lambda x:x.salary_rule_id.code == 'HD').total

                        _logger.info(encashment)
                    # tax_amount = contract.x_studio_income_tax + contract.x_studio_employee_eobi + loan_deduction + umrah_deduction
                    
                    adv_salary_wage = (wage_without_tax + encashment + home_delivery_all + rec.global_input_negative_salary_all + rec.global_input_reward_overtime + rec.global_input_service_charges) - deductions
                    
                    # rec.allowed_amount = adv_salary_wage - (already_taken_bank_amount if already_taken_bank else 0)
                    # rec.allowed_amount = adv_salary_wage - (already_taken_bank_amount if rec.advance_type == 'final_bank_salary' and already_taken_bank else 0)
                    # rec.allowed_amount = adv_salary_wage
                    rec.allowed_amount = float_round(adv_salary_wage, precision_digits=0)
                    rec.allowed_amount_1 = adv_salary_wage


                    _logger.info('check earned salary')
                    _logger.info('check earned salary')
                    _logger.info('check earned salary')
                    _logger.info(deductions)
                    _logger.info(contract.x_studio_income_tax)

        return res
    
    
    def action_confirm(self):
        res = super().action_confirm()
        
        for rec in self:
            _logger.info('action confirmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm')
            _logger.info('action confirmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm')
            _logger.info('action confirmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm')
            if rec.payment == 'fully':
                if rec.request_date:
                    day = rec.request_date.day
                    
                    # if not rec.special_approval and day != 24:
                    #     raise ValidationError('You can only take Advance Salary on 24th date of the month.')
                    # else:
                    month = rec.request_date.month
                    year = rec.request_date.year
                    
                    total_days_in_month = [
                        d for d in (date(year, month, 1) + timedelta(days=i)
                                    for i in range(calendar.monthrange(year, month)[1]))
                        if d.weekday() != 6
                    ]
                    days_in_month = len(total_days_in_month)
                    
                    # days_in_month = calendar.monthrange(year, month)[1]
                    if rec.employee_id.contract_id.schedule_pay == 'daily':
                        wage_per_day = rec.employee_id.contract_id.wage
                    else:
                        wage_per_day = rec.employee_id.contract_id.wage / days_in_month
                    # total_wage = rec.employee_id.contract_id.wage
                    # wage_per_day = total_wage / days_in_month
                    start_date = date(year, month, 1)
                    end_date = date(year, month, day)
                    if rec.employee_id.resource_calendar_id.x_studio_is_zero:
                        attendance_count = self.env['hr.attendance'].search_count([
                            ('employee_id', '=', rec.employee_id.id),
                            ('check_in', '>=', datetime.combine(start_date, datetime.min.time())),
                            ('check_in', '<=', datetime.combine(end_date, datetime.max.time())),
                            ('check_out', '!=', False),

                        ])
                    else:
                        attendance_count = self.env['hr.attendance'].search_count([
                            ('employee_id', '=', rec.employee_id.id),
                            ('check_in', '>=', datetime.combine(start_date, datetime.min.time())),
                            ('check_in', '<=', datetime.combine(end_date, datetime.max.time())),
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
                        ('employee_id', '=', rec.employee_id.id),
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
                    
                    new_wage = wage_per_day * total_working_days
                    
                    contract = self.env['hr.contract'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('state', 'in', ['open','close'])
                    ], order='date_start desc', limit=1)
                    
                    allowances = contract.x_studio_resident_allowance
                    
                    # allowances = (
                    #         contract.x_studio_resident_allowance + contract.x_studio_realocation + contract.x_studio_bike + contract.x_studio_car_maintence +
                    #         contract.x_studio_house + contract.x_studio_car_allowance + contract.x_studio_mobile_allowance + contract.x_studio_miscellaneous_allowance +
                    #         contract.x_studio_fuel_allowance_cash_1 + contract.x_studio_gun_allowance + contract.x_studio_hill)
                    
                    allowance_per_day = allowances / days_in_month
                    
                    total_allowance_amount = allowance_per_day * total_working_days
                    
                    wage_without_tax = new_wage + total_allowance_amount
                    
                    loan_installments = self.env['hr.advance.salary'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('id', '!=', rec.id),
                        ('payment', '=', 'partially'),
                        ('state', '=', 'paid'),
                    ])
                    
                    loan_deduction = 0.0
                    
                    for loan in loan_installments:
                        for line in loan.advance_salary_line_ids:
                            line_month = line.date.month
                            line_year = line.date.year
                            
                            if line_month == month and line_year == year and line.skip != True:
                                loan_deduction += line.amount
                    
                    already_taken = self.env['hr.advance.salary'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('id', '!=', rec.id),
                        ('payment', '=', 'fully'),
                        ('state', 'in', ['paid', 'done']),
                        ('request_date', '>=', date(year, month, 1)),
                        ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    ])
                    
                    already_taken_amount = sum(already_taken.mapped('amount_to_pay'))
                    
                    umrah_deduction = 0
                    
                    if contract.x_studio_umra_deduction:
                        if contract.contract_type_id.name != 'Daily Wage':
                            umrah_deduction += contract.wage * 0.03
                        else:
                            umrah_deduction += (contract.wage*attendance_count) * 0.03
                        # umrah_deduction += contract.wage * 0.03
                    
                    eobi_deduc = 0
                    
                    if contract.x_studio_disallow_eobi:
                        eobi_deduc += self.env.company.x_studio_basic_govt_wage_for_eobi * 0.01
                    
                    fine_deduction = 0.0
                    
                    fine_records = self.env['emp.fine.deduction'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('state', '=', 'approve'),
                        ('date', '>=', date(year, month, 1)),
                        ('date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    ])
                    
                    if fine_records:
                        fine_deduction = sum(fine_records.mapped('amount'))
                    rec.fine_amount = fine_deduction
                    food_deductions = self.env['food.allowances.line'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('food_template.date', '>=', date(year, month, 1)),
                        ('food_template.date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                        ('food_template.state', '=', 'done'),  # ✅ Only lines from "done" wizards
                    ])
                    
                    total_food_deduction = sum(food_deductions.mapped('food_deduction'))
                    
                    global_input_lines = self.env['employee.global.input'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('global_input_id.state', 'in', ['approved','done']),
                        ('global_input_id.date_from', '>=', date(year, month, 1)),  # or 'month' = month
                        ('global_input_id.date_to', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                    ])
                    input_lines = global_input_lines.mapped(
                        'input_line_ids')  # or 'input_line_ids' - check your model
                    
                    rec.global_input_deduction = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Deduction').mapped('amount'))
                    rec.global_input_negative_salary_all = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Negative Salary Allowance').mapped(
                            'amount'))
                    rec.global_input_cutlery = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Cutlery').mapped('amount'))
                    rec.global_input_laundry = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Laundry').mapped('amount'))
                    rec.global_input_chillar = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Chiller').mapped('amount'))
                    rec.global_input_negative_salary = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Negative Salary').mapped('amount'))
                    rec.global_input_crockery = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Crockery Manual').mapped('amount'))
                    rec.global_input_cashier = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Cashier Debit').mapped('amount'))
                    rec.global_input_accomodation = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Accomodation Manual').mapped(
                            'amount'))
                    rec.global_input_fine = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Fine').mapped('amount'))
                    rec.global_input_debit = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Debit').mapped('amount'))
                    rec.global_input_service_charges = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Service Charges').mapped('amount'))
                    rec.global_input_food_all = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Food Allowance').mapped('amount'))
                    rec.global_input_uniform = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Uniform').mapped('amount'))
                    rec.global_input_bonus = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Bonus').mapped('amount'))
                    rec.global_input_Gratuity = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Gratuity').mapped('amount'))
                    rec.global_input_reward_overtime = sum(
                        input_lines.filtered(lambda l: l.input_type_id.name == 'Reward/Overtime').mapped('amount'))
                    
                    # global_input_deductions = sum(input_lines.mapped('amount'))
                    # rec.total_global_input_deduction = global_input_deductions
                    # rec.total_global_input_deduction -= (
                    #         rec.global_input_negative_salary_all +
                    #         rec.global_input_fine +
                    #         rec.global_input_service_charges +
                    #         rec.global_input_bonus +
                    #         rec.global_input_Gratuity +
                    #         rec.global_input_reward_overtime
                    # )
                    rec.total_global_input_deduction = rec.global_input_deduction + rec.global_input_cutlery+ rec.global_input_laundry+ rec.global_input_chillar + rec.global_input_negative_salary + rec.global_input_cashier + rec.global_input_accomodation  + rec.global_input_debit + rec.global_input_uniform

                    a = rec.total_global_input_deduction
                    # rec.global_input_crockery = self.company_id.x_studio_crockery_deduction
                    if self.company_id.x_studio_crockery_deduction > 0:
                        crockery = self.company_id.x_studio_crockery_deduction if attendance_count >= 18 else attendance_count * 10
                    else:
                        crockery = 0
                    rec.global_input_crockery += crockery
                    accomodation_deduction = 0
                    if contract.x_studio_allow_accommodation:
                        accomodation_deduction = self.company_id.x_studio_allow_accomodation
                        rec.accommodation_amount = accomodation_deduction

                    
                    deductions = contract.x_studio_income_tax  + rec.uniform_amount + rec.accommodation_amount + rec.global_input_crockery +fine_deduction + eobi_deduc + loan_deduction + umrah_deduction + already_taken_amount + total_food_deduction + a
                    
                    
                    n_date = rec.request_date.date()
                    payslip = self.env['hr.payslip'].search([('employee_id','=',rec.employee_id.id),('date_from','<=', n_date),('date_to','>=', n_date)], limit=1)
                    encashment = 0
                    home_delivery_all = 0
                    if payslip:
                        encashment = payslip.line_ids.filtered(lambda x:x.salary_rule_id.code == 'ENCASH').total
                        home_delivery_all = payslip.line_ids.filtered(lambda x:x.salary_rule_id.code == 'HD').total

                        _logger.info(encashment)
                    # tax_amount = contract.x_studio_income_tax + contract.x_studio_employee_eobi + loan_deduction + umrah_deduction
                    
                    adv_salary_wage = (wage_without_tax + encashment + home_delivery_all + rec.global_input_negative_salary_all + rec.global_input_reward_overtime + rec.global_input_service_charges) - deductions
                    # adv_salary_wage = wage_without_tax - deductions
                    
                    bank_salary = contract.x_studio_bank_salary
                    
                    if rec.advance_type in ['bank', 'final_bank_salary']:
                        max_bank_amount = bank_salary
                        # state_filter = ['paid', 'done']
                        # if rec.advance_type == 'final_bank_salary':
                        #     state_filter = [ 'gm_finance','paid', 'done']
                        #
                        # already_taken_bank = self.env['hr.advance.salary'].search([
                        #     ('employee_id', '=', rec.employee_id.id),
                        #     ('id', '!=', rec.id),
                        #     ('advance_type', 'in', ['bank','final_bank_salary']),
                        #     ('payment', '=', 'fully'),
                        #     ('state', 'in', state_filter),
                        #     ('request_date', '>=', date(year, month, 1)),
                        #     ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                        # ])
                        state_filter = ['paid', 'done']
                        
                        already_taken_bank1 = self.env['hr.advance.salary'].search([
                            ('employee_id', '=', rec.employee_id.id),
                            ('id', '!=', rec.id),
                            ('payment', '=', 'fully'),
                            ('advance_type', 'in', ['bank']),
                            ('state', 'in', state_filter),
                            ('request_date', '>=', date(year, month, 1)),
                            ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                        ])
                        
                        state_filter = ['gm_finance', 'done', 'paid']
                        
                        already_taken_bank2 = self.env['hr.advance.salary'].search([
                            ('employee_id', '=', rec.employee_id.id),
                            ('id', '!=', rec.id),
                            ('payment', '=', 'fully'),
                            ('advance_type', 'in', ['final_bank_salary']),
                            ('state', 'in', state_filter),
                            ('request_date', '>=', date(year, month, 1)),
                            ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                        ])
                        
                        already_taken_bank = already_taken_bank2 + already_taken_bank1
                        
                        if already_taken_bank:
                            already_taken_bank_amount = sum(already_taken_bank.mapped('amount_to_pay'))
                            
                            remaining_bank_amount = max_bank_amount - already_taken_bank_amount
                            
                            if rec.request_amount > remaining_bank_amount:
                                raise ValidationError(
                                    f" {rec.employee_id.name} You’ve already taken {already_taken_bank_amount:.2f} from your Bank advance. "
                                    f"Your remaining eligible amount is {remaining_bank_amount:.2f}, "
                                    f"but you requested {rec.request_amount:.2f}."
                                )
                        
                        if rec.request_amount > max_bank_amount:
                            raise ValidationError(
                                f"{rec.employee_id.name} Your eligible Bank advance amount is {max_bank_amount:.2f}. "
                                f"You cannot request more than this."
                            )
                    
                    if rec.advance_type == 'cash':
                        
                        max_bank_amount = bank_salary
                        
                        # already_taken_bank = self.env['hr.advance.salary'].search([
                        #     ('employee_id', '=', rec.employee_id.id),
                        #     ('id', '!=', rec.id),
                        #     ('advance_type', '=', 'bank'),
                        #     ('state', 'in', ['paid', 'done']),
                        #     ('request_date', '>=', date(year, month, 1)),
                        #     ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                        # ])
                        state_filter = ['paid', 'done']
                        
                        already_taken_bank1 = self.env['hr.advance.salary'].search([
                            ('employee_id', '=', rec.employee_id.id),
                            ('id', '!=', rec.id),
                            ('payment', '=', 'fully'),
                            ('advance_type', 'in', ['bank']),
                            ('state', 'in', state_filter),
                            ('request_date', '>=', date(year, month, 1)),
                            ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                        ])
                        
                        state_filter = ['gm_finance', 'done', 'paid']
                        
                        already_taken_bank2 = self.env['hr.advance.salary'].search([
                            ('employee_id', '=', rec.employee_id.id),
                            ('id', '!=', rec.id),
                            ('payment', '=', 'fully'),
                            ('advance_type', 'in', ['final_bank_salary']),
                            ('state', 'in', state_filter),
                            ('request_date', '>=', date(year, month, 1)),
                            ('request_date', '<=', date(year, month, calendar.monthrange(year, month)[1])),
                        ])
                        
                        already_taken_bank = already_taken_bank2 + already_taken_bank1
                        if already_taken_bank:
                            
                            already_taken_bank_amount = sum(already_taken_bank.mapped('amount_to_pay'))
                            print(already_taken_bank_amount)
                            remaining_bank_limit = max_bank_amount - already_taken_bank_amount
                            print(remaining_bank_limit)
                            max_cash_amount = rec.allowed_amount_1 - remaining_bank_limit
                            _logger.info(f"Maximum cash limittttt if already taken by bank{max_cash_amount}")
                            _logger.info(f"Maximum cash limittttt if already taken by bank{max_cash_amount}")
                            print('GEOOOOOOOOOOOOOOO')
                            
                            if rec.request_amount > max_cash_amount:
                                raise ValidationError(
                                    f"{rec.employee_id.name}Your eligible Cash advance amount is {max_cash_amount:.2f}. "
                                    f"You cannot request more than this."
                                )
                        else:
                            max_cash_amount = rec.allowed_amount_1 - max_bank_amount
                            _logger.info(f"Maximum cash limittttt {max_cash_amount}")
                            _logger.info(f"Maximum cash limittttt {max_cash_amount}")
                            print('this condition got hit.....')
                            if rec.request_amount > max_cash_amount:
                                raise ValidationError(
                                    f"{rec.employee_id.name}Your eligible Cash advance amount is {max_cash_amount:.2f}. "
                                    f"You cannot request more than this."
                                )
                    
                    if rec.request_amount > rec.allowed_amount_1:
                        raise ValidationError(
                            f'Advance salary for {day}th cannot exceed salary of {total_working_days} working days. Employee {rec.employee_id.name}/ Request Amount {rec.request_amount} / Earned Salary {rec.allowed_amount_1}')
        
        return res


class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    x_studio_resident_allowance = fields.Float(string="Resident Allowance", default=1000,tracking=True)
    x_studio_realocation = fields.Float(string="Relocation Allowance", default=1000,tracking=True)
    x_studio_bike = fields.Float(string="Bike Allowance", default=1000,tracking=True)
    x_studio_car_maintence = fields.Float(string="Car Maintenance Allowance", default=1000,tracking=True)
    x_studio_house = fields.Float(string="House Allowance", default=1000,tracking=True)
    x_studio_car_allowance = fields.Float(string="Car Allowance", default=1000,tracking=True)
    x_studio_mobile_allowance = fields.Float(string="Mobile Allowance", default=1000,tracking=True)
    x_studio_miscellaneous_allowance = fields.Float(string="Miscellaneous Allowance", default=1000,tracking=True)
    x_studio_fuel_allowance_cash_1 = fields.Float(string="Fuel Allowance (Cash)", default=1000,tracking=True)
    x_studio_food_allowance = fields.Float(string="Food Allowance", default=1000,tracking=True)
    x_studio_gun_allowance = fields.Float(string="Gun Allowance", default=1000,tracking=True)
    x_studio_hill = fields.Float(string="Hill Allowance", default=1000,tracking=True)
    
    x_studio_income_tax = fields.Float(string="Tax", default=2000.0,tracking=True)
    x_studio_employee_eobi = fields.Float(string="EOBI Amount", default=2000.0,tracking=True)
    x_studio_umra_deduction = fields.Boolean(string="Umrah Deduction", tracking=True)
    x_studio_disallow_eobi = fields.Boolean(string="Disallow EOBI",tracking=True)
    
    x_studio_bank_salary = fields.Float(string="Bank Salary", default=1000,tracking=True)
