from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from odoo.exceptions import ValidationError, UserError


logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    disable_edit_lines = fields.Boolean(
        compute="_compute_disable_edit_lines",
        store=False
    )
    
    
    @api.depends("origin")
    def _compute_disable_edit_lines(self):
        for picking in self:
            picking.disable_edit_lines = bool(picking.origin)


class StockMove(models.Model):
    _inherit = "stock.move"
    
    picking_hide_field = fields.Boolean(
        string="Created from Sale Order",
        copy=False,
        default=False,
        store=True,
        compute='picking_hide_field_compute'
    )
    
    
    @api.depends('picking_id.origin')
    def picking_hide_field_compute(self):
        for rec in self:
            if rec.picking_id.origin:
                rec.picking_hide_field = True
            else:
                rec.picking_hide_field = False
    
    
    @api.onchange('product_id')
    def _onchange_product_id_custom(self):
        for rec in self:
            if rec.product_id and rec.picking_id.origin:
                raise ValidationError(_("You cannot add a product"))
    
    
    # def unlink(self):
    #     for move in self:
    #         if move.picking_id and move.picking_id.origin:
    #             raise ValidationError(
    #                 "You cannot delete stock move lines when Origin is set."
    #             )
    #     return super().unlink()


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    
    # @api.onchange('product_id')
    # def _onchange_product_id_custom(self):
    #     for rec in self:
    #         if (rec.product_id and rec.order_id.partner_ref) or rec.order_id.state != 'draft':
    #             raise ValidationError(_("You cannot add a product"))
    #
    #
    # def unlink(self):
    #     for rec in self:
    #         if rec.order_id.partner_ref or rec.order_id.state != 'draft':
    #             raise ValidationError(
    #                 "You cannot delete lines when Vendor Reference is set."
    #             )
    #     return super().unlink()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    
    @api.onchange('product_id')
    def _onchange_product_id_custom(self):
        for rec in self:
            if (rec.product_id and rec.order_id.client_order_ref) or rec.order_id.state != 'draft':
                raise ValidationError(_("You cannot add a product"))
    
    
    def unlink(self):
        for rec in self:
            if rec.order_id.client_order_ref or rec.order_id.state != 'draft':
                raise ValidationError(
                    "You cannot delete lines when Customer Reference is set."
                )
        return super().unlink()
