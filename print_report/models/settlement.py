from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date

class EmployeeFinalSettlement(models.Model):
    _inherit = 'employee.final.settlement'

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