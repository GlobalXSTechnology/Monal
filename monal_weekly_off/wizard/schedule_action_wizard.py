from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import calendar
import logging

logger = logging.getLogger(__name__)


class WeeklyOffAllocationWizard(models.TransientModel):
    _name = 'weekly.off.allocation.wizard'
    _description = 'Manual Weekly Off Allocation Wizard'

    # monal_evaluation_period_id = fields.Many2one(
    #     'monal.evaluation.period',
    #     string="Evaluation Period",
    #     required=False,
    #     help="Select the evaluation period you want to run allocations for."
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

    def action_create_allocations(self):
        logger.info('startttttttttttttttttttttttttttt')
        """Run the same allocation logic manually for the selected period."""
        self.ensure_one()
        period = self.month
        leave_type = self.env['hr.leave.type'].search([('name', '=', 'Weekly Off')], limit=1)
        if not leave_type:
            raise ValidationError("Leave Type 'Weekly Off' not found.")

        # Dates come from selected period
        current_month_start = self.month_start_date
        current_month_end = self.month_end_date
        logger.info(current_month_end)
        logger.info(current_month_end)

        # We still want to allocate for the *next* month as in your scheduled action
        next_month_start = (current_month_start + relativedelta(months=1)).replace(day=1)
        next_month_end = next_month_start.replace(
            day=calendar.monthrange(next_month_start.year, next_month_start.month)[1])
        logger.info(next_month_start)
        logger.info(next_month_end)

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

                # Count Sundays
                sundays_count = 0
                day = current_month_start
                while day <= current_month_end:
                    if day.weekday() == 6:
                        sundays_count += 1
                    day += timedelta(days=1)

                paid_leave_count = self.env['hr.leave'].search_count([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'validate'),
                    ('company_id', '=', emp.company_id.id),
                    ('request_date_from', '>=', current_month_start),
                    ('request_date_to', '<=', current_month_end),
                    ('holiday_status_id.is_leave_unpaid', '=', False),
                    ('leave_encashed_check', '=', False)
                ])
                total_days = attendance_count + paid_leave_count
                logger.info(total_days)
                logger.info(attendance_count)
                logger.info(paid_leave_count)

                total_month_days = (current_month_end - current_month_start).days + 1
                logger.info(total_month_days)

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

                old_existing_alloc = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', emp.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('employee_company_id', '=', emp.company_id.id),
                    ('state', '=', 'validate'),
                    ('date_from', '>=', current_month_start),
                    ('date_to', '<=', current_month_end),
                ], limit=1)
                existing_alloc = self.env['hr.leave.allocation'].search([
                        ('employee_id', '=', emp.id),
                        ('holiday_status_id', '=', leave_type.id),
                        ('state', '=', 'validate'),
                        ('employee_company_id', '=', emp.company_id.id),
                        ('date_from', '<=', next_month_end),
                        ('date_to', '>=', next_month_start),
                        #('date_from', '>=', next_month_start),
                        #('date_to', '<=', next_month_end),
                    ], limit=1)
                if existing_alloc:
                    # Skip if already exists
                    logger.info(f"Skipping {emp.name}, already has allocation for {period}")
                    continue
                extra_days = 0
                if total_days >= working_days:
                    extra_days = total_days - working_days
                    # else:
                    #     extra_days = 0
                    old_existing_alloc = self.env['hr.leave.allocation'].search([
                        ('employee_id', '=', emp.id),
                        ('holiday_status_id', '=', leave_type.id),
                        ('state', '=', 'validate'),
                        ('employee_company_id', '=', emp.company_id.id),
                        # ('state', '=', 'validate1'),
                        ('date_from', '<=', current_month_end),
                        ('date_to', '>=', current_month_start),
                    ], limit=1)
                    logger.info(old_existing_alloc)
                    logger.info(old_existing_alloc.max_leaves)
                    logger.info(old_existing_alloc.leaves_taken)
                    logger.info(next_month_start - relativedelta(months=1))
                    logger.info(next_month_end - relativedelta(months=1))
                    # if old_existing_alloc:
                    #     remaining_leaves = old_existing_alloc.number_of_days - old_existing_alloc.leaves_taken
                    #     if remaining_leaves < 0:
                    #         remaining_leaves = 0
                    # remaining_leaves = old_existing_alloc.max_leaves - old_existing_alloc.leaves_taken if old_existing_alloc else 0
                    # logger.info(f"remainingggggggggggggggggggggggg leavessss")
                    # logger.info(f"remainingggggggggggggggggggggggg leavessss")
                    # logger.info(f"remainingggggggggggggggggggggggg leavessss{remaining_leaves}")
                    # extra_days += remaining_leaves
                remaining_leaves = 0
                if old_existing_alloc:
                    remaining_leaves = old_existing_alloc.max_leaves - old_existing_alloc.leaves_taken
                    if remaining_leaves < 0:
                        remaining_leaves = 0
                
                # Always add carry forward
                total_alloc_days = extra_days + remaining_leaves

                    # Rules by emp type
                    # if emp.emp_type == 'local':
                    #     extra_days = 2 if extra_days > 2 else extra_days
                    # elif emp.emp_type == 'outsider':
                    #     if sundays_count < 5:
                    #         extra_days = 4 if extra_days > 4 else extra_days
                    #     else:
                    #         extra_days = 5 if extra_days > 5 else extra_days
                    # elif emp.emp_type == 'northern':
                    #     extra_days = 20 if extra_days > 20 else extra_days
                if emp.emp_type == 'local':
                    total_alloc_days = min(total_alloc_days, 2)
                elif emp.emp_type == 'outsider':
                    if sundays_count < 5:
                        total_alloc_days = min(total_alloc_days, 4)
                    else:
                        total_alloc_days = min(total_alloc_days, 5)
                elif emp.emp_type == 'northern':
                    total_alloc_days = min(total_alloc_days, 20)
                if total_alloc_days > 0:
                    new_alloc = self.env['hr.leave.allocation'].create({
                        'employee_id': emp.id,
                        'holiday_status_id': leave_type.id,
                        'number_of_days': total_alloc_days,
                        'name': f"Weekly Off Allocation - {next_month_start.strftime('%B')} ({period})",
                        'date_from': next_month_start,
                        'employee_company_id' : emp.company_id.id,
                        'date_to': next_month_end,
                        'state': 'confirm',
                        'month': period,
                        'month_start_date': self.month_start_date,
                        'month_end_date': self.month_end_date,
                    })
                    new_alloc.action_approve()
                    new_alloc.action_validate()
                    logger.info(f"✅ Created new allocation for {emp.name}: {total_alloc_days} days")
