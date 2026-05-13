from odoo import models, fields, api
from datetime import datetime
from collections import defaultdict


class ConsumptionReportWizard(models.TransientModel):
    _name = 'consumption.report.wizard'
    _description = 'Consumption Report Wizard'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    filter_type = fields.Selection([
        ('category', 'By Category'),
        ('product', 'By Product'),
    ], string="Filter By", required=True, default='category')

    category_ids = fields.Many2many('product.category', string="Product Category")
    product_ids = fields.Many2many('product.product', string="Product")

    source_location_id = fields.Many2one('stock.location', string="Consumption Location")
    dest_location_id = fields.Many2one('stock.location', string="Destination Location")

    line_ids = fields.One2many('consumption.report.wizard.line', 'wizard_id', string="Lines")

    @api.onchange('filter_type', 'category_id', 'product_id', 'start_date', 'end_date', 'source_location_id',
                  'dest_location_id')
    def _onchange_filter(self):
        if not self.start_date or not self.end_date:
            return

        domain = [
            ('transfer_id.transfer_date', '>=', self.start_date),
            ('transfer_id.transfer_date', '<=', self.end_date),
            ('transfer_id.approval_stage', '=', 'done')
        ]

        if self.source_location_id:
            domain.append(('transfer_id.source_location_id', '=', self.source_location_id.id))
        if self.dest_location_id:
            domain.append(('dest_location_id', '=', self.dest_location_id.id))

        if self.filter_type == 'category' and self.category_ids:
            domain.append(('product_id.categ_id', 'in', self.category_ids.ids))

        elif self.filter_type == 'product':
            if self.product_ids:
                domain.append(('product_id', 'in', self.product_ids.ids))

        consumption_lines = self.env['transfer.consumption.line'].search(domain)

        self.line_ids = [(5, 0, 0)]

        vals = []
        for line in consumption_lines:
            vals.append((0, 0, {
                'product_id': line.product_id.id,
                'sku': line.product_id.default_code,
                'quantity': line.quantity,
                'uom': line.product_uom_id.name,
                'transfer_ref': line.transfer_id.name,
                'transfer_date': line.transfer_id.transfer_date,
                'select': True
            }))
        self.line_ids = vals

    def action_confirm(self):
        self.ensure_one()

        domain = [
            ('transfer_id.transfer_date', '>=', self.start_date),
            ('transfer_id.transfer_date', '<=', self.end_date),
            ('transfer_id.approval_stage', '=', 'done')
        ]

        if self.source_location_id:
            domain.append(('transfer_id.source_location_id', '=', self.source_location_id.id))
        if self.dest_location_id:
            domain.append(('dest_location_id', '=', self.dest_location_id.id))

        if self.filter_type == 'category' and self.category_ids:
            domain.append(('product_id.categ_id', 'in', self.category_ids.ids))
        elif self.filter_type == 'product' and self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))

        selected_lines = self.env['transfer.consumption.line'].search(domain)

        product_month_map = defaultdict(lambda: defaultdict(lambda: {
            'quantity': 0.0,
            'cost': 0.0,
            'price': 0.0
        }))

        months = set()

        for line in selected_lines:
            if not line.transfer_id.transfer_date:
                continue

            month_key = line.transfer_id.transfer_date.strftime('%b-%y').upper()
            months.add(month_key)

            product_id = line.product_id.id
            product = product_month_map[product_id]

            if 'product_info' not in product:
                product['product_info'] = {
                    'name': line.product_id.name,
                    'uom': line.product_uom_id.name or ''
                }

            valuation = self.env['stock.picking'].search([('origin','=',line.transfer_id.name)]).mapped('move_ids_without_package').filtered(lambda a:a.product_id == line.product_id).mapped('stock_valuation_layer_ids')
            valuation_qty = 0.0
            valuation_value = 0.0
            for val in valuation:
                valuation_value += abs(val.value)
                valuation_qty += abs(val.quantity)
            product[month_key]['quantity'] += valuation_qty
            product[month_key]['cost'] += round(valuation_value / valuation_qty,2) if valuation_value and valuation_qty else 0.0
            product[month_key]['price'] += valuation_value


        sorted_months = sorted(months, key=lambda m: datetime.strptime(m, '%b-%y'))

        final_lines = []
        # Used to collect totals
        total_qty_by_month = []
        total_amt_by_month = []
        grand_total_qty = 0.0
        grand_total_amt = 0.0

        # Fill product lines
        for product_data in product_month_map.values():
            product_info = product_data.pop('product_info')
            line_data = {
                'product': product_info['name'],
                'uom': product_info['uom'],
                'monthly_data': [],
                'total_quantity': 0.0,
                'total_cost': 0.0,
                'total_price': 0.0
            }

            for month in sorted_months:
                if month in product_data:
                    monthly = product_data[month]
                    line_data['monthly_data'].append({
                        'month': month,
                        'quantity': "{:,.3f}".format(monthly['quantity']),
                        'cost': "{:,.2f}".format( monthly['price'] / monthly['quantity'] if monthly['quantity'] and monthly['price'] else 0.0),
                        'price': "{:,.2f}".format(monthly['price']),
                    })
                    line_data['total_quantity'] += monthly['quantity']
                    line_data['total_cost'] += monthly['price'] / monthly['quantity'] if monthly['quantity'] and monthly['price'] else 0.0
                    line_data['total_price'] += monthly['price']
                else:
                    line_data['monthly_data'].append({
                        'month': month,
                        'quantity': "0.000",
                        'cost': "0.00",
                        'price': "0.00",
                    })

            line_data['total_quantity'] = "{:,.3f}".format(line_data['total_quantity'])
            line_data['total_cost'] = "{:,.2f}".format(line_data['total_cost'])
            line_data['total_price'] = "{:,.2f}".format(line_data['total_price'])
            final_lines.append(line_data)

        # Compute monthly and overall totals
        for month in sorted_months:
            month_qty = 0.0
            month_amt = 0.0
            for product_data in product_month_map.values():
                if month in product_data:
                    month_qty += product_data[month]['quantity']
                    month_amt += product_data[month]['price']
            total_qty_by_month.append("{:,.2f}".format(month_qty))
            total_amt_by_month.append("{:,.2f}".format(month_amt))
            grand_total_qty += month_qty
            grand_total_amt += month_amt

        report_data = {
            'start_date': self.start_date.strftime('%b %Y'),
            'end_date': self.end_date.strftime('%b %Y'),
            'filter_type': self.filter_type,
            'category': ', '.join(self.category_ids.mapped('name')) if self.category_ids else 'All',
            'product': ', '.join(self.product_ids.mapped('name')) if self.product_ids else 'All',
            'source_location': self.source_location_id.complete_name if self.source_location_id else 'All',
            'dest_location': self.dest_location_id.complete_name if self.dest_location_id else 'All',
            'month_headers': sorted_months,
            'lines': final_lines,
            'total_qty_by_month': total_qty_by_month,
            'total_amt_by_month': total_amt_by_month,
            'total_qty': "{:,.2f}".format(grand_total_qty),
            'total_amt': "{:,.2f}".format(grand_total_amt),
        }

        return {
            'type': 'ir.actions.report',
            'report_name': 'consumption_report_wizard.report_consumption_pdf',
            'report_type': 'qweb-pdf',
            'data': {'doc_ids': self.ids, 'doc_model': self._name, 'data': report_data},
            'context': self.env.context,
            'formatLang': self.env['ir.qweb.field.float'].value_to_html
        }


class ConsumptionReportWizardLine(models.TransientModel):
    _name = 'consumption.report.wizard.line'
    _description = 'Consumption Report Wizard Line'

    wizard_id = fields.Many2one('consumption.report.wizard')
    product_id = fields.Many2one('product.product', string="Product")
    sku = fields.Char(string="SKU")
    quantity = fields.Float(string="Quantity")
    uom = fields.Char(string="Unit of Measure")
    transfer_ref = fields.Char(string="Transfer Reference")
    transfer_date = fields.Datetime(string="Transfer Date")
    select = fields.Boolean(string="Select", default=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.sku = self.product_id.default_code

class TransferConsumption(models.Model):
    _inherit = 'transfer.consumption'

    def action_open_consumption_wizard(self):
        return {
            'name': 'Select Products',
            'type': 'ir.actions.act_window',
            'res_model': 'consumption.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
            },
        }
