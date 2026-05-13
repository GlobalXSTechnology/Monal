from odoo import models, fields, api, _
from odoo.exceptions import ValidationError




class StockRequestOrder(models.Model):
	_inherit = 'stock.request.order'
	
	
	def action_confirm(self):
		for order in self:
			if not order.expected_date:
				continue
			expected_date = order.expected_date
			company_id = order.company_id.id
			errors = []
			product_checked = set()
			for line in order.stock_request_ids:
				product = line.product_id
				if product.id in product_checked:
					continue
				product_checked.add(product.id)
				restriction = self.env['product.issues.restriction'].search([
					('company_id', '=', company_id),
					('date_from', '<=', expected_date),
					('date_to', '>=', expected_date),
				], limit=1)
				if not restriction:
					continue
				restriction_line = restriction.restriction_line_ids.filtered(
					lambda l: l.product_id.id == product.id
				)
				if not restriction_line:
					continue
				restricted_qty = sum(restriction_line.mapped('product_qty'))
				
				all_orders = self.env['stock.request.order'].search([
					('expected_date', '>=', restriction.date_from),
					('expected_date', '<=', restriction.date_to),
					('company_id', '=', company_id),
				])
				all_lines = all_orders.mapped('stock_request_ids').filtered(
					lambda l: l.product_id.id == product.id
				)
				total_demand_qty = sum(all_lines.mapped('product_uom_qty'))
				if total_demand_qty > restricted_qty:
					errors.append(_(
						"Product: %s | Total Demand: %.2f | Restricted: %.2f"
					) % (
		              product.display_name,
		              total_demand_qty,
		              restricted_qty
	                ))
			if errors:
				raise ValidationError(_("Restricted product issue detected:\n\n") + "\n".join(errors))
		
		return super(StockRequestOrder, self).action_confirm()


































