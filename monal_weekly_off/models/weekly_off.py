from odoo import models, api, fields, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta
import calendar
import logging

logger = logging.getLogger(__name__)


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_leave_unpaid = fields.Boolean(string='Unpaid Leave', default=False)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    emp_type = fields.Selection([
        ('local', 'Local'),
        ('outsider', 'Outsider'),
        ('northern', 'Northern'),
    ], default=False, track_visibility='always')


class HRLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    # monal_evaluation_period_id = fields.Many2one(
    #     'monal.evaluation.period',
    #     string="Evaluation Period",
    #     help="The evaluation period for which this allocation was created."
    # )
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

    def action_allocate_weekly_off(self):
        logger.info("🕒 Running Monthly Weekly Off Allocation...")
        leave_type = self.env['hr.leave.type'].search([('name', '=', 'Weekly Off')], limit=1)
        if not leave_type:
            raise ValidationError("Leave Type 'Weekly Off' not found.")

        today = date.today()

        current_month_start = today.replace(day=1)
        current_month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])

        # period = self.env['monal.evaluation.period'].search([
        #     ('period_start_date', '=', current_month_start),
        #     ('period_end_date', '=', current_month_end),
        # ], limit=1)
        #
        # # ✅ If not found, create it automatically
        # if not period:
        #     month_str = f"{today.month:02}"  # e.g. '09'
        #     period = self.env['monal.evaluation.period'].create({
        #         'month': month_str,
        #         'year': today.year,
        #         # period_start_date & end_date will compute automatically
        #     })
        #     logger.info(f"Created new evaluation period: {period.name}")
        current_month_value = f"{today.year}-{today.month:02}"

        # You already have month_start_date and month_end_date in allocation
        month = current_month_value
        month_start_date = current_month_start
        month_end_date = current_month_end

        next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)
        next_month_end = next_month_start.replace(
            day=calendar.monthrange(next_month_start.year, next_month_start.month)[1])
        logger.info(today)
        logger.info(current_month_start)
        logger.info(current_month_end)
        logger.info(next_month_start)
        logger.info(next_month_end)

        # today = date.today()
        # last_day = calendar.monthrange(today.year, today.month)[1]
        #
        # # 🚫 Only run on the last day of the month
        # # if today.day != last_day:
        # #     logger.info("Not the last day of the month — exiting.")
        # #     return

        employees = self.env['hr.employee'].search([])
        for emp in employees:
            if emp.emp_type:
                if emp.resource_calendar_id.x_studio_is_zero:
                    attendance_count = self.env['hr.attendance'].search_count([
                        ('employee_id', '=', emp.id),
                        ('check_in', '>=', current_month_start),
                        ('check_in', '<=', current_month_end)
                    ])
                else:
                    attendance_count = self.env['hr.attendance'].search_count([
                        ('employee_id', '=', emp.id),
                        ('check_in', '>=', current_month_start),
                        ('check_in', '<=', current_month_end),
                        ('worked_hours', '>=', 6),

                    ])

                logger.info(f"{attendance_count} Total Attendancessssssssss")
                sundays_count = 0
                day = current_month_start
                while day <= current_month_end:
                    if day.weekday() == 6:  # 6 = Sunday (0=Monday, 6=Sunday)
                        sundays_count += 1
                    day += timedelta(days=1)

                logger.info("Total Sundays in month: %s", sundays_count)
                logger.info("Total Sundays in month: %s", sundays_count)
                logger.info("Total Sundays in month: %s", sundays_count)
                logger.info("Total Sundays in month: %s", sundays_count)
                logger.info("Total Sundays in month: %s", sundays_count)
                logger.info("Total Sundays in month: %s", sundays_count)

                # ✅ Validated Paid Leaves
                paid_leave_count = self.env['hr.leave'].search_count([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'validate'),
                    ('request_date_from', '>=', current_month_start),
                    ('request_date_to', '<=', current_month_end),
                    ('holiday_status_id.is_leave_unpaid', '=', False),
                    ('leave_encashed_check', '=', False)
                ])
                logger.info(f"{paid_leave_count} Total LEavesssssssssssssss")
                total_days = attendance_count + paid_leave_count
                logger.info(f"{total_days} Total Dayssssssssss")

                total_month_days = (current_month_end - current_month_start).days + 1

                # Count Sundays in the month
                sundays_in_month = 0
                day = current_month_start
                while day <= current_month_end:
                    if day.weekday() == 6:  # Sunday
                        sundays_in_month += 1
                    day += timedelta(days=1)

                # Calculate actual working days of the month
                working_days = total_month_days - sundays_in_month

                logger.info(f"Total Days: {total_month_days}")
                logger.info(f"Sundays: {sundays_in_month}")
                logger.info(f"Working Days: {working_days}")

                # Now compare attendance with working days
                if total_days >= working_days:
                    extra_days = total_days - working_days
                    # else:
                    #     extra_days = 0
                    existing_alloc = self.env['hr.leave.allocation'].search([
                        ('employee_id', '=', emp.id),
                        ('holiday_status_id', '=', leave_type.id),
                        ('state', '=', 'validate'),
                        # ('state', '=', 'validate1'),
                        ('date_from', '>=', next_month_start),
                        ('date_to', '<=', next_month_end),
                        # ('name', '=', f"Weekly Off Allocation - {next_month.strftime('%B')}")
                    ], limit=1)
                    leaves = 0
                    if existing_alloc:
                        pass
                        # leaves = existing_alloc.number_of_days
                        # existing_alloc.action_refuse()
                        # existing_alloc.unlink()
                        # ➕ Update existing allocation
                        # existing_alloc.write({
                        #     'number_of_days': existing_alloc.number_of_days + extra_days,
                        #     'date_from': next_month,
                        #     'date_to': next_month_end,
                        # })
                        # logger.info(f"✅ Updated allocation for {emp.name}: +{extra_days} days")
                    else:
                        old_existing_alloc = self.env['hr.leave.allocation'].search([
                            ('employee_id', '=', emp.id),
                            ('holiday_status_id', '=', leave_type.id),
                            ('state', '=', 'validate'),
                            # ('state', '=', 'validate1'),
                            ('date_from', '>=', current_month_start),
                            ('date_to', '<=', current_month_end),
                        ], limit=1)
                        remaining_leaves = old_existing_alloc.max_leaves - old_existing_alloc.leaves_taken  if old_existing_alloc else 0
                        extra_days = extra_days + remaining_leaves
                        if emp.emp_type == 'local':
                            extra_days = 2 if extra_days > 2 else extra_days  # = extra_days
                        elif emp.emp_type == 'outsider':
                            if sundays_count < 5:
                                extra_days = 4 if extra_days > 4 else extra_days
                            else:
                                extra_days = 5 if extra_days > 5 else extra_days
                        elif emp.emp_type == 'northern':
                            extra_days = 20 if extra_days > 20 else extra_days  # = extra_days
                        if extra_days > 0:
                            new_alloc = self.env['hr.leave.allocation'].create({
                                'employee_id': emp.id,
                                'holiday_status_id': leave_type.id,
                                'number_of_days': extra_days,
                                'name': f"Weekly Off Allocation - {next_month_start.strftime('%B')}",
                                'date_from': next_month_start,
                                'date_to': next_month_end,
                                'state': 'confirm',
                                # 'monal_evaluation_period_id': period.id,
                                'month': f"{next_month_start.month:02}-{next_month_start.year}",
                                'month_start_date': next_month_start,
                                'month_end_date': next_month_end,
                            })
                            new_alloc.action_approve()
                            new_alloc.action_validate()
                            logger.info(f"✅ Created new allocation for {emp.name}: {extra_days} days")
