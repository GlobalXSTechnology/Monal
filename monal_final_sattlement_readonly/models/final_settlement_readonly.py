from odoo import models, fields, api


class EmployeeFinalSettlement(models.Model):
    _inherit = 'employee.final.settlement'

    readonly_settlement = fields.Boolean(string='Readonly Settlement')

    @api.model
    def create(self,vals):
        vals['readonly_settlement'] = True
        return super(EmployeeFinalSettlement, self). create(vals)

