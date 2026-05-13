from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging
from datetime import date


_logger = logging.getLogger(__name__)



class HrEmployee(models.Model):
    _name = 'employee.final.settlement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Final Settlement'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('1st_appr', 'HR Approval'),
        # ('2nd_appr', '2nd Approval'),
        ('payslip', 'Payslip'),
        ('final_appr', 'Approved'),
        ('paid', 'Paid'),
        ('cancel', 'Cancel'),
    ], string='Status', default='draft', copy=True, tracking=True)
    name = fields.Many2one('hr.employee', string="Name", store=True, tracking=True)
    batch = fields.Char(string="Badge ID", store=True, compute='_compute_employee_details', tracking=True)
    company_id = fields.Many2one('res.company', string="Company", store=True, tracking=True,  default=lambda self: self.env.company.id)
    company = fields.Char(string='Company', store=True, tracking=True)
    department = fields.Char(string='Department', store=True, compute='_compute_employee_details', tracking=True)
    designation = fields.Char(string='Designation', store=True, compute='_compute_employee_details', tracking=True)
    emp_bank_name = fields.Char(string='Employee Bank Name', store=True, compute='_compute_employee_details',
                                tracking=True)
    emp_acc_no = fields.Char(string='Account #', store=True, compute='_compute_employee_details', tracking=True)
    # grade = fields.Char(string='Grade', store=True, compute='_compute_employee_details', tracking=True)
    location = fields.Char(string='Location', store=True, compute='_compute_employee_details', tracking=True)
    dob = fields.Char(string='Birth Date', store=True, compute='_compute_employee_details', tracking=True)
    jod = fields.Char(string='Joining Date', store=True, compute='_compute_employee_details', tracking=True)
    gratuity_date = fields.Date(string='Gratuity Date', compute='_compute_employee_details', store=True, tracking=True)
    leave_reason = fields.Many2one('hr.departure.reason', string='Leaving Reason', store=True, tracking=True)
    resign_date = fields.Date(string="Payslip Date", store=True, tracking=True)
    # last_work_date = fields.Date(string="Last Working Date", tracking=True)
    contract_end_date = fields.Date(string="Contract End Date", tracking=True)
    count_days = fields.Integer(string="Worked Days", compute='_compute_days_from_start_of_month', store=True)
    pf_end_date = fields.Date(string="PF End Date", tracking=True)
    basic_salary = fields.Boolean(string="Basic Salary", store=True, tracking=True)
    notice_pay = fields.Boolean(string="Notice Pay", store=True, tracking=True)
    gratuity = fields.Boolean(string="Gratuity", store=True, tracking=True)
    pf_loan = fields.Boolean(string="PF Loan", store=True, tracking=True)
    comp_loan = fields.Boolean(string="Comp Loan", store=True, tracking=True)
    vehicle_loan = fields.Boolean(string="Vehicle Loan", store=True, tracking=True)
    prov_fund = fields.Boolean(string="Provident Fund", store=True, tracking=True)
    remarks = fields.Char(string='Remarks', store=True, tracking=True)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip')
    payslip_line_ids = fields.One2many(
        comodel_name='hr.payslip.line',
        compute='_compute_payslip_line_ids',
        string='Payslip Lines',
        readonly=True
    )
    resignation_date = fields.Date(string="Resignation Date", tracking=True)
    last_working_date = fields.Date(string="Last Working Date", tracking=True)
    net_salary_amount = fields.Char(
        string="Net Salary", compute="_compute_payslip_amounts", store=True
    )
    bonus_amount = fields.Char(
        string="Bonus", compute="_compute_payslip_amounts", store=True
    )
    gratuity_amount = fields.Char(
        string="Gratuity", compute="_compute_payslip_amounts", store=True
    )
    all_ded_amount = fields.Char(
        string="Deductions", compute="_compute_payslip_amounts", store=True
    )

    report_uniform_line_ids = fields.Many2many(
        'employee.uniform.line',
        compute='_compute_report_uniform_lines',
        string="Uniform Lines for Report",
        compute_sudo=True
    )

    @api.depends('name')
    def _compute_report_uniform_lines(self):
        date_limit = date.today() - relativedelta(months=6)
        for record in self:
            if record.name:
                lines = self.env['employee.uniform.line'].sudo().search([
                    ('employee_id', '=', record.name.id),
                    ('uniform_id.distribution_date', '>=', date_limit)
                ])
                record.report_uniform_line_ids = lines
            else:
                record.report_uniform_line_ids = False
    # @api.constrains('resignation_date','contract_end_date','resign_date')
    # def _check_dates_against_lock_date(self):
    #     for rec in self:
    #         if not rec.company_id:
    #             continue
    #
    #         # Get latest DONE lock date for the company
    #         lock = self.env['lock.date'].search([
    #             ('company_id', '=', rec.company_id.id),
    #             ('state', '=', 'done')
    #         ], order='lock_date desc', limit=1)
    #
    #         if not lock or not lock.lock_date:
    #             continue
    #
    #         lock_date = lock.lock_date
    #
    #         date_fields = {
    #             'Payslip Date': rec.resign_date,
    #             'Resignation Date': rec.resignation_date,
    #             'Contract End Date': rec.contract_end_date,
    #             # 'Gratuity Date': rec.gratuity_date,
    #         }
    #
            # for label, date_value in date_fields.items():
            #     if date_value and date_value < lock_date:
            #         raise ValidationError(_("%s (%s) cannot be earlier than the Payroll Lock Date (%s).") % (label,date_value,lock_date))

    @api.depends("payslip_id")
    def _compute_payslip_amounts(self):
        for rec in self:
            if rec.payslip_line_ids:
                rec.net_salary_amount = rec.payslip_line_ids.filtered(lambda l: l.code == "NET").total
                rec.bonus_amount = rec.payslip_line_ids.filtered(lambda l: l.code == "BON").total
                rec.gratuity_amount = rec.payslip_line_ids.filtered(lambda l: l.code == "GRAT").total
                ded_lines = rec.payslip_line_ids.filtered(lambda l: l.category_id.code == 'DED')
                rec.all_ded_amount = sum(ded_lines.mapped('total')) if ded_lines else 0.0


    @api.depends('payslip_id')
    def _compute_payslip_line_ids(self):
        for rec in self:
            if rec.payslip_id:
                lines = rec.payslip_id.line_ids.filtered(lambda l: l.amount != 0)
                rec.payslip_line_ids = lines
            else:
                rec.payslip_line_ids = False

    @api.onchange('resign_date')
    def _onchange_resign_date(self):
        if self.resign_date:
            self.pf_end_date = self.resign_date
        else:
            self.pf_end_date = False

    # @api.onchange('contract_end_date')
    # def _onchange_last_work_date(self):
    #     if self.contract_end_date:
    #         self.name.contract_id.date_end = self.contract_end_date
    #     else:
    #         self.name.contract_id.date_end = False

    @api.depends('contract_end_date')
    def _compute_days_from_start_of_month(self):
        for record in self:
            if record.contract_end_date:
                contract_end_date = fields.Date.from_string(record.contract_end_date)
                first_day_of_month = contract_end_date.replace(day=1)
                days_diff = (contract_end_date - first_day_of_month).days + 1
                record.count_days = days_diff
            else:
                record.count_days = 0

    @api.depends('name')
    def _compute_employee_details(self):
        for record in self:
            if record.name:
                record.batch = record.name.barcode
                # self.company = self.name.emp_company_id.name
                record.department = record.name.department_id.name
                record.designation = record.name.job_id.name
                # self.emp_bank_name = self.name.bank_name
                # self.emp_acc_no = self.name.bank_account
                # self.grade = self.name.contract_id.x_studio_employee_grade
                record.location = record.name.work_location_id.name
                # record.dob = record.name.birthday
                # record.jod = record.name.contract_id.date_start
                record.dob = record.name.birthday.strftime('%d/%m/%Y') if record.name.birthday else ''
                record.jod = record.name.contract_id.date_start.strftime(
                    '%d/%m/%Y') if record.name.contract_id.date_start else ''
                record.gratuity_date = record.name.contract_id.date_start
            else:
                record.batch = False
                # record.company = False
                record.department = False
                record.designation = False
                # record.emp_bank_name = False
                # record.emp_acc_no = False
                # record.grade = False
                record.location = False
                record.dob = False
                record.jod = False
                record.gratuity_date = False

    def action_1st_appr(self):
        for rec in self:
            if rec.contract_end_date:
                rec.name.contract_id.date_end = rec.contract_end_date
            else:
                rec.name.contract_id.date_end = False
            rec.state = '1st_appr'

    def coo_appr(self):
        self.state = 'final_appr'

    # def action_2nd_appr(self):
    #     self.state = '2nd_appr'

    def action_payslip(self):
        if self.resign_date:
            resign_date = fields.Date.from_string(self.resign_date)
            date_from = resign_date.replace(day=1)
            date_to = date_from + relativedelta(months=1, days=-1)

            payslip_name = f'Payslip for {self.name.name} ({date_from.strftime("%B %Y")})'
            contract = self.env['hr.contract'].search([('employee_id','=',self.name.id)],limit=1)
            _logger.info(contract)
            _logger.info(contract)
            structure = self.env['hr.payroll.structure'].search([('type_id', '=', contract.structure_type_id.id)], limit=1)
            _logger.info(structure)
            _logger.info(structure)
            if not structure:
                raise ValidationError('Payroll Structure  not found')
            
            payslip = self.env['hr.payslip'].search([
                ('employee_id', '=', self.name.id),
                ('date_from', '=', date_from),
                ('date_to', '=', date_to),
                # ('state', '!=', 'cancel'),
            ], limit=1)
            print(payslip)
            print(payslip)
            print(payslip)
            print(payslip)
            print(payslip)

            if not payslip:
                payslip_vals = {
                    'name': f'Payslip for {self.name.name} ({date_from.strftime("%B %Y")})',
                    'employee_id': self.name.id,
                    'date_from': date_from,
                    'date_to': date_to,
                    'contract_id': self.name.contract_id.id,
                    'struct_id': structure.id,
                    'final_settlement_id': self.id,
                    'last_work_date': self.contract_end_date,
                    'count_days': self.count_days,
                }
                payslip = self.env['hr.payslip'].create(payslip_vals)

            # 🔗 LINK FINAL SETTLEMENT WITH PAYSLIP
            else:
                self.payslip_id = payslip.id
            self.state = 'payslip'

            # 👉 REDIRECT TO PAYSLIP
            return {
                'type': 'ir.actions.act_window',
                'name': _('Payslip'),
                'res_model': 'hr.payslip',
                'view_mode': 'form',
                'res_id': payslip.id,
                'target': 'current',
            }
            # payslip_vals = {
            #     'name': payslip_name,
            #     'employee_id': self.name.id,
            #     'date_from': date_from,
            #     'date_to': date_to,
            #     'contract_id': self.name.contract_id.id,
            #     'struct_id': structure.id,
            #     'final_settlement_id': self.id,
            #     # 'emp_bank_name': self.emp_bank_name,
            #     # 'emp_acc_no': self.emp_acc_no,
            #     'last_work_date': self.contract_end_date,
            #     'count_days': self.count_days,
            # }
            # payslip = self.env['hr.payslip'].create(payslip_vals)
            # self.state = 'payslip'
            # self.payslip_id = payslip.id

    def action_cancel(self):
        self.state = 'cancel'

    def action_reset(self):
        self.state = 'draft'

    def action_update(self):
        if self.resign_date:
            resign_date = fields.Date.from_string(self.resign_date)
            date_from = resign_date.replace(day=1)
            date_to = date_from + relativedelta(months=1, days=-1)

            payslip_name = f'Payslip for {self.name.name} ({date_from.strftime("%B %Y")})'
            contract = self.env['hr.contract'].search([('employee_id','=',self.name.id)],limit=1)
            structure = self.env['hr.payroll.structure'].search([('type_id', '=', contract.structure_type_id.id)], limit=1)
            # structure = self.env['hr.payroll.structure'].search([('name', '=', 'Final Settlement')], limit=1)
            if not structure:
                raise ValidationError('Payroll Structure not found')

            payslip_vals = {
                'name': payslip_name,
                'employee_id': self.name.id,
                'date_from': date_from,
                'date_to': date_to,
                'contract_id': self.name.contract_id.id,
                'struct_id': structure.id,
                'final_settlement_id': self.id,
                # 'emp_bank_name': self.emp_bank_name,
                # 'emp_acc_no': self.emp_acc_no,
                'last_work_date': self.contract_end_date,
                'count_days': self.count_days,
            }
            self.payslip_id.write(payslip_vals)
            # self.state = 'payslip'
            # self.payslip_id = payslip.id

    def action_open_payslip(self):
        return {
            'name': 'Payslip',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'view_mode': 'form',
            'domain': [('employee_id', '=', self.name)],
            'res_id': self.payslip_id.id,
            'target': 'current',
        }

    def action_print_final_settlement(self):
        return self.env.ref('monal_employee_final_settelment.report_employee_final_settlement').report_action(self)
