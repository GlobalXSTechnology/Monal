from odoo import models
from datetime import datetime
import base64
import io


class ReportMultiMonthComparisonXlsx(models.AbstractModel):
    _name = 'report.consumption_month_comparison.report_comparison_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Multi-Month Comparison XLSX Report'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet("Comparison Report")

        # ------------------- Formats -------------------
        title_fmt = workbook.add_format(
            {'bold': True, 'font_size': 16, 'align': 'center',
             'valign': 'vcenter', 'bg_color': '#4B4B4B',
             'font_color': '#FFFFFF'})
        company_name_fmt = workbook.add_format(
            {'bold': True, 'font_size': 19,
             'align': 'center', 'valign': 'vcenter'})
        address_fmt = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'italic': True,
            'font_size': 11,
            'text_wrap': True
        })

        header_fmt = workbook.add_format(
            {'bold': True, 'bg_color': '#D9E1F2',
             'border': 1, 'align': 'center', 'valign': 'vcenter'})
        bold_right = workbook.add_format({'bold': True, 'align': 'right'})
        normal_center = workbook.add_format(
            {'border': 1, 'align': 'center', 'valign': 'vcenter'})
        normal_left = workbook.add_format(
            {'border': 1, 'align': 'left', 'valign': 'vcenter'})
        number_wrap_fmt = workbook.add_format(
            {'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,'num_format':'#,##0.0###'})
        total_fmt = workbook.add_format(
            {'bold': True, 'bg_color': '#FFF2CC',
             'border': 1, 'align': 'center', 'valign': 'vcenter',
             'text_wrap': True,'num_format':'#,##0.0###'})
        product_header_fmt = workbook.add_format(
            {'bold': True, 'bg_color': '#BDD7EE',
             'border': 1, 'align': 'left', 'valign': 'vcenter'})
        period_fmt = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'bold': True})
        filter_fmt = workbook.add_format(
            {'align': 'left', 'valign': 'vcenter', 'italic': True})

        # ------------------- Column Widths -------------------
        sheet.set_column(0, 0, 25)  # Location / Product
        sheet.set_column(1, 1, 12)  # UoM
        sheet.set_column(2, 100, 22)  # Month data

        row = 0
        last_col = 1 + (len(data.get('month_headers', [])) *3)

        # ------------------- Company Info -------------------
        company = wizard.company_id or wizard.env.company
        company_name = company.name or ""

        # Build address manually without repeating company name
        partner = company.partner_id
        address_parts = [
            partner.street or "",
            partner.street2 or "",
            partner.city or "",
            partner.state_id.name if partner.state_id else "",
            partner.zip or "",
            partner.country_id.name if partner.country_id else "",
        ]
        company_address = ", ".join([part for part in address_parts if part])

        sheet.set_row(row, 80)

        sheet.merge_range(row, 0, row, last_col, company_name, company_name_fmt)

        # =================== Logo ===================
        if company.logo_web or company.logo:
            logo_data = base64.b64decode(company.logo_web or company.logo)
            image_stream = io.BytesIO(logo_data)
            sheet.insert_image(row, 0, "logo.png", {
                'image_data': image_stream,
                'x_scale': 0.4,
                'y_scale': 0.4,
                'x_offset': 5,
                'y_offset': 5,
            })

        row += 1

        # =================== Company Address ===================
        if company_address:
            sheet.merge_range(row, 0, row, last_col, company_address, address_fmt)
            row += 1

        # =================== Report Title ===================
        sheet.merge_range(row, 0, row, last_col, "Monthly Consumption Comparison", title_fmt)
        row += 2

        # ------------------- Period & Filters -------------------
        sheet.merge_range(
            row, 0, row, last_col,
            f"Period: {data.get('start_date', '')} to {data.get('end_date', '')}",
            period_fmt
        )
        row += 1
        filter_map = {
            'category': 'Category',
            'product': 'Product',
            'location': 'Location',
            'account': 'Account',
            'analytic': 'Analytic'
        }
        sheet.merge_range(
            row, 0, row, last_col,
            f"Filter By: {filter_map.get(data.get('filter_type', ''), '')}",
            filter_fmt
        )
        row += 2

        # ------------------- Product blocks -------------------
        for group in data['lines']:
            # Product header
            product_name = group.get('product', '') or group.get('category', '') or group.get('location', '')
            sheet.merge_range(row, 0, row, last_col, product_name, product_header_fmt)
            row += 1

            # Month headers
            sheet.merge_range(row, 0, row + 1, 0, "Product", header_fmt)
            sheet.merge_range(row, 1, row + 1, 1, "UoM", header_fmt)
            col = 2
            for mh in data.get('month_headers', []):
                if "to" in mh:
                    try:
                        parts = mh.split("to")
                        start = datetime.strptime(parts[0].strip(), "%d-%b-%Y")
                        end = datetime.strptime(parts[1].strip(), "%d-%b-%Y")
                        if start.strftime("%b-%Y") == end.strftime("%b-%Y"):
                            display = start.strftime("%b-%Y")
                        else:
                            display = f"{start.strftime('%b')} - {end.strftime('%b %Y')}"
                    except Exception:
                        display = mh
                else:
                    display = mh

                sheet.merge_range(row, col, row, col+2, display, header_fmt)
                sheet.write(row+1, col, 'Quantity', header_fmt)
                sheet.write(row+1, col+1, 'Cost', header_fmt)
                sheet.write(row+1, col+2, 'Amount', header_fmt)
                col += 3
            row += 2

            # Location / Product rows
            rows = group.get('rows', []) or group.get('products', [])
            for i, loc in enumerate(rows):
                row_fmt = normal_left if i % 2 == 0 else workbook.add_format(
                    {'border': 1, 'align': 'left', 'bg_color': '#F9F9F9'})
                sheet.write(row, 0, loc.get('product_name', ''), row_fmt)
                sheet.write(row, 1, loc.get('uom', ''), normal_center)
                col = 2
                for m in loc.get('months', []):
                    sheet.write(row, col, m.get('qty', 0), number_wrap_fmt)
                    col += 1
                    sheet.write(row, col, m.get('cost', 0.0), number_wrap_fmt)
                    col += 1
                    sheet.write(row, col, m.get('amt', 0.0), number_wrap_fmt)
                    col += 1
                row += 1

            # Totals
            sheet.write(row, 0, "Total", bold_right)
            sheet.write(row, 1, "", normal_center)
            col = 2
            for t in group.get('totals', []):
                sheet.write(row, col, t.get('qty', 0), total_fmt)
                col += 1
                sheet.write(row, col, '', total_fmt)
                col += 1
                sheet.write(row, col, t.get('amt', 0), total_fmt)
                col += 1
            # row += 1
            #
            # sheet.write(row, 0, "Total Amount", bold_right)
            # sheet.write(row, 1, "", normal_center)
            # col = 2
            # for t in group.get('totals', []):
            #     value = f"{t.get('amt', 0.0):,.2f}"
            #     sheet.write(row, col, value, total_fmt)
            #     col += 1
            row += 2
