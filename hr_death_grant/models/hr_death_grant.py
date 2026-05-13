from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError


class HRDeathPolicy(models.Model):
    _name = 'hr.death.policy'
    _description = 'Death Grant Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Policy Name", required=True)
    company_id = fields.Many2one('res.company', string="Company", required=True)
    department_ids = fields.Many2many('hr.department', 'a_b', 'c_d', string="Departments", compute='get_departments',
                                      store=True)
    department_id = fields.Many2many('hr.department', 'e_f', 'g_h', string="Department")
    min_years_service = fields.Float(string="Minimum Years of Service", required=True)
    grant_amount = fields.Float(string="Grant Amount", required=True, store=True)
    max_salary = fields.Float(string="Maximum Monthly Salary", required=True)

    @api.depends('company_id')
    def get_departments(self):
        for rec in self:
            if rec.company_id:
                rec.department_ids = False
                departments = self.env['hr.department'].search([('company_id', '=', rec.company_id.id)])
                rec.department_ids = departments.ids
            else:
                departments = self.env['hr.department'].search([])
                rec.department_ids = departments.ids


class HRDeathGrant(models.Model):
    _name = 'hr.death.grant'
    _description = 'Employee Death Grant'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 default=lambda self: self.env.company)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  domain="[('company_id', '=', company_id)]")
    leave_encashment = fields.Boolean(string='3 Days Leave Encashment')
    deceased_relation = fields.Selection([
        ('parent', 'Parent'),
        ('sibling', 'Sibling (Unmarried)'),
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('employee', 'Staff (Self)'),
    ], string='Relation of Deceased', required=True)
    actual_expenses = fields.Float(string='Actual Expenses (If staff deceased)')
    is_staff_deceased = fields.Boolean(string='Is Staff Deceased?')
    years_of_service = fields.Float(string='Years of Service', compute='_compute_years_of_service', store=True)
    eligible = fields.Boolean(string='Eligible?', compute='_compute_eligibility')
    notes = fields.Text(string='Remarks')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approval', 'Approval'),
        ('done', 'Done'),
    ], string='Status', default='draft', tracking=True)
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )
    payment_count = fields.Integer(string="Payment Count", compute="_compute_payment_count", store=False)
    payment_ready = fields.Boolean(string="Ready for Payment", readonly=True)
    badge_id = fields.Char(related='employee_id.barcode', string="Badge ID", readonly=True)
    department_id = fields.Many2one(related='employee_id.department_id', string="Department", readonly=True)
    job_id = fields.Many2one(related='employee_id.job_id', string="Designation", readonly=True)
    basic_salary = fields.Monetary(related='employee_id.contract_id.wage', string="Basic Salary", readonly=True,
                                   currency_field='currency_id')
    joining_date = fields.Date(related='employee_id.first_contract_date', string="Joining Date", readonly=True)

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'death_grant_ir_attachments_rel',  # <-- custom relation table
        'death_grant_id',
        'attachment_id',
        string="Attachments"
    )

    def _compute_payment_count(self):
        for record in self:
            record.payment_count = self.env['account.payment'].search_count([
                ('death_grant_id', '=', record.id)
            ])

    def action_view_death_grant_payments(self):
        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('death_grant_id', '=', self.id)],
            'context': {'default_death_grant_id': self.id},
        }

    @api.onchange('deceased_relation', 'employee_id')
    def _onchange_deceased_relation(self):
        for rec in self:
            if rec.deceased_relation == 'employee':
                rec.actual_expenses = 0.0
            elif rec.deceased_relation:
                policy = self.env['hr.death.policy'].search([
                    '|',
                    ('department_id', 'in', rec.employee_id.department_id.id),
                    ('department_id', '=', False),
                    ('company_id', '=', rec.employee_id.company_id.id)
                ], limit=1)
                rec.actual_expenses = policy.grant_amount if policy else 0.0

    @api.model
    def create(self, vals):
        employee = self.env['hr.employee'].browse(vals.get('employee_id'))
        deceased_relation = vals.get('deceased_relation')

        if deceased_relation == 'employee':
            vals['actual_expenses'] = 0.0
        elif deceased_relation:
            policy = self.env['hr.death.policy'].search([
                '|',
                ('department_id', 'in', employee.department_id.id),
                ('department_id', '=', False),
                ('company_id', '=', employee.company_id.id)
            ], limit=1)
            vals['actual_expenses'] = policy.grant_amount if policy else 0.0

        staff_self_exists = self.search([
            ('employee_id', '=', employee.id),
            ('deceased_relation', '=', 'employee'),
            ('state', '!=', 'draft'),
        ], limit=1)
        if staff_self_exists:
            raise ValidationError("⚠️ A Staff (Self) death grant is already approved.")

        return super(HRDeathGrant, self).create(vals)

    def write(self, vals):
        for rec in self:
            if 'deceased_relation' in vals or 'employee_id' in vals:
                relation = vals.get('deceased_relation') or rec.deceased_relation
                employee = self.env['hr.employee'].browse(vals.get('employee_id')) if vals.get(
                    'employee_id') else rec.employee_id

                if relation == 'employee':
                    vals['actual_expenses'] = 0.0
                elif relation:
                    policy = self.env['hr.death.policy'].search([
                        '|',
                        ('department_id', 'in', employee.department_id.id),
                        ('department_id', '=', False),
                        ('company_id', '=', employee.company_id.id)
                    ], limit=1)
                    vals['actual_expenses'] = policy.grant_amount if policy else 0.0

        return super(HRDeathGrant, self).write(vals)

    @api.constrains('employee_id')
    def _check_staff_self_lock_all(self):
        for rec in self:
            if rec.employee_id:
                staff_self_grant = self.env['hr.death.grant'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('deceased_relation', '=', 'employee'),
                    ('state', '!=', 'draft'),
                    ('id', '!=', rec.id)
                ], limit=1)
                if staff_self_grant:
                    raise ValidationError("⚠️ A Staff (Self) death grant is already approved.")

    def action_submit_for_approval(self):
        for rec in self:
            contract = rec.employee_id.contract_id
            if not contract or not contract.date_start:
                raise ValidationError("⚠️ No contract found or contract start date missing.")

            today = date.today()
            service_years = (today - contract.date_start).days / 365

            # ✅ Correct: assign policy BEFORE checking its values
            policy = self.env['hr.death.policy'].search([
                '|',
                ('department_id', 'in', rec.employee_id.department_id.id),
                ('department_id', '=', False),
                ('company_id', '=', rec.employee_id.company_id.id)
            ], limit=1)

            if not policy:
                raise ValidationError("⚠️ No applicable death policy found for this employee.")

            if service_years < policy.min_years_service:
                raise ValidationError(
                    f"⚠️ Employee must have completed at least {policy.min_years_service} years of service to submit for approval.")

            if contract.wage > policy.max_salary:
                raise ValidationError(
                    f"⚠️ Employee's salary ({contract.wage}) exceeds the maximum allowed ({policy.max_salary}) in the selected policy."
                )

            if rec.deceased_relation == 'employee' and not rec.actual_expenses:
                raise ValidationError("⚠️ Please enter Actual Expenses if the deceased is the staff (self).")

            staff_self_grant = self.env['hr.death.grant'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('deceased_relation', '=', 'employee'),
                ('state', '!=', 'draft'),
                ('id', '!=', rec.id)
            ], limit=1)
            if staff_self_grant:
                raise ValidationError(
                    "⚠️ A Staff (Self) death grant is already approved. No more death grants allowed for this employee.")

            rec.state = 'approval'

    def action_approve_done(self):
        for rec in self:
            rec.state = 'done'
            rec.payment_ready = False

            # journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
            # if not journal:
            #     raise ValidationError("⚠️ No Bank Journal found to create payment.")
            #
            # # ✅ Search for partner (employee name)
            # partner = self.env['res.partner'].search([('name', '=', rec.employee_id.name)], limit=1)
            # if not partner:
            #     partner = self.env['res.partner'].create({
            #         'name': rec.employee_id.name,
            #         'supplier_rank': 1,
            #     })
            #
            # # ✅ Use the defined partner here
            # payment_vals = {
            #     'payment_type': 'outbound',
            #     'partner_type': 'supplier',
            #     'partner_id': partner.id,
            #     'amount': rec.actual_expenses,
            #     'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
            #     'journal_id': journal.id,
            #     'death_grant_id': rec.id,
            #     'payment_reference': f'Death Grant Payment for {rec.employee_id.name}', }
            #
            # payment = self.env['account.payment'].create(payment_vals)
            # payment.action_post()

    def action_create_transfer(self):
        for rec in self:
            rec.payment_ready = True
            journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
            if not journal:
                raise ValidationError("⚠️ No Bank Journal found to create payment.")

            # ✅ Search for partner (employee name)
            partner = self.env['res.partner'].search([('name', '=', rec.employee_id.name)], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': rec.employee_id.name,
                    'supplier_rank': 1,
                })

            # ✅ Use the defined partner here
            payment_vals = {
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'partner_id': partner.id,
                'amount': rec.actual_expenses,
                'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
                'journal_id': journal.id,
                'death_grant_id': rec.id,
                'payment_reference': f'Death Grant Payment for {rec.employee_id.name}', }

            payment = self.env['account.payment'].create(payment_vals)
            # payment.action_post()

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.depends('employee_id.contract_id.date_start')
    def _compute_years_of_service(self):
        for rec in self:
            start_date = rec.employee_id.contract_id.date_start
            if start_date:
                rec.years_of_service = (date.today() - start_date).days / 365
            else:
                rec.years_of_service = 0.0

    @api.depends('deceased_relation', 'employee_id.job_title', 'years_of_service')
    def _compute_eligibility(self):
        for rec in self:
            policy = self.env['hr.death.policy'].search([
                '|',
                ('department_id', 'in', rec.employee_id.department_id.id),
                ('department_id', '=', False),
                ('company_id', '=', rec.employee_id.company_id.id)
            ], limit=1)

            min_service = policy.min_years_service if policy else 0.0
            rec.eligible = (
                    rec.years_of_service >= min_service and bool(rec.employee_id.job_title)
            )


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    def action_view_death_grants(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Death Grants',
            'res_model': 'hr.death.grant',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
            'target': 'current',
        }


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    death_grant_id = fields.Many2one('hr.death.grant', string='Death Grant')
