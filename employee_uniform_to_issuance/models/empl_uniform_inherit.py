import pytz
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date
from datetime import datetime


class EmployeeUniform(models.Model):
    _inherit = 'employee.uniform'

    transfer_id = fields.Many2one('transfer.consumption', string="Transfer")
    accounting_date = fields.Date(string="Accounting Date", tracking=True, store=True)
    transfer_count = fields.Integer(
        string="Transfers",
        compute="_compute_transfer_count"
    )

    def _compute_transfer_count(self):
        for rec in self:
            rec.transfer_count = 1 if rec.transfer_id else 0

    def action_view_transfer(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfer',
            'view_mode': 'form',
            'res_model': 'transfer.consumption',
            'res_id': self.transfer_id.id,
            'target': 'current',
        }

    def _create_transfer_consumption(self):
        Transfer = self.env['transfer.consumption']
        TransferLine = self.env['transfer.consumption.line']
        last_transfer = False
        for rec in self:
            if not rec.line_ids:
                continue
            transfer = rec.transfer_id or Transfer.search([
                ('uniform_id', '=', rec.id)
            ], limit=1)
            analytic_json = {}
            first_line = rec.line_ids.filtered(lambda l: l.employee_id.contract_id.analytic_account_id)[:1]

            if first_line:
                analytic_json = {
                    str(first_line.employee_id.contract_id.analytic_account_id.id): 100
                }
            if transfer:

                transfer.with_context(from_uniform=True).write({
                    'reference': rec.name,
                    'approval_stage': 'admin',
                    'warehouse_id': rec.warehouse_id.id,
                    'company_id': rec.company_id.id,
                    'source_location_id': rec.source_location_id.id,
                    'transfer_date': rec.distribution_date,
                    'accounting_date': rec.accounting_date,
                    'analytic_distribution': analytic_json,
                })

                # ❗ Remove old lines
                transfer.line_ids.with_context(from_uniform=True).unlink()

            else:
                # =====================================================
                # ✅ CREATE NEW TRANSFER (first time only)
                # =====================================================
                transfer = Transfer.create({
                    'reference': rec.name,
                    'approval_stage': 'admin',
                    'uniform_id': rec.id,
                    'is_from_uniform': True,
                    'warehouse_id': rec.warehouse_id.id,
                    'company_id': rec.company_id.id,
                    'source_location_id': rec.source_location_id.id,
                    'transfer_date': rec.distribution_date,
                    'accounting_date': fields.Date.today(),
                    'analytic_distribution': analytic_json,
                })

            rec.transfer_id = transfer.id

            # =========================================================
            # ✅ RE-CREATE LINES
            # =========================================================
            grouped_lines = {}

            for line in rec.line_ids.filtered(lambda l: l.product_id and l.quantity > 0):
                key = (
                    line.product_id.id,
                    rec.destination_location_id.id
                )

                if key not in grouped_lines:
                    grouped_lines[key] = {
                        'product_id': line.product_id.id,
                        'demand': 0.0,
                        'dest_location_id': rec.destination_location_id.id,
                    }

                grouped_lines[key]['demand'] += line.quantity

            for vals in grouped_lines.values():
                TransferLine.create({
                    'transfer_id': transfer.id,
                    'product_id': vals['product_id'],
                    'demand': vals['demand'],
                    'dest_location_id': vals['dest_location_id'],
                })
            last_transfer = transfer

        return last_transfer


    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(_("Please add at least one line before confirming."))


            for line in rec.line_ids.filtered(lambda l: l.check_filter in ['new', 'used']):
                if line.product_id:
                    quants = self.env['stock.quant'].search([
                        ('product_id', '=', line.product_id.id),
                        ('location_id', '=', rec.source_location_id.id),
                    ])
                    stock_qty = sum(quants.mapped('quantity'))

                    reserved_qty = 0.0
                    for l in rec.line_ids:
                        if l.id == line.id:
                            continue
                        if l.product_id and l.product_id.id == line.product_id.id and l.check_filter in ['new',
                                                                                                         'used']:
                            reserved_qty += l.quantity or 0.0

                    available_for_this_line = max(0, stock_qty - reserved_qty)

                    if (line.quantity or 0.0) > available_for_this_line:
                        raise ValidationError(_(
                            "Cannot confirm! Insufficient stock for product %s.\n"
                            "Available: %s, Requested: %s"
                        ) % (
                                                  line.product_id.display_name,
                                                  available_for_this_line,
                                                  line.quantity
                                              ))

                    # Replace validation
                    if line.check_filter == 'new':
                        line._check_replace_validation()

            transfer = rec.transfer_id
            if not transfer:
                transfer = self.env['transfer.consumption'].search([
                    ('uniform_id', '=', rec.id)
                ], limit=1)

                if transfer:
                    rec.transfer_id = transfer.id
            # ✅ Create transfer
            transfer = rec._create_transfer_consumption()

            # ✅ Link back
            rec.transfer_id = transfer.id

            rec.state = 'confirmed'
            rec.is_confirmed = True


class EmployeeUniformLine(models.Model):
    _inherit = 'employee.uniform.line'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        compute='_compute_analytic_account',
        store=True,
        readonly=True
    )

    @api.depends('employee_id')
    def _compute_analytic_account(self):
        for line in self:
            line.analytic_account_id = line.employee_id.contract_id.analytic_account_id.id if line.employee_id else False

    @api.onchange('employee_id')
    def _check_same_analytic_account(self):
        for line in self:
            if not line.uniform_id or not line.employee_id:
                continue

            analytics = line.uniform_id.line_ids.mapped('analytic_account_id')
            analytics = analytics.filtered(lambda a: a)

            if analytics and any(a != line.employee_id.contract_id.analytic_account_id for a in analytics):
                warning = {
                    'title': "Invalid Analytic Account",
                    'message': "All employees must have the same Analytic Account."
                }

                # line.employee_id = False  # ? reset instead of error
                line.uniform_id.line_ids -= line

                return {'warning': warning}


class TransferConsumption(models.Model):
    _inherit = 'transfer.consumption'

    uniform_id = fields.Many2one('employee.uniform', string="Uniform")
    is_from_uniform = fields.Boolean(default=False)

    def action_approve_by_admin(self):
        res = super().action_approve_by_admin()
        StockPicking = self.env['stock.picking']
        for rec in self:
            if rec.uniform_id:
                rec.uniform_id.state = 'done'
            pickings = StockPicking.search([
                ('origin', '=', rec.name)
            ])

            # ✅ Update reference/description
            pickings.write({
                'reference': rec.reference
            })

        return res

    def write(self, vals):
        for rec in self:

            # allow only system (uniform) updates
            if rec.uniform_id and rec.approval_stage == 'draft':
                    if rec.is_from_uniform and not self.env.context.get('from_uniform'):
                        raise ValidationError(
                            "This transfer is managed by Uniform.\n"
                            "You cannot modify it manually."
                        )

        return super().write(vals)

    def action_reject(self):
        # ✅ allow internal write
        res = super(TransferConsumption, self.with_context(from_uniform=True)).action_reject()

        for rec in self:
            if rec.uniform_id:
                rec.uniform_id.write({
                    'state': 'draft',
                    'is_confirmed': False,
                    'picking_id': False,
                })

        return res


class TransferConsumptionLine(models.Model):
    _inherit = 'transfer.consumption.line'

    # 👇 ADD HERE
    # def write(self, vals):
    #     for rec in self:
    #         if rec.transfer_id.is_from_uniform and not self.env.context.get('from_uniform'):
    #             raise ValidationError(
    #                 "You cannot edit lines. This transfer is controlled by Uniform."
    #             )
    #     return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.transfer_id.is_from_uniform and not self.env.context.get('from_uniform'):
                raise ValidationError(
                    "You cannot delete lines. This transfer is controlled by Uniform."
                )
        return super().unlink()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    reference = fields.Char(string="Transfer Description")
