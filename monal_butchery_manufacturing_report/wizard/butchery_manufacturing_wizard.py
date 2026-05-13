from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class ButcheryManufacturingReport(models.TransientModel):
    _name = 'butchery.manufacturing.report'
    _description = 'Butchery Manufacturing Report'

    date_from = fields.Datetime("Date From", required=False)
    date_to = fields.Datetime("Date To ", required=False)

    product_id = fields.Many2one('product.product', string="Product")
    categ_id = fields.Many2one('product.category', string="Category")

    def action_print_manufacturing_report(self):
        _logger.info('Button clickkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
        _logger.info('Button clickkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
        # domain = [
        #     ('create_date', '>=', self.date_from),
        #     ('create_date', '<=', self.date_to),
        # ]
        domain = []
        if self.date_from:
            domain.append(('date_finished', '>=', self.date_from))
        if self.date_to:
            domain.append(('date_finished', '<=', self.date_to))
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        if self.categ_id:
            domain.append(('product_id.categ_id', '=', self.categ_id.id))

        company = self.env.company
        unbuild_records = self.env['mrp.production'].search(domain)
        line_data = []
        for unbuild in unbuild_records:
            main_valuation = self.env['stock.valuation.layer'].search([
                ('product_id', '=', unbuild.product_id.id),
                ('reference', '=', unbuild.name)
            ], order="create_date desc", limit=1)

            main_unit_price = main_valuation.unit_cost if main_valuation else unbuild.product_id.standard_price
            lines = []
            for line in unbuild.move_raw_ids:
                valuation = self.env['stock.valuation.layer'].search([
                    ('product_id', '=', line.product_id.id),
                    ('reference', '=', unbuild.name)
                ], order="create_date desc", limit=1)

                unit_price = valuation.unit_cost if valuation else line.product_id.standard_price
                lines.append({
                    'product_name': line.product_id.display_name,
                    'product_qty': line.quantity,
                    'uom': line.product_uom.name if line.product_uom else '',
                    # 'weight': line.weight,
                    'price': unit_price,
                    'total_price': unit_price * line.quantity,
                    # 'locator': line.location_id.display_name if hasattr(line, 'location_id') else '',
                })
            line_data.append({
                'unbuild_id': unbuild.id,
                'unbuild_name': unbuild.name,
                'item_code': unbuild.product_id.default_code,
                'product_name': unbuild.product_id.display_name,
                'qty': unbuild.product_qty,
                # 'yield': unbuild.weight_percentage,
                'warehouse': unbuild.warehouse_id.name,
                'gross_wt': unbuild.product_qty,  # adjust if you have actual gross/net fields
                'net_wt': unbuild.product_qty,
                'doc_date': unbuild.date_finished.strftime('%d-%m-%Y'),
                'ref': unbuild.name,
                'main_price': main_unit_price,
                'main_total_price': main_unit_price * unbuild.product_qty,
                'lines': lines,
                'company_name': company.name,
                'company_logo': company.logo,
            })
            _logger.info(unbuild_records)
            _logger.info(unbuild)
            # _logger.info(lines)
            _logger.info(line_data)
        return self.env.ref('monal_butchery_manufacturing_report.action_report_butchery_manufacturing').report_action(
            unbuild_records, data={'records': line_data,
                                   'company_name': company.name,
                                   'company_logo': company.logo,
                                   'date_from': self.date_from.strftime('%d-%m-%Y') if self.date_from else '',
                                   'date_to': self.date_to.strftime('%d-%m-%Y') if self.date_to else '',
                                   })


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft', track_visibility='always')
