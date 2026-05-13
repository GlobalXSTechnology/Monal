from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, time
from datetime import datetime, timedelta

import logging

_logger = logging.getLogger(__name__)


class EmployeeGlobalInputs(models.Model):
    _name = 'employee.global.input'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Global Input'

    employee_id = fields.Many2one('hr.employee', 'Employee', store=True, tracking=True)
    department_id = fields.Many2one('hr.department', 'Department', tracking=True)
    job_id = fields.Many2one('hr.job', 'Job Position', related='employee_id.job_id', store=True, tracking=True)
    badge_id = fields.Char('Badge ID', related='employee_id.barcode', store=True, tracking=True)
    date_to = fields.Date(string='Date To', tracking=True)
    date_from = fields.Date(string='Date From', tracking=True)
    apply_by = fields.Selection([
        ('batch', "Batch"),
        ('dpt', "Department"),
        ('comp', "Company"),
        ('emp', "Employees"),
        ('group_department', "Group By Department"),
    ], string="Apply Inputs By", default=False, tracking=True)

    global_input_id = fields.Many2one('global.input', 'Global Input', tracking=True)
    batch_id = fields.Many2one('hr.payslip.run', 'Batch', tracking=True)
    department_group = fields.Many2one('department.group', string='Department Group')
    company_id = fields.Many2one('res.company', 'Company', store=True,
                                 tracking=True)

    input_line_ids = fields.One2many(
        'employee.global.input.line', 'input_id', string='Payslip Inputs', store=True,
        readonly=False)
    present_days = fields.Float(string='Present Days', store=True)
    month = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string="Month",
        required=True,
        tracking=True
    )
    amount = fields.Float('Amount', tracking=True, store=True, compute='compute_lines_mount')

    @api.depends('input_line_ids.amount')
    def compute_lines_mount(self):
        for rec in self:
            amount = 0
            for line in rec.input_line_ids:
                if line.amount:
                    amount += line.amount
            rec.amount = amount

    def _get_month_selection(self):
        months = [
            ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
            ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        month_selection = []
        for year in range(2025, 3001):
            for code, name in months:
                month_selection.append((f'{year}-{code}', f'{name} {year}'))
        return month_selection

    @api.onchange('month')
    def _onchange_month(self):
        if self.month:
            year, month = map(int, self.month.split('-'))
            self.date_from = f'{year}-{month:02d}-01'
            last_day = calendar.monthrange(year, month)[1]
            self.date_to = f'{year}-{month:02d}-{last_day}'

    @api.depends('employee_id', 'date_from', 'date_to')
    def compute_present_days(self):
        for rec in self:
            present_days = 0
            if not rec.employee_id or not rec.date_from or not rec.date_to:
                rec.present_days = 0
                continue

            start_datetime = datetime.combine(rec.date_from, time.min)
            end_datetime = datetime.combine(rec.date_to, time.max)
            _logger.info(start_datetime)
            _logger.info(start_datetime)
            _logger.info('xsxsxsxsxs')
            _logger.info(end_datetime)

            attendance_domain = [
                ('employee_id', '=', rec.employee_id.id),
                ('check_in', '>=', start_datetime),
                ('check_in', '<=', end_datetime),
            ]

            if not rec.employee_id.resource_calendar_id.x_studio_is_zero:
                attendance_domain.append(('worked_hours', '>=', 6))
            z = self.env['hr.attendance'].search(attendance_domain)
            _logger.info(z)
            _logger.info(z)
            _logger.info(z)
            _logger.info(z)
            rec.present_days = len(z)
            # rec.present_days = self.env['hr.attendance'].search_count(attendance_domain)


class EmployeeGlobalInputLine(models.Model):
    _name = 'employee.global.input.line'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Description")
    input_id = fields.Many2one('employee.global.input', string='Global Input', ondelete='cascade', index=True)
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Type', required=True)
    sequence = fields.Integer(required=True, index=True, default=10)
    amount = fields.Float(string="Amount")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    department_id = fields.Many2one('hr.department', 'Department', related='employee_id.department_id', store=True,
                                    tracking=True)
    job_id = fields.Many2one('hr.job', 'Job Position', related='employee_id.job_id', store=True, tracking=True)
    badge_id = fields.Char('Badge ID', related='employee_id.barcode', store=True, tracking=True)
    apply_by = fields.Selection([
        ('batch', "Batch"),
        ('dpt', "Department"),
        ('comp', "Company"),
        ('emp', "Employees"),
        ('group_department', "Group By Department"),
    ], string="Apply Inputs By", default=False, store=True, tracking=True)
    month = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string="Month",
        required=True,
        tracking=True
    )
    present_days = fields.Float(string='Present Days', store=True)
    global_input_id = fields.Many2one('global.input', 'Global Input',store=True)


    def _get_month_selection(self):
        months = [
            ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
            ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        month_selection = []
        for year in range(2025, 3001):
            for code, name in months:
                month_selection.append((f'{year}-{code}', f'{name} {year}'))
        return month_selection

    @api.depends('employee_id')
    def compute_present_days(self):
        for rec in self:
            present_days = 0
            if not rec.employee_id or not rec.input_id.date_from or not rec.input_id.date_to:
                rec.present_days = 0
                continue

            start_datetime = datetime.combine(rec.input_id.date_from, time.min)
            end_datetime = datetime.combine(rec.input_id.date_to, time.max)

            attendance_domain = [
                ('employee_id', '=', rec.employee_id.id),
                ('check_in', '>=', start_datetime),
                ('check_in', '<=', end_datetime),
            ]

            if not rec.employee_id.resource_calendar_id.x_studio_is_zero:
                attendance_domain.append(('worked_hours', '>=', 6))

            rec.present_days = self.env['hr.attendance'].search_count(attendance_domain)
