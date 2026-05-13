from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPaymentDeduction(models.TransientModel):
    _name = "account.direct.payment.deduction"
    _description = "Direct Payment Deduction"

    payment_id = fields.Many2one(
        comodel_name="account.payment",
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="payment_id.currency_id",
        readonly=True,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        domain=[("deprecated", "=", False)],
        required=False,
    )
    tax_id = fields.Many2one(
        comodel_name = 'account.tax',
        string="Taxes",
    )
    amount = fields.Monetary(string="Deduction Amount", required=True)
    name = fields.Char(string="Label") 
    company_id = fields.Many2one('res.company',related="payment_id.company_id",string="Company")

    is_direct_deduct = fields.Boolean(string="Direct Deduct",copy=False)
    
    use_deducted_amount_for_tax = fields.Boolean(
        string="Use Deducted Amount for Tax",
        help="If enabled, tax will be calculated on the deducted amount instead of actual amount."
    )

    @api.onchange('amount')
    def _onchange_amount_protection(self):
        for line in self:
            if not line.is_direct_deduct and line.tax_id:
                raise UserError(_("You cannot manually edit amount when Tax is selected. Uncheck 'Direct Deduct' to enable manual input."))

   