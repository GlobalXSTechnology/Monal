from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class PriceList(models.Model):
    _inherit = "product.pricelist.item"

    pro_ids = fields.Many2many(
        'product.template',
        string='Products',
        compute='_compute_selected_products',
    )

    @api.depends('product_tmpl_id')
    @api.constrains('product_tmpl_id')
    def _compute_selected_products(self):
        for rec in self:
            rec.pro_ids = rec.pricelist_id.item_ids.filtered(lambda a: a.id != rec.id).mapped('product_tmpl_id').ids

    # @api.model
    # def default_get(self, fields_list):
    #     res = super().default_get(fields_list)
    #     pricelist_id = self.env.context.get("default_pricelist_id")
    #     domain = [('pricelist_id', '=', pricelist_id)] if pricelist_id else []
    #     last = self.search(domain, order="id desc")
    #     if last and last.pro_ids:
    #         res['pro_ids'] = [(6, 0, last.pro_ids.ids)]
    #     return res


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # @api.onchange('product_tmpl_id', 'company_id')
    def _check_unique_bom_per_product_company(self):
        for bom in self:
            domain = [
                ('product_tmpl_id', '=', bom.product_tmpl_id.id),
                ('id', '!=', bom.id),  # exclude current
            ]
            if bom.company_id:
                domain = ['|',
                          ('company_id', '=', bom.company_id.id),
                          ('company_id', '=', False),
                          ] + domain
                print(f'domain with company filter: {domain}')

            else:
                domain = domain
                print(f'domain without company filter: {domain}')

            # if bom.company_id:
            #     # Check if another BoM already exists for same product + company
            #     domain.append(('company_id', '=', bom.company_id.id))
            # else:
            #     # Check if another company-independent BoM exists
            #     domain.append(('company_id', '=', False))

            existing = self.search(domain, limit=1)
            # if existing:
            #     raise ValidationError(
            #         "A Bill of Materials already exists for product")
            if existing:
                raise ValidationError(_(
                    "A Bill of Materials already exists for product '%s' "
                    "with the same company.\n\n"
                    "Product: %s\nCompany: %s"
                ) % (
                                          bom.product_tmpl_id.display_name,
                                          bom.product_tmpl_id.display_name,
                                          bom.company_id.display_name if bom.company_id else "No Company"
                                      ))

# class ProductTemplate(models.Model):
#     _inherit = 'product.template'
#
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('done', 'Done'),
#     ], default='draft', track_visibility='always')
#
