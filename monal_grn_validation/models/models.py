from odoo import fields, models, api, _,Command
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_is_zero
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        errors = []
        for picking in self:
            # if picking.origin and self.env['purchase.order'].search([('name', '=', picking.origin)], limit=1):
            for move in picking.move_ids_without_package:
                if move.quantity > move.product_uom_qty:
                    errors.append(
                        _(
                            "Done Quantity Greater Than Demand Quantity for the following lines:\n\nProduct: %s | Demand: %s | Done: %s"
                        ) % (
                            move.product_id.display_name,
                            move.product_uom_qty,
                            move.quantity
                        )
                    )
                if move.origin_returned_move_id:
                    if move.quantity > move.origin_returned_move_id.quantity:
                        errors.append(
                            _(
                                "Done Quantity Greater Than Demand Quantity for the following lines:\n\nProduct: %s | Demand: %s | Done: %s can not exceed from original transfer of return."
                            ) % (
                                move.product_id.display_name,
                                move.product_uom_qty,
                                move.quantity
                            )
                        )
            # purchase_order_id = self.env['purchase.order'].sudo().search([('name','=',picking.origin)],limit=1)
            # sale_order_id = self.env['sale.order'].sudo().search([('id','=',picking.sale_id.id)],limit=1)
            # _logger.info('purchase_order_id')
            # _logger.info('sale_order_id')
            # _logger.info(purchase_order_id)
            # _logger.info(sale_order_id)
            # if purchase_order_id:
            #     _logger.info('purchase_order_id')
            #     _logger.info(purchase_order_id)
            #     order_so_id = self.env['sale.order'].sudo().search([('name','=',purchase_order_id.partner_ref),('company_id','in',purchase_order_id.partner_id.ref_company_ids.ids)],limit=1)
            #     _logger.info('order_so_id')
            #     _logger.info(order_so_id)
            #     if order_so_id:
            #         if purchase_order_id.create_date > order_so_id.create_date:
            #             _logger.info('purchase_order_id.create_date < order_so_id.create_date')
            #             _logger.info(purchase_order_id.create_date)
            #             _logger.info(order_so_id.create_date)
            #             po_picking = self.env['stock.picking'].sudo().search([('origin','=',purchase_order_id.partner_ref),('state','not in',['cancel','done']),('company_id','in',purchase_order_id.partner_id.ref_company_ids.ids)])
            #             _logger.info('po_picking')
            #             _logger.info(po_picking)
            #             if po_picking:
            #                 errors.append(
            #                     _(
            #                         "You can not validate %s because its linked document is not yet validated.\nPlease contact your adminstration for further action."
            #                     ) % (
            #                         picking.name
            #                     )
            #                 )
            # elif sale_order_id:
            #     _logger.info('sale_order_id')
            #     _logger.info(sale_order_id)
            #     _logger.info(sale_order_id.client_order_ref)
            #     order_po_id = self.env['purchase.order'].sudo().search([('name','=',sale_order_id.client_order_ref),('company_id','in',sale_order_id.partner_id.ref_company_ids.ids)],limit=1)
            #     _logger.info('order_po_id')
            #     _logger.info(order_po_id)
            #     _logger.info(sale_order_id.create_date)
            #     _logger.info(order_po_id.create_date)
            #     if order_po_id:
            #         if sale_order_id.create_date > order_po_id.create_date:
            #             _logger.info('sale_order_id.create_date < order_po_id.create_date')
            #             _logger.info(sale_order_id.create_date)
            #             _logger.info(order_po_id.create_date)
    
            #             sale_picking = self.env['stock.picking'].sudo().search([('origin','=',sale_order_id.client_order_ref),('state','not in',['cancel','done']),('company_id','in',sale_order_id.partner_id.ref_company_ids.ids)])
            #             _logger.info('sale_picking')
            #             _logger.info(sale_picking)
    
            #             if sale_picking:
            #                 errors.append(
            #                     _(
            #                         "You can not validate %s because its linked document is not yet validated.\nPlease contact your adminstration for further action."
            #                     ) % (
            #                         picking.name
            #                     )
            #                 )
            # purchase_order_id = self.env['purchase.order'].sudo().search([('name','=',picking.origin)],limit=1)
            #
            # if purchase_order_id:
            #
            #     sale_picking = self.env['stock.picking'].sudo().search([('origin','=',purchase_order_id.origin),('state','not in',['cancel','done']),('company_id','in',purchase_order_id.partner_id.ref_company_ids.ids)])
            #     if sale_picking:
            #         errors.append(
            #             _(
            #                 "You can not validate %s because its linked document is not yet validated.\nPlease contact your adminstration for further action."
            #             ) % (
            #                 picking.name
            #             )
            #         )
            
            if errors:
                raise ValidationError(
                    "\n".join(errors)
                )
        return super(StockPicking, self).button_validate()


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    returned_qty = fields.Float('Returned Qty')

    @api.onchange('quantity')
    def onchange_quantity_custom(self):
        for rec in self:
            if rec.quantity > rec.move_quantity:
                raise ValidationError(f"You can not return quantity {rec.quantity} more than Move Quantity {rec.move_quantity}")
            if rec.quantity > rec.move_quantity - rec.returned_qty:
                raise ValidationError(f"You can not return quantity {rec.quantity} more than remaining to return Quantity {rec.move_quantity - rec.returned_qty}")


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'



    def refresh_return_lines(self):
        for wizard in self:
            wizard._compute_moves_locations()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.return.picking',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }




    @api.depends('picking_id')
    def _compute_moves_locations(self):
        for wizard in self:
            product_return_moves = [Command.clear()]
            if not wizard.picking_id._can_return():
                raise UserError(_("You may only return Done pickings."))
            # In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
            # default values for creation.
            line_fields = list(self.env['stock.return.picking.line']._fields)
            product_return_moves_data_tmpl = self.env['stock.return.picking.line'].default_get(line_fields)
            for move in wizard.picking_id.move_ids:
                if move.state == 'cancel':
                    continue
                if move.scrapped:
                    continue
                product_return_moves_data = dict(product_return_moves_data_tmpl)
                line_vals = wizard._prepare_stock_return_picking_line_vals_from_move(move)
                if line_vals:
                    product_return_moves_data.update(line_vals)
                    product_return_moves.append(Command.create(product_return_moves_data))
            if wizard.picking_id and not product_return_moves:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)."))
            if wizard.picking_id:
                wizard.product_return_moves = product_return_moves
            for r_move in wizard.product_return_moves:
                returned_qty = sum(r_move.move_id.returned_move_ids.filtered(lambda a: a.state != 'cancel').mapped('product_uom_qty')) if r_move.move_id.returned_move_ids else 0.0
                r_move.returned_qty = returned_qty

    @api.model
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
        if stock_move.returned_move_ids:
            if sum(stock_move.returned_move_ids.filtered(lambda a: a.state != 'cancel').mapped('product_uom_qty')) >= stock_move.product_uom_qty:
                return {}
        return {
            'product_id': stock_move.product_id.id,
            'quantity': 0,
            'move_id': stock_move.id,
            'uom_id': stock_move.product_id.uom_id.id,
        }

    def action_create_returns_all(self):
        """ Create a return matching the total delivered quantity and open it.
        """
        self.ensure_one()
        for return_move in self.product_return_moves:
            # stock_move = return_move.move_id
            # if not stock_move or stock_move.state == 'cancel' or stock_move.scrapped:
            #     continue
            # quantity = stock_move.quantity
            # for move in stock_move.move_dest_ids:
            #     if not move.origin_returned_move_id or move.origin_returned_move_id != stock_move:
            #         continue
            #     quantity -= move.quantity
            quantity = return_move.move_quantity - return_move.returned_qty
            quantity = float_round(quantity, precision_rounding=return_move.move_id.product_id.uom_id.rounding)
            return_move.quantity = quantity
        return self.action_create_returns()
