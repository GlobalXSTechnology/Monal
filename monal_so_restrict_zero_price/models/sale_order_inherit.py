from odoo import models, api, fields, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta
import calendar
import logging

logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.constrains('order_line')
    def _check_zero_qty(self):
        for order in self:
            for line in order.order_line:
                if line.price_unit <= 0:
                    raise ValidationError(
                        _("You cannot set Unit Price = 0 for product '%s'. "
                          "Please correct the Price before confirming the Sale Order.")
                        % (line.product_id.name)
                    )
