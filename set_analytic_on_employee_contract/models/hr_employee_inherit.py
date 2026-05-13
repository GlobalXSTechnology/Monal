from odoo import models, fields, api



class EmployeePayslip(models.Model):
    _inherit = 'hr.payslip'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        domain="[('company_id', '=', company_id)]",
        readonly=True,
        store=True  # editable only in draft
    )

    @api.model
    def create(self, vals):
        if not vals.get('analytic_account_id'):
            contract = False

            # First priority: contract_id from vals
            if vals.get('contract_id'):
                contract = self.env['hr.contract'].browse(vals['contract_id'])

            # Second priority: find active contract from employee
            elif vals.get('employee_id'):
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', vals['employee_id']),
                    ('state', '=', 'open')
                ], limit=1)

            if contract and contract.analytic_account_id:
                vals['analytic_account_id'] = contract.analytic_account_id.id

        return super().create(vals)

    @api.onchange('employee_id', 'contract_id')
    def _onchange_employee_or_contract_id(self):
        for rec in self:
            contract = rec.contract_id or self.env['hr.contract'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'open')
            ], limit=1)

            rec.analytic_account_id = contract.analytic_account_id.id if contract else False



class EmployeeFields(models.Model):
    _inherit = 'hr.employee'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        domain="[('company_id', '=', company_id)]"
    )

    def write(self, vals):
        res = super().write(vals)

        if 'analytic_account_id' in vals:
            for emp in self:
                contracts = self.env['hr.contract'].search([
                    ('employee_id', '=', emp.id),
                    ('state', 'in', ['draft','open', 'close'])
                ])

                contracts.write({
                    'analytic_account_id': emp.analytic_account_id.id
                })

        return res

    @api.model
    def create(self, vals):
        emp = super().create(vals)

        if vals.get('analytic_account_id'):
            contracts = self.env['hr.contract'].search([
                ('employee_id', '=', emp.id),
                ('state', 'in', ['open', 'close'])
            ])

            contracts.write({
                'analytic_account_id': emp.analytic_account_id.id
            })

        return emp