import ast
import base64
import datetime
import io
import json
import logging
import re
from ast import literal_eval
from collections import defaultdict
from functools import cmp_to_key
from itertools import groupby

import markupsafe
from dateutil.relativedelta import relativedelta
from PIL import ImageFont

from odoo import models, fields, api, _, osv
from odoo.addons.web.controllers.utils import clean_action
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.service.model import get_public_method
from odoo.tools import date_utils, get_lang, float_is_zero, float_repr, SQL, parse_version, Query
from odoo.tools.float_utils import float_round, float_compare
from odoo.tools.misc import file_path, format_date, formatLang, split_every, xlsxwriter
from odoo.tools.safe_eval import expr_eval, safe_eval

_logger = logging.getLogger(__name__)

class AccountReportInherit(models.Model):
    _inherit = 'account.report'

    def _get_lines(self, options, all_column_groups_expression_totals=None, warnings=None):
        self.ensure_one()

        if options['report_id'] != self.id:
            raise UserError(_("Inconsistent report_id in options dictionary."))

        self.env.flush_all()

        if warnings is not None:
            self._generate_common_warnings(options, warnings)

        if all_column_groups_expression_totals is None:
            self._init_currency_table(options)
            all_column_groups_expression_totals = self._compute_expression_totals_for_each_column_group(
                self.line_ids.expression_ids, options, warnings=warnings,
            )

        dynamic_lines = self._get_dynamic_lines(options, all_column_groups_expression_totals, warnings=warnings)
        lines = []
        line_cache = {}
        hide_if_zero_lines = self.env['account.report.line']

        # Merge static + dynamic lines
        for line in self.line_ids:
            while dynamic_lines and line.sequence > dynamic_lines[0][0]:
                lines.append(dynamic_lines.pop(0)[1])

            parent_generic_id = None
            if line.parent_id:
                try:
                    parent_generic_id = line_cache[line.parent_id]['id']
                except KeyError as e:
                    raise UserError(_(
                        "Line '%(child)s' is configured to appear before its parent '%(parent)s'.",
                        child=line.name, parent=e.args[0].name
                    ))

            line_dict = self._get_static_line_dict(options, line, all_column_groups_expression_totals,
                                                   parent_id=parent_generic_id)
            line_cache[line] = line_dict
            if line.hide_if_zero:
                hide_if_zero_lines += line
            lines.append(line_dict)

        for dummy, left_dynamic_line in dynamic_lines:
            lines.append(left_dynamic_line)

        # -----------------------------
        # 💹 Manage growth comparison
        # -----------------------------
        if options.get('column_percent_comparison') == 'growth':
            for line in lines:
                # Defensive defaults
                first_value = line['columns'][0].get('no_format') or 0.0
                second_value = line['columns'][1].get('no_format') or 0.0

                # Compute absolute difference
                value_diff = (second_value or 0.0) - (first_value or 0.0)

                # Determine green_on_positive flag
                green_on_positive = True
                model, line_id = self._get_model_info_from_id(line['id'])
                if model == 'account.report.line' and line_id:
                    report_line = self.env['account.report.line'].browse(line_id)
                    compared_expression = report_line.expression_ids.filtered(
                        lambda expr: expr.label == line['columns'][0].get('expression_label')
                    )
                    if compared_expression:
                        green_on_positive = compared_expression.green_on_positive

                # Compute percentage difference (built-in helper)
                column_percent = self._compute_column_percent_comparison_data(
                    options, first_value, second_value, green_on_positive=green_on_positive
                )

                # Add both new fields
                line['value_diff'] = {
                    'name': round(value_diff,2),
                    'no_format_name': value_diff,
                    'class': 'number',
                }
                line['column_percent_comparison_data'] = column_percent

        # -----------------------------
        # Manage budget comparison
        # -----------------------------
        elif options.get('column_percent_comparison') == 'budget':
            for line in lines:
                self._set_budget_column_comparisons(options, line)

        # -----------------------------
        # Hide if zero logic
        # -----------------------------
        hidden_lines_dict_ids = set()
        for line in hide_if_zero_lines:
            children_to_check = line
            current = line
            while current:
                children_to_check |= current
                current = current.children_ids

            all_children_zero = True
            hide_candidates = set()
            for child in children_to_check:
                child_line_dict_id = line_cache[child]['id']

                if child_line_dict_id in hidden_lines_dict_ids:
                    continue
                elif all(col.get('is_zero', True) for col in line_cache[child]['columns']):
                    hide_candidates.add(child_line_dict_id)
                else:
                    all_children_zero = False
                    break

            if all_children_zero:
                hidden_lines_dict_ids |= hide_candidates

        lines[:] = filter(
            lambda x: x['id'] not in hidden_lines_dict_ids and x.get('parent_id') not in hidden_lines_dict_ids,
            lines
        )

        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)

        lines = self._add_totals_below_sections(lines, options)
        lines = self._fully_unfold_lines_if_needed(lines, options)

        if self.custom_handler_model_id:
            lines = self.env[self.custom_handler_model_name]._custom_line_postprocessor(self, options, lines)

        if warnings is not None:
            custom_handler_name = self.custom_handler_model_name or self.root_report_id.custom_handler_model_name
            if custom_handler_name:
                self.env[custom_handler_name]._customize_warnings(
                    self, options, all_column_groups_expression_totals, warnings
                )

        self._format_column_values(options, lines)

        if options.get('export_mode') == 'print' and options.get('hide_0_lines'):
            lines = self._filter_out_0_lines(lines)

        return lines

    def _inject_report_into_xlsx_sheet(self, options, workbook, sheet):

        # We start by gathering the bold, italic and regular fonts to use later.
        fonts = {}
        for font_type in ('Reg', 'Bol', 'RegIta', 'BolIta'):
            try:
                lato_path = f'web/static/fonts/lato/Lato-{font_type}-webfont.ttf'
                fonts[font_type] = ImageFont.truetype(file_path(lato_path), 12)
            except (OSError, FileNotFoundError):
                # This won't give great result, but it will work.
                fonts[font_type] = ImageFont.load_default()

        def write_cell(sheet, x, y, value, style, colspan=1, datetime=False):
            self._set_xlsx_cell_sizes(sheet, fonts, x, y, value, style, colspan > 1)
            if colspan == 1:
                if datetime:
                    sheet.write_datetime(y, x, value, style)
                else:
                    sheet.write(y, x, value, style)
            else:
                sheet.merge_range(y, x, y, x + colspan - 1, value, style)

        default_format_props = {'font_name': 'Lato', 'font_size': 12, 'font_color': '#666666', 'num_format': '#,##0.00'}
        text_format_props = {'font_name': 'Lato', 'font_size': 12, 'font_color': '#666666'}
        date_format_props = {'font_name': 'Lato', 'font_size': 12, 'font_color': '#666666', 'align': 'left', 'num_format': 'yyyy-mm-dd'}
        title_format = workbook.add_format({'font_name': 'Lato', 'font_size': 12, 'bold': True, 'bottom': 2})
        annotation_format = workbook.add_format({**text_format_props, 'text_wrap': True})
        workbook_formats = {
            0: {
                'default': workbook.add_format({**default_format_props, 'bold': True, 'font_size': 13, 'bottom': 6}),
                'text': workbook.add_format({**text_format_props, 'bold': True, 'font_size': 13, 'bottom': 6}),
                'date': workbook.add_format({**date_format_props, 'bold': True, 'font_size': 13, 'bottom': 6}),
                'total': workbook.add_format({**default_format_props, 'bold': True, 'font_size': 13, 'bottom': 6}),
            },
            1: {
                'default': workbook.add_format({**default_format_props, 'bold': True, 'font_size': 13, 'bottom': 1}),
                'text': workbook.add_format({**text_format_props, 'bold': True, 'font_size': 13, 'bottom': 1}),
                'date': workbook.add_format({**date_format_props, 'bold': True, 'font_size': 13, 'bottom': 1}),
                'total': workbook.add_format({**default_format_props, 'bold': True, 'font_size': 13, 'bottom': 1}),
                'default_indent': workbook.add_format({**default_format_props, 'bold': True, 'font_size': 13, 'bottom': 1, 'indent': 1}),
                'date_indent': workbook.add_format({**date_format_props, 'bold': True, 'font_size': 13, 'bottom': 1, 'indent': 1}),
            },
            2: {
                'default': workbook.add_format({**default_format_props, 'bold': True}),
                'text': workbook.add_format({**text_format_props, 'bold': True}),
                'date': workbook.add_format({**date_format_props, 'bold': True}),
                'initial': workbook.add_format(default_format_props),
                'total': workbook.add_format({**default_format_props, 'bold': True}),
                'default_indent': workbook.add_format({**default_format_props, 'bold': True, 'indent': 2}),
                'date_indent': workbook.add_format({**date_format_props, 'bold': True, 'indent': 2}),
                'initial_indent': workbook.add_format({**default_format_props, 'indent': 2}),
                'total_indent': workbook.add_format({**default_format_props, 'bold': True, 'indent': 1}),
            },
            'default': {
                'default': workbook.add_format(default_format_props),
                'text': workbook.add_format(text_format_props),
                'date': workbook.add_format(date_format_props),
                'total': workbook.add_format(default_format_props),
                'default_indent': workbook.add_format({**default_format_props, 'indent': 2}),
                'date_indent': workbook.add_format({**date_format_props, 'indent': 2}),
                'total_indent': workbook.add_format({**default_format_props, 'indent': 2}),
            },
        }

        def get_format(content_type='default', level='default'):
            if isinstance(level, int) and level not in workbook_formats:
                workbook_formats[level] = {
                    **workbook_formats['default'],
                    'default_indent': workbook.add_format({**default_format_props, 'indent': level}),
                    'date_indent': workbook.add_format({**date_format_props, 'indent': level}),
                    'total_indent': workbook.add_format({**default_format_props, 'bold': True, 'indent': level - 1}),
                }

            level_formats = workbook_formats[level]
            if '_indent' in content_type and not level_formats.get(content_type):
                return level_formats.get('default_indent', level_formats.get(content_type.removesuffix('_indent'), level_formats['default']))
            return level_formats.get(content_type, level_formats['default'])

        print_mode_self = self.with_context(no_format=True)
        lines = self._filter_out_folded_children(print_mode_self._get_lines(options))
        annotations = self.get_annotations(options)

        # For reports with lines generated for accounts, the account name and codes are shown in a single column.
        # To help user post-process the report if they need, we should in such a case split the account name and code in two columns.
        account_lines_split_names = {}
        for line in lines:
            line_model = self._get_model_info_from_id(line['id'])[0]
            if line_model == 'account.account':
                # Reuse the _split_code_name to split the name and code in two values.
                account_lines_split_names[line['id']] = self.env['account.account']._split_code_name(line['name'])

        # Set the (Account) Name column width to 50.
        # If we have account lines and split the name and code in two columns, we will also set the code column.
        if len(account_lines_split_names) > 0:
            sheet.set_column(0, 0, 13)
            sheet.set_column(1, 1, 50)
        else:
            sheet.set_column(0, 0, 50)

        if not options.get('no_xlsx_currency_code_columns'):
            self._add_xlsx_currency_codes_columns(options, lines)

        original_x_offset = 1 if len(account_lines_split_names) > 0 else 0

        y_offset = 0
        # 1 and not 0 to leave space for the line name. original_x_offset allows making place for the code column if needed.
        x_offset = original_x_offset + 1

        # Add headers.
        # For this, iterate in the same way as done in main_table_header template
        column_headers_render_data = self._get_column_headers_render_data(options)
        for header_level_index, header_level in enumerate(options['column_headers']):
            for header_to_render in header_level * column_headers_render_data['level_repetitions'][header_level_index]:
                colspan = header_to_render.get('colspan', column_headers_render_data['level_colspan'][header_level_index])
                write_cell(sheet, x_offset, y_offset, header_to_render.get('name', ''), title_format, colspan + (1 if options['show_horizontal_group_total'] and header_level_index == 0 else 0))
                x_offset += colspan
            if options.get('column_percent_comparison') == 'growth':
                write_cell(sheet, x_offset, y_offset, 'Difference', title_format)
                x_offset += 1
            if options.get('column_percent_comparison') == 'growth':
                write_cell(sheet, x_offset, y_offset, '%', title_format)
                x_offset += 1

            if options['show_horizontal_group_total'] and header_level_index != 0:
                horizontal_group_name = next((group['name'] for group in options['available_horizontal_groups'] if group['id'] == options['selected_horizontal_group_id']), None)
                write_cell(sheet, x_offset, y_offset, horizontal_group_name, title_format)
                x_offset += 1
            if annotations:
                annotations_x_offset = x_offset
                write_cell(sheet, annotations_x_offset, y_offset, 'Annotations', title_format)
                x_offset += 1
            y_offset += 1
            x_offset = original_x_offset + 1

        for subheader in column_headers_render_data['custom_subheaders']:
            colspan = subheader.get('colspan', 1)
            write_cell(sheet, x_offset, y_offset, subheader.get('name', ''), title_format, colspan)
            x_offset += colspan
        y_offset += 1
        x_offset = original_x_offset + 1

        if account_lines_split_names:
            # If we have a separate account code column, add a title for it
            write_cell(sheet, x_offset - 2, y_offset, _("Code"), title_format)
            write_cell(sheet, x_offset - 1, y_offset, _("Account Name"), title_format)
        sheet.set_column(x_offset, x_offset + len(options['columns']), 10)

        for column in options['columns']:
            colspan = column.get('colspan', 1)
            write_cell(sheet, x_offset, y_offset, column.get('name', ''), title_format, colspan)
            x_offset += colspan

        if options['show_horizontal_group_total']:
            write_cell(sheet, x_offset, y_offset, options['columns'][0].get('name', ''), title_format, colspan)

        if options.get('column_percent_comparison') == 'growth':
            write_cell(sheet, x_offset, y_offset, '', title_format, colspan)
        y_offset += 1

        if options.get('order_column'):
            lines = self.sort_lines(lines, options)

        # Disable bold styling for the max level.
        max_level = max(line.get('level', -1) for line in lines) if lines else -1
        if max_level in {0, 1, 2}:
            # Total lines are supposed to be a level above, so we don't touch them.
            for wb_format in (s for s in workbook_formats[max_level] if 'total' not in s):
                workbook_formats[max_level][wb_format].set_bold(False)

        # Add lines.
        counter = 1
        for y, line in enumerate(lines):
            level = line.get('level')
            if level == 0:
                y_offset += 1
            elif not level:
                level = 'default'

            line_id = self._parse_line_id(line.get('id'))
            is_initial_line = line_id[-1][0] == 'initial' if line_id else False
            is_total_line = line_id[-1][0] == 'total' if line_id else False

            # Write the first column(s), with a specific style to manage the indentation.
            cell_type, cell_value = self._get_cell_type_value(line)
            account_code_cell_format = get_format('text', level)

            if cell_type == 'date':
                cell_format = get_format('date_indent', level)
            elif is_initial_line:
                cell_format = get_format('initial_indent', level)
            elif is_total_line:
                cell_format = get_format('total_indent', level)
            else:
                cell_format = get_format('default_indent', level)

            x_offset = original_x_offset + 1
            if lines[y]['id'] in account_lines_split_names:
                # Write the Account Code and Name columns.
                code, name = account_lines_split_names[lines[y]['id']]
                # Don't indent the account code and don't format is as a monetary value either.
                write_cell(sheet, 0, y + y_offset, code, account_code_cell_format)
                write_cell(sheet, 1, y + y_offset, name, cell_format)
            else:
                write_cell(sheet, original_x_offset, y + y_offset, cell_value, cell_format, datetime=cell_type == 'date')

                if 'parent_id' in line and line['parent_id'] in account_lines_split_names:
                    write_cell(sheet, 1 + original_x_offset, y + y_offset, account_lines_split_names[line['parent_id']][0], account_code_cell_format)
                elif account_lines_split_names:
                    write_cell(sheet, 1 + original_x_offset, y + y_offset, "", account_code_cell_format)

            # Write all the remaining cells.
            columns = line['columns']
            if options.get('column_percent_comparison') == 'growth':
                # Add absolute difference
                if 'value_diff' in line:
                    columns.append(line['value_diff'])
                else:
                    columns.append({'name': '', 'no_format_name': '', 'class': 'number'})

            if options.get('column_percent_comparison') and 'column_percent_comparison_data' in line:
                columns += [line['column_percent_comparison_data']]

            if options['show_horizontal_group_total']:
                columns += [line.get('horizontal_group_total_data', {'name': 0})]
            for x, column in enumerate(columns, start=x_offset):
                cell_type, cell_value = self._get_cell_type_value(column)
                if cell_type == 'date':
                    cell_format = get_format('date', level)
                elif is_initial_line:
                    cell_format = get_format('initial', level)
                elif is_total_line:
                    cell_format = get_format('total', level)
                else:
                    cell_format = get_format('default', level)
                write_cell(sheet, x + line.get('colspan', 1) - 1, y + y_offset, cell_value, cell_format, datetime=cell_type == 'date')

            # Write annotations.
            if annotations and (line_annotations := annotations.get(line['id'])):
                line_annotation_text = []
                for line_annotation in line_annotations:
                    line_annotation_text.append(f"{counter} - {line_annotation['text']}")
                    counter += 1
                write_cell(sheet, annotations_x_offset, y + y_offset, "\n".join(line_annotation_text), annotation_format)
