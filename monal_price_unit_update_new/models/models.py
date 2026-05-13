from odoo import models, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'
	
	
	
	def action_update_rate_from_partner_ref_sale_order(self):
		for purchase_order in self:
			if self.env['stock.picking'].search([('origin','=',purchase_order.name),('state','in',['done'])]):
				raise UserError(_("You are not allowed update rates of the Purchase order. Because GRN of the PO is already done."))

			if not purchase_order.partner_ref:
				raise UserError(_("No Partner Reference found on this Purchase Order."))
			
			sale_order = self.env['sale.order'].sudo().search([
				('name', '=', purchase_order.partner_ref)
			], limit=1)
			if not sale_order:
				raise UserError(
					_("No Sale Order found with name matching Partner Reference '%s'.") % purchase_order.partner_ref)
			sale_order = sale_order.with_company(sale_order.company_id)
			sale_order_price_map = {
				line.product_id.id: line.price_unit
				for line in sale_order.order_line
			}
			
			updated_lines = 0
			for line in purchase_order.order_line:
				new_price = sale_order_price_map.get(line.product_id.id)
				if new_price is not None:
					line.price_unit = new_price
					updated_lines += 1
			# purchase_order.write({'update_rate_related_order':True})
			
			if updated_lines == 0:
				raise UserError(_("No matching products found to update prices."))


