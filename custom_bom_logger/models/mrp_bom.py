import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # Parent fields tracking
    product_tmpl_id = fields.Many2one('product.template', tracking=True)
    product_qty = fields.Float(string="Quantity", tracking=True)
    product_id = fields.Many2one('product.product', tracking=True)
    code = fields.Char(tracking=True)
    x_studio_recipe_locator = fields.Many2one('stock.location', string="Recipe Locator", tracking=True)


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    # Fields with tracking enabled
    product_id = fields.Many2one('product.product', string="Product", tracking=True)
    product_qty = fields.Float(string="Quantity", tracking=True)
    factor = fields.Float(string="Factor", tracking=True)

    def write(self, vals):
        for line in self:
            if line.bom_id:
                # 1. Product Change Track karna
                if 'product_id' in vals:
                    old_product = line.product_id.display_name
                    new_product = self.env['product.product'].browse(vals['product_id']).display_name
                    msg = f"Line Product Changed: {old_product} ➔ {new_product}"
                    line.bom_id.message_post(body=msg)

                # 2. Quantity Change Track karna
                if 'product_qty' in vals:
                    old_qty = line.product_qty
                    new_qty = vals['product_qty']
                    msg = f"Line Updated ({line.product_id.name}): Quantity {old_qty} ➔ {new_qty}"
                    line.bom_id.message_post(body=msg)

                # 3. Factor Change Track karna
                if 'factor' in vals:
                    old_factor = line.factor
                    new_factor = vals['factor']
                    msg = f"Line Updated ({line.product_id.name}): Factor {old_factor} ➔ {new_factor}"
                    line.bom_id.message_post(body=msg)

        return super(MrpBomLine, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(MrpBomLine, self).create(vals_list)
        for line in lines:
            if line.bom_id:
                msg = f"New Line Added: {line.product_id.display_name} | Qty: {line.product_qty}"
                line.bom_id.message_post(body=msg)
        return lines

    def unlink(self):
        for line in self:
            if line.bom_id:
                msg = f"Line Removed: {line.product_id.display_name}"
                line.bom_id.message_post(body=msg)
        return super(MrpBomLine, self).unlink()
# import logging
# from odoo import models, fields, api
#
# _logger = logging.getLogger(__name__)
#
#
# class MrpBom(models.Model):
#     _inherit = 'mrp.bom'
#
#     product_tmpl_id = fields.Many2one('product.template', tracking=True)
#     product_qty = fields.Float(tracking=True)
#     product_id = fields.Many2one('product.product', tracking=True)
#     code = fields.Char(tracking=True)
#     company_id = fields.Many2one('res.company', tracking=True)
#
#     @api.model_create_multi
#     def create(self, vals_list):
#         records = super(MrpBom, self).create(vals_list)
#
#         for record in records:
#             message = "<b>[ BOM LOGGER ] - NEW BOM CREATED</b><br/>"
#             message += f"• Product: <b>{record.product_tmpl_id.display_name}</b><br/>"
#             message += f"• Quantity: <b>{record.product_qty}</b><br/>"
#             if record.code:
#                 message += f"• Reference: <b>{record.code}</b><br/>"
#
#             if record.bom_line_ids:
#                 message += "<b>Initial Components:</b><br/>"
#                 for line in record.bom_line_ids:
#                     message += f"&nbsp;&nbsp;&nbsp;- {line.product_id.display_name} | Qty: {line.product_qty}<br/>"
#
#             record.message_post(body=message)
#         return records
#
#     def write(self, vals):
#         res = super(MrpBom, self).write(vals)
#
#         for record in self:
#             changes = []
#
#             if 'product_qty' in vals:
#                 changes.append(f"• Quantity: <b>{vals.get('product_qty')}</b>")
#
#             if 'product_tmpl_id' in vals:
#                 template = self.env['product.template'].browse(vals.get('product_tmpl_id'))
#                 changes.append(f"• Product: <b>{template.display_name}</b>")
#
#             if 'product_id' in vals:
#                 product = self.env['product.product'].browse(vals.get('product_id'))
#                 changes.append(f"• Variant: <b>{product.display_name}</b>")
#
#             if 'code' in vals:
#                 changes.append(f"• Reference: <b>{vals.get('code')}</b>")
#
#             if 'bom_line_ids' in vals:
#                 for command in vals.get('bom_line_ids'):
#                     if command[0] == 0:
#                         p_id = command[2].get('product_id')
#                         p_name = self.env['product.product'].browse(p_id).display_name if p_id else "Unknown"
#                         changes.append(f"• Added: {p_name} (Qty: {command[2].get('product_qty')})")
#
#                     elif command[0] == 1:
#                         line = self.env['mrp.bom.line'].browse(command[1])
#                         p_name = line.product_id.display_name
#                         qty = command[2].get('product_qty', line.product_qty)
#                         changes.append(f"• Updated: {p_name} ➔ Qty: {qty}")
#
#                     elif command[0] == 2:
#                         line = self.env['mrp.bom.line'].browse(command[1])
#                         changes.append(f"• Removed: {line.product_id.display_name}")
#
#             if changes:
#                 message = "<br/>".join(changes)
#                 record.message_post(body=message)
#
#         return res
#
#
# class MrpBomLine(models.Model):
#     _inherit = 'mrp.bom.line'
#
#     product_id = fields.Many2one('product.product', tracking=True)
#     product_qty = fields.Float(tracking=True)
