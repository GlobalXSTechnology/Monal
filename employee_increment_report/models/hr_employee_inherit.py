from odoo import models, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def action_open_increment_report_wizard(self):
        return {
            'name': _('Employee Increment Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'employee.increment.report.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('employee_increment_report.view_employee_increment_report_wizard_form').id,
            'target': 'new',
            'context': {
                'default_employee_ids': [(6, 0, self.ids)],
            }
        }
