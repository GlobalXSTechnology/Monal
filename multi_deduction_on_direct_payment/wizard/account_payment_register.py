# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class AccountPaymentRegister(models.TransientModel):
    _name = "account.payment.register"
    _inherit = ["account.payment.register", "analytic.mixin"]

    payment_difference_handling = fields.Selection(
        selection_add=[
            ("reconcile_multi_deduct", "Mark invoice as fully paid (multi deduct)")
        ],
        ondelete={"reconcile_multi_deduct": "cascade"},
    )
    deduct_residual = fields.Monetary(
        string="Remainings", compute="_compute_deduct_residual"
    )
    deduction_ids = fields.One2many(
        comodel_name="account.payment.deduction",
        inverse_name="payment_id",
        string="Deductions",
        copy=False,
        help="Sum of deduction amount(s) must equal to the payment difference",
    )
    deduct_analytic_distribution = fields.Json()

    # cheq_no = fields.Char(string='Ref/Chq#',help='This value will shown in Bank Payment Voucher.')
    actual_amount = fields.Monetary(string="Actual Amount",currency_field='currency_id')
    
    @api.onchange('amount')
    def onchange_on_amount(self):
        # if self.amount < 0:
        #     raise UserError(_("Deduction amount must be positive."))
        if self.deduction_ids:
            total_deduction = sum(
                line.amount for line in self.deduction_ids
            )
            if total_deduction > self.amount:
                raise UserError(
                    _("Total deduction amount must be less than or equal to the payment difference.")
                )
        # raise UserError(str([self.env.context]))
        amount = 0
        if self.amount:
            if self.amount > 0:
                amount = self.amount
            
        if self.deduction_ids:
            for line in self.deduction_ids:
                amount += line.amount
                
        self.actual_amount = amount
        
    def _update_vals_deduction(self, moves):
        
        move_lines = moves.mapped("line_ids")
        
        analytic = {}
        [
            analytic.update(item)
            for item in move_lines.mapped("analytic_distribution")
            if item
        ]
        self.analytic_distribution = analytic

    def _update_vals_multi_deduction(self, moves):
        
        move_lines = moves.mapped("line_ids")        
        analytic = {}
        [
            analytic.update(item)
            for item in move_lines.mapped("analytic_distribution")
            if item
        ]
        self.deduct_analytic_distribution = analytic

    @api.onchange("payment_difference", "payment_difference_handling")
    def _onchange_default_deduction(self):
        '''modified (Saif)
        change the logic to get current invoice/ bill record by applying search
        '''
        active_ids = self.env.context.get("active_ids", [])
        # logic changed
        moves = self.env["account.move"].search([('name','=', self.communication)])
        # moves = self.env["account.move"].browse(active_ids)
        if self.payment_difference_handling == "reconcile":
            self._update_vals_deduction(moves)
        if self.payment_difference_handling == "reconcile_multi_deduct":
            self._update_vals_multi_deduction(moves)

    @api.constrains("deduction_ids", "payment_difference_handling")
    def _check_deduction_amount(self):
        prec_digits = self.env.user.company_id.currency_id.decimal_places
        for rec in self:
            if rec.payment_difference_handling == "reconcile_multi_deduct":
                if (
                    float_compare(
                        rec.payment_difference,
                        sum(rec.deduction_ids.mapped("amount")),
                        precision_digits=prec_digits,
                    )
                    != 0
                ):
                    raise UserError(
                        _("The total deduction should be %s") % rec.payment_difference
                    )

    @api.depends("payment_difference", "deduction_ids")
    def _compute_deduct_residual(self):
        for rec in self:
            rec.deduct_residual = rec.payment_difference - sum(
                rec.deduction_ids.mapped("amount")
            )
            
    @api.onchange("deduction_ids")
    def _onchange_deduction_ids(self):
        '''onchnage methid to get tax account label and amount from selected tax'''
        for rec in self:
            # rec.can_edit_wizard = False
            if len(rec.deduction_ids) == 1 and not rec.journal_id:
                raise UserError("Please Select Journal First!")
            else:
                rec.payment_difference = rec.amount
                rec.payment_difference_handling = 'reconcile_multi_deduct'
                if rec.deduction_ids:
                    rec.amount = rec.actual_amount
                    for line in rec.deduction_ids:
                        if line.tax_id:
                            # line.account_id = line.tax_id.invoice_repartition_line_ids[-1].account_id.id
                            ##account from tax
                            for account_line in line.tax_id.invoice_repartition_line_ids:
                                if account_line.account_id:
                                    line.account_id = account_line.account_id.id
                                    break
                            base_amount = rec.amount if line.use_deducted_amount_for_tax else rec.actual_amount
                            line.amount = base_amount * (line.tax_id.amount / 100)
                            # line.amount = rec.actual_amount * (line.tax_id.amount /100) 
                            line.name = line.tax_id.invoice_label
                            rec.amount = rec.amount - line.amount

                        elif line.account_id and line.is_direct_deduct:
                            rec.amount = rec.amount - line.amount
                        else:
                            pass
                        

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        # payment_vals["cheq_no"] = self.cheq_no
        if (
            not self.currency_id.is_zero(self.payment_difference)
            and self.payment_difference_handling == "reconcile"
        ):
            payment_vals["write_off_line_vals"][0][
                "analytic_distribution"
            ] = self.analytic_distribution
        # elif (
        #     self.payment_difference
        #     and self.payment_difference_handling == "reconcile_multi_deduct"
        # ):
        payment_vals["write_off_line_vals"] = [
            self._prepare_deduct_move_line(deduct)
            for deduct in self.deduction_ids.filtered(lambda l: not l.is_open)
        ]
        payment_vals["is_multiple_deduction"] = True if self.deduction_ids else False
        payment_vals["actual_amount"] = self.actual_amount
        payment_vals["deduction_ids"] = [
            (0, 0, {
                'tax_id': d.tax_id.id,
                'account_id': d.account_id.id,
                'amount': d.amount,
                'name': d.name,
                'use_deducted_amount_for_tax': d.use_deducted_amount_for_tax,
                'is_direct_deduct': d.is_direct_deduct,
                # ... add other fields if needed
            })
            for d in self.deduction_ids
        ]
        return payment_vals

    def _prepare_deduct_move_line(self, deduct):
        conversion_rate = self.env["res.currency"]._get_conversion_rate(
            self.currency_id,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )
        write_off_amount_currency = (
            deduct.amount if self.payment_type == "inbound" else -deduct.amount
        )
        write_off_balance = self.company_id.currency_id.round(
            write_off_amount_currency * conversion_rate
        )
        return {
            "name": deduct.name,
            "account_id": deduct.account_id.id,
            "partner_id": self.partner_id.id,
            "currency_id": self.currency_id.id,
            "amount_currency": write_off_amount_currency,
            "balance": write_off_balance,
            "analytic_distribution": deduct.analytic_distribution,
        }
        
        
    '''override default method to set differnce amount as multi deduction (saif)'''
    @api.depends('early_payment_discount_mode')
    def _compute_payment_difference_handling(self):
        for wizard in self:
            if wizard.can_edit_wizard:
                wizard.payment_difference_handling = 'reconcile' if wizard.early_payment_discount_mode else 'reconcile_multi_deduct'
            else:
                wizard.payment_difference_handling = False
    
    @api.model
    def default_get(self, fields_list):
        # OVERRIDE
        res = super().default_get(fields_list)
        res['journal_id'] = None
        if 'line_ids' in res and len(res['line_ids'][0][2]) ==1:
            amount = 0
            account_move_line = self.env['account.move.line'].search([('id','=',res['line_ids'][0][2][0])],limit=1)
            if account_move_line:
                if account_move_line.amount_currency:
                    amount += account_move_line.amount_currency
                else:
                    if account_move_line.credit:
                        amount += account_move_line.credit
                    elif account_move_line.debit:
                        amount += account_move_line.debit
            
            res['actual_amount'] = abs(amount)        
        return res

   