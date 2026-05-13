from odoo import models, fields, api
from odoo.exceptions import ValidationError
import calendar
from datetime import datetime, date, timedelta
import logging
_logger = logging.getLogger(__name__)


class FoodAllowance(models.Model):
    _inherit = 'food.allowances'

    def done_button(self):
        _logger.info('startttttttttttt proceeeeeeeeeeeeeeed')
        _logger.info('startttttttttttt proceeeeeeeeeeeeeeed')
        # Call original method first
        res = super().done_button()
        for rec in self:

            # 🔒 Safety check
            if not rec.month_start_date or not rec.month_end_date:
                continue

            start_date = rec.month_start_date
            end_date = rec.month_end_date
            _logger.info(f"start dateeeeeeeeeeeeeeee{start_date}")
            _logger.info(f"start dateeeeeeeeeeeeeeee{end_date}")

            for line in rec.food_line_template:
                emp = line.employee_id
                contract = emp.contract_id

                if not contract:
                    continue

                wage = contract.wage or 0.0
                _logger.info(f"wageeeeeeeeeeeeee{wage}")

                # 1️⃣ 7% food limit
                food_limit_7percent = wage * 0.07
                _logger.info(f"percentttttttttttt 7777777777777{food_limit_7percent}")

                # 2️⃣ Attendance calculation
                # attendances = self.env['hr.attendance'].search([
                #     ('employee_id', '=', emp.id),
                #     ('check_in', '>=', datetime.combine(start_date, datetime.min.time())),
                #     ('check_in', '<=', datetime.combine(end_date, datetime.max.time())),
                # ])
                # _logger.info(f"attendanceeeeeeeeeeeeeeeeee{attendances}")

                # working_days = len(set(
                #     a.check_in.date()
                #     for a in attendances
                #     if a.worked_hours > 6
                # ))
                if emp.resource_calendar_id.x_studio_is_zero:
                    attendance_count = self.env['hr.attendance'].search_count([
                        ('employee_id', '=', emp.id),
                        ('check_in', '>=', datetime.combine(start_date, datetime.min.time())),
                        ('check_in', '<=', datetime.combine(end_date, datetime.max.time()))
                    ])
                else:
                    attendance_count = self.env['hr.attendance'].search_count([
                        ('employee_id', '=', emp.id),
                        ('check_in', '>=', datetime.combine(start_date, datetime.min.time())),
                        ('check_in', '<=', datetime.combine(end_date, datetime.max.time())),
                        ('worked_hours', '>=', 6),

                    ])
                # _logger.info(f"working daysssssssssssssssssss{working_days}")
                paid_leaves = self.env['hr.leave'].search([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'validate'),
                    ('request_date_from', '<=', end_date),
                    ('request_date_to', '>=', start_date),
                    ('holiday_status_id.is_leave_unpaid', '!=', True),
                    ('leave_encashed_check', '=', False),
                    # ('holiday_status_id.unpaid', '=', False),  # Only paid leaves
                ])

                paid_leave_days = sum(
                    leave.number_of_days
                    for leave in paid_leaves
                )
                # working_days = working_days + paid_leave_days
                working_days = attendance_count + paid_leave_days

                # 3️⃣ Allowed percentage
                # if contract.contract_type_id.name != '':
                if working_days <= 10:
                    allowed_percentage = 0.3333
                elif working_days <= 20:
                    allowed_percentage = 0.6666
                else:
                    allowed_percentage = 1.0

                # 4️⃣ Allowed amount
                if contract.contract_type_id.name != 'Daily Wage':
                    allowed_amount = food_limit_7percent * allowed_percentage
                else:
                    allowed_amount = food_limit_7percent * working_days
                _logger.info(f"allowed amountttttttttttttttttt{allowed_amount}")
                _logger.info(f"allowed percentageeeeeeeeeeee{allowed_percentage}")
                # 5️⃣ Deduction
                deduction_amount = max(0.0, line.total_amount - allowed_amount)
                _logger.info(f"deductionnnnnnnnnnnnnnnnnnnn amountttttttt{deduction_amount}")

                # 6️⃣ Write values
                line.write({
                    'working_days': working_days,
                    'allowed_food_limit': round(allowed_amount),
                    'food_deduction': round(deduction_amount),
                })

        return res
        # for rec in self:
        #     month = rec.date.month
        #     year = rec.date.year
        #
        #     start_date = date(year, month, 1)
        #     end_date = date(year, month, calendar.monthrange(year, month)[1])
        #
        #     for line in rec.food_line_template:
        #
        #         emp = line.employee_id
        #         contract = emp.contract_id
        #
        #         if not contract:
        #             continue
        #
        #         wage = contract.wage
        #
        #         # 1) Employee can get 7% of wage
        #         food_limit_7percent = wage * 0.07
        #
        #         # 2) Working days in the selected month
        #         attendances = self.env['hr.attendance'].search([
        #             ('employee_id', '=', emp.id),
        #             ('check_in', '>=', datetime.combine(start_date, datetime.min.time())),
        #             ('check_in', '<=', datetime.combine(end_date, datetime.max.time())),
        #         ])
        #
        #         working_days = len(set(a.check_in.date() for a in attendances if a.worked_hours > 6))
        #
        #         # 3) Allowed percentage rules
        #         if working_days <= 10:
        #             allowed_percentage = 0.33
        #         elif working_days <= 20:
        #             allowed_percentage = 0.66
        #         else:
        #             allowed_percentage = 1.0
        #
        #         # 4) Allowed amount
        #         allowed_amount = food_limit_7percent * allowed_percentage
        #
        #         # 5) Deduction calculation
        #         if line.total_amount > allowed_amount:
        #             deduction_amount = line.total_amount - allowed_amount
        #         else:
        #             deduction_amount = 0.0
        #
        #         # 6) Write computed results
        #         line.write({
        #             'working_days': working_days,
        #             'allowed_food_limit': allowed_amount,
        #             'food_deduction': deduction_amount,
        #         })
        #
        # return res


class FoodAllowancesLine(models.Model):
    _inherit = 'food.allowances.line'

    allowed_food_limit = fields.Float(string="Allowed Limit", digits=(16, 0), readonly=True)
    food_deduction = fields.Float(string="Deduction", digits=(16, 0), readonly=True)
    working_days = fields.Integer(string="Working Days", readonly=True)
