from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

class TransferConsumption(models.Model):
    _name = 'transfer.consumption'
    _inherit = ['mail.thread']  # 👈 add this line
    _description = 'Inventory Transfer Tracker'
    _order = 'transfer_date desc'

    reference = fields.Char(string="Description")
    backorder = fields.Char(string="Backorder", compute='_compute_backorder_reference', store=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        tracking=True
    )

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    name = fields.Char(string="Reference", required=False, readonly=True)
    source_location_id = fields.Many2one('stock.location', string='From Location',readonly="1", required=True)
    dest_location_id = fields.Many2one('stock.location', string='To Location', tracking=True)
    transfer_date = fields.Datetime(string='Transfer Date', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Transferred By', default=lambda self: self.env.user)
    apply_check = fields.Boolean(string="Ally Check")

    analytic_distribution = fields.Json(inverse="_inverse_analytic_distribution",)
    analytic_precision = fields.Integer(default=2)

    
    def _inverse_analytic_distribution(self):
        pass
    product_check = fields.Boolean()
    approval_user_id = fields.Many2one(
        'res.users',
        string='Approver User',
        tracking=True
    )
    backorder_count = fields.Integer(
        string='Backorders',
        compute='_compute_backorder_count'
    )

    @api.depends('backorder_ids')
    def _compute_backorder_count(self):
        for rec in self:
            rec.backorder_count = len(rec.backorder_ids)

    line_ids = fields.One2many('transfer.consumption.line', 'transfer_id', string='Transfer Lines')

    approval_stage = fields.Selection([
        ('draft', 'Draft'),
        ('admin', 'GM Project Approval'),
        ('done', 'Done'),
    ], string="Approval Stage", default='draft', tracking=True)
    internal_transfer_count = fields.Integer(string='Internal Transfers', compute='_compute_internal_transfer_count')
    quantity_check = fields.Boolean(string="Qty Checked")
    accounting_date = fields.Date(string='Accounting Date', tracking=True, required=True,default=fields.Datetime.now)

    @api.constrains('accounting_date','approval_stage')
    def validation_accounting_date(self):
        for rec in self:
            if rec.x_studio_from_location_company.fiscalyear_lock_date and rec.accounting_date:
                if rec.accounting_date <= rec.x_studio_from_location_company.fiscalyear_lock_date:
                    raise ValidationError(_(f'Your are not allowed to change accounting date bellow or equal to \nthe lock date {rec.x_studio_from_location_company.fiscalyear_lock_date}.\nIf you really need to post records in previous dates\nplease contact your administration in this regard.'))

    @api.depends('name')
    def _compute_backorder_reference(self):
        for rec in self:
            if rec.reference and "Backorder of" in rec.reference:
                rec.backorder = rec.reference
            else:
                rec.backorder = False

    def _compute_backorder_count(self):
        for rec in self:
            # Assuming backorders are also stock.picking records with a reference to this document
            rec.backorder_count = self.env['stock.picking'].search_count([
                ('origin', '=', rec.name),
                ('backorder_id', '!=', False)  # only those created as backorders
            ])

    def action_view_backorders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Backorders',
            'res_model': 'transfer.consumption',
            'view_mode': 'list,form',
            'domain': [('backorder_id', '=', self.id)],
            'context': dict(self.env.context),
        }

    def action_fill_all_quantities(self):
        for rec in self:
            # rec.line_ids._compute_available_quantity()
            for line in rec.line_ids:
                # if line.demand <= 0:
                #     continue

                if line.demand > line.avb_quantity:
                    line.quantity = line.avb_quantity
                else:
                    line.quantity = line.demand
                #
                # # Make field editable if needed
                line.can_edit_quantity = True

            rec.quantity_check = True

    def copy(self, default=None):
        new_orders = super().copy(default)
        new_orders.approval_stage = 'draft'
        new_orders.name = self.env['ir.sequence'].next_by_code('transfer.consumption')
        unbuild_lines = self.line_ids
        for i in unbuild_lines:
            new = i.copy()
            new.transfer_id = new_orders.id
            new.can_edit_quantity = True

        return new_orders

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id:
            self.source_location_id = self.warehouse_id.lot_stock_id.id

    @api.depends('name')
    def _compute_internal_transfer_count(self):
        for record in self:

            count = self.env['stock.picking'].search_count([
                ('picking_type_id.code', '=', 'internal'),
                ('origin', '=', record.name),('company_id','=',record.x_studio_from_location_company.id)
            ])
            picking_ids = self.env['stock.picking'].search([
                ('picking_type_id.code', '=', 'internal'),
                ('origin', '=', record.name),('company_id','=',record.x_studio_from_location_company.id)
            ])
            count = len(picking_ids.ids) + len(picking_ids.return_ids.ids)
            record.internal_transfer_count = count

    def action_view_internal_transfers(self):
        self.ensure_one()

        if not self.id or not self.name:
            raise ValidationError("Please create and save the record before viewing internal transfers.")

        if self.approval_stage != 'done':
            raise ValidationError("You can only view internal transfers after the transfer is marked as 'Done'.")
        picking_ids = self.env['stock.picking'].search([
            ('picking_type_id.code', '=', 'internal'),
            ('origin', '=', self.name),('company_id','=',self.x_studio_from_location_company.id)
        ])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Internal Transfers',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', picking_ids.ids +  picking_ids.return_ids.ids)],
            'context': dict(self.env.context),
        }

    # @api.model
    # def create(self, vals):
    #     if vals.get('reference', 'New') == 'New':
    #         vals['reference'] = self.env['ir.sequence'].next_by_code('transfer.consumption') or 'New'
    #     return super().create(vals)sd

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('transfer.consumption')
        return super(TransferConsumption, self).create(vals)

    # @api.model
    # def default_get(self, fields):
    #     res = super(TransferConsumption, self).default_get(fields)
    #     res['source_location_id'] = self.env.ref(
    #         'stock.stock_location_stock').id
    #     return res

    def action_submit_to_admin(self):
        for rec in self:
            # if not rec.approval_user_id:
            #     raise ValidationError("Please select an Approver User before submitting to Admin.")
            rec.approval_stage = 'admin'
            rec.apply_check = True
            # rec.line_ids.rec.line_ids._compute_available_quantity()

    def action_approve_by_admin(self):
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        _logger.info('action_approve_by_admin')
        _logger.info('action_approve_by_admin')
        _logger.info('action_approve_by_admin')
        _logger.info('action_approve_by_admin')
        _logger.info('action_approve_by_admin')
        _logger.info('action_approve_by_admin')
        _logger.info('action_approve_by_admin')
        _logger.info('action_approve_by_admin')
        for rec in self:
            need_backorder = any(line.demand > line.quantity for line in rec.line_ids)
            _logger.info('need_backorder')
            _logger.info(need_backorder)
            if need_backorder:
                # Return the wizard action
                return {
                    'name': 'Backorder Confirmation',
                    'type': 'ir.actions.act_window',
                    'res_model': 'transfer.backorder.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_transfer_id': rec.id,
                        'default_need_backorder': True,
                    },
                }
            # if not rec.line_ids:
            #     raise ValidationError("No transfer lines found to approve.")
            # if not rec.quantity_check:
            #     raise ValidationError("⚠️ Please click the 'Check Qty' button before approving this request.")

            rec.product_check = True
            _logger.info('rec.product_check')
            _logger.info(rec.product_check)
            # Filter valid lines (quantity > 0 and avb_quantity > 0)
            valid_lines = [line for line in rec.line_ids if line.quantity > 0 and line.avb_quantity > 0]
            _logger.info('valid_lines')
            _logger.info(valid_lines)
            # if not valid_lines:
            #     # No valid lines to transfer, just approve
            #     raise ValidationError("⚠️ Cannot validate consumption as available qty less than 1")
            for x in rec.line_ids:
                if x.avb_quantity <= 0 and not x.quantity == 0 or x.quantity > x.avb_quantity:
                    raise ValidationError(
                        f"⚠️ Cannot validate consumption as available qty less than 1 {x.product_id.name}")

            transfer_map = {}
            for line in valid_lines:
                key = line.dest_location_id.id
                transfer_map.setdefault(key, []).append(line)
            _logger.info('transfer_map')
            _logger.info(transfer_map)
            for dest_loc_id, lines in transfer_map.items():
                picking_type = self.env['stock.picking.type'].search([
                    ('sequence_code', 'ilike', 'CONS'),
                    ('code', '=', 'internal'),
                    ('warehouse_id', '=', rec.warehouse_id.id)
                ], limit=1)
                _logger.info('picking_type')
                _logger.info(picking_type)
                if not picking_type:
                    raise ValidationError("No suitable picking type found for internal transfer.")

                picking = StockPicking.create({
                    'picking_type_id': picking_type.id,
                    'location_id': rec.source_location_id.id,
                    'location_dest_id': dest_loc_id,
                    'origin': rec.name,
                    'accounting_date':rec.accounting_date,
                })
                _logger.info('picking')
                _logger.info(picking)
                _logger.info('lines')
                _logger.info(lines)
                for line in lines:
                    StockMove.create({
                        'name': line.product_id.display_name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.quantity,
                        'product_uom': line.product_id.uom_id.id,
                        'location_id': rec.source_location_id.id,
                        'location_dest_id': line.dest_location_id.id,
                        'picking_id': picking.id,
                        'analytic_distribution': line.analytic_distribution,
                        'remarks': line.remarks,
                    })
                _logger.info('picking.action_confirm()')
                picking.action_confirm()
                _logger.info('picking.action_assign()')
                picking.action_assign()
                _logger.info('picking.with_context(force_period_date=rec.accounting_date).button_validate()')
                picking.with_context(force_period_date=rec.accounting_date).button_validate()
                # AFTER
                # picking.action_confirm()
                # picking.action_assign()
                # for move in picking.move_ids:
                #     move.quantity = move.product_uom_qty
                # picking.with_context(force_period_date=rec.accounting_date).button_validate()
                _logger.info('after validate')
                account_moves = picking.move_ids.mapped('account_move_ids')
                _logger.info('account_moves')
                _logger.info(account_moves)
                account_moves.write({'state': 'posted'})
            _logger.info('dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd')
            rec.approval_stage = 'done'
        _logger.info('completed execution.........................................................................')
    # def action_approve_by_admin(self):
    #     StockPicking = self.env['stock.picking']
    #     StockMove = self.env['stock.move']
    #     _logger.info('action_approve_by_admin')
    #     _logger.info('action_approve_by_admin')
    #     _logger.info('action_approve_by_admin')
    #     _logger.info('action_approve_by_admin')
    #     _logger.info('action_approve_by_admin')
    #     _logger.info('action_approve_by_admin')
    #     _logger.info('action_approve_by_admin')
    #     _logger.info('action_approve_by_admin')
    #     for rec in self:
    #         need_backorder = any(line.demand > line.quantity for line in rec.line_ids)
    #         _logger.info('need_backorder')
    #         _logger.info(need_backorder)
    #         if need_backorder:
    #             return {
    #                 'name': 'Backorder Confirmation',
    #                 'type': 'ir.actions.act_window',
    #                 'res_model': 'transfer.backorder.wizard',
    #                 'view_mode': 'form',
    #                 'target': 'new',
    #                 'context': {
    #                     'default_transfer_id': rec.id,
    #                     'default_need_backorder': True,
    #                 },
    #             }

    #         rec.product_check = True
    #         _logger.info('rec.product_check')
    #         _logger.info(rec.product_check)

    #         # Filter valid lines (quantity > 0 and avb_quantity > 0)
    #         valid_lines = [line for line in rec.line_ids if line.quantity > 0 and line.avb_quantity > 0]
    #         _logger.info('valid_lines')
    #         _logger.info(valid_lines)

    #         # Check for insufficient stock — show backorder wizard instead of error
    #         partial_lines = any(
    #             line.quantity > 0 and (line.avb_quantity <= 0 or line.quantity > line.avb_quantity)
    #             for line in rec.line_ids
    #         )
    #         if partial_lines:
    #             return {
    #                 'name': 'Backorder Confirmation',
    #                 'type': 'ir.actions.act_window',
    #                 'res_model': 'transfer.backorder.wizard',
    #                 'view_mode': 'form',
    #                 'target': 'new',
    #                 'context': {
    #                     'default_transfer_id': rec.id,
    #                     'default_need_backorder': True,
    #                 },
    #             }

    #         transfer_map = {}
    #         for line in valid_lines:
    #             key = line.dest_location_id.id
    #             transfer_map.setdefault(key, []).append(line)
    #         _logger.info('transfer_map')
    #         _logger.info(transfer_map)

    #         for dest_loc_id, lines in transfer_map.items():
    #             picking_type = self.env['stock.picking.type'].search([
    #                 ('sequence_code', 'ilike', 'CONS'),
    #                 ('code', '=', 'internal'),
    #                 ('warehouse_id', '=', rec.warehouse_id.id)
    #             ], limit=1)
    #             _logger.info('picking_type')
    #             _logger.info(picking_type)
    #             if not picking_type:
    #                 raise ValidationError("No suitable picking type found for internal transfer.")

    #             picking = StockPicking.create({
    #                 'picking_type_id': picking_type.id,
    #                 'location_id': rec.source_location_id.id,
    #                 'location_dest_id': dest_loc_id,
    #                 'origin': rec.name,
    #                 'accounting_date': rec.accounting_date,
    #             })
    #             _logger.info('picking')
    #             _logger.info(picking)
    #             _logger.info('lines')
    #             _logger.info(lines)

    #             for line in lines:
    #                 StockMove.create({
    #                     'name': line.product_id.display_name,
    #                     'product_id': line.product_id.id,
    #                     'product_uom_qty': line.quantity,
    #                     'product_uom': line.product_id.uom_id.id,
    #                     'location_id': rec.source_location_id.id,
    #                     'location_dest_id': line.dest_location_id.id,
    #                     'picking_id': picking.id,
    #                     'analytic_distribution': line.analytic_distribution,
    #                     'remarks': line.remarks,
    #                 })

    #             _logger.info('picking.action_confirm()')
    #             picking.action_confirm()
    #             _logger.info('picking.action_assign()')
    #             picking.action_assign()

    #             # Set done qty to what was reserved by action_assign
    #             # If nothing reserved, fall back to product_uom_qty
    #             for move in picking.move_ids:
    #                 if move.quantity <= 0:
    #                     move.quantity = move.product_uom_qty

    #             _logger.info('button_validate')
    #             picking.with_context(
    #                 force_period_date=rec.accounting_date,
    #             ).button_validate()
    #             _logger.info('after validate')

    #             # Find backorder if created
    #             backorder = self.env['stock.picking'].search([
    #                 ('backorder_id', '=', picking.id),
    #                 ('state', 'not in', ('done', 'cancel')),
    #             ], limit=1)
    #             if backorder:
    #                 _logger.info('Backorder created: %s', backorder.name)

    #             account_moves = picking.move_ids.mapped('account_move_ids')
    #             _logger.info('account_moves')
    #             _logger.info(account_moves)
    #             account_moves.write({'state': 'posted'})

    #         _logger.info('dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd')
    #         rec.approval_stage = 'done'
    #     _logger.info('completed execution.........................................................................')
    def action_approve_by_admin_process(self):
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']

        for rec in self:

            rec.product_check = True

            valid_lines = [line for line in rec.line_ids if line.quantity > 0 and line.avb_quantity > 0]

            for x in rec.line_ids:
                if x.avb_quantity <= 0 and not x.quantity == 0 or x.quantity > x.avb_quantity:
                    raise ValidationError(
                        f"⚠️ Cannot validate consumption as available qty less than 1 {x.product_id.name}")

            transfer_map = {}
            for line in valid_lines:
                key = line.dest_location_id.id
                transfer_map.setdefault(key, []).append(line)

            for dest_loc_id, lines in transfer_map.items():
                picking_type = self.env['stock.picking.type'].search([
                    ('sequence_code', 'ilike', 'CONS'),
                    ('code', '=', 'internal'),
                    ('warehouse_id', '=', rec.warehouse_id.id)
                ], limit=1)

                if not picking_type:
                    raise ValidationError("No suitable picking type found for internal transfer.")

                picking = StockPicking.create({
                    'picking_type_id': picking_type.id,
                    'location_id': rec.source_location_id.id,
                    'location_dest_id': dest_loc_id,
                    'origin': rec.name,
                    'accounting_date':rec.accounting_date,
                })

                for line in lines:
                    StockMove.create({
                        'name': line.product_id.display_name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.quantity,
                        'product_uom': line.product_id.uom_id.id,
                        'location_id': rec.source_location_id.id,
                        'location_dest_id': line.dest_location_id.id,
                        'picking_id': picking.id,
                        'analytic_distribution': line.analytic_distribution,
                        'remarks': line.remarks,
                    })

                picking.action_confirm()
                picking.action_assign()
                picking.with_context(force_period_date=rec.accounting_date).button_validate()

                account_moves = picking.move_ids.mapped('account_move_ids')
                account_moves.write({'state': 'posted'})

            rec.approval_stage = 'done'

        return True

    def action_reject(self):
        StockPicking = self.env['stock.picking']

        for rec in self:
            # rec.line_ids._compute_available_quantity()
            # related_pickings = StockPicking.search([('origin', '=', rec.name)])

            # if not related_pickings:
            #     raise ValidationError(f"No internal transfer found for '{rec.name}'.")

            # for picking in related_pickings:
            if rec.approval_stage == 'done':
                raise ValidationError(f"Cannot reject an already completed consumption.")

                # if rec.state != 'cancel':
                #     picking.action_cancel()

                # picking.unlink()

            rec.approval_stage = 'draft'
            rec.apply_check = False
            rec.product_check = False

            # rec.approval_stage = 'draft'
            # rec.apply_check = False
            # rec.product_check = False

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('transfer.consumption') or 'New'
        vals.setdefault('approval_stage', 'draft')
        return super().create(vals)

    def unlink(self):
        for rec in self:
            if rec.approval_stage == 'done':
                raise UserError("You cannot delete a record that is in the 'Done' stage.")
        return super(TransferConsumption, self).unlink()


class TransferConsumptionLine(models.Model):
    _name = 'transfer.consumption.line'
    _description = 'Transfer Line'

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)

    transfer_id = fields.Many2one('transfer.consumption', string='Internal Reference', required=True,
                                  ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom_id = fields.Many2one(related='product_id.uom_id', string="Unit of Measure", store=True, readonly=True)
    # analytic_distribution = fields.Json(inverse="_inverse_analytic_distribution",)
    # analytic_precision = fields.Integer(default=2)

    analytic_distribution = fields.Json(inverse="_inverse_analytic_distribution",related="transfer_id.analytic_distribution")
    analytic_precision = fields.Integer(default=2,related="transfer_id.analytic_precision")
    
    quantity = fields.Float(string='Done Qty', default=0.0)
    avb_quantity = fields.Float(string='Available Qty',compute="_compute_available_quantity")
    demand = fields.Float(string='Demand', required=True)
    dest_location_id = fields.Many2one('stock.location', string='Destination Location', required=True)
    can_edit_quantity = fields.Boolean(string="New", compute='_compute_apply_check')
    remarks = fields.Char(string='Remarks')

    def _inverse_analytic_distribution(self):
        pass

    def unlink(self):
        for rec in self:
            if rec.transfer_id and rec.transfer_id.approval_stage == 'done':
                raise UserError("You cannot delete a line from a transfer that is in the 'Done' stage.")
        return super(TransferConsumptionLine, self).unlink()

    # @api.depends('product_id', 'transfer_id.warehouse_id', 'transfer_id.source_location_id')
    # def _compute_available_quantity(self):
    #     for line in self:
    #         line.avb_quantity = 0.0
    #         if line.product_id and line.transfer_id.source_location_id:
    #             location = line.transfer_id.source_location_id

    #             quants = self.env['stock.quant'].search([
    #                 ('product_id', '=', line.product_id.id),
    #                 ('location_id', '=', location.id)
    #             ], limit=1)

    #             if quants:
    #                 line.avb_quantity = quants.available_quantity

    @api.depends('product_id', 'transfer_id.warehouse_id')
    def _compute_available_quantity(self):
        for line in self:
            line.avb_quantity = 0.0
            if line.product_id and line.transfer_id.warehouse_id:
                warehouse = line.transfer_id.warehouse_id
                location = warehouse.lot_stock_id

                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', location.id)
                ], limit=1)

                if quants:
                    line.avb_quantity = quants.available_quantity

    @api.depends('transfer_id.apply_check')
    def _compute_apply_check(self):
        for rec in self:
            rec.can_edit_quantity = rec.transfer_id.apply_check

    # @api.onchange('quantity')
    # def _onchange_quantity_set_demand(self):
    #     for rec in self:
    #         if rec.quantity:
    #             rec.demand = rec.quantity

    @api.constrains('quantity')
    def _onchange_quantity_set_demand(self):
        for rec in self:
            if rec.quantity > rec.demand:
                raise ValidationError(f"You are not set to done quantity {rec.quantity} of product \n{rec.product_id.display_name} more than the demanded quantity{rec.demand}.")
                rec.demand = rec.quantity

    @api.model
    def create(self, vals):
        transfer = self.env['transfer.consumption'].browse(vals.get('transfer_id'))
        # if transfer and transfer.approval_stage != 'draft':
        #     raise ValidationError("⚠️ You cannot add new lines after this request is submitted or approved.")
        return super().create(vals)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        if self.env.context.get('force_period_date') and 'date' not in vals:
            vals['date'] = self.env.context['force_period_date']
        return super().create(vals)


class TransferBackorderWizard(models.TransientModel):
    _name = 'transfer.backorder.wizard'
    _description = 'Transfer Backorder Wizard'

    transfer_id = fields.Many2one('transfer.consumption', string="Transfer")

    def action_backorder(self):
        """Create a backorder record for remaining quantity"""
        self.ensure_one()
        transfer = self.transfer_id

        # Create new backorder for remaining quantities
        new_transfer = transfer.copy(default={
            'name': self.env['ir.sequence'].next_by_code('transfer.consumption'),
            'approval_stage': 'draft',
            'apply_check': False,
            'product_check': False,
            'reference': f"Backorder of {transfer.name}",
            'backorder': f"Backorder of {transfer.name}",
        })

        # Update lines in both transfers
        for orig_line in transfer.line_ids:
            # Find corresponding line in new transfer
            new_line = new_transfer.line_ids.filtered(
                lambda l: l.product_id == orig_line.product_id and
                          l.dest_location_id == orig_line.dest_location_id
            )

            if new_line:
                remaining = orig_line.demand - orig_line.quantity
                if remaining > 0:
                    # Update original line to only transfer the fulfilled quantity
                    orig_line.demand = orig_line.quantity

                    # Update backorder line with remaining quantity
                    new_line.write({
                        'demand': remaining,
                        'quantity': 0.0,
                        'remarks': f"Backorder from {transfer.name}",
                    })
                else:
                    # No remaining quantity, delete the backorder line
                    new_line.unlink()

        # Approve current transfer (only fulfilled quantities)
        transfer.action_approve_by_admin_process()

        # Return action to view the created backorder
        return {
            'name': 'Backorder',
            'type': 'ir.actions.act_window',
            'res_model': 'transfer.consumption',
            'res_id': new_transfer.id,
            'view_mode': 'form',
            'target': 'current',
        }
        return {'type': 'ir.actions.act_window_close'}

    def action_no_backorder(self):
        """Complete transfer without creating a backorder"""
        self.ensure_one()
        self.transfer_id.action_approve_by_admin_process()
        return {'type': 'ir.actions.act_window_close'}



class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    remarks = fields.Char(string="Remarks")

    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('remarks') and vals.get('move_id'):
                move = self.env['stock.move'].browse(vals['move_id'])
                vals['remarks'] = move.remarks

        return super().create(vals_list)

class StockMove(models.Model):
    _inherit = 'stock.move'

    remarks = fields.Char(string="Remarks")
    avb_quantity = fields.Float(string='Available Qty',compute="_compute_available_quantity")

    @api.depends('product_id', 'picking_id.location_id')
    def _compute_available_quantity(self):
        for line in self:
            line.avb_quantity = 0.0
            if line.product_id and line.picking_id.location_id:
                location = line.picking_id.location_id
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', location.id)
                ], limit=1)
                if quants:
                    line.avb_quantity = quants.available_quantity
