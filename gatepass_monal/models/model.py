from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError


class GatePass(models.Model):
    _name = 'monal.gatepass'
    _display_name = 'Inventory Gate Pass'
    _rec_name = 'name'

    name = fields.Char(string='Name', readonly=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Partner')
    ware_house = fields.Many2one('stock.warehouse', string='Warehouse', domain="[('company_id', '=', company_id)]", required=True)
    loc_ids = fields.Many2many('stock.location', compute='get_warehouse_locations', store=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company)
    from_location = fields.Many2one('stock.location', string='From Location')
    ref = fields.Char(string='Ref')
    transfer_date = fields.Datetime(string="Date", default=datetime.now())
    transferred_by = fields.Many2one('res.users', string='Transferred By', default=lambda self: self.env.user,
                                     readonly=True)
    return_of = fields.Char(string='Related Documents')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('returnable', 'Returnable'),
        ('done', 'Done')
    ], string="Status", default="draft", tracking=True)
    type = fields.Selection([('inwards', 'Inwards'), ('outwards', 'Outwards')], string="Type", required=True)
    remarks = fields.Char(string="Remarks")

    parent_id = fields.Many2one('monal.gatepass', string="Parent Gatepass", index=True)
    return_ids = fields.One2many('monal.gatepass', 'parent_id', string="Return Gatepasses")

    return_count = fields.Integer(
        string="Return Count",
        compute="_compute_return_count"
    )

    def _compute_return_count(self):
        for rec in self:
            rec.return_count = len(rec.return_ids)

    line_ids = fields.One2many('monal.gatepass.line', 'gatepass_id', string="GatePass Lines")

    @api.onchange('ware_house')
    def get_warehouse_locations(self):
        for rec in self:
            if rec.ware_house:
                locations = self.env['stock.location'].search([('warehouse_id', '=', rec.ware_house.id)])
                rec.loc_ids = locations.ids
                print('done')

    @api.onchange('ware_house')
    def _onchange_warehouse_set_location(self):
        for rec in self:
            if rec.ware_house:
                rec.from_location = rec.ware_house.lot_stock_id

    def proceed_button(self):
        for rec in self:
            has_returnable = False
            for line in rec.line_ids:
                if line.return_type == 'returnable':
                    line.status = 'returnable'
                    has_returnable = True
                else:
                    line.status = 'done'
            rec.state = 'returnable' if has_returnable else 'done'

    def return_button(self):
        self.ensure_one()
        return_lines = self.line_ids.filtered(lambda l: l.return_type == "returnable" and  l.returned_qty < l.product_qty)

        if not return_lines:
            return

        wizard = self.env["gatepass.return.wizard"].create({
            "gatepass_id": self.id,
            "line_ids": [(0, 0, {
                "original_line_id": line.id,
                "product_id": line.product_id.id,
                "product_qty": line.product_qty,
                "returned_qty": line.returned_qty,
            }) for line in return_lines]
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": "gatepass.return.wizard",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }


    def create(self, vals):
        if not vals.get('type') and self._context.get('default_type'):
            vals['type'] = self._context['default_type']

        if vals.get('type') == 'outwards':
            vals['name'] = self.env['ir.sequence'].next_by_code('monal.gatepass.outwards') or '/'
        elif vals.get('type') == 'inwards':
            vals['name'] = self.env['ir.sequence'].next_by_code('monal.gatepass.inwards') or '/'

        return super(GatePass, self).create(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("You can only delete GatePass in Draft state!")
        return super(GatePass, self).unlink()

    def action_view_returns(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Return Gatepasses',
            'res_model': 'monal.gatepass',
            'view_mode': 'list,form',
            'domain': [('parent_id', '=', self.id)],
            'context': dict(self._context, default_parent_id=self.id),
        }


class LineModel(models.Model):
    _name = 'monal.gatepass.line'

    gatepass_id = fields.Many2one('monal.gatepass', string="Gatepass")
    product_id = fields.Many2one('product.product', string='Product')
    product_qty = fields.Float(string='Quantity', required=True)
    returned_qty = fields.Float(string='Returned Quantity', readonly=True)
    remaining_qty = fields.Float(string='Remaining Quantity', compute='compute_remaining_qty')
    return_type = fields.Selection([('returnable', 'Returnable'), ('not_returnable', 'Not-Returnable')],
                                   string="Return Type", required=True)
    remarks = fields.Char(string="Remarks")
    transfer_date = fields.Datetime(related="gatepass_id.transfer_date",string="Date",readonly=True)

    status = fields.Selection([
        ('returnable', 'Returnable'),
        ('done', 'Done')
    ], compute='compute_state', string="Status", store=True)

    @api.depends('product_qty', 'returned_qty', 'remaining_qty')
    def compute_state(self):
        for rec in self:
            if rec.gatepass_id.state != 'draft':
                if rec.product_qty == rec.returned_qty or rec.remaining_qty == 0:
                    rec.status = 'done'
                else:
                    rec.status = 'returnable'
            else:
                rec.status = False

    @api.depends('returned_qty', 'remaining_qty')
    def compute_remaining_qty(self):
        for rec in self:
            if rec.returned_qty > 0:
                rec.remaining_qty = rec.product_qty - rec.returned_qty
            else:
                rec.remaining_qty = 0
