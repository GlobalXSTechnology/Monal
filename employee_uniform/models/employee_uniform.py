import pytz
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date
from datetime import datetime

class EmployeeUniform(models.Model):
    _name = 'employee.uniform'
    _description = 'Employee Uniform Distribution'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference No", readonly=True, default='New')
    distribution_date = fields.Datetime(
        string="Distribution Date",
        default=lambda self: fields.Datetime.now(),
        required=True
    )

    half_price = fields.Boolean(string='Is Used')
    line_ids = fields.One2many('employee.uniform.line', 'uniform_id', string='Employees', copy=True)

    source_location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        required=True,
        domain="[('company_id', '=', company_id)]"
    )
    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=True,
        domain="[('company_id', '=', company_id)]"
    )
    # ('usage', '=', 'internal'),

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company, required=True
    )
    picking_id = fields.Many2one('stock.picking', string="Stock Picking", readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
    ], string="Status", default='draft', tracking=True)
    is_confirmed = fields.Boolean(string='Confirmed', default=False)

    total_payment = fields.Monetary(
        string="Total Payment",
        compute='_compute_total_payment',
        store=True,
        currency_field='company_currency_id'
    )
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        compute='_compute_warehouse_id',
        store=True
    )

    @api.depends('source_location_id', 'company_id')
    def _compute_warehouse_id(self):
        for rec in self:
            if rec.source_location_id:
                warehouse = self.env['stock.warehouse'].search([
                    ('company_id', '=', rec.company_id.id),
                    '|',
                    ('lot_stock_id', '=', rec.source_location_id.id),
                    ('view_location_id', '=', rec.source_location_id.location_id.id),
                ], limit=1)
                rec.warehouse_id = warehouse.id if warehouse else False
            else:
                rec.warehouse_id = False

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('employee.uniform') or 'New'
        return super().create(vals)

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = self.env['ir.sequence'].next_by_code('employee.uniform') or 'New'
        default['picking_id'] = False
        default['state'] = 'draft'
        default['is_confirmed'] = False

        new_record = super(EmployeeUniform, self).copy(default)

        for line in self.line_ids:
            line.copy({'uniform_id': new_record.id})

        return new_record

    def get_karachi_datetime(self):
        tz = pytz.timezone('Asia/Karachi')
        return datetime.now(tz)
    def action_confirm(self):
        print('Hammaddd')
        # Picking = self.env['stock.picking']
        # Move = self.env['stock.move']
        # PickingType = self.env['stock.picking.type']
        #
        # for rec in self:
        #     if not rec.line_ids:
        #         raise ValidationError(_("Please add at least one line before confirming."))
        #
        #     # ✅ STOCK VALIDATION (tumhara existing logic)
        #     for line in rec.line_ids.filtered(lambda l: l.check_filter in ['new', 'used']):
        #         if line.product_id:
        #             quants = self.env['stock.quant'].search([
        #                 ('product_id', '=', line.product_id.id),
        #                 ('location_id', '=', rec.source_location_id.id),
        #             ])
        #             stock_qty = sum(quants.mapped('quantity'))
        #
        #             reserved_qty = 0.0
        #             for l in rec.line_ids:
        #                 if l.id == line.id:
        #                     continue
        #                 if l.product_id and l.product_id.id == line.product_id.id and l.check_filter in ['new', 'used']:
        #                     reserved_qty += l.quantity or 0.0
        #
        #             available_for_this_line = max(0, stock_qty - reserved_qty)
        #
        #             if (line.quantity or 0.0) > available_for_this_line:
        #                 raise ValidationError(
        #                     _("Cannot confirm! Insufficient stock for product %s.\n"
        #                       "Available: %s, Requested: %s")
        #                     % (line.product_id.display_name, available_for_this_line, line.quantity)
        #                 )
        #
        #             if line.check_filter == 'new':
        #                 line._check_replace_validation()
        #
        #     rec.state = 'confirmed'
        #     rec.is_confirmed = True
        #
        #
        #
        #     all_lines = rec.line_ids.filtered(lambda l: l.check_filter in ['new', 'used', 'return'])
        #
        #     if not all_lines:
        #         continue
        #
        #     search_priorities = [
        #         [('sequence_code', 'ilike', 'CONS'), ('code', '=', 'internal'),
        #          ('warehouse_id', '=', rec.warehouse_id.id)],
        #
        #         [('code', '=', 'internal'), ('company_id', '=', rec.company_id.id)],
        #
        #         [('code', '=', 'internal')],
        #     ]
        #
        #     ptype = False
        #     for domain in search_priorities:
        #         ptype = PickingType.search(domain, limit=1)
        #         if ptype:
        #             break
        #
        #     if not ptype:
        #         raise ValidationError(_("No internal picking type found."))
        #
        #     picking_vals = {
        #         'picking_type_id': ptype.id,
        #         'location_id': rec.source_location_id.id,
        #         'location_dest_id': rec.destination_location_id.id,
        #         'origin': rec.name,
        #         'company_id': rec.company_id.id,
        #         'scheduled_date': rec.distribution_date,
        #
        #     }
        #
        #     picking = Picking.create(picking_vals)
        #
        #
        #     for line in all_lines:
        #         if line.check_filter == 'return':
        #             location_id = rec.destination_location_id.id
        #             location_dest_id = rec.source_location_id.id
        #             qty = line.quantity or 0.0
        #             move_name = f"Return: {line.product_id.display_name}"
        #         else:
        #             location_id = rec.source_location_id.id
        #             location_dest_id = rec.destination_location_id.id
        #             qty = line.quantity or 0.0
        #             move_name = f"{'Replace' if line.check_filter == 'new' else 'Issue'}: {line.product_id.display_name}"
        #
        #         Move.create({
        #             'name': move_name,
        #             'product_id': line.product_id.id,
        #             'product_uom_qty': qty,
        #             'product_uom': line.product_id.uom_id.id,
        #             'picking_id': picking.id,
        #             'location_id': location_id,
        #             'location_dest_id': location_dest_id,
        #             'company_id': rec.company_id.id,
        #         })
        #     picking.action_confirm()
        #     picking.action_assign()
        #     picking.write({
        #         'scheduled_date': rec.distribution_date,
        #
        #     })
        #     rec.picking_id = picking

    @api.onchange('quantity', 'product_id', 'check_filter')
    def _onchange_quantity_check_availability(self):
        for rec in self:
            if rec.check_filter in ['new',
                                    'used'] and rec.product_id and rec.uniform_id and rec.uniform_id.source_location_id:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', '=', rec.uniform_id.source_location_id.id),
                ])
                stock_qty = sum(quants.mapped('quantity'))

                reserved_qty = 0.0
                for l in rec.uniform_id.line_ids:
                    if l.id == rec.id:
                        continue
                    if l.product_id and l.product_id.id == rec.product_id.id and l.check_filter in ['new', 'used']:
                        reserved_qty += l.quantity or 0.0

                available_for_this_line = max(0, stock_qty - reserved_qty)

                if rec.quantity > available_for_this_line:
                    warning = {
                        'title': _('Quantity Exceeds Available Stock'),
                        'message': _(
                            "Quantity cannot exceed available stock for product '%s'.\n"
                            "Available: %s\n"
                            "Quantity has been reset to available amount."
                        ) % (rec.product_id.display_name, available_for_this_line)
                    }
                    rec.quantity = available_for_this_line
                    return {'warning': warning}

    @api.onchange('quantity')
    def _onchange_quantity_prevent_excess(self):
        for rec in self:
            if rec.check_filter in ['new',
                                    'used'] and rec.product_id and rec.uniform_id and rec.uniform_id.source_location_id:
                rec._compute_available_qty()

                if rec.quantity > rec.available_qty:
                    return {
                        'warning': {
                            'title': _('Invalid Quantity'),
                            'message': _(
                                "Quantity cannot exceed available stock (%s units)."
                            ) % rec.available_qty
                        },
                        'value': {'quantity': min(rec.quantity, rec.available_qty)}
                    }

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_draft(self):
        for rec in self:
            # ✅ Cancel Picking if exists
            if rec.picking_id and rec.picking_id.state not in ['done', 'cancel']:
                rec.picking_id.action_cancel()

            # ✅ Reset uniform
            rec.state = 'draft'
            rec.is_confirmed = False
            rec.picking_id = False

    def action_update_all_quantities(self):
        """Wizard to update all done quantities at once"""
        self.ensure_one()
        return {
            'name': _('Update All Issued Quantities'),
            'type': 'ir.actions.act_window',
            'res_model': 'update.all.quantities.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_uniform_id': self.id}
        }

    def action_view_internal_transfers(self):
        self.ensure_one()

        if not self.picking_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Internal Transfers'),
                'res_model': 'stock.picking',
                'view_mode': 'list,form',
                'domain': [('id', '=', 0)],
            }

        return {
            'type': 'ir.actions.act_window',
            'name': _('Internal Transfer'),
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.picking_id.id,
            'views': [(False, 'form')],
            'target': 'current',
            'context': {
                'default_picking_type_id': self.picking_id.picking_type_id.id,
                'default_location_id': self.picking_id.location_id.id,
                'default_location_dest_id': self.picking_id.location_dest_id.id,
            }
        }

    @api.depends('line_ids.payment_amount')
    def _compute_total_payment(self):
        for rec in self:
            rec.total_payment = sum(rec.line_ids.mapped('payment_amount') or [])


class EmployeeUniformLine(models.Model):
    _name = 'employee.uniform.line'
    _description = 'Employee Uniform Line'
    _order = 'id'

    uniform_id = fields.Many2one('employee.uniform', string='Uniform Reference', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one(related='uniform_id.company_id', store=True, readonly=True)
    product_id = fields.Many2one('product.product', string='Uniform Product', required=True)
    available_qty = fields.Float(
        string="Available Quantity",
        compute="_compute_available_qty",
        store=False
    )
    check_filter = fields.Selection(
        selection=[
            ('used', 'Issue'),
            ('return', 'Return'),
            ('new', 'Replace'),
        ],
        string="Check Filter",
        default='used',
    )
    quantity = fields.Float(string='Planned Quantity', default=1.0)
    done_quantity = fields.Float(string='Actual Issued Quantity')
    price_unit = fields.Float(
        string='Unit Price',
        compute='_compute_price',
        store=True,
    )
    payment_amount = fields.Monetary(
        string="Payment Amount",
        compute='_compute_payment_amount',
        store=True,
        currency_field='currency_id'
    )
    total_price = fields.Float(string='Total Price', compute='_compute_total_price', store=True)
    sr_no = fields.Integer(string="Sr No", compute="_compute_sr_no", store=False)
    total_issued_to_employee = fields.Float(string="Issued Before", compute="_compute_issued_qty", store=False)
    badge_id = fields.Char(related='employee_id.barcode', string="Badge ID", readonly=True)
    department_id = fields.Many2one(related='employee_id.department_id', string="Department", readonly=True)
    job_id = fields.Many2one(related='employee_id.job_id', string="Designation", readonly=True)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'uniform_ir_attachments_rel',
        'uniform_id',
        'attachment_id',
        string="Attachments"
    )
    contract_id = fields.Many2one('hr.contract', string="Contract", compute='_compute_contract', store=True)
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )
    joining_date = fields.Date(string="Joining Date", compute="_compute_joining_date", store=True)
    basic_salary = fields.Monetary(
        string="Basic Salary",
        compute="_compute_basic_salary",
        readonly=True,
        currency_field='currency_id',
        store=True
    )
    state = fields.Selection(related='uniform_id.state', string="State", store=True, readonly=True)
    cost_price = fields.Float(
        string="Cost Price",
        compute="_compute_cost_price",
        store=True
    )
    charged_price = fields.Float(
        string="Charged Price",
        help="Editable charged amount",
    )

    last_issue_date = fields.Date(
        string="Last Issue Date",
        compute="_compute_last_issue_info",
        store=False
    )
    days_since_last_issue = fields.Integer(
        string="Days Since Last Issue",
        compute="_compute_last_issue_info",
        store=False
    )

    @api.depends('product_id', 'quantity')
    def _compute_cost_price(self):
        for line in self:
            base_cost = line.product_id.standard_price or 0.0
            qty = line.quantity or 1.0
            line.cost_price = base_cost * qty

    @api.onchange('quantity', 'product_id')
    def _onchange_quantity_update_charged_price(self):
        if self.product_id:
            base_cost = self.product_id.standard_price or 0.0
            qty = self.quantity or 1.0
            self.charged_price = base_cost * qty

    @api.onchange('quantity', 'charged_price')
    def _onchange_quantity_amount(self):
        self.payment_amount = (self.quantity or 0.0) * (self.charged_price or 0.0)

    @api.onchange('check_filter', 'employee_id', 'product_id', 'uniform_id.distribution_date')
    def _onchange_check_filter(self):
        """Show warning when selecting Replace if 6 months haven't passed"""
        if self.check_filter == 'new' and self.employee_id and self.product_id:
            last_issue = self._get_last_issue()
            if last_issue:
                last_date = last_issue.uniform_id.distribution_date
                current_date = self.uniform_id.distribution_date or date.today()

                if last_date and current_date:
                    six_months_ago = last_date + relativedelta(months=6)
                    if current_date < six_months_ago:
                        days_left = (six_months_ago - current_date).days
                        warning = {
                            'title': _('Replace Not Allowed'),
                            'message': _(
                                "Cannot replace '%(product)s' for %(employee)s. "
                                "Last issue was on %(last_date)s. "
                                "Replacement is only allowed after 6 months. "
                                "Please wait for %(days_left)s more days or change the check filter."
                            ) % {
                                           'product': self.product_id.display_name,
                                           'employee': self.employee_id.name,
                                           'last_date': last_date.strftime('%Y-%m-%d'),
                                           'days_left': days_left,
                                       }
                        }
                        return {'warning': warning}

    def _get_last_issue(self):
        """Get the last issue of the same product to the same employee"""
        domain = [
            ('employee_id', '=', self.employee_id.id),
            ('product_id', '=', self.product_id.id),
            ('uniform_id.state', 'in', ['confirmed', 'done']),
            ('check_filter', 'in', ['used', 'new']),
            ('id', '!=', self.id),
        ]

        last_issues = self.search(domain)
        last_issues = last_issues.sorted(
            key=lambda l: l.uniform_id.distribution_date or fields.Date.today(),
            reverse=True
        )[:1]
        return last_issues[0] if last_issues else False

    def _check_replace_validation(self):
        """Check if replace is allowed based on 6-month rule"""
        for line in self:
            if line.check_filter == 'new':
                last_issue = line._get_last_issue()
                if last_issue:
                    last_date = last_issue.uniform_id.distribution_date
                    current_date = line.uniform_id.distribution_date or date.today()

                    if last_date and current_date:
                        six_months_ago = last_date + relativedelta(months=6)
                        if current_date < six_months_ago:
                            days_left = (six_months_ago - current_date).days
                            raise ValidationError(_(
                                "Cannot replace uniform item '%(product)s' for employee '%(employee)s'. "
                                "Last issue was on %(last_date)s. "
                                "Replacement is only allowed after 6 months. "
                                "Please wait for %(days_left)s more days."
                            ) % {
                                                      'product': line.product_id.display_name,
                                                      'employee': line.employee_id.name,
                                                      'last_date': last_date.strftime('%Y-%m-%d'),
                                                      'days_left': days_left,
                                                  })

    @api.constrains('check_filter', 'employee_id', 'product_id', 'uniform_id.distribution_date')
    def _check_replace_constraint(self):
        """Constraint to prevent replace within 6 months"""
        for line in self:
            if line.check_filter == 'new' and line.state in ['draft', 'confirmed']:
                line._check_replace_validation()

    @api.depends('employee_id', 'product_id')
    def _compute_last_issue_info(self):
        """Compute information about the last issue"""
        for line in self:
            line.last_issue_date = False
            line.days_since_last_issue = 0

            if line.employee_id and line.product_id:
                last_issue = line._get_last_issue()
                if last_issue:
                    last_date = last_issue.uniform_id.distribution_date
                    line.last_issue_date = last_date

                    if last_date:
                        current_date = line.uniform_id.distribution_date or date.today()
                        delta = (current_date - last_date).days
                        line.days_since_last_issue = delta

    def action_view_issued_wizard(self):
        self.ensure_one()
        return {
            'name': 'Issued Uniforms Details',
            'type': 'ir.actions.act_window',
            'res_model': 'employee.uniform.issued.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'employee_id': self.employee_id.id},
        }

    def action_update_done_quantity(self):
        self.ensure_one()
        return {
            'name': _('Update Issued Quantity'),
            'type': 'ir.actions.act_window',
            'res_model': 'update.done.quantity.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_line_id': self.id,
                'default_current_quantity': self.quantity,
                'default_current_done_quantity': self.done_quantity,
            }
        }

    @api.onchange('quantity')
    def _onchange_quantity(self):
        """When planned quantity changes, set done quantity to the same value by default"""
        if self.quantity and self.uniform_id.state == 'draft':
            self.done_quantity = self.quantity

    @api.depends('product_id', 'uniform_id.source_location_id', 'uniform_id.line_ids.quantity',
                 'uniform_id.line_ids.check_filter')
    def _compute_available_qty(self):
        """Compute available quantity for display only"""
        for rec in self:
            if rec.product_id and rec.uniform_id and rec.uniform_id.source_location_id:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', '=', rec.uniform_id.source_location_id.id),
                ])
                stock_qty = sum(quants.mapped('quantity'))

                reserved_qty = 0.0
                for l in rec.uniform_id.line_ids:
                    if l.id == rec.id:
                        continue
                    if l.product_id and l.product_id.id == rec.product_id.id and l.check_filter in ['new', 'used']:
                        reserved_qty += l.quantity or 0.0

                available_for_display = max(0, stock_qty - reserved_qty)
                rec.available_qty = available_for_display

            else:
                rec.available_qty = 0.0

    @api.constrains('quantity', 'check_filter')
    def _check_quantity_availability(self):
        for rec in self:
            if rec.check_filter in ['new',
                                    'used'] and rec.product_id and rec.uniform_id and rec.uniform_id.source_location_id:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', '=', rec.uniform_id.source_location_id.id),
                ])
                stock_qty = sum(quants.mapped('quantity'))

                reserved_qty = 0.0
                for l in rec.uniform_id.line_ids:
                    if l.id == rec.id:
                        continue
                    if l.product_id and l.product_id.id == rec.product_id.id and l.check_filter in ['new', 'used']:
                        reserved_qty += l.quantity or 0.0

                available_for_this_line = max(0, stock_qty - reserved_qty)

                if rec.quantity > available_for_this_line:
                    raise ValidationError(_(
                        "Cannot save! Insufficient stock for product '%s'.\n"
                        "Available for this line: %s\n"
                        "Requested quantity: %s"
                    ) % (rec.product_id.display_name, available_for_this_line, rec.quantity))

    @api.depends('employee_id')
    def _compute_contract(self):
        for line in self:
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', line.employee_id.id),
                ('state', '=', 'open')
            ], limit=1)
            line.contract_id = contract.id if contract else False

    @api.depends('contract_id')
    def _compute_basic_salary(self):
        for line in self:
            line.basic_salary = line.contract_id.wage if line.contract_id else 0.0

    @api.depends('contract_id')
    def _compute_joining_date(self):
        for line in self:
            line.joining_date = line.contract_id.date_start if line.contract_id else False

    @api.onchange('employee_id', 'quantity', 'product_id', 'check_filter', 'uniform_id.distribution_date')
    def _onchange_employee_or_qty(self):
        self._compute_price()
        self._compute_payment_amount()
        self._compute_available_qty()
        self._compute_last_issue_info()

    @api.depends('product_id', 'check_filter', 'quantity', 'employee_id', 'uniform_id.distribution_date',
                 'uniform_id.line_ids')
    def _compute_price(self):
        for line in self:
            price = 0.0
            if line.product_id:
                base_price = line.product_id.lst_price or 0.0

                if line.check_filter == 'return':
                    price = 0.0
                else:
                    last_issue = self.env['employee.uniform.line'].search([
                        ('employee_id', '=', line.employee_id.id),
                        ('product_id', '=', line.product_id.id),
                        ('uniform_id.state', 'in', ['confirmed', 'done']),
                        ('id', '!=', line.id),
                    ])
                    last_issue = last_issue.sorted(
                        key=lambda l: l.uniform_id.distribution_date or fields.Date.today(),
                        reverse=True
                    )[:1]

                    if not last_issue:
                        price = base_price
                    else:
                        last_date = last_issue[0].uniform_id.distribution_date
                        cur_date = line.uniform_id.distribution_date
                        if last_date and cur_date:
                            if cur_date <= last_date + relativedelta(months=6):
                                price = base_price
                            else:
                                price = 0.0
                        else:
                            price = base_price

            line.price_unit = price

    @api.depends('quantity', 'price_unit')
    def _compute_payment_amount(self):
        for line in self:
            line.payment_amount = (line.quantity or 0.0) * (line.price_unit or 0.0)

    @api.depends('quantity', 'price_unit')
    def _compute_total_price(self):
        for line in self:
            line.total_price = (line.quantity or 0.0) * (line.price_unit or 0.0)

    @api.depends('uniform_id.line_ids')
    def _compute_sr_no(self):
        for rec in self:
            if rec.uniform_id:
                for idx, line in enumerate(rec.uniform_id.line_ids.sorted('id'), start=1):
                    line.sr_no = idx

    def _compute_issued_qty(self):
        for rec in self:
            if rec.employee_id:
                issued = rec.employee_id.uniform_line_ids.filtered(lambda l: l.id != rec.id)
                rec.total_issued_to_employee = sum(issued.mapped('done_quantity')) if issued else 0.0
            else:
                rec.total_issued_to_employee = 0.0

    @api.constrains('employee_id', 'uniform_id')
    def _check_company_consistency(self):
        for line in self:
            if line.uniform_id and line.employee_id and line.uniform_id.company_id != line.employee_id.company_id:
                raise ValidationError(
                    _("The employee's company must be the same as the uniform's company.")
                )


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    uniform_line_ids = fields.One2many('employee.uniform.line', 'employee_id', string="Uniform Lines")

    total_uniforms_issued = fields.Integer(
        string="Total Uniforms Issued", compute="_compute_total_uniforms_issued", store=True
    )

    def action_view_uniforms(self):
        self.ensure_one()
        return {
            'name': 'Uniforms Issued',
            'type': 'ir.actions.act_window',
            'res_model': 'employee.uniform',
            'view_mode': 'list,form',
            'domain': [('line_ids.employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
            'views': [(False, 'list'), (False, 'form')],
        }

    @api.depends('uniform_line_ids.done_quantity')
    def _compute_total_uniforms_issued(self):
        for employee in self:
            lines = self.env['employee.uniform.line'].search([('employee_id', '=', employee.id)])
            employee.total_uniforms_issued = sum(line.done_quantity for line in lines) if lines else 0


class UpdateDoneQuantityWizard(models.TransientModel):
    _name = 'update.done.quantity.wizard'
    _description = 'Update Done Quantity Wizard'

    line_id = fields.Many2one('employee.uniform.line', string="Uniform Line", required=True)
    current_quantity = fields.Float(string="Planned Quantity")
    current_done_quantity = fields.Float(string="Current Issued Quantity")
    new_done_quantity = fields.Float(string="New Issued Quantity")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self._context.get('default_line_id'):
            line = self.env['employee.uniform.line'].browse(self._context['default_line_id'])
            res['current_quantity'] = line.quantity
            res['current_done_quantity'] = line.done_quantity
            res['new_done_quantity'] = line.done_quantity or line.quantity
        return res

    def action_update(self):
        self.ensure_one()
        if self.line_id:
            self.line_id.done_quantity = self.new_done_quantity
        return {'type': 'ir.actions.act_window_close'}


class UpdateAllQuantitiesWizard(models.TransientModel):
    _name = 'update.all.quantities.wizard'
    _description = 'Update All Quantities Wizard'

    uniform_id = fields.Many2one('employee.uniform', string="Uniform Distribution", required=True)
    line_ids = fields.One2many('update.all.quantities.line', 'wizard_id', string="Lines")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self._context.get('default_uniform_id'):
            uniform = self.env['employee.uniform'].browse(self._context['default_uniform_id'])
            line_vals = []
            for line in uniform.line_ids:
                line_vals.append((0, 0, {
                    'line_id': line.id,
                    'employee_id': line.employee_id.id,
                    'product_id': line.product_id.id,
                    'planned_quantity': line.quantity,
                    'current_done_quantity': line.done_quantity,
                    'new_done_quantity': line.done_quantity or line.quantity,
                }))
            res['line_ids'] = line_vals
        return res

    def action_update_all(self):
        self.ensure_one()
        for wizard_line in self.line_ids:
            if wizard_line.line_id:
                wizard_line.line_id.done_quantity = wizard_line.new_done_quantity
        return {'type': 'ir.actions.act_window_close'}


class UpdateAllQuantitiesLine(models.TransientModel):
    _name = 'update.all.quantities.line'
    _description = 'Update All Quantities Line'

    wizard_id = fields.Many2one('update.all.quantities.wizard', string="Wizard")
    line_id = fields.Many2one('employee.uniform.line', string="Original Line")
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    planned_quantity = fields.Float(string="Planned Quantity")
    current_done_quantity = fields.Float(string="Current Issued")
    new_done_quantity = fields.Float(string="New Issued Quantity", required=True)


class EmployeeUniformIssuedWizard(models.TransientModel):
    _name = 'employee.uniform.issued.wizard'
    _description = 'Employee Uniform Issued Wizard'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    line_ids = fields.One2many('employee.uniform.issued.line', 'wizard_id', string="Issued Uniforms")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self._context.get('employee_id'):
            employee = self.env['hr.employee'].browse(self._context['employee_id'])
            res['employee_id'] = employee.id

            issued_lines = self.env['employee.uniform.line'].search([('employee_id', '=', employee.id),
                                                                     ('uniform_id.state', 'in', ['confirmed', 'done']),
                                                                     ('check_filter', 'in', ['used', 'new']), ],
                                                                    order='uniform_id.distribution_date desc')

            line_vals = []
            for line in issued_lines:
                line_vals.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.done_quantity or line.quantity,
                    'issue_date': line.uniform_id.distribution_date,
                    'check_filter': line.check_filter,
                    'uniform_ref': line.uniform_id.name,
                }))
            res['line_ids'] = line_vals
        return res


class EmployeeUniformIssuedLine(models.TransientModel):
    _name = 'employee.uniform.issued.line'
    _description = 'Employee Uniform Issued Line'

    wizard_id = fields.Many2one('employee.uniform.issued.wizard', string="Wizard")
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    quantity = fields.Float(string="Quantity", readonly=True)
    issue_date = fields.Date(string="Issue Date", readonly=True)
    check_filter = fields.Selection([
        ('used', 'Issue'),
        ('new', 'Replace'),
    ], string="Type", readonly=True)
    uniform_ref = fields.Char(string="Uniform Reference", readonly=True)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()

        for picking in self:
            if picking.origin:
                uniform = self.env['employee.uniform'].search([
                    ('name', '=', picking.origin),
                    ('picking_id', '=', picking.id)
                ], limit=1)

                if uniform:
                    uniform.state = 'done'

        return res
