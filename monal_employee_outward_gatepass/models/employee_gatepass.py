from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from datetime import datetime, time, timedelta, date
import calendar
import logging
import pytz

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    per_hour = fields.Float(string="Per Hour", compute="get_overtime_amount")

    @api.depends('wage', 'resource_calendar_id')
    def get_overtime_amount(self):
        for contract in self:
            # rec = self.env['hr.attendance'].search([('employee_id', '=', contract.employee_id.id)], limit=1, order='id desc')
            #
            year = date.today().year
            month = date.today().month
            #
            # # Calculate the total number of days in the month
            total_days_in_month = calendar.monthrange(year, month)[1]
            # if rec:
            #     planned_time_str = str(rec.planned_time)
            #     planned_time_list = list(planned_time_str)
            #     h = 0
            #
            #     for i in planned_time_str:
            #         h = h + 1
            #         if i == '.':
            #             hour = planned_time_str[0:h - 1]
            #             if len(hour) == 1:
            #                 hour = '0' + hour
            #
            #             mints = planned_time_str[h:]
            #             if len(mints) == 1:
            #                 mints = '0' + mints
            #
            #             rec.mint_15 = datetime.strftime(rec.check_in, f'%Y-%m-%d {hour}:{mints}:%S')
            #
            #     planned_exit_time_str = str(rec.planned_exit_time)
            #
            #     h = 0
            #     s = 0
            #     for i in planned_exit_time_str:
            #         h = h + 1
            #         if i == '.':
            #             hour = planned_exit_time_str[0:h - 1]
            #             if len(hour) == 1:
            #                 hour = '0' + hour
            #
            #             mints = planned_exit_time_str[h:]
            #             if len(mints) == 1:
            #                 mints = '0' + mints
            #
            #             rec.mint_out = datetime.strftime(rec.check_in, f'%Y-%m-%d {hour}:{mints}:%S')
            #
            #     work_hours = rec.mint_out - rec.mint_15
            #     shift_time = work_hours.total_seconds() / 3600.0
            shift_time = contract.resource_calendar_id.hours_per_day

            # if rec:
            contract.per_hour = ((contract.wage / total_days_in_month) / 8) * 1.5
            print(contract.wage, total_days_in_month, shift_time, 'eeeeeeeeeee')

            # else:
            #     contract.per_hour = ((contract.wage / total_days_in_month) / 8)*1.5
            #
            #     print(contract.wage,total_days_in_month)


class EmployeeGatePass(models.Model):
    _name = 'employee.gatepass'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee GatePass"

    badge_id = fields.Char(string='ID #', related='name.barcode', tracking=True)
    amount_deduc = fields.Float(string='Amount Deduct', tracking=True)
    date = fields.Date(string='Date', tracking=True)
    time_out = fields.Datetime(string='Time Out', tracking=True)
    time_in = fields.Datetime(string='Time In', tracking=True)
    total_time = fields.Float(string='Total Time', compute='_compute_total_time', store=True, tracking=True)
    name = fields.Many2one('hr.employee', string='Name', tracking=True)
    department = fields.Many2one('hr.department', related='name.department_id', string='Department', tracking=True)
    designation = fields.Many2one('hr.job', related='name.job_id', string='Designation', tracking=True)
    gate_pass_type = fields.Selection([
        ('personal', 'Personal'),
        ('official', 'Official'),
    ], string='Type', required=True, tracking=True)
    description = fields.Text(string='Purpose', tracking=True)
    image = fields.Binary(string='Image', readonly=False, tracking=True)
    time_in_display = fields.Char(
        string="Time In",
        compute="_compute_time_display"
    )
    time_out_display = fields.Char(
        string="Time Out",
        compute="_compute_time_display"
    )
    check_in_display = fields.Char(
        string="Check In",
        compute="_compute_check_in_out_display"
    )
    check_out_display = fields.Char(
        string="Check Out",
        compute="_compute_check_in_out_display"
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        help="Define which company can select the multi-ledger in report filters. If none is provided, available for all companies",
        default=lambda self: self.env.company, readonly=True, store=True, force_save=True, tracking=True
    )
    check_in = fields.Datetime(string='Check_In', compute="_get_check_in_out", tracking=True)
    check_out = fields.Datetime(string='Check_Out', compute="_get_check_in_out", tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),

    ], string='Status', default='draft', tracking=True)

    @api.depends('name')
    def _get_check_in_out(self):
        _logger.info('todaytodaytodaytodaytoday')
        _logger.info('todaytodaytodaytodaytoday')
        _logger.info('todaytodaytodaytodaytoday')
        _logger.info('todaytodaytodaytodaytoday')
        for rec in self:
            rec.check_in = False
            rec.check_out = False

            if not rec.name:
                return

            today = date.today()
            start_dt = datetime.combine(today, time.min)
            end_dt = datetime.combine(today, time.max)

            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', rec.name.id),
                ('check_in', '>=', start_dt),
                ('check_out', '<=', end_dt),
            ])
            if attendance:
                rec.check_in = attendance.check_in
                rec.check_out = attendance.check_out

            _logger.info(today)
            _logger.info(start_dt)
            _logger.info(end_dt)
            _logger.info(attendance)

    def action_done(self):
        for record in self:
            record.state = 'done'

    def action_set_draft(self):
        for record in self:
            record.state = 'draft'

    @api.depends('time_in', 'time_out')
    def _compute_time_display(self):
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        for rec in self:
            if rec.time_in:
                local_dt = rec.time_in.replace(tzinfo=pytz.UTC).astimezone(user_tz)
                rec.time_in_display = local_dt.strftime('%I:%M %p')
            else:
                rec.time_in_display = False

            if rec.time_out:
                local_dt = rec.time_out.replace(tzinfo=pytz.UTC).astimezone(user_tz)
                rec.time_out_display = local_dt.strftime('%I:%M %p')
            else:
                rec.time_out_display = False

    @api.depends('check_in', 'check_out')
    def _compute_check_in_out_display(self):
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        for rec in self:
            if rec.check_in:
                local_dt = rec.check_in.replace(tzinfo=pytz.UTC).astimezone(user_tz)
                rec.check_in_display = local_dt.strftime('%I:%M %p')
            else:
                rec.check_in_display = False

            if rec.check_out:
                local_dt = rec.check_out.replace(tzinfo=pytz.UTC).astimezone(user_tz)
                rec.check_out_display = local_dt.strftime('%I:%M %p')
            else:
                rec.check_out_display = False

    def karachi_time_in(self):
        for rec in self:
            if rec.time_in:
                user_tz = pytz.timezone('Asia/Karachi')
                local_time_in = fields.Datetime.context_timestamp(self, rec.time_in).astimezone(user_tz)
                return local_time_in.strftime('%H:%M:%S')
        return ''

    def karachi_time_out(self):
        for rec in self:
            if rec.time_out:
                user_tz = pytz.timezone('Asia/Karachi')
                local_time_out = fields.Datetime.context_timestamp(self, rec.time_out).astimezone(user_tz)
                return local_time_out.strftime('%H:%M:%S')
        return ''

    def action_time_out(self):
        self.time_out = datetime.now()
        self.date = datetime.now().date()

    @api.depends('time_in', 'gate_pass_type', 'time_out')
    def _compute_total_time(self):
        for rec in self:
            if rec.name and rec.time_in and rec.time_out:
                contract = self.env['hr.contract'].search([('employee_id', '=', self.name.id), ('state', '=', 'open')])
                # rec = self.env['hr.attendance'].search([('employee_id','=',self.name.id)],limit=1, order='id desc')
                if not rec.date:
                    rec.date = date.today()
                year = rec.date.year
                month = rec.date.month

                # Calculate the total number of days in the month
                total_days_in_month = calendar.monthrange(year, month)[1]

                pr_hour = (contract.wage / total_days_in_month) / 8
                if rec.gate_pass_type == 'official':
                    pr_hour = 0

                date_day = date.today()
                day_check = date_day.strftime("%A")

                if day_check == 'Friday':
                    in_time = datetime.strftime(datetime.now(), f'%Y-%m-%d {13}:{00}:%S')
                    in_time = datetime.strptime(in_time, f'%Y-%m-%d {13}:{00}:%S')
                    out_time = datetime.strftime(datetime.now(), f'%Y-%m-%d {14}:{30}:%S')
                    out_time = datetime.strptime(out_time, f'%Y-%m-%d {14}:{30}:%S')
                else:
                    in_time = datetime.strftime(datetime.now(), f'%Y-%m-%d {13}:{00}:%S')
                    in_time = datetime.strptime(in_time, f'%Y-%m-%d {13}:{00}:%S')
                    out_time = datetime.strftime(datetime.now(), f'%Y-%m-%d {14}:{00}:%S')
                    out_time = datetime.strptime(out_time, f'%Y-%m-%d {14}:{00}:%S')

                if rec.time_out >= in_time and rec.time_in <= out_time:
                    rec.amount_deduc = 0

                elif rec.time_out <= in_time and rec.time_in >= out_time:
                    break_time = out_time - in_time
                    break_time = (break_time.total_seconds() / 3600.0)
                    rec.total_time = round(break_time, 2)
                    work_hours = rec.time_in - rec.time_out
                    total_break_time = (work_hours.total_seconds() / 3600.0) - break_time
                    rec.amount_deduc = total_break_time * pr_hour



                elif rec.time_out <= in_time and rec.time_in <= out_time and rec.time_in > in_time:
                    break_time = in_time - rec.time_in
                    break_time = (break_time.total_seconds() / 3600.0)
                    rec.total_time = round(break_time, 2)
                    work_hours = rec.time_in - rec.time_out
                    total_break_time = (work_hours.total_seconds() / 3600.0) - break_time
                    rec.amount_deduc = total_break_time * pr_hour



                elif rec.time_out > in_time and rec.time_out < out_time and rec.time_in > out_time:
                    break_time = rec.time_out - out_time
                    break_time = (break_time.total_seconds() / 3600.0)
                    rec.total_time = round(break_time, 2)
                    work_hours = rec.time_in - rec.time_out
                    total_break_time = (work_hours.total_seconds() / 3600.0) - break_time
                    rec.amount_deduc = total_break_time * pr_hour



                else:
                    work_hours = rec.time_in - rec.time_out
                    total_break_time = (work_hours.total_seconds() / 3600.0)
                    rec.total_time = round(total_break_time, 2)
                    rec.amount_deduc = total_break_time * pr_hour

                    # if attendance:
                    #     attendance_hours = attendance.worked_hours or 0.0
                    #     gatepass_hours = total_break_time
                    #     worked_hours = attendance_hours - gatepass_hours
                    #     attendance.write({'worked_hours': worked_hours})
                    #

    # @api.onchange('time_in', 'time_out')
    # def _onchange_time_in_out_validation(self):
    #     today = date.today()
    #     user_tz = pytz.timezone(self.env.user.tz or 'UTC')
    #
    #     for rec in self:
    #         lock_date = False
    #         if rec.company_id:
    #             lock = self.env['lock.date'].search([
    #                 ('company_id', '=', rec.company_id.id),
    #                 ('state', '=', 'done')
    #             ], order='lock_date desc', limit=1)
    #             lock_date = lock.lock_date if lock else False
    #
    #         if rec.time_in:
    #             time_in_date = rec.time_in.replace(
    #                 tzinfo=pytz.UTC
    #             ).astimezone(user_tz).date()
    #
    #             if time_in_date != today:
    #                 raise ValidationError(_(
    #                     "Time In should be of the current day only."
    #                 ))
    #
    #             if lock_date and time_in_date < lock_date:
    #                 raise ValidationError(_(
    #                     "You cannot select Time In before the Payroll Lock Date (%s)."
    #                 ) % lock_date)
    #
    #         if rec.time_out:
    #             time_out_date = rec.time_out.replace(
    #                 tzinfo=pytz.UTC
    #             ).astimezone(user_tz).date()
    #
    #             if time_out_date != today:
    #                 raise ValidationError(_(
    #                     "Time Out should be of the current day only."
    #                 ))
    #
    #             if lock_date and time_out_date < lock_date:
    #                 raise ValidationError(_(
    #                     "You cannot select Time Out before the Payroll Lock Date (%s)."
    #                 ) % lock_date)
