from odoo import models, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        for picking in self:

            if picking.picking_type_id.code != 'incoming':
                continue

            purchase_order = picking.purchase_id
            if not purchase_order:
                continue

            if purchase_order.x_studio_purchase_type != 'General':
                continue

            sale_order = self.env['sale.order'].sudo().search([
                ('auto_purchase_order_id', '=', purchase_order.id)
            ], limit=1)

            if not sale_order:
                continue
            delivery_pickings = sale_order.picking_ids.filtered(
                lambda p: p.picking_type_id.code == 'outgoing'
            )

            if not delivery_pickings or any(p.state != 'done' for p in delivery_pickings):
                raise ValidationError(_("Kindly complete Delivery first."))

            # if all(p.state == 'done' for p in delivery_pickings):
            #     continue

            error_lines = []

            for po_line in purchase_order.order_line:
                so_line = sale_order.order_line.filtered(
                    lambda l: l.product_id.id == po_line.product_id.id
                )

                if so_line:
                    po_price = po_line.price_unit
                    so_price = so_line[0].price_unit

                    if round(po_price, 2) != round(so_price, 2):
                        error_lines.append(
                            _("Product: %s | Purchase Rate: %.2f | Sale Rate: %.2f") %
                            (po_line.product_id.display_name, po_price, so_price)
                        )
                else:
                    error_lines.append(
                        _("Product: %s not found in Related Sale Order %s") %
                        (po_line.product_id.display_name, sale_order.name)
                    )

            if error_lines:
                raise ValidationError(
                    _("Kindly Update Related Sale Order Rate.\n\n%s") %
                    ("\n".join(error_lines))
                )

        return super(StockPicking, self).button_validate()


# class SaleOrder(models.Model):
#     _inherit = "sale.order"

#     def action_confirm(self):
#         for order in self:

#             if order.auto_purchase_order_id and order.auto_purchase_order_id.x_studio_purchase_type == 'General':
#                 po = order.auto_purchase_order_id

#                 if po.state not in ['purchase', 'done']:
#                     raise ValidationError(_(
#                         "You cannot confirm this Sale Order because the related Purchase Order (%s) is not confirmed yet.\n"
#                         "Kindly confirm the Purchase Order first."
#                     ) % po.name)

#                 receipt_pickings = po.picking_ids.filtered(
#                     lambda p: p.picking_type_id.code == 'incoming'
#                 )

#                 if not receipt_pickings:
#                     raise ValidationError(_(
#                         "You cannot confirm this Sale Order because the Purchase Order (%s) receipt is not created yet."
#                     ) % po.name)

#                 if any(p.state != 'done' for p in receipt_pickings):
#                     raise ValidationError(_(
#                         "You cannot confirm this Sale Order because the Purchase Order (%s) receipt is not validated yet.\n"
#                         "Kindly validate the Receipt first."
#                     ) % po.name)

#         return super(SaleOrder, self).action_confirm()

# from odoo import models, api, fields, _
# from odoo.exceptions import ValidationError
#
#
# class PurchaseOrder(models.Model):
#     _inherit = "purchase.order"
#
#     update_rate_related_order = fields.Boolean(string="Update rate", default=False)
#
#     def button_confirm(self):
#         for order in self:
#             if order.auto_generated and order.auto_sale_order_id and not order.update_rate_related_order:
#                 raise ValidationError(_("Kindly Update Related Sale Order Rate"))
#
#         return super().button_confirm()
#
#     def action_update_rate_from_partner_ref_sale_order(self):
#         res = super().action_update_rate_from_partner_ref_sale_order()
#         self.write({'update_rate_related_order': True})
#         return res
