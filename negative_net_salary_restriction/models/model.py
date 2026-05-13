from odoo import api, fields, models, _
import logging

from datetime import date, datetime
from datetime import timedelta
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from odoo import models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
import logging
import random
import math
import pytz

from collections import defaultdict, Counter
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from functools import reduce

from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, date_utils, convert_file, format_amount
from odoo.tools.float_utils import float_compare
from odoo.tools.misc import format_date
from odoo.tools.safe_eval import safe_eval, datetime as safe_eval_datetime, dateutil as safe_eval_dateutil

_logger = logging.getLogger(__name__)


class DefaultDictPayroll(defaultdict):
    def get(self, key, default=None):
        if key not in self and default is not None:
            self[key] = default
        return self[key]


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _get_payslip_lines(self):
        line_vals = []

        if any(self.mapped('ytd_computation')):
            last_ytd_payslips = self._get_last_ytd_payslips()
            code_set = set(self.struct_id.rule_ids.mapped('code'))
        else:
            last_ytd_payslips = defaultdict(lambda: self.env['hr.payslip'])
            code_set = set()
        ytd_payslips = reduce(
            lambda ytd_payslips, payslip: ytd_payslips | payslip, last_ytd_payslips.values(),
            self.env['hr.payslip']
        )

        line_values = ytd_payslips._get_line_values(code_set, ['ytd'])

        for payslip in self:
            if not payslip.contract_id:
                raise UserError(_("There's no contract set on payslip %(payslip)s for %(employee)s. Check that there is at least a contract set on the employee form.", payslip=payslip.name, employee=payslip.employee_id.name))

            localdict = self.env.context.get('force_payslip_localdict', None)
            if localdict is None:
                localdict = payslip._get_localdict()

            rules_dict = localdict['rules']
            result_rules_dict = localdict['result_rules']

            blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])

            result = {}
            for rule in sorted(payslip.struct_id.rule_ids, key=lambda x: x.sequence):
                if rule.id in blacklisted_rule_ids:
                    continue
                localdict.update({
                    'result': None,
                    'result_qty': 1.0,
                    'result_rate': 100,
                    'result_name': False
                })
                if rule._satisfy_condition(localdict):
                    # Retrieve the line name in the employee's lang
                    employee_lang = payslip.employee_id.lang or self.env.lang
                    # This actually has an impact, don't remove this line
                    if rule.code in localdict['same_type_input_lines']:
                        for multi_line_rule in localdict['same_type_input_lines'][rule.code]:
                            localdict['inputs'][rule.code] = multi_line_rule
                            amount, qty, rate = rule._compute_rule(localdict)
                            tot_rule = payslip._get_payslip_line_total(amount, qty, rate, rule)

                            result_rules_dict[rule.code]['total'] += tot_rule
                            result_rules_dict[rule.code]['amount'] += tot_rule
                            result_rules_dict[rule.code]['quantity'] = 1
                            result_rules_dict[rule.code]['rate'] = 100
                            rules_dict[rule.code] = rule

                            localdict = rule.category_id._sum_salary_rule_category(localdict,
                                                                                   tot_rule)
                            rule_name = payslip._get_rule_name(localdict, rule, employee_lang)
                            line_vals.append({
                                'sequence': rule.sequence,
                                'code': rule.code,
                                'name':  rule_name,
                                'salary_rule_id': rule.id,
                                'contract_id': localdict['contract'].id,
                                'employee_id': localdict['employee'].id,
                                'amount': amount,
                                'quantity': qty,
                                'rate': rate,
                                'total': tot_rule,
                                'slip_id': payslip.id,
                                'ytd': line_values[rule.code][last_ytd_payslips[payslip].id]
                                    ['ytd'] + tot_rule,
                            })
                        input_line_ids = localdict['same_type_input_lines'][rule.code].ids
                        localdict['inputs'][rule.code] = self.__get_aggregator_hr_payslip_input_model()(
                            env=self.env, ids=input_line_ids, prefetch_ids=input_line_ids,
                        )
                    else:
                        amount, qty, rate = rule._compute_rule(localdict)
                        #check if there is already a rule computed with that code
                        previous_amount = localdict.get(rule.code, 0.0)
                        #set/overwrite the amount computed for this rule in the localdict
                        tot_rule = payslip._get_payslip_line_total(amount, qty, rate, rule)
                        localdict[rule.code] = tot_rule
                        result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty, 'rate': rate}
                        rules_dict[rule.code] = rule
                        # sum the amount for its salary category
                        localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
                        rule_name = payslip._get_rule_name(localdict, rule, employee_lang)
                        # create/overwrite the rule in the temporary results
                        result[rule.code] = {
                            'sequence': rule.sequence,
                            'code': rule.code,
                            'name': rule_name,
                            'salary_rule_id': rule.id,
                            'contract_id': localdict['contract'].id,
                            'employee_id': localdict['employee'].id,
                            'amount': amount,
                            'quantity': qty,
                            'rate': rate,
                            'total': tot_rule,
                            'slip_id': payslip.id,
                            'ytd': line_values[rule.code][last_ytd_payslips[payslip].id]
                                ['ytd'] + tot_rule,
                        }
            line_vals += list(result.values())
        return line_vals


    def action_payslip_done(self):
        for payslip in self:
            net_line = payslip.line_ids.filtered(lambda l: l.code == 'NET')
            if net_line and net_line.total < 0:
                raise ValidationError(
                    _("Net Salary is negative for %s. Draft entry cannot be created!") % payslip.employee_id.name
                )

        return super(HrPayslip, self).action_payslip_done()

    def compute_sheet(self):
        res = super().compute_sheet()
        _logger.info(res)

        for slip in self:
            non_zero_lines = slip.line_ids.filtered(lambda l: l.total != 0)

            vals_list = []
            _logger.info(non_zero_lines)
            _logger.info('Non Zero Liens')
            for line in non_zero_lines:
                vals_list.append({
                    'salary_rule_id': line.salary_rule_id.id,
                    'contract_id': line.contract_id.id,
                    'name': line.name,
                    'code': line.code,
                    'category_id': line.category_id.id,
                    'sequence': line.sequence,
                    'appears_on_payslip': line.appears_on_payslip,
                    'amount_select': line.amount_select,
                    'amount_fix': line.amount_fix,
                    'amount_percentage': line.amount_percentage,
                    'quantity': line.quantity,
                    'rate': line.rate,
                    'total': line.total,
                    'amount': line.amount,
                })

            slip.line_ids = [(5, 0, 0)]

            slip.line_ids = [(0, 0, vals) for vals in vals_list]

        return res
