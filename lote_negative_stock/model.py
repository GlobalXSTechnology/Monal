from datetime import date,datetime
import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class StockMoveLineproduction(models.Model):
    _inherit = "mrp.production"

    def action_confirm(self):
        
        for rec in self.move_raw_ids:
            
            quants_lot2 = self.env['stock.quant'].search([('location_id','=',rec.location_id.id),('product_id','=',rec.product_id.id)])
            print(quants_lot2)
            quants_lot = quants_lot2.mapped('lot_id.id')
            quantity = sum(quants_lot2.mapped('inventory_quantity_auto_apply'))
            if quantity < rec.product_uom_qty:
                 raise ValidationError(f"Insufficient quantity available at the selected location for {rec.product_id.display_name}.")
            
        res = super(StockMoveLineproduction, self).action_confirm()
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    # @api.constrains('lot_id', 'product_id', 'qty_done')
    # def _check_stock_availability(self):
    #     for rec in self:
    #         # Skip if not outgoing/internal
    #         if rec.picking_type_id.code not in ["outgoing", "internal"]:
    #             continue

    #         # Skip if same source/dest
    #         if rec.picking_id.location_id.id == rec.picking_id.location_dest_id.id:
    #             continue

    #         # For tracked products (serial/lot)
    #         if rec.product_id.tracking != 'none':
    #             quants = self.env['stock.quant'].read_group(
    #                 [('location_id', '=', rec.picking_id.location_id.id),
    #                  ('lot_id', '=', rec.lot_id.id)],
    #                 ['quantity:sum'],
    #                 ['lot_id']
    #             )
    #             available_qty = quants and quants[0]['quantity'] or 0.0

    #             if available_qty < rec.qty_done:
    #                 raise ValidationError(
    #                     _(f"Insufficient qty for product {rec.product_id.display_name} in lot {rec.lot_id.display_name}.")
    #                 )

    #         # For untracked products
    #         else:
    #             quants = self.env['stock.quant'].read_group(
    #                 [('location_id', '=', rec.picking_id.location_id.id),
    #                  ('product_id', '=', rec.product_id.id)],
    #                 ['quantity:sum'],
    #                 ['product_id']
    #             )
    #             available_qty = quants and quants[0]['quantity'] or 0.0

    #             if available_qty < rec.qty_done:
    #                 raise ValidationError(
    #                     _(f"Insufficient qty for product {rec.product_id.display_name} in {rec.picking_id.location_id.display_name}.")
    #new saad                 )

    @api.constrains('lot_id','product_id','quantity')
    def _get_lot_domain_custom(self):
        for rec in self:
            quants_lot2 = self.env['stock.quant'].search([('location_id','=',rec.picking_id.location_id.id),('lot_id','=',rec.lot_id.id)])
            quants_lot = quants_lot2.mapped('lot_id.id')
            quantity = sum(quants_lot2.mapped('inventory_quantity_auto_apply'))
            if rec.product_id.tracking == 'none':
                quants_lot21 = self.env['stock.quant'].search([('location_id','=',rec.picking_id.location_id.id),('product_id','=',rec.product_id.id)])
                quantity1 = sum(quants_lot21.mapped('inventory_quantity_auto_apply'))
                qty_all = sum(self.env['stock.move.line'].search([('move_id','=',rec.move_id.id)]).mapped('quantity'))
                if quantity1 < qty_all and rec.picking_id.location_id.id != rec.picking_id.location_dest_id.id and rec.picking_type_id.code in ["outgoing",'internal'] :
                    raise ValidationError(f"This product({rec.product_id.name}) is not available in the selected location.")
            elif rec.product_id.tracking != 'none' and rec.picking_type_id.code in ["outgoing",'internal'] and quantity < rec.quantity and rec.picking_id.location_id.id != rec.picking_id.location_dest_id.id:
                raise ValidationError(f"Insufficient quantity available at the selected lot/location.")

            elif rec.lot_id.id not in quants_lot and rec.product_id.tracking != 'none' and rec.picking_type_id.code in ["outgoing",'internal']:
                raise ValidationError(f"This lot({rec.lot_id.name}) is not available in the selected location.")
