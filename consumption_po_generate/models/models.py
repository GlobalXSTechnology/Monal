from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ConsumptionPOGenerate(models.TransientModel):
    _name = 'po.generate.wizard'

    wizard_vendor = fields.Many2one('res.partner', string='Vendor')
    consumption_id = fields.Many2one('transfer.consumption', string='Consumption', readonly=True)

    def create_po(self):
        for wizard in self:
            if not wizard.consumption_id:
                continue

            consumption = wizard.consumption_id

            lines_to_order = consumption.line_ids.filtered(
                lambda l: l.generate_po == True
            )
            if not lines_to_order:
                raise ValidationError('No products require purchase — all demands are covered by available stock.')

            # existing = self.env['purchase.order'].search([('consumption_id','=', consumption.id,)])
            #
            # if existing:
            #     raise ValidationError('Purchase Order is already generated of this Record')

            po = self.env['purchase.order'].create({
                'partner_id': wizard.wizard_vendor.id,
                'date_order': consumption.accounting_date,
                'picking_type_id': consumption.warehouse_id.in_type_id.id,
                'origin': consumption.name,
                'consumption_id': consumption.id,
            })

            for line in lines_to_order:
                qty_to_order = line.demand
                self.env['purchase.order.line'].create({
                    'order_id': po.id,
                    'product_id': line.product_id.id,
                    'product_qty': qty_to_order,
                })

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': po.id,
            }


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    consumption_id = fields.Many2one('transfer.consumption', string='Consumption', readonly=True)


class TransferConsumptionLine(models.Model):
    _inherit = "transfer.consumption.line"

    generate_po = fields.Boolean(string="Purchase", default=False)
    purchase_status = fields.Selection([('draft', 'RFQ'),('sent', 'RFQ Sent'),('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),('done', 'Locked'),('cancel', 'Cancelled')],
        compute='_compute_purchase_status', string='Purchase Status', store=True)
    purchase_editable = fields.Boolean(compute='compute_editable_purchase', default=True)

    @api.depends('purchase_status')
    def compute_editable_purchase(self):
        for rec in self:
            if not rec.purchase_status:
                rec.purchase_editable = False
            else:
                rec.purchase_editable = True


    @api.depends('product_id', 'transfer_id.purchase_ids.state', 'transfer_id.purchase_ids.order_line.product_id')
    def _compute_purchase_status(self):
        for line in self:
            purchase_lines = self.env['purchase.order.line'].search([
                ('product_id', '=', line.product_id.id),
                ('order_id.consumption_id', '=', line.transfer_id.id)
            ])

            if purchase_lines:
                line.purchase_status = purchase_lines[0].order_id.state
            else:
                line.purchase_status = False

class TransferConsumption(models.Model):
    _inherit = "transfer.consumption"

    purchase_ids = fields.One2many(
        "purchase.order", "consumption_id", string="Purchase Orders"
    )
    purchase_count = fields.Integer(
        string="PO", compute="_compute_purchase_count"
    )
    purchase_all = fields.Boolean(string='Select All', default=False)

    @api.onchange('purchase_all')
    def select_all_lines(self):
        for rec in self:
            if rec.purchase_all:
                rec.line_ids.generate_po = True
            else:
                rec.line_ids.generate_po = False


    def _compute_purchase_count(self):
        for rec in self:
            rec.purchase_count = len(rec.purchase_ids)

    def action_view_po(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('consumption_id', '=', self.id)],
            'context': [('default_consumption_id', '=', self.id)],
        }
