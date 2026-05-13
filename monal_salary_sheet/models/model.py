import logging
from odoo import models, fields, api
import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict

_logger = logging.getLogger(__name__)


class StockField(models.TransientModel):
    _name = 'monal.salary.sheet'

    date_from = fields.Date(string='Date')
    daily_wager = fields.Boolean(string='Daily Wager')
    company = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company)
    employee = fields.Many2many('hr.employee', string='Employee')
    department = fields.Many2many('hr.department', string='Department')
    analytic_ids = fields.Many2many(
        'account.analytic.account',
        string="Accounts",
    )
    archive = fields.Boolean(
        string="Archived Employees",
    )
    filter_by = fields.Selection([
        ('company', 'Company '),
        ('employee', 'Employee'),
        ('department', 'Department'),
        ('analytic', 'Analytic Accounts'),
    ], string='Filter By', default=False)

    month = fields.Selection(selection=lambda self: self._get_month_selection(), string="Month", required=True)

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

    def get_weekly_off_count(self, date_from, date_to):

        weekly_off_count = 0
        current_date = date_from

        while current_date <= date_to:
            if current_date.weekday() == 6:
                weekly_off_count += 1
            current_date += relativedelta(days=1)

        return weekly_off_count

    # month = fields.Selection(
    #     [(str(i), calendar.month_name[i]) for i in range(1, 13)],
    #     string="Month",
    # )
    # year = fields.Integer(string="Year", required=True, default=lambda self: date.today().year)

    def print_report(self):
        year_str, month_str = self.month.split('-')

        year = int(year_str)
        month = int(month_str)

        date_from = None
        date_to = None

        if self.daily_wager and self.date_from:
            date_from = self.date_from
            date_to = self.date_from
        else:

            date_from = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            date_to = date(year, month, last_day)

            # month_int = int(self.month)
            # date_from = date(self.year, month_int, 1)
            # last_day = calendar.monthrange(self.year, month_int)[1]
            # date_to = date(self.year, month_int, last_day)

        print(date_from)
        print(date_to)
        domain = [
            ('date_from', '=', date_from),
            ('date_to', '=', date_to),
            ('state', '!=', ['draft', 'cancel']),
            ('struct_id.name', 'not ilike', 'Allowance')
        ]
        if self.archive:
            domain.append(('employee_id.active', '=', False))

        if self.filter_by == 'company' and self.company:
            domain.append(('company_id', '=', self.company.id))

        elif self.filter_by == 'employee' and self.employee:
            domain.append(('employee_id', 'in', self.employee.ids))

        elif self.filter_by == 'analytic' and self.analytic_ids:
            # domain.append(('contract_id.analytic_account_id', 'in', self.analytic_ids.ids))
            domain += ['|',
                       ('analytic_account_id', 'in', self.analytic_ids.ids),  # Payslip analytic
                       '&',
                       ('analytic_account_id', '=', False),  # If NOT on payslip
                       ('contract_id.analytic_account_id', 'in', self.analytic_ids.ids)  # fallback
                       ]

        elif self.filter_by == 'department' and self.department:
            domain.append(('employee_id.department_id', 'in', self.department.ids))
        _logger.info(domain)
        payslips = self.env['hr.payslip'].search(domain)
        _logger.info(payslips)
        result = []
        for slip in payslips:
            employee = slip.employee_id
            department_name = employee.department_id.name if employee.department_id else 'Unassigned'

            calendar_days = (date_to - date_from).days + 1
            total_sundays = 0
            current_day = date_from
            while current_day <= date_to:
                if current_day.weekday() == 6:  # Sunday
                    total_sundays += 1
                current_day += relativedelta(days=1)

            x = calendar_days - total_sundays

            working_days_in_month = 0

            # if self.daily_wager:
            #     attendances = self.env['hr.attendance'].search([
            #         ('check_in', '>=', self.date_from),
            #         ('check_out', '<=', self.date_from),
            #         ('employee_id', '=', employee.id)
            #     ])
            if self.daily_wager:
                attendances = self.env['hr.attendance'].search([
                    ('attend_check_in', '>=', self.date_from),
                    ('attend_check_in', '<=', self.date_from),
                    ('employee_id', '=', employee.id),
                    ('check_out','!=',False)
                ])
            else:
                attendances = self.env['hr.attendance'].search([
                    ('attend_check_in', '>=', date_from),
                    ('attend_check_in', '<=', date_to),
                    ('employee_id', '=', employee.id),
                    ('check_out','!=',False)
                ])

            if self.daily_wager:
                absents = 0
                sundays = 0
                working_days_in_month = 1
            else:
                _logger.info(f"Calculating working days for employee {employee.name} for month {month} and year {year}")
                total_days_in_month = calendar.monthrange(year, month)[1]
                all_days = [date(year, month, d) for d in range(1, total_days_in_month + 1)]
                sundays = sum(1 for d in all_days if d.weekday() == 6)
                total_days = total_days_in_month - sundays
                working_days_in_month = total_days
                absents = total_days - len(attendances)
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info('working_days_in_month')
                _logger.info(working_days_in_month)
                _logger.info(total_days)
                _logger.info(total_days_in_month)
                _logger.info(all_days)
                _logger.info(sundays)
                _logger.info(absents)

                if absents < 0:
                    absents = 0

            rules = {
                'BASIC': 'Basic Salary',
                'GROSS': 'Gross Salary',
                'UM': 'Umrah',
                'ADV/CSH': 'Cash Adv',
                'FA': 'Food over',
                'ABSF': 'Absent Fine',
                'EOBIEE': 'EOBI',
            }

            line_totals = {}
            loan_deduct_total = 0
            allowances_amount = 0
            accomodation_allowance = 0
            crockery_deduction = 0
            total_ded = 0
            bank_ac = 0
            net_salary = 0
            umrah = 0
            advance_cash = 0
            bank_advance = 0
            food_over = 0
            absent_fine = 0
            eobi = 0
            loan_deduct = 0
            fine_debt = 0
            final_bank = 0
            crockery_deduction = 0

            for line in slip.line_ids:
                if line.code == 'UM':
                    umrah += line.total or 0
                if line.code == 'ADV/CSH':
                    advance_cash += line.total or 0
                if line.code == 'ADV/BNK':
                    bank_advance += line.total or 0
                elif line.code == 'FA':
                    food_over += line.total or 0
                elif line.code == 'ABSF':
                    absent_fine += line.total or 0
                elif line.code == 'EOBIEE':
                    eobi += line.total or 0
                elif line.code in ['LOAN/MED', 'LOAN/EDU']:
                    loan_deduct += line.total or 0
                elif line.code in ['CUT', 'LAUN', 'CHI', 'NS','AA', 'CM', 'CSHD', 'ACCM', 'FI', 'DEB', 'FA', 'UNI', 'MAD',
                                   'FOD', 'TXD', 'SISSI', 'ABS']:
                    fine_debt += line.total
                elif line.code == 'ADV/FBNK':
                    final_bank += line.total
                elif line.code in ['CM', 'CD']:
                    crockery_deduction += line.total
                elif line.category_id.name == 'Allowance' and line.code != 'RA':
                    allowances_amount += line.total
                elif line.code == 'RA':
                    accomodation_allowance += line.total


                _logger.info("Payslip Line Code: %s Amount: %s", line.salary_rule_id.code, line.total)
                if line.code in rules:
                    line_totals[line.code] = line.total
                elif line.salary_rule_id and line.salary_rule_id.code in ['LOAN/MED', 'LOAN/EDU']:
                    loan_deduct_total += line.total

                elif line.salary_rule_id and line.salary_rule_id.code == 'ADV/BNK':
                    bank_ac += line.total or 0
                elif line.salary_rule_id and line.salary_rule_id.code == 'NET':
                    net_salary += line.total or 0
                elif line.code in ['CM', 'CD', '']:
                    total_ded += line.total or 0

            line_totals['LOAN_DEDUCT'] = loan_deduct_total
            # line_totals['ALLOW'] = allowances_amount
            line_totals['FINE'] = fine_debt
            line_totals['CD'] = crockery_deduction
            line_totals['ADV_FBNK'] = final_bank
            line_totals['ADV_BNK'] = bank_ac
            line_totals['NET'] = net_salary
            line_totals['ADV/CSH'] = advance_cash
            line_totals['total_deduction'] = total_ded

            paid_leave_days = 0

            leave_records = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('leave_encashed_check', '!=', True),
                ('request_date_from', '<=', date_to),
                ('request_date_to', '>=', date_from),
            ])
            hr_leave = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', date_to),
                ('request_date_to', '>=', date_from),
            ])

            annual_leave = hr_leave.filtered(lambda l: l.holiday_status_id.name == 'Annual Leave')
            sick_leave = hr_leave.filtered(lambda l: l.holiday_status_id.name == 'Sick / Emergency')
            weekl_off = hr_leave.filtered(lambda l: l.holiday_status_id.name == 'Weekly Off')
            annual_leave_days = sum(annual_leave.mapped('number_of_days'))
            sick_leave_days = sum(sick_leave.mapped('number_of_days'))
            carry_forward = sum(weekl_off.mapped('number_of_days'))

            paid_leave_days = sum(l.number_of_days for l in leave_records)
            absents -= paid_leave_days
            if absents < 0:
                absents = 0

            paid_leaves = 0
            unpaid_leaves = 0
            short_leaves = 0

            all_leave_dates = set()
            paid_leave_dates = set()
            unpaid_leave_dates = set()
            short_leave_dates = set()

            for leave in leave_records:
                leave_start = max(leave.request_date_from, date_from)
                leave_end = min(leave.request_date_to, date_to)

                current_leave_date = leave_start
                while current_leave_date <= leave_end:
                    is_short_leave = False
                    if leave.request_unit_half or leave.request_unit_hours:
                        is_short_leave = True

                    is_unpaid_leave = leave.holiday_status_id.unpaid or False

                    if is_short_leave:
                        short_leave_dates.add(current_leave_date)
                        short_leaves += 1
                    elif is_unpaid_leave:
                        unpaid_leave_dates.add(current_leave_date)
                        unpaid_leaves += 1
                    else:
                        paid_leave_dates.add(current_leave_date)
                        paid_leaves += 1

                    all_leave_dates.add(current_leave_date)
                    current_leave_date += relativedelta(days=1)

            basic_salary = line_totals.get('BASIC') or line_totals.get('GROSS') or 0

            salary_per_day = 0
            if working_days_in_month > 0:
                salary_per_day = basic_salary / working_days_in_month
            _logger.info(salary_per_day)
            _logger.info(f"Calculating encashment for employee {employee.name}")
            _logger.info(basic_salary)

            contract = employee.contract_id
            contract_wage = contract.wage if contract else 0.0

            encashment_per_day = contract_wage / 30

            encashment_lines = [line for line in slip.line_ids if line.code == 'ENCASH']
            encashment_amount = sum(line.total for line in encashment_lines) or 0

            if encashment_per_day > 0:
                encashment_days = encashment_amount / encashment_per_day
            else:
                encashment_days = 0
            _logger.info(f"Payslip lines for employee {employee.name}: {[line.code for line in slip.line_ids]}")
            _logger.info(f"Line Totals: {line_totals}")
            _logger.info(f"Encashment Amount: {encashment_amount}")
            _logger.info(f"Employee contract wage: {contract_wage}, Calculating encashment per day")
            _logger.info(f"Encashment per day: {encashment_per_day}, Encashment days: {encashment_days}")
            presents = len(attendances)
            presents = sum(
                1 for att in attendances
                if (getattr(att, 'is_zero', False) or att.worked_hours > 6)
            )

            work_days = presents + paid_leave_days + sundays

            if not self.daily_wager:
                total_days_in_month = calendar.monthrange(year, month)[1]

                work_days = min(work_days, total_days_in_month)

            # salary_days = presents + paid_leave_days + sundays + encashment_days
            # salary_days = work_days + encashment_days

            payslip_from = slip.date_from
            payslip_to = slip.date_to

            if isinstance(payslip_from, str):
                payslip_from = fields.Date.from_string(payslip_from)
            if isinstance(payslip_to, str):
                payslip_to = fields.Date.from_string(payslip_to)
            loan_records = self.env['hr.advance.salary'].search([
                ('employee_id', '=', employee.id),
                ('state', 'in', ['paid', 'done']),
                ('payment', '=', 'partially'),
                ('request_date', '<=', payslip_to),
                '|',
                ('payment_end_date', '=', False),
                ('payment_end_date', '>=', payslip_from),
            ])

            current_month = False
            if getattr(slip, 'date_from', False):
                if isinstance(slip.date_from, str):
                    try:
                        current_month = fields.Date.from_string(slip.date_from).strftime('%Y-%m')
                    except Exception:
                        current_month = slip.date_from[:7]
                else:
                    current_month = slip.date_from.strftime('%Y-%m')
            out_standing = 0.0
            pre_out_starting = 0.0
            total_loan_paid_before = 0.0
            total_loan_deduction_current = 0.0
            if current_month:
                year, month = map(int, current_month.split('-'))
                month_start_date = date(year, month, 1)

                loan_start_dates = loan_records.mapped('payment_start_date')
                if loan_start_dates:
                    min_loan_date = min(loan_start_dates)
                    previous_loan_deductions = self.env['hr.payslip.line'].search([
                        ('employee_id', '=', slip.employee_id.id),
                        ('slip_id.date_from', '<', month_start_date),
                        ('slip_id.date_from', '>=', min_loan_date),
                        ('salary_rule_id.code', 'like', 'LOAN/%'),
                    ])
                else:
                    previous_loan_deductions = self.env['hr.payslip.line'].browse()  # empty recordset

                total_loan_paid_before = sum(previous_loan_deductions.mapped('total'))

                current_loan_deductions = self.env['hr.payslip.line'].search([
                    ('slip_id', '=', slip.id),
                    ('salary_rule_id.code', 'like', 'LOAN/%'),
                ])
                total_loan_deduction_current = sum(current_loan_deductions.mapped('total'))
                total_loan_paid_up_to_now = total_loan_paid_before + total_loan_deduction_current

            ONE2M_NAMES = ['line_ids', 'advance_line_ids', 'installment_ids', 'payment_line_ids', 'lines']
            LINE_DATE_FIELDS = ['date', 'payment_date', 'date_pay', 'date_due', 'payment_on', 'paid_date']
            LINE_SKIP_FIELDS = ['skip', 'is_skip', 'skipped', 'skip_this', 'skip_line']
            LINE_DEDUCTION_FIELDS = ['deduction_amount', 'amount', 'amount_to_pay', 'deducted', 'deduction']
            LINE_REMAINING_FIELDS = ['remaining_amount', 'remaining', 'balance', 'balance_amount']

            for loan in loan_records:
                loan_lines = getattr(loan, 'advance_salary_line_ids', False) or getattr(loan, 'advance_line_ids',
                                                                                        False) or getattr(loan,
                                                                                                          'line_ids',
                                                                                                          False) or []

                # loan_outstanding = loan.amount_to_pay or loan.total_amount or loan.loan_amount or 0.0
                loan_outstanding = loan.amount_to_pay or loan.loan_amount or 0.0
                out_standing += loan.request_amount - total_loan_paid_before

                skip_this_month = False
                deduction_amount = getattr(loan, 'deduction_amount', 0.0) or 0.0

                for line in loan_lines:
                    line_date = getattr(line, 'date', getattr(line, 'payment_date', False))
                    if not line_date:
                        continue

                    line_month = line_date.strftime('%Y-%m') if isinstance(line_date, date) else str(line_date)[:7]
                    if line_month == current_month:
                        if getattr(line, 'skip', True):
                            skip_this_month = True
                        break

                if skip_this_month:
                    pre_out_starting += out_standing
                else:
                    pre_out_starting += out_standing - deduction_amount

                if loan.payment_start_date and loan.payment_start_date.date() > payslip_to:
                    pre_out_starting = out_standing
            leave_balances = []

            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                '|',
                ('date_to', '=', False),
                ('date_to', '>=', date_from),
                # ('date_to', '>=', date_from),
                # ('date_from', '>=', date_from),
            ])

            for alloc in allocations:
                if (alloc.date_to and not alloc.date_to <= date_to) or not alloc.date_to:
                    taken_days = sum(self.env['hr.leave'].search([
                        ('employee_id', '=', employee.id),
                        ('state', 'in', ['validate']),
                        ('holiday_status_id', '=', alloc.holiday_status_id.id),
                        # ('request_date_to', '=', False),
                        ('request_date_to', '<=', alloc.date_to or date_to),
                    ]).mapped('number_of_days'))

                    allocated_days = alloc.number_of_days
                    remaining_days = allocated_days - taken_days

                    if remaining_days > 0:
                        leave_balances.append({
                            'leave_type': alloc.holiday_status_id.name,
                            'allocated': allocated_days,
                            'taken': taken_days,
                            'remaining': remaining_days,
                        })
            contract = employee.contract_id

            wage_amount = contract.wage if contract else 0.0
            if working_days_in_month > 0 and wage_amount > 0:
                salary_per_day = wage_amount / working_days_in_month

            new_s = total_days_in_month - (paid_leave_days + presents)

            leave_records = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('leave_encashed_check', '!=', True),
                ('request_date_from', '<=', date_to),
                ('request_date_to', '>=', date_from),

            ])

            paid_leaves = 0
            unpaid_leaves = 0
            short_leaves = 0

            all_leave_dates = set()
            paid_leave_dates = set()
            unpaid_leave_dates = set()
            short_leave_dates = set()

            for leave in leave_records:
                leave_start = max(leave.request_date_from, date_from)
                leave_end = min(leave.request_date_to, date_to)

                current_leave_date = leave_start
                while current_leave_date <= leave_end:
                    is_short_leave = False
                    if leave.request_unit_half or leave.request_unit_hours:
                        is_short_leave = True

                    is_unpaid_leave = leave.holiday_status_id.unpaid or False

                    if is_short_leave:
                        short_leave_dates.add(current_leave_date)
                        short_leaves += 1
                    elif is_unpaid_leave:
                        unpaid_leave_dates.add(current_leave_date)
                        unpaid_leaves += 1
                    else:
                        paid_leave_dates.add(current_leave_date)
                        paid_leaves += 1

                    all_leave_dates.add(current_leave_date)
                    current_leave_date += relativedelta(days=1)

            total_leave_days = len(all_leave_dates)

            attendance_records = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('attend_check_in', '>=', date_from),
                ('attend_check_in', '<=', date_to),
                ('check_out','!=',False)
            ])

            present_days = 0
            days_with_less_work = 0
            is_zero_schedule = employee.resource_calendar_id.x_studio_is_zero

            for attendance in attendance_records:
                work_hours = float(attendance.worked_hours or 0.0)
                if is_zero_schedule:
                    present_days += 1
                    if work_hours < 6:
                        days_with_less_work += 1
                else:
                    if work_hours >= 6:
                        present_days += 1
                    else:
                        days_with_less_work += 1
            work_dayss = present_days + paid_leaves

            total_work_able_days_month_new = (date_to - date_from).days + 1
            _logger.info(total_work_able_days_month_new)
            total_weekly_offs_work = self.get_weekly_off_count(
                date_from,
                date_to
            )
            x_final_work_days = total_work_able_days_month_new - total_weekly_offs_work
            _logger.info(x_final_work_days)
            _logger.info('Abdullah')
            if work_dayss > x_final_work_days:
                work_dayss = x_final_work_days
            salary_days = work_dayss + encashment_days
            if salary_days > calendar_days:
                salary_days = calendar_days

            data = {
                'period': f"{calendar.month_name[int(month)]} {year}" if not self.daily_wager else date_from.strftime(
                    '%d-%b-%Y'),
                'project': employee.company_id.name,
                'calendar_days': calendar_days,
                'employee_name': employee.name,
                'emp_code': employee.barcode,
                'designation': employee.job_id.name,
                'department': employee.department_id.name,
                # 'accommodation_allow': employee.contract_id.x_studio_resident_allowance,
                'allowances_amount': allowances_amount,
                'accommodation_allow': accomodation_allowance,
                'presents': present_days,
                'absents': absents,
                'sundays': new_s,
                'paid_leaves': paid_leaves,
                'unpaid': unpaid_leaves,
                'annual_leave_days': annual_leave_days,
                'sick_leave_days': sick_leave_days,
                'carry_forward': carry_forward,
                'salary_per_day': round(salary_per_day, 2),
                'working_days': round(x),
                'encashment_days': round(encashment_days),
                'encashment_amount': round(encashment_amount),
                'salary_days': round(salary_days),
                'total_days': round(encashment_days + salary_days),
                'outstanding': out_standing,
                'pre_outstanding': pre_out_starting,
                'total_lta_deduction': out_standing - pre_out_starting,
                'total_leaves': annual_leave_days + sick_leave_days + carry_forward,
                'lines': line_totals,
                'leave_balances': leave_balances,
                'wage': wage_amount,
                'basic_salary': basic_salary,
                'work_dayss': work_dayss,
                'umrah': umrah,
                'advance_cash': advance_cash,
                'bank_advance': bank_advance,
                'food_over': food_over,
                'absent_fine': absent_fine,
                'eobi': eobi,
                'loan_deduct': loan_deduct,
                'fine_debt': fine_debt,
                'final_bank': final_bank,
                'crockery_deduction': crockery_deduction,
                'total_deductions': umrah + advance_cash + bank_advance + food_over + absent_fine + eobi + loan_deduct + fine_debt + final_bank + crockery_deduction,
                'image_url': '/web/image?model=hr.employee&id=%s&field=image_1920' % employee.id,
            }

            result.append(data)

        # First, add actual wage values for sorting to each record
        for rec in result:
            # Store actual wage/basic salary for sorting
            rec['_wage'] = rec.get('wage', 0) or 0
            rec['_basic_salary'] = rec.get('basic_salary', 0) or 0

        # Group by department
        dept_dict = defaultdict(list)
        for rec in result:
            dept_name = rec['department'] or 'ZZZ'  # unassigned goes last
            dept_dict[dept_name].append(rec)

        final_result = []

        # Sort departments alphabetically
        for dept_name in sorted(dept_dict.keys()):
            employees = dept_dict[dept_name]

            # Sort employees by wage in descending order (highest first)
            employees.sort(key=lambda x: x.get('_wage', 0), reverse=True)

            # Add sequence number after sorting
            for seq, emp_data in enumerate(employees, 1):
                emp_data['sr_no'] = seq

            final_result.extend(employees)

        final_data = {'payslips': final_result}

        # def get_basic(x):
        #     return x['lines'].get('BASIC') or x['lines'].get('GROSS') or 0

        # dept_dict = defaultdict(list)
        # for rec in result:
        #     dept_name = rec['department'] or 'ZZZ'  # unassigned goes last
        #     dept_dict[dept_name].append(rec)

        # final_result = []
        # for dept_name in sorted(dept_dict.keys()):
        #     employees = dept_dict[dept_name]
        #     employees.sort(key=lambda x: (x['employee_name'] or '').lower())
        #     final_result.extend(employees)

        # final_data = {'payslips': final_result}

        # final_data = {'payslips': result}

        return self.env.ref('monal_salary_sheet.action_hr_playslip_report').report_action(self, data=final_data)
