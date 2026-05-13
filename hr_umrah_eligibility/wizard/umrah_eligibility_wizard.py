from odoo import models, fields


class UmrahEligibilityCheckWizard(models.TransientModel):
    _name = 'umrah.eligibility.check.wizard'
    _description = 'Umrah Eligibility Checker Wizard'

    def action_check_eligibility(self):
        Employee = self.env['hr.employee']

        # Apply exact same domain as used in hr.umrah.application
        eligible_employees = Employee.search([
            ('umrah_cut_count', '>=', 12),
            ('umrah_remaining_balance', '<=', 0.0),
        ])

        return {
            'type': 'ir.actions.act_window',
            'name': 'Eligible Employees',
            'res_model': 'hr.employee',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('hr_umrah_eligibility.view_hr_employee_umrah_list').id, 'list'),
                (self.env.ref('hr.view_employee_form').id, 'form')
            ],
            'domain': [('id', 'in', eligible_employees.ids),('company_id', '=', self.env.company.id)],
            'target': 'current',
        }
