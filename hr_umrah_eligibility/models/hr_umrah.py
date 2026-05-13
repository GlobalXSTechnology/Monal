from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class HREmployeeUmrah(models.Model):
    _name = 'hr.umrah.contribution'
    _description = 'Umrah Contribution and Eligibility'

    employee_id = fields.Many2one('hr.employee', required=True)
    contributed_percent = fields.Float(default=3.0)
    contribution_date = fields.Date(default=fields.Date.today())
    eligible_for_balloting = fields.Boolean(string="Eligible?", compute="_compute_eligibility", store=True)
    stage = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed')
    ], default='draft', string="Stage")

    @api.depends('employee_id.umrah_contribution_ids')
    def _compute_eligibility(self):
        for rec in self:
            rec.eligible_for_balloting = True


class HrContract(models.Model):
    _inherit = 'hr.contract'

    enroll_in_umrah = fields.Boolean(string="Enroll in Umrah Package")
    umrah_enroll_date = fields.Date(string="Umrah Enrollment Date")

    @api.model
    def create(self, vals):
        contract = super().create(vals)
        if vals.get('enroll_in_umrah') and contract.employee_id:
            contract._create_umrah_contribution()
        return contract

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if vals.get('enroll_in_umrah') and rec.employee_id:
                rec._create_umrah_contribution()
        return res

    def _create_umrah_contribution(self):
        self.ensure_one()
        existing = self.env['hr.umrah.contribution'].search([
            ('employee_id', '=', self.employee_id.id)
        ])
        if not existing:
            self.env['hr.umrah.contribution'].create({
                'employee_id': self.employee_id.id,
                'contributed_percent': 3.0,
                'contribution_date': fields.Date.today(),
            })


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    payment_move_id = fields.Many2one('account.move', string="Umrah Payment Entry", readonly=True)

    umrah_total_cut = fields.Float(string="Total Deduction", compute="_compute_umrah_deductions", store=True)
    manual_umrah_amount_add = fields.Float(string="Manual Deduction Amount", default=0.0, tracking=True)
    umrah_monthly_cut = fields.Float(string="Monthly Deduction", compute="_compute_umrah_deductions", store=True)
    umrah_cut_count = fields.Integer(string="Total Months Deducted", compute="_compute_umrah_deductions", store=True,
                                     tracking=True)
    manual_umrah_cut_add = fields.Integer(string="Manually Added Months", default=0)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    application_date = fields.Date(string="Application Date", default=fields.Date.today(), tracking=True)
    enroll_in_umrah = fields.Boolean(string="Enroll in Umrah Package")

    umrah_application_ids = fields.One2many(
        'hr.umrah.application', 'employee_id', string="Umrah Applications")
    umrah_contribution_ids = fields.One2many('hr.umrah.contribution', 'employee_id', string="Umrah Contributions")
    umrah_total_expense = fields.Float(string="Total Umrah Expense", tracking=True)
    umrah_remaining_balance = fields.Float(string="Remaining Balance", compute="_compute_remaining_balance", store=True)
    can_apply_for_umrah = fields.Boolean(string="Can Apply Again?", compute="_compute_can_apply_for_umrah", store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft', tracking=True)
    total_payslips = fields.Integer(
        string="Payslips",
        compute="_compute_total_payslips",
        store=False
    )

    def _compute_total_payslips(self):
        for emp in self:
            emp.total_payslips = self.env['hr.payslip'].search_count([
                ('employee_id', '=', emp.id)
            ])

    def action_open_payslips(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payslips',
            'res_model': 'hr.payslip',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    @api.depends('umrah_contribution_ids', 'manual_umrah_cut_add', 'manual_umrah_amount_add')
    def _compute_umrah_deductions(self):
        for employee in self:
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'open')
            ], limit=1)
            if not contract:
                employee.umrah_total_cut = employee.manual_umrah_amount_add
                employee.umrah_monthly_cut = 0.0
                employee.umrah_cut_count = employee.manual_umrah_cut_add
                continue

            salary = contract.wage or 0.0
            monthly_cut = (salary * 3.0) / 100.0
            count = len(employee.umrah_contribution_ids)
            total = (monthly_cut * count) + employee.manual_umrah_amount_add

            employee.umrah_cut_count = count + employee.manual_umrah_cut_add
            employee.umrah_monthly_cut = monthly_cut
            employee.umrah_total_cut = total

    @api.depends('umrah_total_cut', 'umrah_total_expense')
    def _compute_remaining_balance(self):
        for employee in self:
            employee.umrah_remaining_balance = employee.umrah_total_expense - employee.umrah_total_cut

    @api.depends('umrah_total_expense', 'umrah_cut_count', 'umrah_remaining_balance')
    def _compute_can_apply_for_umrah(self):
        for rec in self:
            rec.can_apply_for_umrah = rec.umrah_total_expense == 0 and rec.umrah_cut_count >= 12

    def add_umrah_expense(self):
        for rec in self:
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', rec.id),
                ('state', '=', 'open')
            ], limit=1)
            if not contract:
                raise ValidationError("No active contract found.")

            if contract.date_start and fields.Date.today() < contract.date_start + relativedelta(years=1):
                raise ValidationError("Employee must complete 1 year before Umrah expense.")

            if rec.umrah_remaining_balance > 0:
                raise ValidationError("Previous Umrah balance is not cleared.")

            policy = self.env['hr.umrah.expense.policy'].search([
                ('company_id', '=', rec.company_id.id),
                ('active', '=', True)
            ], limit=1, order="create_date desc")

            if not policy:
                raise ValidationError("No active Umrah expense policy found for this employee's company.")

            rec.umrah_total_expense += policy.expense_amount
            rec.message_post(body=f"Applied Umrah expense from policy '{policy.name}': {policy.expense_amount}")

    def action_add_manual_month(self):
        for rec in self:
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', rec.id),
                ('state', '=', 'open')
            ], limit=1)
            if not contract:
                raise ValidationError("No active contract found for employee.")

            self.env['hr.umrah.contribution'].create({
                'employee_id': rec.id,
                'contributed_percent': 3.0,
                'contribution_date': fields.Date.today(),
            })

            rec.manual_umrah_cut_add += 1


class HrUmrahApplication(models.Model):
    _name = 'hr.umrah.application'
    _description = 'Umrah Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'application_date desc'
    is_confirmed = fields.Boolean(string='Is confirm', default=False)
    policy_id = fields.Many2one('hr.umrah.expense.policy', string="Umrah Policy", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 default=lambda self: self.env.company)
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        domain="[('umrah_cut_count', '>=', 12), ('umrah_remaining_balance', '<=', 0.0), ('company_id', '=', company_id)]",
   required=True)

    payment_id = fields.Many2one('account.payment', string="Umrah Payment", readonly=True)

    application_date = fields.Date(string="Application Date", default=fields.Date.today(), tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft', tracking=True)
    umrah_total_cut = fields.Float(related='employee_id.umrah_total_cut', string="Total Deduction", readonly=True)
    umrah_monthly_cut = fields.Float(related='employee_id.umrah_monthly_cut', string="Monthly Deduction", readonly=True)
    umrah_cut_count = fields.Integer(related='employee_id.umrah_cut_count', string="Total Months Deducted",
                                     readonly=True)
    payment_move_id = fields.Many2one('account.move', string="Umrah Payment Entry", readonly=True)
    expense_amount = fields.Monetary(
        string="Expense Amount",
        currency_field='currency_id',
        readonly=True,
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    eligible = fields.Boolean(string="Eligible?", compute="_compute_eligibility", store=True)
    badge_id = fields.Char(related='employee_id.barcode', string="Badge ID", readonly=True)
    department_id = fields.Many2one(related='employee_id.department_id', string="Department", readonly=True)
    job_id = fields.Many2one(related='employee_id.job_id', string="Designation", readonly=True)
    basic_salary = fields.Monetary(related='employee_id.contract_id.wage', string="Basic Salary", readonly=True,
                                   currency_field='currency_id')
    joining_date = fields.Date(related='employee_id.first_contract_date', string="Joining Date", readonly=True)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'umrah_application_ir_attachments_rel',
        'umrah_application_id',
        'attachment_id',
        string="Attachments"
    )
    @api.onchange('employee_id')
    def _onchange_employee_id_set_expense(self):
        for record in self:
            if record.employee_id:
                policy = self.env['hr.umrah.expense.policy'].search([
                    ('company_id', '=', record.employee_id.company_id.id),
                    ('active', '=', True)
                ], limit=1, order="create_date desc")

                if policy:
                    record.expense_amount = policy.expense_amount
                    record.policy_id = policy.id
                else:
                    record.expense_amount = 0.0
                    record.policy_id = False

    def action_view_umrah_payment(self):
        self.ensure_one()
        if not self.payment_id:
            raise ValidationError("No payment record linked to this application.")
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': self.payment_id.id,
            'target': 'current',
        }

    def action_create_umrah_payment(self):
        for rec in self:
            # Bank journal dhundo
            journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
            if not journal:
                raise ValidationError("⚠️ Bank journal nahi mila. Payment create nahi ho sakti.")

            # Employee ke name ka partner dhundo (ya create karo)
            partner = self.env['res.partner'].search([('name', '=', rec.employee_id.name)], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': rec.employee_id.name,
                    'supplier_rank': 1,
                })

            # 🔁 Expense record banao based on policy
            rec.employee_id.add_umrah_expense()

            # 🎯 Policy read karo (latest aur active)
            policy = self.env['hr.umrah.expense.policy'].search([
                ('company_id', '=', rec.employee_id.company_id.id),
                ('active', '=', True)
            ], limit=1, order="create_date desc")

            if not policy:
                raise ValidationError("Koi active Umrah policy nahi mili.")

            # 💰 Ab payment create karo based on policy amount
            payment_vals = {
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'partner_id': partner.id,
                'amount': policy.expense_amount,
                'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
                'journal_id': journal.id,
                'payment_reference': f"Umrah Payment for {rec.employee_id.name}",
            }

            payment = self.env['account.payment'].create(payment_vals)

            # Linking payment with employee and record
            rec.employee_id.payment_move_id = payment.move_id
            rec.payment_move_id = payment.move_id
            rec.payment_id = payment
            rec.is_confirmed = True

            rec.message_post(
                body=f"💸 Payment of {policy.expense_amount} created for Umrah using policy '{policy.name}'.")

    @api.depends('employee_id')
    def _compute_eligibility(self):
        for record in self:
            record.eligible = record.employee_id.can_apply_for_umrah

    def action_confirm(self):
        for record in self:
            employee = record.employee_id

            if not employee:
                raise ValidationError("Employee is required.")

            if employee.umrah_cut_count < 12:
                raise ValidationError("Employee must have at least 12 months of Umrah deductions to apply.")

            if employee.umrah_remaining_balance > 0:
                raise ValidationError("Previous Umrah package balance must be cleared before applying again.")

            past_apps = self.env['hr.umrah.application'].search_count([
                ('employee_id', '=', employee.id),
                ('state', '=', 'confirmed')
            ])

            if past_apps > 0 and employee.umrah_cut_count < (12 * (past_apps + 1)):
                raise ValidationError(
                    f"This is Umrah application #{past_apps + 1}, so employee needs at least {12 * (past_apps + 1)} months of deductions."
                )

            policy = self.env['hr.umrah.expense.policy'].search([
                ('company_id', '=', employee.company_id.id),
                ('active', '=', True)
            ], limit=1, order="create_date desc")

            if not policy:
                raise ValidationError("No active Umrah expense policy found.")

            record.expense_amount = policy.expense_amount
            record.state = 'confirmed'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_reset_draft(self):
        for record in self:
            record.state = 'draft'


class HrUmrahExpensePolicy(models.Model):
    _name = 'hr.umrah.expense.policy'
    _description = 'Umrah Expense Policy'
    _order = 'create_date desc'

    name = fields.Char(string="Policy Name", required=True)
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 default=lambda self: self.env.company)
    expense_amount = fields.Float(string="Expense Amount", required=True)
    active = fields.Boolean(string="Active", default=True)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        res = super().action_payslip_done()

        for slip in self:
            # Only if payslip contains Umrah Deduction rule line
            umra_rule = slip.line_ids.filtered(lambda l: l.salary_rule_id.code == 'UM')

            if umra_rule:
                # Avoid duplicate contributions for the same month
                first_day = fields.Date.today().replace(day=1)
                existing = self.env['hr.umrah.contribution'].search([
                    ('employee_id', '=', slip.employee_id.id),
                    ('contribution_date', '>=', first_day)
                ])
                if not existing:
                    self.env['hr.umrah.contribution'].create({
                        'employee_id': slip.employee_id.id,
                        'contributed_percent': 3.0,
                        'contribution_date': fields.Date.today(),
                    })

                    # Update employee totals
                    slip.employee_id._compute_umrah_deductions()

        return res


class HrUmrahDeductionStatus(models.TransientModel):
    _name = 'hr.umrah.deduction.status'
    _description = 'Umrah Deduction Status Report'

    name = fields.Char(default="Umrah Deduction Status", readonly=True)
    deducted_employee_ids = fields.Many2many(
        'hr.employee',
        'umrah_deduction_status_deducted_rel',
        'status_id',
        'employee_id',
        string="Employees With Deduction"
    )
    not_deducted_employee_ids = fields.Many2many(
        'hr.employee',
        'umrah_deduction_status_not_deducted_rel',
        'status_id',
        'employee_id',
        string="Employees Without Deduction"
    )

    payslip_ids = fields.One2many(
        'hr.payslip',
        compute="_compute_payslip_ids",
        string="Payslips",
        readonly=True
    )
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 default=lambda self: self.env.company)

    @api.depends('deducted_employee_ids')
    def _compute_payslip_ids(self):
        for rec in self:
            if rec.deducted_employee_ids:
                rec.payslip_ids = self.env['hr.payslip'].search([
                    ('employee_id', 'in', rec.deducted_employee_ids.ids)
                ])
            else:
                rec.payslip_ids = False

    @api.model
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        Employee = self.env['hr.employee']
        company = self.env.company

        # Sirf current company ke contributions lo
        deducted_emps = self.env['hr.umrah.contribution'].search([
            ('employee_id.company_id', '=', company.id)
        ]).mapped('employee_id')

        # Sirf current company ke active employees lo
        all_emps = Employee.search([
            ('active', '=', True),
            ('company_id', '=', company.id)
        ])

        # Jo deducted nahi hue
        not_deducted = all_emps - deducted_emps

        res['deducted_employee_ids'] = [(6, 0, deducted_emps.ids)]
        res['not_deducted_employee_ids'] = [(6, 0, not_deducted.ids)]
        return res
