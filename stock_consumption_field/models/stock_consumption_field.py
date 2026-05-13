from odoo import models, fields, api


class StockConsumptionField(models.Model):
    _inherit = 'stock.picking'

    custom_operation_type = fields.Selection([('issuance', 'Issuance'), ('consumption', 'Consumption')], string='Type',
                                             tracking=True)

    check_type = fields.Boolean(default=False, compute='compute_check_field')

    loc_ids = fields.Many2many('stock.location','stock_picking_loc_rel', compute='get_inventory_locations', store=True)
    dest_loc_ids = fields.Many2many('stock.location','stock_picking_dest_loc_rel', compute='get_inventory_locations', store=True)

    @api.depends('custom_operation_type')
    def compute_check_field(self):
        if self.custom_operation_type == 'consumption':
            self.check_type = True
        else:
            self.check_type = False

    @api.depends('custom_operation_type')
    def get_inventory_locations(self):
        for rec in self:
            rec.loc_ids = False
            rec.dest_loc_ids = False
            if rec.custom_operation_type == 'issuance':
                locations = self.env['stock.location'].search([('usage', '!=', 'inventory'), ('company_id', '=', self.env.company.id)])
                rec.loc_ids = locations.ids
                rec.dest_loc_ids = locations.ids

            elif rec.custom_operation_type == 'consumption':
                locations = self.env['stock.location'].search([('usage', '!=', 'inventory'), ('company_id', '=', self.env.company.id)])
                rec.loc_ids = locations.ids
                dest_locations = self.env['stock.location'].search([('usage', '=', 'inventory'), ('company_id', '=', self.env.company.id)])
                rec.dest_loc_ids = dest_locations.ids

            else:
                locations = self.env['stock.location'].search([('company_id', '=', self.env.company.id)])
                rec.loc_ids = locations.ids
                rec.dest_loc_ids = locations.ids



