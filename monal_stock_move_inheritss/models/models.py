from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = "stock.move"

    total = fields.Float(
        string="Total",
        compute="_compute_total",
        store=True,
        readonly=True,
        force_save=True
    )
    cost = fields.Float(
        string="Cost",
        store=True,
        readonly=True,
        force_save=True
    )

    @api.depends('quantity', 'cost')
    def _compute_total(self):
        for move in self:
            qty = move.quantity
            move.total = move.cost * qty

    @api.constrains('product_id', 'state')
    @api.onchange('product_id', 'state')
    def _compute_cost(self):
        for move in self:
            qty = move.quantity
            move.cost = move.product_id.standard_price
            move._compute_total()

