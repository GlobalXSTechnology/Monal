from odoo import models, fields, api

from collections import defaultdict
from odoo.exceptions import ValidationError, UserError

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
from odoo.tools.misc import clean_context

from odoo.tools.float_utils import float_is_zero, float_compare

class StockMove(models.Model):
    _inherit = 'stock.move'
    def _get_price_unit(self):
        self.ensure_one()
    
        # 👉 Check if this move is related to an unbuild order
        if self.unbuild_id and self.unbuild_id.is_butchery:
            # You can adjust this logic as needed
            print('in iherited fucntion')
            if self.product_id.categ_id.property_cost_method != 'standard':
                costing = self.unbuild_id.line_ids.filtered(lambda x: x.product_id.id ==
                                                                      self.product_id.id).product_uom_qty_share if \
                    not self.unbuild_id.line_ids.filtered(lambda x: x.product_id.id ==
                                                                    self.product_id.id).product_uom.name=='pcs'  else \
                    (self.unbuild_id.line_ids.filtered(lambda x: x.product_id.id ==
                                                                self.product_id.id).product_uom_qty_share*self.unbuild_id.line_ids.filtered(lambda x: x.product_id.id ==
                                                                self.product_id.id).weight) / \
                    self.unbuild_id.line_ids.filtered(
                        lambda x: x.product_id.id ==
                                  self.product_id.id).product_qty
            else:
                costing = self.unbuild_id.line_ids.filtered(lambda x:
                                                            x.product_id.id==self.product_id.id).product_qty * \
                          self.product_id.standard_price
            if costing:
                return {self.env['stock.lot']: costing}
    
        # 👇 Fallback to default Odoo logic
        return super()._get_price_unit()
    # def _get_price_unit(self):
    #     self.ensure_one()

    #     # 👉 Check if this move is related to an unbuild order
    #     if self.unbuild_id and self.unbuild_id.is_butchery:
    #         # You can adjust this logic as needed
    #         print('in iherited fucntion')
    #         costing = self.unbuild_id.line_ids.filtered(lambda x: x.product_id.id ==
    #                                                               self.product_id.id).product_uom_qty_share if \
    #             not self.unbuild_id.line_ids.filtered(lambda x: x.product_id.id ==
    #                                                               self.product_id.id).weight >0 else \
    #             self.unbuild_id.line_ids.filtered(lambda x: x.product_id.id ==
    #                                                               self.product_id.id).product_uom_qty_share / self.unbuild_id.line_ids.filtered(lambda x: x.product_id.id ==
    #                                                               self.product_id.id).product_qty
    #         if costing:
    #             return {self.env['stock.lot']: costing}

    #     # 👇 Fallback to default Odoo logic
    #     return super()._get_price_unit()

class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    factor = fields.Float('Factor',store=True)

class MrpBomUn(models.Model):
    _inherit = 'mrp.bom'

    is_butchery = fields.Boolean('Is Butchery BOM?',store=True)

class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    line_ids = fields.One2many('butcher.unbuild.line', 'unbuild_id', string="BOM Lines")
    is_butchery = fields.Boolean('Is Butchery',store=True)
    
    weight_sum = fields.Float(string="Total Weight", compute='_compute_weight_sum', store=True)
    weight_percentage = fields.Float(string="Yield %", compute='_compute_weight_sum', store=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', domain=[('is_butchery', '=', True)])

    total_product_qty = fields.Float(string='Total Qty', compute='_compute_weight_sum', store=True)

    
    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        
        if self.warehouse_id:
            self.location_id = self.warehouse_id.lot_stock_id
            self.location_dest_id = self.warehouse_id.lot_stock_id
        else:
            self.location_id = False
            self.location_dest_id = False
            
            
            
    @api.depends('line_ids.weight', 'product_qty')
    def _compute_weight_sum(self):
        for rec in self:
            total_weight = sum(line.weight for line in rec.line_ids)
            total_product_qty = sum(line.product_qty for line in rec.line_ids)
            rec.weight_sum = total_weight
            rec.total_product_qty = total_product_qty
            if rec.product_qty:
                rec.weight_percentage = (total_weight / rec.product_qty) * 100
            else:
                rec.weight_percentage = 0

    def copy(self, default=None):
        new_orders = super().copy(default)
        unbuild_lines = self.line_ids
        for i in unbuild_lines:
            new = i.copy()
            new.unbuild_id = new_orders.id

        return new_orders
    
    my_ribbon = fields.Char(
        compute='_compute_my_ribbon',
        string='Ribbon'
    )
    
    @api.depends('weight_percentage', 'state')
    def _compute_my_ribbon(self):
        for rec in self:
            if rec.state != 'done':
                rec.my_ribbon = False
            elif rec.weight_percentage > 100:
                rec.my_ribbon = 'Yield is %.2f%% > product qty' % rec.weight_percentage
            else:
                rec.my_ribbon = 'Yield of this butchery order is low - %.2f%%' % rec.weight_percentage



    @api.depends('company_id')
    def _compute_location_id(self):
        for order in self:
            if order.company_id and 2==3:
                warehouse = self.env['stock.warehouse'].search([('company_id', '=', order.company_id.id)], limit=1)
                if order.location_id.company_id != order.company_id:
                    order.location_id = warehouse.lot_stock_id
                if order.location_dest_id.company_id != order.company_id:
                    order.location_dest_id = warehouse.lot_stock_id



    def _generate_consume_moves_butcher(self):
        moves = self.env['stock.move']
        for unbuild in self:
            if unbuild.mo_id:
                finished_moves = unbuild.mo_id.move_finished_ids.filtered(lambda move: move.state == 'done')
                factor = unbuild.product_qty / unbuild.mo_id.product_uom_id._compute_quantity(unbuild.mo_id.qty_produced, unbuild.product_uom_id)
                for finished_move in finished_moves:
                    moves += unbuild._generate_move_from_existing_move(finished_move, factor, unbuild.location_id, finished_move.location_id)
            else:
                factor = unbuild.product_uom_id._compute_quantity(unbuild.product_qty, unbuild.bom_id.product_uom_id) / unbuild.bom_id.product_qty
                moves += unbuild._generate_move_from_bom_line(self.product_id, self.product_uom_id, unbuild.product_qty)
                # for byproduct in unbuild.bom_id.byproduct_ids:
                # for byproduct in self.line_ids:
                #     # if byproduct._skip_byproduct_line(unbuild.product_id):
                #     #     continue
                #     # quantity = byproduct.product_qty * factor
                #     quantity = byproduct.product_qty * byproduct.product_uom_qty
                #     # moves += unbuild._generate_move_from_bom_line(byproduct.product_id, byproduct.product_uom_id, quantity, byproduct_id=byproduct.id)
                #     moves += unbuild._generate_move_from_bom_line_butcher(byproduct.product_id, byproduct.product_uom, quantity, byproduct_id=byproduct.id)
        return moves

    def _generate_produce_moves_butcher(self):
        moves = self.env['stock.move']
        for unbuild in self:
            if unbuild.mo_id:
                raw_moves = unbuild.mo_id.move_raw_ids.filtered(lambda move: move.state == 'done')
                factor = unbuild.product_qty / unbuild.mo_id.product_uom_id._compute_quantity(unbuild.mo_id.qty_produced, unbuild.product_uom_id)
                for raw_move in raw_moves:
                    moves += unbuild._generate_move_from_existing_move(raw_move, factor, raw_move.location_dest_id, self.location_dest_id)
            else:
                factor = unbuild.product_uom_id._compute_quantity(unbuild.product_qty, unbuild.bom_id.product_uom_id) / unbuild.bom_id.product_qty
                boms, lines = unbuild.bom_id.explode(unbuild.product_id, factor, picking_type=unbuild.bom_id.picking_type_id)
                # for line, line_data in lines:
                #     moves += unbuild._generate_move_from_bom_line_butcher(line.product_id, line.product_uom_id, line_data['qty'], bom_line_id=line.id)
                for line in self.line_ids:
                    moves += unbuild._generate_move_from_bom_line_butcher(line.product_id, line.product_uom, line.product_qty, bom_line_id=line.id)
        return moves

    def _generate_move_from_existing_move(self, move, factor, location_id, location_dest_id):
        return self.env['stock.move'].create({
            'name': self.name,
            'date': self.create_date,
            'product_id': move.product_id.id,
            'product_uom_qty': move.quantity * factor,
            'product_uom': move.product_uom.id,
            'procure_method': 'make_to_stock',
            'location_dest_id': location_dest_id.id,
            'location_id': location_id.id,
            'warehouse_id': location_dest_id.warehouse_id.id,
            'unbuild_id': self.id,
            'company_id': move.company_id.id,
            'origin_returned_move_id': move.id,
        })

    def _generate_move_from_bom_line_butcher(self, product, product_uom, quantity, bom_line_id=False, byproduct_id=False):
        product_prod_location = product.with_company(self.company_id).property_stock_production
        location_id = bom_line_id and product_prod_location or self.location_id
        location_dest_id = bom_line_id and self.location_dest_id or product_prod_location
        warehouse = location_dest_id.warehouse_id

        # byproduct_id =
        return self.env['stock.move'].create({
            'name': self.name,
            'date': self.create_date,
            # 'bom_line_id': bom_line_id,
            # 'byproduct_id': byproduct_id,
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom': product_uom.id,
            'procure_method': 'make_to_stock',
            'location_dest_id': location_dest_id.id,
            'location_id': location_id.id,
            'warehouse_id': warehouse.id,
            'unbuild_id': self.id,
            'company_id': self.company_id.id,
        })

    def action_unbuild(self):
        self.ensure_one()
        self._check_company()
        # remove the default_* keys that was only needed in the unbuild wizard
        self.env.context = dict(clean_context(self.env.context))
        if self.product_id.tracking != 'none' and not self.lot_id.id:
            raise UserError(_('You should provide a lot number for the final product.'))

        if self.mo_id and self.mo_id.state != 'done':
            raise UserError(_('You cannot unbuild a undone manufacturing order.'))
        if not self.line_ids:

            consume_moves = self._generate_consume_moves()
            consume_moves._action_confirm()

            produce_moves = self._generate_produce_moves()
            produce_moves._action_confirm()
        else:
            consume_moves = self._generate_consume_moves_butcher()
            consume_moves._action_confirm()
            produce_moves = self._generate_produce_moves_butcher()
            produce_moves._action_confirm()
            print('llllllllllllll')
        produce_moves.quantity = 0

        finished_moves = consume_moves.filtered(lambda m: m.product_id == self.product_id)
        consume_moves -= finished_moves

        if any(produce_move.has_tracking != 'none' and not self.mo_id for produce_move in produce_moves):
            raise UserError(_('Some of your components are tracked, you have to specify a manufacturing order in order to retrieve the correct components.'))

        if any(consume_move.has_tracking != 'none' and not self.mo_id for consume_move in consume_moves):
            raise UserError(_('Some of your byproducts are tracked, you have to specify a manufacturing order in order to retrieve the correct byproducts.'))

        for finished_move in finished_moves:
            finished_move_line_vals = self._prepare_finished_move_line_vals(finished_move)
            self.env['stock.move.line'].create(finished_move_line_vals)

        # TODO: Will fail if user do more than one unbuild with lot on the same MO. Need to check what other unbuild has aready took
        qty_already_used = defaultdict(float)
        for move in produce_moves | consume_moves:
            original_move = move in produce_moves and self.mo_id.move_raw_ids or self.mo_id.move_finished_ids
            original_move = original_move.filtered(lambda m: m.product_id == move.product_id)
            if not original_move:
                move.quantity = float_round(move.product_uom_qty, precision_rounding=move.product_uom.rounding)
                continue
            needed_quantity = move.product_uom_qty
            moves_lines = original_move.mapped('move_line_ids')
            if move in produce_moves and self.lot_id:
                moves_lines = moves_lines.filtered(lambda ml: self.lot_id in ml.produce_line_ids.lot_id)  # FIXME sle: double check with arm
            for move_line in moves_lines:
                # Iterate over all move_lines until we unbuilded the correct quantity.
                taken_quantity = min(needed_quantity, move_line.quantity - qty_already_used[move_line])
                taken_quantity = float_round(taken_quantity, precision_rounding=move.product_uom.rounding)
                if taken_quantity:
                    move_line_vals = self._prepare_move_line_vals(move, move_line, taken_quantity)
                    self.env["stock.move.line"].create(move_line_vals)
                    needed_quantity -= taken_quantity
                    qty_already_used[move_line] += taken_quantity

        (finished_moves | consume_moves | produce_moves).picked = True
        finished_moves._action_done()
        consume_moves._action_done()
        produce_moves._action_done()
        produced_move_line_ids = produce_moves.mapped('move_line_ids').filtered(lambda ml: ml.quantity > 0)
        consume_moves.mapped('move_line_ids').write({'produce_line_ids': [(6, 0, produced_move_line_ids.ids)]})
        if self.mo_id:
            unbuild_msg = _("%(qty)s %(measure)s unbuilt in %(order)s",
                qty=self.product_qty,
                measure=self.product_uom_id.name,
                order=self._get_html_link(),
            )
            self.mo_id.message_post(
                body=unbuild_msg,
                subtype_xmlid='mail.mt_note',
            )
        return self.write({'state': 'done'})



    # @api.constrains('product_id','bom_id')
    # def on_create_onchange_product_id_first(self):
    #     for rec in self:
    #         for ln in rec.line_ids:
    #             print(ln.product_uom,'------------',ln.product_uom_int_id)
    #             # if not ln.product_uom and ln.product_uom_int_id:
    #             #     ln.product_uom = ln.product_uom_int_id
    #             #     print(ln.product_uom)
    #             print('header ubuild line cons')
    #             print(ln.product_id)
    #             if not ln.product_id and ln.product_id_int_id:
    #                 ln.product_id = ln.product_id_int_id
    #                 print(ln.product_id)
    #             # if ln.product_uom_qty_share == 0:
    #             #     ln.product_uom_qty_share = ln.product_uom_qty_share_hd

    def action_load_bom_lines(self):
        """Button to load BOM lines — bypasses onchange limit"""
        if self.product_id and self.location_id:
            quants = self.env['stock.quant'].search([
                ('location_id', '=', self.location_id.id),
                ('product_id', '=', self.product_id.id)
            ])
            quantity = sum(quants.mapped('inventory_quantity_auto_apply'))
            if quantity <= 0:
                raise ValidationError('Stock is Not available')

        self.line_ids = [(5, 0, 0)]
        lst = []
        price = self.product_id.standard_price

        if self.bom_id:
            for line in self.bom_id.bom_line_ids:
                lst.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_id_int_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'product_uom_qty': line.factor,
                    'product_uom_qty_share': price * line.factor,
                    'product_uom': line.product_uom_id.id,
                    'product_uom_int_id': line.product_uom_id.id,
                }))

        self.write({'line_ids': lst})

    @api.onchange('product_id','bom_id', 'location_id','product_qty')
    def _onchange_product_id(self):
        if self.product_id and self.location_id:
            quants_lot21 = self.env['stock.quant'].search(
                [('location_id', '=', self.location_id.id), ('product_id', '=', self.product_id.id)])
            quantity1 = sum(quants_lot21.mapped('inventory_quantity_auto_apply'))
            if quantity1 > 0:
                pass
            else:
                raise ValidationError('Stock is Not available')

            # bom = self.env['mrp.bom']._bom_find(self.product_id)
            # print(bom)



            # bom = self.env['mrp.bom'].search([('product_id','=',self.product_id.product_tmpl_id.id)])
            self.line_ids = [(5, 0, 0)]
            lst = []
            price = self.product_id.standard_price
            # for lim in range(70):
            if self.bom_id:
                for line in self.bom_id.bom_line_ids:
                    lst.append((0, 0, {
                        'product_id': line.product_id.id,
                        'product_id_int_id':line.product_id.id,
                        'product_qty': line.product_qty,
                        'product_uom_qty':line.factor,
                        'product_uom_qty_share': price * line.factor,
                        'product_uom': line.product_uom_id.id,
                        'product_uom_int_id': line.product_uom_id.id,
                    }))
            self.line_ids = lst



class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    is_butchery = fields.Boolean(string="Is Butchery")

class ButcherUnbuildLine(models.Model):
    _name = 'butcher.unbuild.line'
    _description = 'Unbuild Line'


    unbuild_id = fields.Many2one('mrp.unbuild', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True,readonly=False) 
    product_id_int_id = fields.Integer('id')
    # product_id = fields.Many2one('product.product', string='Product', required=False,readonly=True)

    product_qty = fields.Float(string='Qty')
    product_uom_qty = fields.Float(string='Factor')
    product_uom_qty_share = fields.Float(string='Factor Share' , store=True)

    product_uom_qty_share_hd = fields.Float(string='Factor Share  hd')
    product_uom = fields.Many2one('uom.uom',related='product_id.uom_id' ,string='Unit of Measure',readonly=True,
                                  store=True)
    product_uom_int_id = fields.Integer('id')
    weight = fields.Float('Weight',store=True)

    @api.constrains('product_qty')
    @api.onchange('product_qty')
    def on_create_onchange_kg_qty(self):
        for ln in self:
            if ln.product_uom.name == 'KG' or ln.product_uom.name == 'kg':
                ln.weight = ln.product_qty
    @api.constrains('product_id_int_id')
    def store_prod(self):
        for rec in self:
            rec.product_id = rec.product_id_int_id

    
    # @api.constrains('product_id','product_id_int_id')
    # # @api.onchange('product_id','product_id_int_id')
    # def on_create_onchange_product_id(self):
    #     for ln in self:
    #
    #         # if ln.product_uom_qty_share == 0:
    #         #     ln.product_uom_qty_share = ln.product_uom_qty_share_hd
    #         # if not ln.product_uom:
    #         #     ln.product_uom = ln.product_id.uom_id.id
    #         #     ln.product_uom_int_id = ln.product_id.uom_id.id
    #         print('ubuild line cons')
    #         print(ln.product_id)
    #         print(ln.product_id_int_id)
    #         if not ln.product_id:
    #             if not ln.product_id and ln.product_id_int_id:
    #                 ln.product_id = ln.product_id_int_id
    #
    #
    # @api.depends('product_id')
    def get_share_val(self):
        for rec in self:
            factor = rec.unbuild_id.bom_id.bom_line_ids.filtered(lambda x:x.product_id.id == rec.product_id.id).factor
            rec.product_uom_qty_share = factor * rec.unbuild_id.product_id.standard_price
            rec.product_uom_qty_share_hd = factor * rec.unbuild_id.product_id.standard_price
            rec.product_uom_qty = factor
    

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_butcher_product = fields.Boolean(string="Is Butchery Product?")
    factor = fields.Float(string="Factor", default=0.0)


# class ProductProduct(models.Model):
#     _inherit = 'product.product'
#
#     factor = fields.Float(string="Factor", default=1.0)

class AssignFactor(models.Model):
    _name = 'assign.factor'
    _description = 'Assign Factor'




    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('assign.factor.sequence')
        return super(AssignFactor, self).create(vals)

    name = fields.Char(string="Reference", required=False,readonly=True)

    apply_check = fields.Boolean()
    product_check = fields.Boolean()
    date_to = fields.Date(string="Date To")
    date_from = fields.Date(string="Date From")
    line_ids = fields.One2many('assign.factor.line', 'assign_id', string="Product Lines")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Applied'),
    ], string='Status', default='draft', readonly=True)

    def get_prod(self):
        self.product_check = True
        """Fetch butcher products and create lines"""
        self.ensure_one()
        self.line_ids.unlink()
        prod = self.env['product.product'].search([('is_butcher_product', '=', True)])
        for i in prod:
            self.env['assign.factor.line'].create({
                'assign_id': self.id,
                'product_id': i.id,
                'current_factor': i.factor,
            })

    def assign_factor(self):
        self.apply_check = True
        """Apply new factors to products and lock the form"""
        for line in self.line_ids:
            line.product_id.factor = line.new_factor
        self.state = 'done'


class AssignFactorLine(models.Model):
    _name = 'assign.factor.line'
    _description = 'Assign Factor Line'

    assign_id = fields.Many2one('assign.factor', string="Assign Factor", required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    current_factor = fields.Float(string="Current Factor", readonly=True)
    new_factor = fields.Float(string="New Factor")
