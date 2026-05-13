from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Destination Warehouse",
    )

    location_dest_id = fields.Many2one(
        'stock.location',
        string="Destination Location",
        domain="[('usage','!=','view'), ('warehouse_id','=', warehouse_id)]"
    )

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):

        if self.warehouse_id:
            if not self.location_dest_id or self.location_dest_id.warehouse_id != self.warehouse_id:
                self.location_dest_id = self.warehouse_id.lot_stock_id.id
        else:
            self.location_dest_id = False

    @api.depends('picking_type_id', 'partner_id','warehouse_id')
    def _compute_location_id(self):
        for picking in self:
            if picking.state in ('cancel', 'done') or picking.return_id:
                continue
            picking = picking.with_company(picking.company_id)
            if picking.picking_type_id:
                location_src = picking.picking_type_id.default_location_src_id
                if location_src.usage == 'supplier' and picking.partner_id:
                    location_src = picking.partner_id.property_stock_supplier
                location_dest = self.warehouse_id.lot_stock_id if self.warehouse_id else False
                picking.location_id = location_src.id
                picking.location_dest_id = location_dest.id if location_dest else False

