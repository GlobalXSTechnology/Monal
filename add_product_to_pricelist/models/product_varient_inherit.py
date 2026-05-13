from odoo import models, api, fields, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta
import calendar
import logging

logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # @api.model
    def action_approve_by_admin(self):
        logger.info('Creating product and adding to all companies\' pricelists (except excluded ones)')

        res = super(ProductTemplate, self).action_approve_by_admin()
        for product in self:
            if product.id:
                # excluded_company_ids = [1]
                excluded_company_ids = [4,28,45]

                pricelists = self.env['product.pricelist'].sudo().search([
                    ('company_id', 'not in', excluded_company_ids)
                ])

                logger.info('Found %d pricelists (excluding companies %s)', len(pricelists), excluded_company_ids)

                for pricelist in pricelists:
                    company_id = pricelist.company_id.id

                    pricelistitem = self.env['product.pricelist.item'].with_company(company_id).sudo()

                    existing = pricelistitem.search([
                        ('pricelist_id', '=', pricelist.id),
                        ('product_tmpl_id', '=', product.name),
                        # ('product_tmpl_id', '=', product.id)
                    ], limit=1)

                    if not existing:
                        pricelistitem.create({
                            'pricelist_id': pricelist.id,
                            'applied_on': '1_product',
                            'compute_price': 'formula',
                            'base': 'standard_price',
                            'product_tmpl_id': product.id,
                            'price_min_margin': 0.00,
                            'price_max_margin': 0.00,
                            'company_id': company_id,
                        })
                        logger.info('Pricelist item created in: %s (Company: %s)', pricelist.name,
                                    pricelist.company_id.name)
                    else:
                        logger.info('Already exists in: %s (Company: %s)', pricelist.name, pricelist.company_id.name)

        return res
