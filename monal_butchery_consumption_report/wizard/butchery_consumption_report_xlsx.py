from odoo import models
from odoo.exceptions import UserError
import base64
import io

class PatientReportXls(models.AbstractModel):
    _name = "report.monal_butchery_consumption_report.butchery_template_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet("Butchery Consumption")

        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center'
        })
        header_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'bg_color': '#D9D9D9', 'align': 'center'
        })
        border_fmt = workbook.add_format({'border': 1})
        num_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        num_int_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0'})
        bold_fmt = workbook.add_format({'bold': True, 'border': 1})

        sheet.set_column(1, 1, 30)
        sheet.set_column(9, 9, 30)
        sheet.set_column(7, 7, 20)

        for col in range(0, 15):
            if col not in (1, 7, 9):
                sheet.set_column(col, col, 13)

        row = 0

        sheet.merge_range(row, 0, row, 14, "Butchery Consumption Report", title_fmt)
        row += 2

        date_from = data.get("date_from", "")
        date_to = data.get("date_to", "")
        period = f"Period: {date_from} - {date_to}"

        sheet.merge_range(row, 0, row, 14, period, bold_fmt)
        row += 2

        sheet.merge_range(row, 0, row, 7, "CONSUMPTION", header_fmt)
        sheet.merge_range(row, 8, row, 14, "PRODUCTION", header_fmt)
        row += 1

        sheet.write_row(row, 0, [
            "REF#", "PRODUCT", "QTY", "UNIT PRICE", "TOTAL PRICE", "YIELD", "DOC DATE", "WAREHOUSE"
        ], header_fmt)

        sheet.write_row(row, 8, [
            "SR#", "ITEM", "UOM", "QUANTITY", 'WEIGHT', "UNIT PRICE", "TOTAL PRICE"
        ], header_fmt)
        row += 1

        sr = 1
        total_qty_consumption = 0
        total_unit_price_consumption = 0
        total_total_price_consumption = 0
        total_qty_production = 0
        total_unit_production = 0
        total_weight_production = 0
        total_total_price_production = 0

        for rec in data["records"]:
            sheet.write(row, 0, rec["unbuild_name"], border_fmt)
            sheet.write(row, 1, rec["product_name"], border_fmt)
            sheet.write(row, 2, rec["qty"], num_fmt)
            sheet.write(row, 3, rec["main_price"], num_fmt)
            sheet.write(row, 4, rec["main_total_price"], num_fmt)
            sheet.write(row, 5, rec["yield"], num_fmt)
            sheet.write(row, 6, rec["doc_date"], border_fmt)
            sheet.write(row, 7, rec["warehouse"], border_fmt)

            total_qty_consumption += rec["qty"]
            total_unit_price_consumption += rec["main_price"]
            total_total_price_consumption += rec["main_total_price"]

            start_row = row

            for line in rec["lines"]:

                if line["product_qty"] == 0:
                    continue

                sheet.write(start_row, 8, sr, num_int_fmt)
                sheet.write(start_row, 9, line["product_name"], border_fmt)
                sheet.write(start_row, 10, line["uom"], border_fmt)
                sheet.write(start_row, 11, line["product_qty"], num_fmt)
                sheet.write(start_row, 12, line["weight"], num_fmt)
                sheet.write(start_row, 13, line["price"], num_fmt)
                sheet.write(start_row, 14, line["total_price"], num_fmt)

                total_qty_production += line["product_qty"]
                total_weight_production += line["weight"]
                total_unit_production += line["price"]
                total_total_price_production += line["total_price"]
                sr += 1
                start_row += 1

            row = start_row + 1


            record_qty_total = sum(l["product_qty"] for l in rec["lines"] if l["product_qty"] != 0)
            record_weight_total = sum(l["weight"] for l in rec["lines"] if l["product_qty"] != 0)
            record_unit_total = sum(l["price"] for l in rec["lines"] if l["product_qty"] != 0)
            record_price_total = sum(l["total_price"] for l in rec["lines"] if l["product_qty"] != 0)

            sheet.merge_range(row, 8, row, 10, "Total", bold_fmt)
            sheet.write(row, 11, record_qty_total, num_fmt)
            sheet.write(row, 12, record_weight_total, num_fmt)
            sheet.write(row, 13, record_unit_total, num_fmt)
            sheet.write(row, 14, record_price_total, num_fmt)

            sr = 1
            row += 1

        row += 2

        sheet.merge_range(row, 0,row, 1, "Grand Total Consumption", bold_fmt)
        sheet.write(row, 2, total_qty_consumption, num_fmt)
        sheet.write(row, 3, total_unit_price_consumption, num_fmt)
        sheet.write(row, 4, total_total_price_consumption, num_fmt)
        sheet.merge_range(row, 8,row, 10, "Grand Total Production", bold_fmt)
        sheet.write(row, 11, total_qty_production, num_fmt)
        sheet.write(row, 12, total_weight_production, num_fmt)
        sheet.write(row, 13, total_unit_production, num_fmt)
        sheet.write(row, 14, total_total_price_production, num_fmt)

        # sheet.merge_range(start_row, 8, start_row, 10, "Total", bold_fmt)
        # sheet.write(start_row, 11, record_qty_total, num_fmt)
        # sheet.write(start_row, 12, record_weight_total, num_fmt)
        # sheet.write(start_row, 13, record_unit_total, num_fmt)
        # sheet.write(start_row, 14, record_price_total, num_fmt)

        # sheet.merge_range(start_row, 0, start_row, 1, "Total", bold_fmt)
        # sheet.write(start_row, 2, rec["qty"], num_fmt)
        # sheet.write(start_row, 3, rec["main_price"], num_fmt)
        # sheet.write(start_row, 4, rec["main_total_price"], num_fmt)
        # sheet.merge_range(start_row, 6,start_row, 8, "Total", bold_fmt)
        # sheet.write(start_row, 9, record_qty_total, num_fmt)
        # sheet.write(start_row, 10, record_unit_total, num_fmt)
        # sheet.write(start_row, 11, record_price_total, num_fmt)


