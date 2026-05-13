from odoo import models, fields, api


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    structure_type_id = fields.Many2one('hr.payroll.structure.type', string='Salary Structure Type')

class HrContract(models.Model):
    _inherit = 'hr.contract'

    # structure_type_id = fields.Many2one('hr.payroll.structure.type', string='Salary Structure Type')

    @api.onchange('department_id')
    def onchange_department(self):
        for rec in self:
             if rec.department_id and rec.department_id.structure_type_id:
                 rec.structure_type_id = rec.department_id.structure_type_id


