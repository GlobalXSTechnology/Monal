from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from datetime import datetime, date, timedelta, time
import pytz
from odoo.exceptions import ValidationError, UserError


logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    sale_order_invoice = fields.Boolean(
        string="Created from Sale Order",
        copy=False,
        default=False,
        store=True,
        compute='sale_order_invoice_compute'
    )

    @api.depends('move_id.invoice_origin', 'move_id.partner_id', 'move_id.ref')
    def sale_order_invoice_compute(self):
        for rec in self:
            if rec.move_id.invoice_origin:
                # if not self.env.user.has_group("po_bill_sale_invoice_readonly.group_edit_sale_order_invoices"):
                #     rec.sale_order_invoice = True
                # else:
                rec.sale_order_invoice = True
            else:
                rec.sale_order_invoice = False

    @api.onchange('product_id','account_id')
    def _onchange_product_id(self):
        for rec in self:
            if (rec.product_id or rec.account_id) and rec.move_id.invoice_origin:
                raise ValidationError(_("You cannot add a product"))
                rec.id.unlink()