from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class TransferConsumption(models.Model):
    _inherit = 'stock.picking'

    accounting_date = fields.Date(string='Accounting Date', tracking=True, required=True, default=fields.Datetime.now)
    show_date = fields.Boolean(string='show date', compute='get_picking_type', default=False)

    @api.depends('picking_type_id')
    def get_picking_type(self):
        for rec in self:
            if rec.picking_type_id.code == 'internal':
                rec.show_date = True
            else:
                rec.show_date = False


class StockMove(models.Model):
    _inherit = "stock.move"

    def _account_entry_move(self, qty, description, svl_id, cost):
        print('incoming')
        am_vals = super()._account_entry_move(qty, description, svl_id, cost)
        picking = self.picking_id
        if picking and picking.accounting_date:
            print('progress')
            for vals in am_vals:
                vals['date'] = picking.accounting_date
                for line in vals.get('line_ids', []):
                    if isinstance(line, (list, tuple)) and line[2]:
                        line[2]['date'] = picking.accounting_date
                        print('done')
        return am_vals
