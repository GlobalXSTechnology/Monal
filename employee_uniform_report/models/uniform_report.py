from odoo import models, api


class UniformReport(models.AbstractModel):
    _name = 'report.employee_uniform_report.uniform_pdf'
    _description = 'Uniform Distribution Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['employee.uniform'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'employee.uniform',
            'docs': docs,
            'lines': docs.line_ids,
        }


class EmployeeUniform(models.Model):
    _inherit = 'employee.uniform'

    def action_print_uniform_report(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'employee_uniform_report.uniform_pdf',
            'report_type': 'qweb-pdf',
            'report_file': 'employee_uniform_report.uniform_pdf',
            'data': None,
            'context': dict(self.env.context, active_model='employee.uniform', active_ids=self.ids),
            'config': False
        }
