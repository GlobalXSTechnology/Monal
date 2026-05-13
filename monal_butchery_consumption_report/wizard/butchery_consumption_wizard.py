from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging
from dateutil.relativedelta import relativedelta
from pytz import timezone
from collections import defaultdict

_logger = logging.getLogger(__name__)


class ButcheryConsumptionReport(models.TransientModel):
    _name = 'butchery.consumption.report'
    _description = 'Butchery Consumption Report'

    date_from = fields.Datetime("Date From", required=False)
    date_to = fields.Datetime("Date To ", required=False)

    product_id = fields.Many2one('product.product', string="Product", domain=[('is_butcher_product', '=', True)])
    categ_id = fields.Many2one('product.category', string="Category")

    def action_print_consumption_report(self):
        _logger.info('Button clickkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
        _logger.info('Button clickkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
        tz = self.env.user.tz or 'Asia/Karachi'
        user_tz = timezone(tz)
        # domain = [
        #     ('create_date', '>=', self.date_from),
        #     ('create_date', '<=', self.date_to),
        # ]
        domain = []
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        if self.categ_id:
            domain.append(('product_id.categ_id', '=', self.categ_id.id))

        company = self.env.company
        unbuild_records = self.env['mrp.unbuild'].search(domain)
        line_data = []
        for unbuild in unbuild_records:
            main_valuation = self.env['stock.valuation.layer'].search([
                ('product_id', '=', unbuild.product_id.id),
                ('reference', '=', unbuild.name)
            ], order="create_date desc", limit=1)

            main_unit_price = main_valuation.unit_cost if main_valuation else unbuild.product_id.standard_price
            lines = []
            for line in unbuild.line_ids:
                valuation = self.env['stock.valuation.layer'].search([
                    ('product_id', '=', line.product_id.id),
                    ('reference', '=', unbuild.name)
                ], order="create_date desc", limit=1)

                unit_price = valuation.unit_cost if valuation else line.product_id.standard_price
                lines.append({
                    'product_name': line.product_id.display_name,
                    'product_qty': line.product_qty,
                    'uom': line.product_uom.name if line.product_uom else '',
                    'weight': line.weight,
                    'price': unit_price,
                    'total_price': unit_price * line.product_qty,
                    # 'locator': line.location_id.display_name if hasattr(line, 'location_id') else '',
                })
            local_doc_date = fields.Datetime.context_timestamp(unbuild, unbuild.create_date)
            line_data.append({
                'unbuild_id': unbuild.id,
                'unbuild_name': unbuild.name,
                'item_code': unbuild.product_id.default_code,
                'product_name': unbuild.product_id.display_name,
                'qty': unbuild.product_qty,
                'yield': unbuild.weight_percentage,
                'warehouse': unbuild.warehouse_id.name,
                'gross_wt': unbuild.product_qty,  # adjust if you have actual gross/net fields
                'net_wt': unbuild.product_qty,
                'doc_date': unbuild.create_date.strftime('%d-%m-%Y'),
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
            # _logger.info(line_data)
        return self.env.ref('monal_butchery_consumption_report.action_report_butchery_consumption').report_action(
            unbuild_records, data={'records': line_data,
                                   'company_name': company.name,
                                   'company_logo': company.logo,
                                   'date_from': fields.Datetime.context_timestamp(self, self.date_from).strftime(
                                       '%d-%m-%Y %H:%M:%S') if self.date_from else '',
                                   'date_to': fields.Datetime.context_timestamp(self, self.date_to).strftime(
                                       '%d-%m-%Y %H:%M:%S') if self.date_to else '',

                                   # 'date_from': self.date_from.strftime('%d-%m-%Y %H:%M:%S') if self.date_from else '',
                                   # 'date_to': self.date_to.strftime('%d-%m-%Y %H:%M:%S') if self.date_to else '',
                                   })


    def action_print_consumption_report_xlsx(self):
        print('Button clickkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
        print('Button clickkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
        tz = self.env.user.tz or 'Asia/Karachi'
        user_tz = timezone(tz)
        # domain = [
        #     ('create_date', '>=', self.date_from),
        #     ('create_date', '<=', self.date_to),
        # ]
        domain = []
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        if self.categ_id:
            domain.append(('product_id.categ_id', '=', self.categ_id.id))

        company = self.env.company
        unbuild_records = self.env['mrp.unbuild'].search(domain)
        line_data = []
        for unbuild in unbuild_records:
            main_valuation = self.env['stock.valuation.layer'].search([
                ('product_id', '=', unbuild.product_id.id),
                ('reference', '=', unbuild.name)
            ], order="create_date desc", limit=1)

            main_unit_price = main_valuation.unit_cost if main_valuation else unbuild.product_id.standard_price
            lines = []
            for line in unbuild.line_ids:
                valuation = self.env['stock.valuation.layer'].search([
                    ('product_id', '=', line.product_id.id),
                    ('reference', '=', unbuild.name)
                ], order="create_date desc", limit=1)

                unit_price = valuation.unit_cost if valuation else line.product_id.standard_price
                lines.append({
                    'product_name': line.product_id.display_name,
                    'product_qty': line.product_qty,
                    'uom': line.product_uom.name if line.product_uom else '',
                    'weight': line.weight,
                    'price': unit_price,
                    'total_price': unit_price * line.product_qty,
                    # 'locator': line.location_id.display_name if hasattr(line, 'location_id') else '',
                })
            local_doc_date = fields.Datetime.context_timestamp(unbuild, unbuild.create_date)
            line_data.append({
                'unbuild_id': unbuild.id,
                'unbuild_name': unbuild.name,
                'item_code': unbuild.product_id.default_code,
                'product_name': unbuild.product_id.display_name,
                'qty': unbuild.product_qty,
                'yield': unbuild.weight_percentage,
                'warehouse': unbuild.warehouse_id.name,
                'gross_wt': unbuild.product_qty,  # adjust if you have actual gross/net fields
                'net_wt': unbuild.product_qty,
                'doc_date': unbuild.create_date.strftime('%d-%m-%Y'),
                'ref': unbuild.name,
                'main_price': main_unit_price,
                'main_total_price': main_unit_price * unbuild.product_qty,
                'lines': lines,
                'company_name': company.name,
                'company_logo': company.logo,
            })
            print(unbuild_records)
            print(unbuild)
            # _logger.info(lines)
            # _logger.info(line_data)
        return self.env.ref('monal_butchery_consumption_report.action_report_butchery_consumption_xlsx').report_action(
            unbuild_records, data={'records': line_data,
                                   'company_name': company.name,
                                   'company_logo': company.logo,
                                   'date_from': fields.Datetime.context_timestamp(self, self.date_from).strftime(
                                       '%d-%m-%Y %H:%M:%S') if self.date_from else '',
                                   'date_to': fields.Datetime.context_timestamp(self, self.date_to).strftime(
                                       '%d-%m-%Y %H:%M:%S') if self.date_to else '',

                                   # 'date_from': self.date_from.strftime('%d-%m-%Y %H:%M:%S') if self.date_from else '',
                                   # 'date_to': self.date_to.strftime('%d-%m-%Y %H:%M:%S') if self.date_to else '',
                                   })

    def action_print_consumption_summary_report(self):
        _logger.info('Butchery Consumption Summary report started.')

        tz = self.env.user.tz or 'Asia/Karachi'
        user_tz = timezone(tz)

        domain = []
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        if self.categ_id:
            domain.append(('product_id.categ_id', '=', self.categ_id.id))

        company = self.env.company
        unbuild_records = self.env['mrp.unbuild'].search(domain)

        # === MAIN & COMPONENT SUMMARY ===
        summary_data = {}

        for unbuild in unbuild_records:
            main_prod = unbuild.product_id
            main_key = main_prod.id

            # Get valuation for main product
            main_valuation = self.env['stock.valuation.layer'].search([
                ('product_id', '=', main_prod.id),
                ('reference', '=', unbuild.name)
            ], order="create_date desc", limit=1)
            main_price = main_valuation.unit_cost if main_valuation else main_prod.standard_price
            yield_value = unbuild.weight_percentage or 0.0

            if main_key not in summary_data:
                summary_data[main_key] = {
                    'product_name': main_prod.display_name,
                    'qty': 0.0,
                    'main_price': main_price,
                    'main_price_sum': 0.0,  # sum of unit prices (for avg)
                    'main_price_count': 0,
                    'main_total_price': 0.0,
                    'yield_sum': 0.0,           # sum of yield %
                    'yield_count': 0,
                    'doc_date': '',
                    'warehouse': '',
                    'lines': {},
                }

            rec = summary_data[main_key]
            rec['qty'] += unbuild.product_qty
            rec['main_total_price'] += (main_price * unbuild.product_qty)
            rec['main_price_sum'] += main_price
            rec['main_price_count'] += 1
            # rec['yield'] = unbuild.weight_percentage or rec['yield']
            rec['yield_sum'] += yield_value
            rec['yield_count'] += 1
            rec['warehouse'] = unbuild.warehouse_id.name or rec['warehouse']
            rec['doc_date'] = unbuild.create_date.strftime('%d-%m-%Y')

            # === Components ===
            for line in unbuild.line_ids:
                comp = line.product_id
                if comp.id not in rec['lines']:
                    rec['lines'][comp.id] = {
                        'product_name': comp.display_name,
                        'product_qty': 0.0,
                        'uom': line.product_uom.name if line.product_uom else '',
                        'weight': 0.0,
                        'price_sum': 0.0,  # for avg price
                        'price_count': 0,
                        'price': 0.0,
                        'total_price': 0.0,
                    }

                line_data = rec['lines'][comp.id]
                valuation = self.env['stock.valuation.layer'].search([
                    ('product_id', '=', comp.id),
                    ('reference', '=', unbuild.name)
                ], order="create_date desc", limit=1)
                price = valuation.unit_cost if valuation else comp.standard_price

                line_data['product_qty'] += line.product_qty
                line_data['weight'] += getattr(line, 'weight', 0.0)
                line_data['price_sum'] += price
                line_data['price_count'] += 1
                # line_data['price'] = price
                line_data['total_price'] += (price * line.product_qty)

        # === Flatten for QWeb ===
        line_data = []
        for rec in summary_data.values():
            rec['main_price'] = rec['main_price_sum'] / rec['main_price_count'] if rec['main_price_count'] else 0.0
            rec['yield'] = rec['yield_sum'] / rec['yield_count'] if rec['yield_count'] else 0.0

            # compute component averages
            for line in rec['lines'].values():
                line['price'] = line['price_sum'] / line['price_count'] if line['price_count'] else 0.0
            rec['lines'] = list(rec['lines'].values())
            line_data.append(rec)

        data = {
            'records': line_data,
            'company_name': company.name,
            'company_logo': company.logo,
            'date_from': fields.Datetime.context_timestamp(self, self.date_from).strftime(
                '%d-%m-%Y %H:%M:%S') if self.date_from else '',
            'date_to': fields.Datetime.context_timestamp(self, self.date_to).strftime(
                '%d-%m-%Y %H:%M:%S') if self.date_to else '',
        }

        _logger.info("Final summary data: %s", data)
        return self.env.ref(
            'monal_butchery_consumption_report.action_report_butchery_consumption_summary'
        ).report_action(unbuild_records, data=data)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft', track_visibility='always')
