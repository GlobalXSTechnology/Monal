from odoo.exceptions import ValidationError, UserError

from odoo import models, fields, api, _,SUPERUSER_ID
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from datetime import date
import calendar
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MonthComparisonReportWizard(models.TransientModel):
    _name = 'month.comparison.report.wizard'
    _description = 'Month Comparison Report Wizard'

    date_filter_field = fields.Selection([
        ('transfer_date', 'Transfer Date'),
        ('accounting_date', 'Accounting Date'),
    ], string="Date Filter Field", required=True, default='transfer_date')

    date_type_filter = fields.Selection([
        ('month', 'By Month'),
        ('date', 'By Date'),
        ('qatar', 'By Quarter'),
        ('year', 'By Year'),
    ], string="Date Filter", required=True, default='month')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")

    qatar_selection = fields.Selection([
        ('q1', 'Q1'),
        ('q2', 'Q2'),
        ('q3', 'Q3'),
        ('q4', 'Q4'),
    ], string="Quarter")
    year_selection_for_qatar = fields.Selection(
        selection=lambda self: [(str(y), str(y)) for y in range(date.today().year, 1999, -1)],
        string="Quarter Year",
    )

    year_selection = fields.Selection(
        selection=lambda self: [(str(y), str(y)) for y in range(date.today().year, 1999, -1)],
        string="Year",
    )

    month_ids = fields.One2many(
        'month.comparison.line',
        'wizard_id',
        string="Select Months",
    )

    filter_type = fields.Selection([
        ('category', 'By Category'),
        ('product', 'By Product'),
        ('location', 'By Location'),
        ('account', 'By Account'),
    ], string="Filter By", required=True, default='category')

    category_ids = fields.Many2many('product.category', string="Product Category")
    product_ids = fields.Many2many('product.product', string="Product")
    analytic_account_ids = fields.Many2many('account.analytic.account', string="Analytic Accounts",
                                            default=lambda self: self.env['account.analytic.account'])

    account_ids = fields.Many2many(
        'account.account',
        string="Accounts",
        domain=[('account_type', 'not in',
                 ('asset_receivable', 'liability_payable', 'asset_cash', 'liability_credit_card')),
                ('deprecated', '=', False)]
    )
    source_location_id = fields.Many2one('stock.location', string="Source Location")
    dest_location_id = fields.Many2many(
        'stock.location', string="Consumption Location",
        domain="[('usage','=','inventory')]"
    )

    def _get_month_range(self, month_date):
        start_date = month_date.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - relativedelta(days=1)
        return start_date, end_date

    def _get_qatar_month_range(self, qatar, year):
        qatar_map = {'q1': (1, 3), 'q2': (4, 6), 'q3': (7, 9), 'q4': (10, 12)}
        if qatar not in qatar_map:
            raise UserError("Invalid Qatar selection")
        start_month, end_month = qatar_map[qatar]
        start_date = date(int(year), start_month, 1)
        last_day = calendar.monthrange(int(year), end_month)[1]
        end_date = date(int(year), end_month, last_day)
        return start_date, end_date

    def _get_consumption_data(self, start_date, end_date, exact_dates=False):
        date_field = 'transfer_date'
        if self.date_filter_field == 'accounting_date':
            date_field = 'accounting_date'

        data = defaultdict(lambda: {'quantity': 0.0, 'amount': 0.0, 'cost': 0.0})

        # Get approved consumption transfers (headers only)
        transfer_consumptions = self.env['transfer.consumption'].search([
            (date_field, '>=', start_date),
            (date_field, '<=', end_date),
            ('approval_stage', '=', 'done'),
            ('x_studio_from_location_company', '=', self.company_id.id)
        ])
        _logger.info('transfer_consumptions')
        _logger.info('transfer_consumptions')
        _logger.info('transfer_consumptions')
        _logger.info('transfer_consumptions')
        _logger.info('transfer_consumptions')
        _logger.info('date_field')
        _logger.info(date_field)
        _logger.info('transfer_consumptions')
        _logger.info(transfer_consumptions)
        
        dest_location_id = self.dest_location_id
        if self.account_ids and self.filter_type == 'account':
            dest_location_id = self.env['stock.location'].search([
                ('valuation_out_account_id', 'in', self.account_ids.ids),('company_id', '=', self.company_id.id)
            ])

        if self.dest_location_id and self.filter_type == 'location':
            dest_location_id = self.dest_location_id
        # Get related pickings
        picking_domain = [
            ('picking_type_id.code', '=', 'internal'),
            ('state', '=', 'done'),
            ('origin', 'in', transfer_consumptions.mapped('name')),
            ('company_id', '=', self.company_id.id)
        ]
        if dest_location_id:
            picking_domain.append(('location_dest_id', 'in', dest_location_id.ids))
        _logger.info('picking_domain')
        _logger.info(picking_domain)
        picking_ids = self.env['stock.picking'].search(picking_domain)
        # Pre-fetch moves
        move_lines = picking_ids.mapped('move_ids_without_package')
        _logger.info('picking_ids')
        _logger.info(picking_ids)
        _logger.info('move_linesmove_linesmove_linesmove_linesmove_linesmove_linesmove_lines')
        _logger.info(move_lines)
        # Apply optional filters
        if self.filter_type == 'product' and self.product_ids:
            move_lines = move_lines.filtered(lambda m: m.product_id in self.product_ids)
        elif self.filter_type == 'category' and self.category_ids:
            move_lines = move_lines.filtered(lambda m: m.product_id.categ_id in self.category_ids)
        if self.analytic_account_ids:
            move_lines = move_lines.filtered(
                lambda m: any(
                    str(acc_id) in (m.analytic_distribution or {}) for acc_id in self.analytic_account_ids.ids)
            )

        valuation = self.env['stock.valuation.layer'].search(
                [('reference', 'in', move_lines.mapped('reference')), ('product_id', 'in', move_lines.mapped('product_id').ids),('company_id', '=', self.company_id.id)])
        _logger.info('valuationvaluationvaluationvaluationvaluationvaluationvaluationvaluationvaluation')
        _logger.info(valuation)
        # Process valuation
        for line in move_lines:
            valuation = self.env['stock.valuation.layer'].search(
                [('reference', 'ilike', line.reference), ('product_id', '=', line.product_id.id),('company_id', '=', self.company_id.id)])
            # valuation = line.stock_valuation_layer_ids
            val_qty = (sum((v.quantity) for v in valuation))
            val_amt = (sum((v.value) for v in valuation))

            key = (line.product_id.id, line.location_dest_id.id)
            data[key]['quantity'] += val_qty
            data[key]['amount'] += val_amt
            data[key]['cost'] = (abs(val_amt) / abs(val_qty)) if val_qty != 0.0 else 0.0

        # Pre-fetch moves
        move_lines = picking_ids.return_ids.mapped('move_ids_without_package')

        # Apply optional filters
        if self.filter_type == 'product' and self.product_ids:
            move_lines = move_lines.filtered(lambda m: m.product_id in self.product_ids)
        elif self.filter_type == 'category' and self.category_ids:
            move_lines = move_lines.filtered(lambda m: m.product_id.categ_id in self.category_ids)
        if self.analytic_account_ids:
            move_lines = move_lines.filtered(
                lambda m: any(
                    str(acc_id) in (m.analytic_distribution or {}) for acc_id in self.analytic_account_ids.ids)
            )

        valuation = self.env['stock.valuation.layer'].search(
                [('reference', 'in', move_lines.mapped('reference')), ('product_id', 'in', move_lines.mapped('product_id').ids),('company_id', '=', self.company_id.id)])
        _logger.info('move_linesmove_linesmove_linesmove_linesmove_linesmove_linesmove_linesmove_linesmove_linesmove_linesmove_linesmove_lines2222222222')
        _logger.info(move_lines)
        _logger.info('valuationvaluationvaluationvaluationvaluation2222222222222222222')
        _logger.info(valuation)
        # Process valuation
        for line in move_lines:
            valuation = self.env['stock.valuation.layer'].search(
                [('reference', '=', line.reference), ('product_id', '=', line.product_id.id),('company_id', '=', self.company_id.id)])
            # valuation = line.stock_valuation_layer_ids
            val_qty = val_amt = 0
            for v in valuation:
                val_qty += v.quantity
                val_amt += v.value
            key = (line.product_id.id, line.location_id.id)
            data[key]['quantity'] += val_qty
            data[key]['amount'] += val_amt
            data[key]['cost'] = (abs(val_amt) / abs(val_qty)) if val_qty != 0.0 else 0.0
            
        _logger.info(data)
        return data

    def action_confirm(self):
        report_data = self.with_user(SUPERUSER_ID)._get_report_data_all()
        return self.env.ref(
            'consumption_month_comparison.action_multi_month_comparison_pdf'
        ).report_action(self, data=report_data)

    def _get_report_data_all(self):
        self.ensure_one()

        month_headers = []
        month_data_map = {}

        if self.date_type_filter == 'month':
            if not self.month_ids:
                raise UserError("Please select at least one month.")
            for month_line in self.month_ids:
                month_date = date(int(month_line.year), int(month_line.month), 1)
                start_date, end_date = self._get_month_range(month_date)
                month_key = month_date.strftime('%b-%Y')
                month_headers.append(month_key)
                month_data_map[month_key] = self._get_consumption_data(start_date, end_date)


        elif self.date_type_filter == 'date':
            if not self.date_from or not self.date_to:
                raise UserError("Please select both Start Date and End Date.")
            month_key = f"{self.date_from.strftime('%d-%b-%Y')} to {self.date_to.strftime('%d-%b-%Y')}"
            month_headers.append(month_key)
            month_data_map[month_key] = self._get_consumption_data(self.date_from, self.date_to, exact_dates=True)


        elif self.date_type_filter == 'year':
            if not self.year_selection:
                raise UserError("Please select a Year.")
            for i in range(1, 13):
                month_date = date(int(self.year_selection), i, 1)
                start_date, end_date = self._get_month_range(month_date)
                month_key = month_date.strftime('%b-%Y')
                month_headers.append(month_key)
                month_data_map[month_key] = self._get_consumption_data(start_date, end_date)


        elif self.date_type_filter == 'qatar':
            if not self.qatar_selection or not self.year_selection_for_qatar:
                raise UserError("Please select both Qatar and Qatar Year.")
            start_date, end_date = self._get_qatar_month_range(self.qatar_selection, self.year_selection_for_qatar)
            current = start_date
            while current <= end_date:
                start_d, end_d = self._get_month_range(current)
                month_key = current.strftime('%b-%Y')
                month_headers.append(month_key)
                month_data_map[month_key] = self._get_consumption_data(start_d, end_d)
                current += relativedelta(months=1)

        all_keys = set()
        for data_map in month_data_map.values():
            all_keys |= set(data_map.keys())
        final_lines = []
        grouped_data = defaultdict(list)

        for (product_id, location_id) in all_keys:
            product = self.env['product.product'].browse(product_id)
            location = self.env['stock.location'].browse(location_id)

            month_data_list = []
            has_non_zero = False
            for month in month_headers:
                pdata = month_data_map[month].get((product_id, location_id), {})
                amount = pdata.get('amount', 0.0)
                qty = pdata.get('quantity', 0.0)
                cost = (abs(amount) / abs(qty)) if qty != 0.0 else 0.0
                month_data_list.append({
                    'month': month,
                    'qty': (-1 * qty),
                    'amt': (-1 * amount),
                    'cost': (cost),
                })
                if amount != 0 and qty != 0:
                    has_non_zero = True

            if not has_non_zero:
                continue

            row_data = {
                'location': location.display_name,
                'product_name': product.display_name,
                'uom': product.uom_id.name,
                'months': month_data_list,
                'account': location.valuation_out_account_id.display_name if location.valuation_out_account_id else '',

            }

            if self.filter_type == 'category':
                grouped_data[product.categ_id.display_name].append(row_data)
            elif self.filter_type == 'product':
                grouped_data[product.display_name].append(row_data)
            elif self.filter_type == 'location':
                grouped_data[location.display_name].append(row_data)
            elif self.filter_type == 'account':
                grouped_data[location.valuation_in_account_id.display_name].append(row_data)

        final_lines_grouped = []
        for group_name, rows in grouped_data.items():
            if not rows:
                continue
            totals = []
            for i, month in enumerate(month_headers):
                total_qty = sum(r['months'][i]['qty'] for r in rows)
                total_amt = sum(r['months'][i]['amt'] for r in rows)
                totals.append({
                    'month': month,
                    'qty': total_qty,
                    'amt': total_amt,
                    'cost': (total_amt / total_qty) if total_qty != 0.0 else 0.0,
                })

            if self.filter_type == 'category':
                final_lines_grouped.append({'category': group_name, 'products': rows, 'totals': totals})
            elif self.filter_type == 'product':
                final_lines_grouped.append({'product': group_name, 'rows': rows, 'totals': totals})
            elif self.filter_type in ['location', 'account']:
                final_lines_grouped.append({
                    'location': group_name,
                    'products': rows,
                    'totals': totals,
                    'account': rows[0].get('account', '') if rows else '',
                    # 'analytic': rows[0].get('analytic', '') if rows else '',
                })


        grand_totals = []
        for i, month in enumerate(month_headers):
            total_qty = 0.0
            total_amt = 0.0
            # Loop through all groups (category, product, location, etc.)
            for group in final_lines_grouped:
                # Safely read qty and amt from each group's totals
                if i < len(group['totals']):
                    total_qty += group['totals'][i]['qty']
                    total_amt += group['totals'][i]['amt']
            grand_totals.append({
                'month': month,
                'qty': total_qty,
                'amt': total_amt,
            })
        report_data = {
            'month_headers': month_headers,
            'grand_totals':grand_totals,
            'lines': final_lines_grouped,
            'start_date': self.date_from.strftime('%Y-%m-%d') if self.date_from else '',
            'end_date': self.date_to.strftime('%Y-%m-%d') if self.date_to else '',
            'filter_type': self.filter_type,
            'account_id': ', '.join(self.account_ids.mapped('name')) if self.account_ids else '',
            'analytic_account_ids': ', '.join(
                self.analytic_account_ids.mapped('name')) if self.analytic_account_ids else '',
            'category': ', '.join(self.category_ids.mapped('name')) if self.category_ids else '',
            'product': ', '.join(self.product_ids.mapped('display_name')) if self.product_ids else '',
            'source_location': self.source_location_id.display_name if self.source_location_id else '',
            'dest_location': ', '.join(self.dest_location_id.mapped('display_name')) if self.dest_location_id else '',
        }

        return report_data

    def action_print_report_xlsx(self):
        self.ensure_one()
        report_data = self.with_user(SUPERUSER_ID)._get_report_data_all()
        return self.env.ref(
            'consumption_month_comparison.action_multi_month_comparison_xlsx'
        ).report_action(self, data=report_data)


class MonthComparisonLine(models.TransientModel):
    _name = 'month.comparison.line'
    _description = 'Month Comparison Line'

    wizard_id = fields.Many2one('month.comparison.report.wizard')
    month = fields.Selection([
        ('1', 'Jan'), ('2', 'Feb'), ('3', 'Mar'), ('4', 'Apr'), ('5', 'May'), ('6', 'Jun'),
        ('7', 'Jul'), ('8', 'Aug'), ('9', 'Sep'), ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dec')
    ], string="Month", required=True)
    year = fields.Selection(
        selection=lambda self: [(str(y), str(y)) for y in range(date.today().year, 1999, -1)],
        string="Year", required=True
    )


class ReportMultiMonthComparison(models.AbstractModel):
    _name = 'report.consumption_month_comparison.report_comparison_pdf'
    _description = 'Multi-Month Comparison PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['month.comparison.report.wizard'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'month.comparison.report.wizard',
            'docs': docs,
            'data': data,
        }
