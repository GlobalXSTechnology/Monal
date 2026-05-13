from odoo import models, api, _,fields
from odoo.exceptions import ValidationError




class TransferConsumptionLine(models.Model):
    _inherit = 'transfer.consumption.line'

    @api.onchange('demand', 'product_id', 'dest_location_id')
    def _onchange_quantity_restriction(self):
        for line in self:
            if not line.product_id or not line.dest_location_id or not line.demand:
                continue

            parent = line.transfer_id   # replace with correct many2one field if different
            transfer_date = parent.transfer_date.date() if parent and parent.transfer_date else fields.Date.today()

            restriction = self.env['product.issues.restriction'].search([
                ('location_id', '=', line.dest_location_id.id),
                ('date_from', '<=', transfer_date),
                ('date_to', '>=', transfer_date),
                ('state', '=', 'done'),
            ], limit=1)

            if not restriction:
                continue

            restriction_line = restriction.restriction_line_ids.filtered(
                lambda l: l.product_id.id == line.product_id.id
            )

            if not restriction_line:
                continue

            restricted_qty = sum(restriction_line.mapped('product_qty'))

            # already approved transfers
            all_transfers = self.env['transfer.consumption'].search([
                ('transfer_date', '>=', restriction.date_from),
                ('transfer_date', '<=', restriction.date_to),
                ('approval_stage', '=', 'done'),
            ])

            all_lines = all_transfers.mapped('line_ids').filtered(
                lambda l: l.product_id.id == line.product_id.id and
                          l.dest_location_id.id == line.dest_location_id.id
            )

            existing_qty = sum(all_lines.mapped('demand'))

            # include current form lines
            current_lines = parent.line_ids.filtered(
                lambda l: l.product_id.id == line.product_id.id and
                          l.dest_location_id.id == line.dest_location_id.id
            )

            current_qty = sum(current_lines.mapped('demand'))

            total_qty = existing_qty + current_qty

            if total_qty > restricted_qty:
                raise ValidationError(_(
                    "Restricted product issue detected:\n\n"
                    "Product: %s\n"
                    "Destination Location: %s\n"
                    "Total Demand: %.2f\n"
                    "Restricted: %.2f"
                ) % (
                    line.product_id.display_name,
                    line.dest_location_id.display_name,
                    total_qty,
                    restricted_qty
                ))










#
# class TransferConsumption(models.Model):
#     _inherit = 'transfer.consumption'
#
#
#     def action_approve_by_admin(self):
#         errors = []
#         for rec in self:
#             if not rec.line_ids:
#                 continue
#             transfer_date = rec.transfer_date.date() if rec.transfer_date else self.env.context.get(
#                 'date') or fields.Date.today()
#
#             product_location_checked = set()
#             for line in rec.line_ids:
#                 product = line.product_id
#                 dest_location = line.dest_location_id
#                 key = (product.id, dest_location.id)
#                 if key in product_location_checked:
#                     continue
#                 product_location_checked.add(key)
#                 restriction = self.env['product.issues.restriction'].search([
#                     ('location_id', '=', dest_location.id),
#                     ('date_from', '<=', transfer_date),
#                     ('date_to', '>=', transfer_date),
#                     ('state', '=', 'done'),
#                 ], limit=1)
#                 if not restriction:
#                     continue
#
#                 restriction_line = restriction.restriction_line_ids.filtered(
#                     lambda l: l.product_id.id == product.id
#                 )
#                 if not restriction_line:
#                     continue
#
#                 restricted_qty = sum(restriction_line.mapped('product_qty'))
#
#                 all_transfers = self.env['transfer.consumption'].search([
#                     ('transfer_date', '>=', restriction.date_from),
#                     ('transfer_date', '<=', restriction.date_to),
#                     ('approval_stage', '=', 'done'),
#                 ])
#
#                 all_lines = all_transfers.mapped('line_ids').filtered(
#                     lambda l: l.product_id.id == product.id and l.dest_location_id.id == dest_location.id
#                 )
#                 current_lines = rec.line_ids.filtered(
#                     lambda l: l.product_id.id == product.id and l.dest_location_id.id == dest_location.id
#                 )
#                 all_lines |= current_lines
#
#                 total_qty = sum(all_lines.mapped('quantity'))
#
#                 if total_qty > restricted_qty:
#                     errors.append(_(
#                         "Product: %s\nDestination Location: %s\nTotal Demand: %.2f\nRestricted: %.2f"
#                     ) % (
#                                       product.display_name,
#                                       dest_location.display_name,
#                                       total_qty,
#                                       restricted_qty
#                                   ))
#
#         if errors:
#             raise ValidationError(
#                 _("Restricted product issue detected:\n\n") + "\n\n".join(errors)
#             )
#         return super(TransferConsumption, self).action_approve_by_admin()
