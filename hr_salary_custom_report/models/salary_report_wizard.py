from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class SalarySheetReportWizard(models.TransientModel):
    _name = 'salary.sheet.report.wizard'
    _description = 'Salary Sheet Report Wizard'

    period = fields.Selection(
        selection='_get_period_selection',
        string='Period',
        required=True,
        default=lambda self: self._get_default_period()
    )

    select_employee = fields.Selection(
        [
            ('employee', 'Employee'),
            ('department', 'Department'),
            ('company', 'Company'),
            ('analytic', 'Analytic Accounts'),
        ],
        string="Report Type",
        default='employee',
        required=True
    )
    archive = fields.Boolean(
        string="Archived Employees",
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        domain=lambda self: [('id', '=', self.env.company.id)],
    )

    department_id = fields.Many2many(
        'hr.department',
        string="Departments",
        domain=lambda self: [('company_id', '=', self.env.company.id)]

    )

    employee_ids = fields.Many2many(
        'hr.employee',
        string="Employees",
        domain=lambda self: [('company_id', '=', self.env.company.id)]

    )
    analytic_ids = fields.Many2many(
        'account.analytic.account',
        string="Accounts",
    )

    @api.onchange('select_employee')
    def _onchange_select_employee(self):
        """Show/hide fields based on selection"""
        if self.select_employee == 'company':
            self.department_id = False
            self.employee_ids = False
            self.analytic_ids = False
        elif self.select_employee == 'department':
            self.employee_ids = False
        elif self.select_employee == 'employee':
            self.department_id = False

    def _get_period_selection(self):
        """Return all months from 2015 to the current year"""
        periods = []
        start_year = 2025
        end_year = 2040  # current year only
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                date_obj = datetime(year, month, 1)
                period_value = date_obj.strftime('%Y-%m')
                period_name = date_obj.strftime('%b %Y')
                periods.append((period_value, period_name))
        # Optional: sort descending to show latest months first
        periods.sort(reverse=True)
        return periods

    def _get_default_period(self):
        return fields.Date.today().strftime('%Y-%m')

    def _get_period_dates(self, period_value):
        year, month = map(int, period_value.split('-'))
        from_date = datetime(year, month, 1).date()
        to_date = from_date + relativedelta(months=1, days=-1)
        return from_date, to_date

    def get_total_days_in_month(self, from_date, to_date):
        _logger.info(from_date)
        _logger.info(to_date)
        _logger.info('Datesssssss')
        delta = to_date - from_date
        return delta.days + 1

    def get_weekly_off_count(self, from_date, to_date):

        weekly_off_count = 0
        current_date = from_date

        while current_date <= to_date:
            if current_date.weekday() == 6:
                weekly_off_count += 1
            current_date += relativedelta(days=1)

        return weekly_off_count

    def get_attendance_data(self, employee, from_date, to_date):
        try:
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('state', '!=', 'cancel'),
            ], order='date_start desc', limit=1)

            effective_from_date = from_date
            effective_to_date = to_date


            if contract:
                if contract.date_start and contract.date_start > from_date:
                    effective_from_date = contract.date_start

                if contract.date_end and contract.date_end < to_date:
                    effective_to_date = contract.date_end

            # Agar employee is month bilkul active hi nahi tha
            if effective_from_date > effective_to_date:
                return {
                    'present_days': 0,
                    'absent_days': 0,
                    'leave_days': 0,
                    'paid_leaves': 0,
                    'unpaid_leaves': 0,
                    'short_leaves': 0,
                    'total_work_days': 0,
                    'total_month_days': 0,
                    'weekly_off': 0,
                    'days_with_less_work': 0,
                }

            # total_days_in_month = self.get_total_days_in_month(from_date, to_date)
            total_days_in_month = self.get_total_days_in_month(
                effective_from_date,
                effective_to_date
            )
            total_weekly_offs = self.get_weekly_off_count(
                effective_from_date,
                effective_to_date
            )
            # total_weekly_offs = self.get_weekly_off_count(from_date, to_date)
            # if employee.resource_calendar_id.x_studio_is_zero:
            #     attendance_records = self.env['hr.attendance'].search([
            #         ('employee_id', '=', employee.id),
            #         ('check_in', '>=', effective_from_date),
            #         # ('check_in', '<=', effective_to_date),
            #         # ('check_in', '>=', from_date),
            #         # ('check_in', '<=', to_date)
            #     ])
            # else:
            #     attendance_records = self.env['hr.attendance'].search([
            #         ('employee_id', '=', employee.id),
            #         ('check_in', '>=', effective_from_date),
            #         ('check_in', '<=', effective_to_date),
            #         # ('check_in', '>=', from_date),
            #         # ('check_in', '<=', to_date),
            #         ('worked_hours', '>=', 6),
            #     ])
            _logger.info(f"efective date frommmmmmmmmmmmm{effective_from_date}")
            _logger.info(f"efective date toooooooooooooooooo{effective_to_date}")
            attendance_records = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('attend_check_in', '>=', effective_from_date),
                ('attend_check_in', '<=', effective_to_date),
            ])
            _logger.info(f"attendanceeeeeeeeeeeeee{attendance_records}")

            attendance_dates = {}
            for attendance in attendance_records:
                attend_date = attendance.check_in.date()
                if from_date <= attend_date <= to_date:
                    work_hours = float(attendance.worked_hours or 0.0)
                    # attendance_dates[attend_date] = work_hours
                    if attend_date not in attendance_dates:
                        attendance_dates[attend_date] = []

                    attendance_dates[attend_date].append(work_hours)

            # present_days = 0
            # days_with_less_work = 0
            # is_zero_schedule = employee.resource_calendar_id.x_studio_is_zero
            # for attend_date, work_hours_list in attendance_dates.items():
            #     total_hours_in_day = sum(work_hours_list)
            #     # CASE 1: ZERO schedule → any attendance = present
            #     if is_zero_schedule:
            #         present_days += 1
            #         # optional: track less work (if you still want)
            #         if total_hours_in_day < 6:
            #             days_with_less_work += 1
            #     # CASE 2: NORMAL schedule → must be >= 6 hrs
            #     else:
            #         if total_hours_in_day >= 6:
            #             present_days += 1
            #         else:
            #             days_with_less_work += 1
            present_days = 0
            days_with_less_work = 0
            is_zero_schedule = employee.resource_calendar_id.x_studio_is_zero

            for attendance in attendance_records:
                work_hours = float(attendance.worked_hours or 0.0)
                if is_zero_schedule and attendance.check_out:
                    present_days += 1
                    if work_hours < 6:
                        days_with_less_work += 1
                else:
                    if work_hours >= 6:
                        present_days += 1
                    else:
                        days_with_less_work += 1
            _logger.info(f'present dayssssssssssss{present_days}')

            # present_days = 0
            # days_with_less_work = 0
            # for attend_date, work_hours_list in attendance_dates.items():
            #     for work_hours in work_hours_list:
            #         if work_hours >= 6.0:
            #             present_days += 1
            #         else:
            #             days_with_less_work += 1
            # for attend_date, work_hours in attendance_dates.items():
            #     if work_hours >= 6.0:
            #         present_days += 1
            #     else:
            #         days_with_less_work += 1

            leave_records = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('leave_encashed_check', '!=', True),
                ('request_date_from', '<=', effective_to_date),
                ('request_date_to', '>=', effective_from_date),
                # ('request_date_from', '<=', to_date),
                # ('request_date_to', '>=', from_date),
            ])

            paid_leaves = 0
            unpaid_leaves = 0
            short_leaves = 0

            all_leave_dates = set()
            paid_leave_dates = set()
            unpaid_leave_dates = set()
            short_leave_dates = set()

            for leave in leave_records:
                leave_start = max(leave.request_date_from, from_date)
                leave_end = min(leave.request_date_to, to_date)

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

            total_absent_without_sunday = total_days_in_month - present_days - total_leave_days
            if total_absent_without_sunday < 0:
                total_absent_without_sunday = 0
            unpaid_leaves = unpaid_leaves
            weekly_off_to_show = min(total_weekly_offs, total_absent_without_sunday)
            absent_days = total_absent_without_sunday - weekly_off_to_show + short_leaves
            # work_days = present_days + paid_leaves + weekly_off_to_show
            total_work_able_days_month = 0
            total_work_able_days_month = total_days_in_month - total_weekly_offs
            _logger.info(f'total dayssssssssssss{total_days_in_month}')
            _logger.info(f'weekly off dayssssssssssss{total_weekly_offs}')
            work_days = present_days + paid_leaves
            _logger.info(f'present dayssssssssssss{work_days}')
            # from_date1, to_date1 = wizard.(wizard.period)
            # total_work_able_days_month = (to_date1 - from_date1).days + 1
            _logger.info(total_work_able_days_month)
            total_work_able_days_month_new = (to_date - from_date).days + 1
            _logger.info(total_work_able_days_month_new)
            total_weekly_offs_work = self.get_weekly_off_count(
                from_date,
                to_date
            )
            x_final_work_days = total_work_able_days_month_new - total_weekly_offs_work
            _logger.info(x_final_work_days)
            _logger.info('Abdullah')
            if work_days > x_final_work_days:
                work_days = x_final_work_days
            _logger.info(f'workable dayssssssssssss{total_work_able_days_month}')
            leave_days_with_weekly_off = weekly_off_to_show
            _logger.info(f'absentttttttttttt{absent_days}')

            return {
                'present_days': present_days,
                'absent_days': absent_days,
                'leave_days': leave_days_with_weekly_off,
                'paid_leaves': paid_leaves,
                'unpaid_leaves': unpaid_leaves,
                'short_leaves': short_leaves,
                'total_work_days': work_days,
                'total_month_days': total_days_in_month,
                'weekly_off': weekly_off_to_show,
                'days_with_less_work': days_with_less_work,
            }

        except Exception as e:
            _logger.error(f"Error getting attendance data for {employee.name}: {e}")
            return {
                'present_days': 0,
                'absent_days': 0,
                'leave_days': 0,
                'paid_leaves': 0,
                'unpaid_leaves': 0,
                'short_leaves': 0,
                'total_work_days': 0,
                'total_month_days': 0,
                'weekly_off': 0,
                'days_with_less_work': 0,
            }

    def get_salary_components(self, payslip, attendance_data):
        basic_salary = 0
        gross_salary = 0
        net_salary = payslip.net_wage or 0
        out_standing = 0
        salary_day = 0
        work_days = 0
        encashment = 0
        encashment_days = 0
        leave_encash = 0
        attendance_days = 0
        salary_days = 0
        allowance = 0
        umra_dept = 0
        food_over = 0
        absnty = 0
        eobi = 0
        loan_deduct = 0
        fine_debt = 0
        current_accm = 0
        credit_damage = 0
        pro_out_starting = 0
        crockery_deduction = 0
        bank_ac = 0
        wage = 0
        final_bank = 0
        contract = payslip.contract_id or payslip.employee_id.contract_id
        payslip_from = payslip.date_from
        payslip_to = payslip.date_to

        if isinstance(payslip_from, str):
            payslip_from = fields.Date.from_string(payslip_from)
        if isinstance(payslip_to, str):
            payslip_to = fields.Date.from_string(payslip_to)


        if contract:
            wage = contract.wage or 0.0
    
            if not contract.increment_history_ids:
                wage =  wage
            
            increments = contract.increment_history_ids.sorted(key=lambda x: x.date)
            
            # Check for increment DURING period (PRIORITY 1)
            for increment in increments:
                inc_date = increment.date
                if isinstance(inc_date, datetime):
                    inc_date = inc_date.date()
                
                if payslip_from <= inc_date <= payslip_to:
                    wage =  increment.new_salary or wage
            
            # Check for FIRST increment AFTER period (PRIORITY 2)
            for increment in increments:
                inc_date = increment.date
                if isinstance(inc_date, datetime):
                    inc_date = inc_date.date()
                
                if inc_date > payslip_to:
                    wage =  increment.old_salary or wage


        loan_records = self.env['hr.advance.salary'].search([
            ('employee_id', '=', payslip.employee_id.id),
            ('state', 'in', ['paid','done']),
            ('payment', '=', 'partially'),
            ('request_date', '<=', payslip_to),
            '|',
            ('payment_end_date', '=', False),
            ('payment_end_date', '>=', payslip_from),
        ])

        current_month = False
        if getattr(payslip, 'date_from', False):
            if isinstance(payslip.date_from, str):
                try:
                    current_month = fields.Date.from_string(payslip.date_from).strftime('%Y-%m')
                except Exception:
                    current_month = payslip.date_from[:7]
            else:
                current_month = payslip.date_from.strftime('%Y-%m')

        out_standing = 0.0
        pro_out_starting = 0.0
        total_loan_paid_before = 0.0
        total_loan_deduction_current = 0.0

        if current_month:
            year, month = map(int, current_month.split('-'))
            month_start_date = date(year, month, 1)

            loan_start_dates = loan_records.mapped('payment_start_date')
            if loan_start_dates:
                min_loan_date = min(loan_start_dates)
                previous_loan_deductions = self.env['hr.payslip.line'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('slip_id.date_from', '<', month_start_date),
                    ('slip_id.date_from', '>=', min_loan_date),
                    ('salary_rule_id.code', 'like', 'LOAN/%'),
                ])
            else:
                previous_loan_deductions = self.env['hr.payslip.line'].browse()  # empty recordset

            total_loan_paid_before = sum(previous_loan_deductions.mapped('total'))

            current_loan_deductions = self.env['hr.payslip.line'].search([
                ('slip_id', '=', payslip.id),
                ('salary_rule_id.code', 'like', 'LOAN/%'),
            ])
            total_loan_deduction_current = sum(current_loan_deductions.mapped('total'))
            total_loan_paid_up_to_now = total_loan_paid_before + total_loan_deduction_current

            _logger.info(f"Total LOAN paid up to {current_month}: {total_loan_paid_up_to_now}")

            _logger.info(f"=== LOAN CALCULATION SUMMARY ===")
            _logger.info(f"Employee: {payslip.employee_id.name}")
            _logger.info(f"Current Month: {current_month}")
            _logger.info(f"Previous LOAN deductions found: {len(previous_loan_deductions)}")
            _logger.info(f"Total LOAN paid before {current_month}: {total_loan_paid_before}")
            _logger.info(f"Current month LOAN deduction: {total_loan_deduction_current}")

        ONE2M_NAMES = ['line_ids', 'advance_line_ids', 'installment_ids', 'payment_line_ids', 'lines']
        LINE_DATE_FIELDS = ['date', 'payment_date', 'date_pay', 'date_due', 'payment_on', 'paid_date']
        LINE_SKIP_FIELDS = ['skip', 'is_skip', 'skipped', 'skip_this', 'skip_line']
        LINE_DEDUCTION_FIELDS = ['deduction_amount', 'amount', 'amount_to_pay', 'deducted', 'deduction']
        LINE_REMAINING_FIELDS = ['remaining_amount', 'remaining', 'balance', 'balance_amount']

        for loan in loan_records:
            loan_lines = getattr(loan, 'advance_salary_line_ids', False) or getattr(loan, 'advance_line_ids',
                                                                                    False) or getattr(loan, 'line_ids',
                                                                                                      False) or []
            year, month = map(int, current_month.split('-'))
            month_start_date = date(year, month, 1)
            # loan_outstanding = loan.amount_to_pay or loan.total_amount or loan.loan_amount or 0.0
            loan_outstanding = loan.amount_to_pay  or 0.0
            # payslip_d = sum(loan.payslip_line_ids.filtered(lambda x:x.date < month_start_date).mapped('amount'))
            # loan_outstanding = loan.amount_to_pay or loan.total_amount or loan.loan_amount or 0.0
            loan_paid = loan.amount_paid
            # out_standing += loan_outstanding + loan_paid
            #abd
            # if loan.amount_to_pay > 0:
            out_standing += loan.request_amount - total_loan_paid_before
            # else:
            #     out_standing += 0
            # loan_paid = loan.amount_paid
            # out_standing += loan_outstanding + loan_paid

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
                pro_out_starting += out_standing
                _logger.info(
                    f"✅ SKIP ACTIVE -> emp={payslip.employee_id.name} loan={loan.id} month={current_month} remaining={loan_outstanding}")
            else:
                # pro_out_starting += loan_outstanding - deduction_amount
                # abd
                # if out_standing > 0:
                pro_out_starting += out_standing - loan.deduction_amount
                # else:
                #     pro_out_starting = 0
                # _logger.info(
                #     f"❌ SKIP NOT ACTIVE -> emp={payslip.employee_id.name} loan={loan.id} month={current_month} deduct={deduction_amount} remaining={loan_outstanding - deduction_amount}")
            if loan.payment_start_date.date() > payslip_to:
                pro_out_starting = out_standing
        for line in payslip.line_ids:
            if line.code == 'GROSS':
                gross_salary = line.total
            elif line.code == 'BASIC':
                basic_salary = line.total
            elif line.code == 'NET':
                net_salary = line.total
            # elif line.code == 'ENCASH':
            #     encashment = line.total
            elif line.code == 'FA':
                food_over = line.total
            elif line.code == 'UM':
                umra_dept = line.total
            elif line.code in ['CM', 'CD']:
                crockery_deduction += line.total
            elif line.code in ['RA', 'SC', 'NSA', 'HD','REW']:
                allowance += line.total
            elif line.code == 'ABSF':
                absnty = line.total
            elif line.code == 'EOBIEE':
                eobi = line.total
            # elif line.code == 'ADV/BNK':
            elif line.salary_rule_id and line.salary_rule_id.code == 'ADV/BNK':
                bank_ac += line.total or 0
            elif line.code in ['CUT', 'LAUN', 'CHI', 'NS', 'AA','CSHD', 'ACCM', 'FI', 'DEB', 'UNI', 'MAD',
                               'FOD', 'TXD', 'SISSI', 'ABS']:
                fine_debt += line.total
            elif line.salary_rule_id and line.salary_rule_id.code in ['LOAN/EDU', 'LOAN/MED']:
                loan_deduct += line.total
            # elif line.code in ['ADV/CSH']:
            elif line.salary_rule_id and line.salary_rule_id.code == 'ADV/CSH':
                current_accm += line.total
            # elif line.code in ['ADV/FBNK']:
            elif line.salary_rule_id and line.salary_rule_id.code == 'ADV/FBNK':
                final_bank += line.total

        work_days = attendance_data.get('total_work_days', 0)

        total_month_days = attendance_data.get('total_month_days', 0)
        total_sundays = attendance_data.get('weekly_off', 0)
        working_days_in_month = total_month_days - total_sundays

        # salary_day = round(wage / working_days_in_month,2) if working_days_in_month > 0 else 0
        date_from = payslip.date_from
        date_to = payslip.date_to

        # Ensure date type
        if isinstance(date_from, str):
            date_from = fields.Date.from_string(date_from)
        if isinstance(date_to, str):
            date_to = fields.Date.from_string(date_to)

        # Total days in month
        total_days_in_month = (date_to - date_from).days + 1

        # Count Sundays only
        sunday_count = 0
        current_date = date_from
        while current_date <= date_to:
            if current_date.weekday() == 6:  # Sunday
                sunday_count += 1
            current_date += relativedelta(days=1)

        # Working days = total days - Sundays
        working_days_in_month = total_days_in_month - sunday_count

        # Salary per day
        salary_day = round(wage / working_days_in_month, 2) if working_days_in_month > 0 else 0

        encashment_days = round(encashment / salary_day, 2) if salary_day > 0 and encashment > 0 else 0
        wizard_period = self.period  # selection field value
        encashment_records = self.env['leave.encashment'].search(
            [('em_p', '=', payslip.employee_id.id), ('state', '=', 'approve'), ('month', '=', wizard_period)])
        if encashment_records:
            attendance_days = sum(
                encashment_records.mapped('attendance_lines.encash_2')
            )
            leave_encash = sum(
                encashment_records.mapped('tree_line.encash_leaves')
            )
        #           encashment = sum(encashment_rec.attendance_lines.mapped('encash_2')
        # )
        encashment_days = attendance_days + leave_encash
        salary_days = work_days + encashment_days
        if salary_days > total_days_in_month:
            salary_days = total_month_days

        return {
            'basic_salary': basic_salary,
            'gross_salary': gross_salary,
            'net_salary': net_salary,
            'out_standing': out_standing,
            'salary_day': salary_day,
            'work_days': work_days,
            'encashment': encashment,
            'encashment_days': encashment_days,
            'salary_days': salary_days,
            'allowance': allowance,
            'umra_dept': umra_dept,
            'food_over': food_over,
            'bank_ac': bank_ac,
            'absnty': absnty,
            'eobi': eobi,
            'loan_deduct': loan_deduct,
            'fine_debt': fine_debt,
            'current_accm': current_accm,
            'final_bank': final_bank,
            'credit_damage': credit_damage,
            'pro_out_starting': pro_out_starting ,
            'crockery_deduction': crockery_deduction,
            'wage': wage,
        }

    def action_print_report(self):
        self.ensure_one()

        # if self.select_employee == 'department' and not self.department_id:
        #     raise UserError("Please select departments for department-wise report.")
        # elif self.select_employee == 'employee' and not self.employee_ids:
        #     raise UserError("Please select employees for employee-wise report.")

        return self.env.ref('hr_salary_custom_report.action_salary_sheet_report_pdf').report_action(self)


class SalarySheetReport(models.AbstractModel):
    _name = 'report.hr_salary_custom_report.salary_sheet_report_template'
    _description = 'Salary Sheet Report'

    def format_amount_with_decimals(self, amount):
        """Format amount with comma as thousands separator and 2 decimal places"""
        if amount is None:
            return '0.00'
        try:
            return "{:,.2f}".format(float(amount))
        except (ValueError, TypeError):
            return '0.00'

    def format_amount(self, amount):
        """Format amount with comma as thousands separator"""
        if amount is None:
            return '0'
        try:
            return "{:,.0f}".format(float(amount))
        except (ValueError, TypeError):
            return '0'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['salary.sheet.report.wizard'].browse(docids)
        report_data = self._get_report_data(wizard)
        if not report_data:
            report_data = {}

            # Make sure company_name is always available
        if 'company_name' not in report_data or not report_data['company_name']:
            report_data['company_name'] = wizard.company_id.name or 'Company Name'

        return {
            'doc_ids': docids,
            'doc_model': 'salary.sheet.report.wizard',
            'docs': wizard,
            'data': report_data,
        }

    def _get_report_data(self, wizard):
        from_date, to_date =  wizard._get_period_dates(wizard.period)
        period_name = datetime.strptime(wizard.period + '-01', '%Y-%m-%d').strftime('%b %Y')

        employees = self.env['hr.employee']

        # if wizard.select_employee == 'company':
        #     employees = self.env['hr.employee'].with_context(active_test=False).search([
        #         ('company_id', '=', wizard.company_id.id)
        #     ])
        if wizard.select_employee == 'company':
            domain = [('company_id', '=', wizard.company_id.id)]

            if wizard.archive:
                domain.append(('active', '=', False))  # only archived

            employees = self.env['hr.employee'].with_context(active_test=False).search(domain)
        # elif wizard.select_employee == 'department':
        #     if wizard.department_id:
        #         employees = self.env['hr.employee'].with_context(active_test=False).search([
        #             ('department_id', 'in', wizard.department_id.ids)
        #         ])
        #     else:
        #         employees = self.env['hr.employee'].with_context(active_test=False).search([
        #             ('company_id', '=', wizard.company_id.id)
        #         ])
        elif wizard.select_employee == 'department':
            domain = []

            if wizard.department_id:
                domain.append(('department_id', 'in', wizard.department_id.ids))
            else:
                domain.append(('company_id', '=', wizard.company_id.id))

            if wizard.archive:
                domain.append(('active', '=', False))  # only archived

            employees = self.env['hr.employee'].with_context(active_test=False).search(domain)
        # elif wizard.select_employee == 'employee':
        #     if wizard.employee_ids:
        #         employees = wizard.employee_ids
        #     else:
        #         employees = self.env['hr.employee'].with_context(active_test=False).search([
        #             ('company_id', '=', wizard.company_id.id)
        #         ])
        elif wizard.select_employee == 'employee':
            if wizard.employee_ids:
                employees = wizard.employee_ids.filtered(
                    lambda e: not e.active if wizard.archive else True
                )
            else:
                domain = [('company_id', '=', wizard.company_id.id)]

                if wizard.archive:
                    domain.append(('active', '=', False))  # only archived

                employees = self.env['hr.employee'].with_context(active_test=False).search(domain)
        # elif wizard.select_employee == 'analytic':
        #     if wizard.analytic_ids:
        #         contracts = self.env['hr.contract'].sudo().search([
        #             ('analytic_account_id', 'in', wizard.analytic_ids.ids),
        #         ])
        #         employees = contracts.mapped('employee_id.id')
        #         # employees = employees.sorted()
        #         employees = self.env['hr.employee'].sudo().search([
        #             ('id', 'in', employees)
        #         ])
        #     else:
        #         # employees = self.env['hr.employee']

        #         employees = self.env['hr.employee'].with_context(active_test=False).search([
        #             ('company_id', '=', wizard.company_id.id)
        #         ])
        elif wizard.select_employee == 'analytic':
            domain = []
            if wizard.analytic_ids:
                payslips_in_period = self.env['hr.payslip'].sudo().search([
                    ('state', 'in', ['verify', 'done', 'paid']),
                    ('date_from', '>=', from_date),
                    ('date_to', '<=', to_date),
                    ('struct_id.name', 'not ilike', 'Allowance Structure'),
                ])
                employee_ids = []
                analytic = False
                for slip in payslips_in_period:
                    if slip.analytic_account_id:
                        analytic = slip.analytic_account_id
                    elif slip.contract_id and slip.contract_id.analytic_account_id:
                        analytic = slip.contract_id.analytic_account_id

                    if analytic and analytic.id in wizard.analytic_ids.ids:
                        employee_ids.append(slip.employee_id.id)
                    domain = [('id', 'in', list(set(employee_ids)))]
            else:
                domain.append(('company_id', '=', wizard.company_id.id))

            if wizard.archive:
                domain.append(('active', '=', False))

            employees = self.env['hr.employee'].with_context(active_test=False).search(
                domain)

        # Employee status tracking function
        def get_employee_status(emp, from_date, to_date):
            _logger.info('get_employee_status')
            """
            Determine employee status for the period:
            - 'N' for new employees (joined in current month)
            - 'X' for employees who resigned in same month they joined
            - 'R' for employees who resigned in current month (but joined earlier)
            - '' for regular employees
            """
            contracts = self.env['hr.contract'].search([
                ('employee_id', '=', emp.id)
            ], order='date_start asc')

            if not contracts:
                return ''

            first_contract = contracts[0]
            latest_contract = contracts[-1]

            # Check if employee joined in current month
            joined_this_month = (first_contract.date_start >= from_date and
                                 first_contract.date_start <= to_date)

            # Check if employee resigned in current month
            resigned_this_month = False
            if (latest_contract.date_end and
                    latest_contract.date_end >= from_date and
                    latest_contract.date_end <= to_date and
                    latest_contract.state == 'close'):

                # Check if there are no new contracts after resignation
                new_contracts_after = self.env['hr.contract'].search([
                    ('employee_id', '=', emp.id),
                    ('date_start', '>', latest_contract.date_end)
                ])

                if not new_contracts_after:
                    resigned_this_month = True

            # Check if employee resigned in the same month they joined
            resigned_same_month = False
            if resigned_this_month:
                if (first_contract.date_start.year == latest_contract.date_end.year and
                        first_contract.date_start.month == latest_contract.date_end.month):
                    resigned_same_month = True

            if joined_this_month and resigned_same_month:
                return 'X'
            elif joined_this_month:
                return 'N'
            elif resigned_this_month:
                return 'R'
            else:
                return ''

        domain = [
            ('state', 'in', ['verify', 'done', 'paid']),
            ('date_from', '>=', from_date),
            ('date_to', '<=', to_date),
            ('struct_id.name', 'not ilike', 'Allowance Structure'),
            ('employee_id', 'in', employees.ids)
        ]
        payslip_records = self.env['hr.payslip'].sudo().search(domain)

        # raise ValidationError(f"{domain}-----{payslip_records}-----")

        report_data = {
            'company_name': wizard.company_id.name,
            'period_name': period_name,
            'from_date': from_date.strftime('%d/%m/%Y'),
            'to_date': to_date.strftime('%d/%m/%Y'),
            'print_date': fields.Date.today().strftime('%d/%m/%Y'),
            'departments': [],
            'records': [],
            'has_data': False,
            'grand_totals': {},
            'grand_statistics': {},
        }
        _logger.info('payslip_records')
        _logger.info('payslip_records')
        _logger.info('payslip_records')
        _logger.info('payslip_records')
        _logger.info(payslip_records)
        

        if not payslip_records:
            report_data['message'] = f'No salary data found for {period_name}'
            return report_data

        grand_totals = {
            'present_days': 0,
            'absent_days': 0,
            'leave_days': 0,
            'paid_leaves': 0,
            'unpaid_leaves': 0,
            'wage': 0,
            'basic_salary': 0,
            'out_standing': 0,
            'salary_day': 0,
            'work_days': 0,
            'encashment': 0,
            'encashment_days': 0,
            'salary_days': 0,
            'allowance': 0,
            'gross_salary': 0,
            'umra_dept': 0,
            'bank_ac': 0,
            'food_over': 0,
            'absnty': 0,
            'eobi': 0,
            'loan_deduct': 0,
            'fine_debt': 0,
            'current_accm': 0,
            'final_bank': 0,
            'crockery_deduction': 0,
            'pro_out_standing': 0,
            'net_salary': 0,
            'employee_count': 0,
        }

        def get_employee_statistics(employee_domain):
            all_employees = self.env['hr.employee'].with_context(active_test=False).search(employee_domain)
            _logger.info('get_employee_statistics')
            _logger.info('get_employee_statistics')
            _logger.info('get_employee_statistics')
            _logger.info('get_employee_statistics')
            _logger.info(all_employees)
            total_new_joinings = 0
            total_resigned = 0

            for emp in all_employees:
                contracts = self.env['hr.contract'].search([
                    ('employee_id', '=', emp.id)
                ], order='date_start asc')

                if contracts:
                    first_contract = contracts[0]
                    latest_contract = contracts[-1]

                    if first_contract.date_start >= from_date and first_contract.date_start <= to_date:
                        total_new_joinings += 1

                    if (latest_contract.date_end and
                            latest_contract.date_end >= from_date and
                            latest_contract.date_end <= to_date and
                            latest_contract.state == 'close'):

                        new_contracts_after = self.env['hr.contract'].search([
                            ('employee_id', '=', emp.id),
                            ('date_start', '>', latest_contract.date_end)
                        ])

                        if not new_contracts_after:
                            total_resigned += 1
            
            return {
                'total_employees': len(all_employees),
                'new_joinings': total_new_joinings,
                'resigned_employees': total_resigned,
            }
        employee_domain = []    
        _logger.info('employee_domain')
        _logger.info('employee_domain')
        _logger.info('employee_domain')
        _logger.info('employee_domain')
        _logger.info(employee_domain)
        if wizard.select_employee == 'company':
            _logger.info('companyyyyyyyyyy is set on wizardddddddddddd22222')
            
            employee_domain = [('company_id', '=', wizard.company_id.id)]
        elif wizard.select_employee == 'department':
            if wizard.department_id:
                employee_domain = [('department_id', 'in', wizard.department_id.ids)]
            else:
                employee_domain = [('company_id', '=', wizard.company_id.id)]
        elif wizard.select_employee == 'employee':
            if wizard.employee_ids:
                employee_domain = [('id', 'in', wizard.employee_ids.ids)]
            else:
                employee_domain = [('company_id', '=', wizard.company_id.id)]


        elif wizard.select_employee == 'analytic':
            if wizard.analytic_ids:
                payslips_in_period = self.env['hr.payslip'].sudo().search([
                    ('state', 'in', ['verify', 'done', 'paid']),
                    ('date_from', '>=', from_date),
                    ('date_to', '<=', to_date),
                    ('struct_id.name', 'not ilike', 'Allowance Structure'),
                ])
                emp_ids = []
                analytic = False
                for slip in payslips_in_period:
                    if slip.analytic_account_id:
                        analytic = slip.analytic_account_id

                        # Priority 2: Contract analytic (fallback)
                    elif slip.contract_id and slip.contract_id.analytic_account_id:
                        analytic = slip.contract_id.analytic_account_id
                    if analytic and analytic.id in wizard.analytic_ids.ids:
                        emp_ids.append(slip.employee_id.id)
                    employee_domain = [('id', 'in', list(set(emp_ids)))]
            else:
                employee_domain = [('company_id', '=', wizard.company_id.id)]
        _logger.info(f"Employee domain: {employee_domain}")
        report_data['grand_statistics'] = get_employee_statistics(employee_domain)

        _logger.info('report_data')
        _logger.info('report_data')
        _logger.info('report_data')
        _logger.info('report_data')
        _logger.info('report_data')
        _logger.info('report_data')
        _logger.info('report_data')
        # raise ValidationError(f"{report_data['grand_statistics']}----{wizard.select_employee}---{employee_domain}")

        if wizard.select_employee in ['employee', 'department', 'company','analytic']:
            grouped = {}
            for slip in payslip_records:
                dept = slip.employee_id.department_id or self.env['hr.department']
                dept_name = dept.name if dept else 'No Department'
                grouped.setdefault(dept, []).append(slip)
                

            for dept, dept_payslips in grouped.items():
                dept_employee_domain = [('department_id', '=', dept.id if dept else False)]
                dept_stats = get_employee_statistics(dept_employee_domain)

                dept_data = {
                    'department_name': dept.name if dept else 'No Department',
                    'employees': [],
                    'dept_totals': {
                        'present_days': 0,
                        'absent_days': 0,
                        'leave_days': 0,
                        'paid_leaves': 0,
                        'unpaid_leaves': 0,
                        'wage': 0,
                        'basic_salary': 0,
                        'out_standing': 0,
                        'salary_day': 0,
                        'work_days': 0,
                        'encashment': 0,
                        'encashment_days': 0,
                        'salary_days': 0,
                        'allowance': 0,
                        'gross_salary': 0,
                        'umra_dept': 0,
                        'bank_ac': 0,
                        'food_over': 0,
                        'absnty': 0,
                        'eobi': 0,
                        'loan_deduct': 0,
                        'fine_debt': 0,
                        'current_accm': 0,
                        'final_bank': 0,
                        'crockery_deduction': 0,
                        'pro_out_standing': 0,
                        'net_salary': 0,
                        'employee_count': 0,
                    },
                    'dept_statistics': dept_stats
                }

                employee_data_list = []

                for seq, payslip in enumerate(dept_payslips, 1):
                    attendance_data = wizard.get_attendance_data(
                        payslip.employee_id, from_date, to_date)
                    salary_data = wizard.get_salary_components(payslip, attendance_data)
                    emp = payslip.employee_id

                    emp_status = get_employee_status(emp, from_date, to_date)

                    employee_data = {
                        'sr_no': seq,
                        'emp_code': emp.barcode or emp.id,
                        'emp_name': emp.name,
                        'designation': emp.job_id.name or '',
                        'emp_status': emp_status,
                        'present_days': attendance_data['present_days'],
                        'absent_days': attendance_data['absent_days'],
                        'leave_days': attendance_data['leave_days'],
                        'pl': attendance_data['paid_leaves'],
                        'unpaid_leaves': attendance_data['unpaid_leaves'],
                        'wage': salary_data['wage'],
                        'basic_salary': salary_data['basic_salary'],
                        'out_standing': salary_data['out_standing'],
                        'salary_day': salary_data['salary_day'],
                        'work_days': salary_data['work_days'],
                        'encashment': salary_data['encashment'],
                        'encashment_days': salary_data['encashment_days'],
                        'salary_days': salary_data['salary_days'],
                        'allowance': salary_data['allowance'],
                        'gross_salary': salary_data['gross_salary'],
                        'umra_dept': salary_data['umra_dept'],
                        'bank_ac': salary_data['bank_ac'],
                        'food_over': salary_data['food_over'],
                        'absnty': salary_data['absnty'],
                        'eobi': salary_data['eobi'],
                        'loan_deduct': salary_data['loan_deduct'],
                        'fine_debt': salary_data['fine_debt'],
                        'current_accm': salary_data['current_accm'],
                        'final_bank': salary_data['final_bank'],
                        'crockery_deduction': salary_data['crockery_deduction'],
                        'pro_out_standing': salary_data['pro_out_starting'],
                        'net_salary': salary_data['net_salary'],
                        # Store actual values for totaling
                        '_wage': salary_data['wage'],
                        '_basic_salary': salary_data['basic_salary'],
                        '_out_standing': salary_data['out_standing'],
                        '_salary_day': salary_data['salary_day'],
                        '_encashment': salary_data['encashment'],
                        '_allowance': salary_data['allowance'],
                        '_gross_salary': salary_data['gross_salary'],
                        '_umra_dept': salary_data['umra_dept'],
                        '_bank_ac': salary_data['bank_ac'],
                        '_food_over': salary_data['food_over'],
                        '_absnty': salary_data['absnty'],
                        '_eobi': salary_data['eobi'],
                        '_loan_deduct': salary_data['loan_deduct'],
                        '_fine_debt': salary_data['fine_debt'],
                        '_current_accm': salary_data['current_accm'],
                        '_final_bank': salary_data['final_bank'],
                        '_crockery_deduction': salary_data['crockery_deduction'],
                        '_pro_out_standing': salary_data['pro_out_starting'],
                        '_net_salary': salary_data['net_salary'],
                    }

                    employee_data_list.append(employee_data)

                # Sort employees by basic salary in descending order (highest first)
                # raise ValidationError(f"{employee_data_list}----------")
                employee_data_list.sort(key=lambda x: x['_wage'], reverse=True)

                # Now add formatted data to department
                for seq, emp_data in enumerate(employee_data_list, 1):
                    # Update sequence number after sorting
                    emp_data['sr_no'] = seq

                    # Format the amounts for display
                    formatted_emp_data = emp_data.copy()
                    formatted_emp_data['wage'] = self.format_amount(emp_data['_wage'])
                    formatted_emp_data['basic_salary'] = self.format_amount(emp_data['_basic_salary'])
                    formatted_emp_data['out_standing'] = self.format_amount(emp_data['_out_standing'])
                    formatted_emp_data['salary_day'] = self.format_amount(emp_data['_salary_day'])
                    formatted_emp_data['encashment'] = self.format_amount(emp_data['_encashment'])
                    formatted_emp_data['allowance'] = self.format_amount(emp_data['_allowance'])
                    formatted_emp_data['gross_salary'] = self.format_amount(emp_data['_gross_salary'])
                    formatted_emp_data['umra_dept'] = self.format_amount(emp_data['_umra_dept'])
                    formatted_emp_data['bank_ac'] = self.format_amount(emp_data['_bank_ac'])
                    formatted_emp_data['food_over'] = self.format_amount(emp_data['_food_over'])
                    formatted_emp_data['absnty'] = self.format_amount(emp_data['_absnty'])
                    formatted_emp_data['eobi'] = self.format_amount(emp_data['_eobi'])
                    formatted_emp_data['loan_deduct'] = self.format_amount(emp_data['_loan_deduct'])
                    formatted_emp_data['fine_debt'] = self.format_amount(emp_data['_fine_debt'])
                    formatted_emp_data['current_accm'] = self.format_amount(emp_data['_current_accm'])
                    formatted_emp_data['final_bank'] = self.format_amount(emp_data['_final_bank'])
                    formatted_emp_data['crockery_deduction'] = self.format_amount(emp_data['_crockery_deduction'])
                    formatted_emp_data['pro_out_standing'] = self.format_amount(emp_data['_pro_out_standing'])
                    formatted_emp_data['net_salary'] = self.format_amount(emp_data['_net_salary'])

                    dept_data['employees'].append(formatted_emp_data)

                    # Update department totals with actual values
                    dept_data['dept_totals']['present_days'] += emp_data['present_days']
                    dept_data['dept_totals']['absent_days'] += emp_data['absent_days']
                    dept_data['dept_totals']['leave_days'] += emp_data['leave_days']
                    dept_data['dept_totals']['paid_leaves'] += emp_data['pl']
                    dept_data['dept_totals']['unpaid_leaves'] += emp_data['unpaid_leaves']
                    dept_data['dept_totals']['wage'] += emp_data['_wage']
                    dept_data['dept_totals']['basic_salary'] += emp_data['_basic_salary']
                    dept_data['dept_totals']['out_standing'] += emp_data['_out_standing']
                    dept_data['dept_totals']['salary_day'] += emp_data['_salary_day']
                    dept_data['dept_totals']['work_days'] += emp_data['work_days']
                    dept_data['dept_totals']['encashment'] += emp_data['_encashment']
                    dept_data['dept_totals']['encashment_days'] += emp_data['encashment_days']
                    dept_data['dept_totals']['salary_days'] += emp_data['salary_days']
                    dept_data['dept_totals']['allowance'] += emp_data['_allowance']
                    dept_data['dept_totals']['gross_salary'] += emp_data['_gross_salary']
                    dept_data['dept_totals']['umra_dept'] += emp_data['_umra_dept']
                    dept_data['dept_totals']['bank_ac'] += emp_data['_bank_ac']
                    dept_data['dept_totals']['food_over'] += emp_data['_food_over']
                    dept_data['dept_totals']['absnty'] += emp_data['_absnty']
                    dept_data['dept_totals']['eobi'] += emp_data['_eobi']
                    dept_data['dept_totals']['loan_deduct'] += emp_data['_loan_deduct']
                    dept_data['dept_totals']['fine_debt'] += emp_data['_fine_debt']
                    dept_data['dept_totals']['current_accm'] += emp_data['_current_accm']
                    dept_data['dept_totals']['final_bank'] += emp_data['_final_bank']
                    dept_data['dept_totals']['crockery_deduction'] += emp_data['_crockery_deduction']
                    dept_data['dept_totals']['pro_out_standing'] += emp_data['_pro_out_standing']
                    dept_data['dept_totals']['net_salary'] += emp_data['_net_salary']
                    dept_data['dept_totals']['employee_count'] += 1

                    # Update grand totals
                    grand_totals['present_days'] += emp_data['present_days']
                    grand_totals['absent_days'] += emp_data['absent_days']
                    grand_totals['leave_days'] += emp_data['leave_days']
                    grand_totals['paid_leaves'] += emp_data['pl']
                    grand_totals['unpaid_leaves'] += emp_data['unpaid_leaves']
                    grand_totals['wage'] += emp_data['_wage']
                    grand_totals['basic_salary'] += emp_data['_basic_salary']
                    grand_totals['out_standing'] += emp_data['_out_standing']
                    grand_totals['salary_day'] += emp_data['_salary_day']
                    grand_totals['work_days'] += emp_data['work_days']
                    grand_totals['encashment'] += emp_data['_encashment']
                    grand_totals['encashment_days'] += emp_data['encashment_days']
                    grand_totals['salary_days'] += emp_data['salary_days']
                    grand_totals['allowance'] += emp_data['_allowance']
                    grand_totals['gross_salary'] += emp_data['_gross_salary']
                    grand_totals['umra_dept'] += emp_data['_umra_dept']
                    grand_totals['bank_ac'] += emp_data['_bank_ac']
                    grand_totals['food_over'] += emp_data['_food_over']
                    grand_totals['absnty'] += emp_data['_absnty']
                    grand_totals['eobi'] += emp_data['_eobi']
                    grand_totals['loan_deduct'] += emp_data['_loan_deduct']
                    grand_totals['fine_debt'] += emp_data['_fine_debt']
                    grand_totals['current_accm'] += emp_data['_current_accm']
                    grand_totals['final_bank'] += emp_data['_final_bank']
                    grand_totals['crockery_deduction'] += emp_data['_crockery_deduction']
                    grand_totals['pro_out_standing'] += emp_data['_pro_out_standing']
                    grand_totals['net_salary'] += emp_data['_net_salary']
                    grand_totals['employee_count'] += 1

                report_data['departments'].append(dept_data)

            report_data['departments'] = sorted(
                report_data['departments'],
                key=lambda d: d.get('department_name', '').lower()
            )

            for dept in report_data['departments']:
                for key, value in dept.get('dept_totals', {}).items():
                    if isinstance(value, (int, float)):
                        dept['dept_totals'][key] = self.format_amount(value)

            for key, value in grand_totals.items():
                if isinstance(value, (int, float)):
                    grand_totals[key] = self.format_amount(value)

            report_data['grand_totals'] = grand_totals
            report_data['has_data'] = True
            # raise ValidationError(f"{report_data}----------")
            return report_data
