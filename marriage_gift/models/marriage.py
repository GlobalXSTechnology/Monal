from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError

from dateutil.relativedelta import relativedelta


class MarriageGift(models.Model):
    _name = 'marriage.leave'
    _rec_name = 'employee_name'

    employee_name = fields.Many2one("hr.employee", string='Name', required=True)
    start_date = fields.Date(string='Date', readonly=True, default=date.today())
    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approved'), ('done', 'Done')], default='draft',
                             string='Status')
    gift_amount = fields.Float(compute="compute_gift", string='Gift Amount')
    payment_id = fields.Many2one('account.payment', string="Payment", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    badge_id = fields.Char(related='employee_name.barcode', string="Badge ID", readonly=True)
    department_id = fields.Many2one(related='employee_name.department_id', string="Department", readonly=True)
    job_id = fields.Many2one(related='employee_name.job_id', string="Designation", readonly=True)
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )
    basic_salary = fields.Monetary(related='employee_name.contract_id.wage', string="Basic Salary", readonly=True,
                                   currency_field='currency_id')
    joining_date = fields.Date(related='employee_name.first_contract_date', string="Joining Date", readonly=True)
    marriage_date = fields.Date(string="Marriage Date", required=True)
    service_years_at_marriage = fields.Float(string="Service Years at Marriage",
                                             compute="_compute_service_years_at_marriage",
                                             store=True)

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'marriage_leave_ir_attachments_rel',
        'marriage_leave_id',
        'attachment_id',
        string="Attachments"
    )

    @api.depends('joining_date', 'marriage_date')
    def _compute_service_years_at_marriage(self):
        for rec in self:
            rec.service_years_at_marriage = 0.0
            if rec.joining_date and rec.marriage_date:
                rd = relativedelta(rec.marriage_date, rec.joining_date)
                years = rd.years
                months = rd.months


                rec.service_years_at_marriage = float(f"{years}.{months}")

    def _get_latest_contract(self, employee):
        return self.env['hr.contract'].search(
            [('employee_id', '=', employee.id)],
            order='date_start desc', limit=1
        )

    @api.onchange('employee_name')
    def compute_gift(self):
        for rec in self:
            rec.gift_amount = 0

            employee = rec.employee_name
            if not employee:
                continue

            policy = self.env['marriage.policy'].search([
                '|',
                '&', ('type', '=', 'company'), ('company_id', '=', rec.company_id.id),
                '&', ('type', '=', 'department'), ('department_id', '=', employee.department_id.id),
            ], limit=1)

            if not policy:
                continue

            contract = rec._get_latest_contract(employee)

            if contract and contract.date_start:
                duration_years = (date.today() - contract.date_start).days / 365
                wage = contract.wage

                required_years = {
                    'one': 1,
                    'two': 2,
                    'three': 3,
                    'four': 3
                }

                if duration_years >= required_years.get(policy.service_length, 0) and wage <= policy.minimum_salary:
                    rec.gift_amount = 40000

    def confirm_button(self):
        for rec in self:
            employee = rec.employee_name
            if employee.marital != 'single':
                raise ValidationError(
                    "This employee is not single, marriage gift can only be granted to single employees.")

            policy = self.env['marriage.policy'].search([
                '|',
                '&', ('type', '=', 'company'), ('company_id', '=', employee.company_id.id),
                '&', ('type', '=', 'department'), ('department_id', '=', employee.department_id.id),
            ], limit=1)

            if not policy:
                raise ValidationError("No applicable marriage policy found for this employee's company or department.")

            existing_gift = self.search([
                ('employee_name', '=', rec.employee_name.id),
                ('state', '=', 'done'),
                ('id', '!=', rec.id)  # Exclude current record in case of editing
            ], limit=1)

            if existing_gift:
                raise ValidationError("This employee has already received a marriage gift.")

            if not rec.joining_date:
                raise ValidationError("Joining Date not found on employee.")
            if not rec.marriage_date:
                raise ValidationError("Please set the Marriage Date.")

            rd = relativedelta(rec.marriage_date, rec.joining_date)
            total_months_at_marriage = rd.years * 12 + rd.months

            required_years_map = {
                'one': 1,
                'two': 2,
                'three': 3,
                'four': 4,
            }

            req_years = required_years_map.get(policy.service_length, 0)
            required_months = req_years * 12


            if total_months_at_marriage < required_months:
                raise ValidationError(
                    f"Employee must have at least {policy.service_length.replace('_', ' ')} of service.")

            contract = rec._get_latest_contract(rec.employee_name)
            if not contract:
                raise ValidationError("No Contract Found for this Employee.")
            if not contract.date_start:
                raise ValidationError("The latest contract has no start date.")

            wage = contract.wage
            if wage > policy.minimum_salary:
                raise ValidationError(f"Employee's wage exceeds the allowed minimum salary ({policy.minimum_salary}).")

            rec.state = 'approve'

    def reset_button(self):
        self.state = 'draft'

    def create_payment(self):
        self.state = 'done'

        for rec in self:
            if not rec.gift_amount or rec.gift_amount <= 0:
                raise ValidationError("Gift amount must be greater than zero to create a payment.")

            if rec.payment_id:
                raise ValidationError("Payment already created for this gift.")
            partner = self.env['res.partner'].search([('name', '=', rec.employee_name.name)], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': rec.employee_name.name,
                    'supplier_rank': 1,
                })

            payment = self.env['account.payment'].create({
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'partner_id': partner.id,
                'amount': rec.gift_amount,
                'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
                'journal_id': self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id,
                'date': fields.Date.today(),
                'memo': f"Marriage Gift for {rec.employee_name.name}",
            })

            rec.payment_id = payment.id
            return {
                'type': 'ir.actions.act_window',
                'name': 'Payment',
                'res_model': 'account.payment',
                'view_mode': 'form',
                'res_id': payment.id,
            }

    def action_view_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': self.payment_id.id,
        }

    @api.onchange('employee_name')
    def _onchange_employee_name_check_done(self):
        for rec in self:
            if rec.employee_name:
                existing_done = self.search([
                    ('employee_name', '=', rec.employee_name.id),
                    ('state', '=', 'done')
                ], limit=1)

                if existing_done:
                    raise ValidationError(
                        f"Employee {rec.employee_name.name} has already received a marriage gift."
                    )


class EmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    marriage_gift_ids = fields.One2many('marriage.leave', 'employee_name', string="Marriage Gifts")

    def action_view_marriage_gifts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Marriage Gifts',
            'view_mode': 'form',
            'res_model': 'marriage.leave',
            'domain': [('employee_name', '=', self.id)],
            'context': {'default_employee_name': self.id},
        }
