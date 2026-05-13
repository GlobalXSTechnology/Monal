from odoo import models, api
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def create(self, vals):
        result = super().create(vals)
        print(result.picking_id.state)
        if result.picking_id and result.picking_id.state == 'draft':

            raise UserError("unable to Create the line !")
        else:
            return result

    def unlink(self,user=False):
        for move in self:
            if move.picking_id and move.picking_id.state != 'draft' and user == False:
                raise UserError(
                    "unable to delete the line ! This Line delete only on  'Draft' stage .")

        return super(StockMove, self).unlink()
