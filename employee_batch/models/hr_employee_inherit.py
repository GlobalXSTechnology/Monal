# from odoo import models, api
#
#
# class HrEmployee(models.Model):
#     _inherit = 'hr.employee'
#
#     @api.model
#     def create(self, vals):
#
#         employee = super(HrEmployee, self).create(vals)
#
#         barcode = f"{employee.barcode}-" if employee.barcode else ""
#         company = f" ({employee.company_id.name})" if employee.company_id else ""
#
#         display_name = f"{barcode}{employee.name}{company}"
#
#
#         self.env['employee.batch'].create({
#             'name': display_name,
#             'badge_id': employee.barcode or '',
#             'company_id': employee.company_id.id,
#         })
#
#         return employee


from odoo import models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def create(self, vals):
        employee = super(HrEmployee, self).create(vals)

        # Get active contract for the employee
        active_contract = self.env['hr.contract'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'open')
        ], limit=1)

        barcode = f"{employee.barcode}-" if employee.barcode else ""
        company = f" ({employee.company_id.name})" if employee.company_id else ""
        display_name = f"{barcode}{employee.name}{company}"

        self.env['employee.batch'].create({
            'name': display_name,
            'employee_id': employee.id,
            'badge_id': employee.barcode or '',
            'company_id': employee.company_id.id,
            'contract_id': active_contract.id if active_contract else False,
        })
        return employee

    def write(self, vals):
        res = super(HrEmployee, self).write(vals)
        # Update employee.batch when employee changes
        for employee in self:
            batch_record = self.env['employee.batch'].search([
                '|',
                ('employee_id', '=', employee.id),
                ('badge_id', '=', employee.barcode)
            ], limit=1)

            if batch_record:
                active_contract = self.env['hr.contract'].search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'open')
                ], limit=1)
                barcode = f"{employee.barcode}-" if employee.barcode else ""
                company = f" ({employee.company_id.name})" if employee.company_id else ""
                display_name = f"{barcode}{employee.name}{company}"

                batch_record.write({
                    'badge_id': employee.barcode or '',
                    'company_id': employee.company_id.id,
                    'contract_id': active_contract.id if active_contract else False,
                })
        return res