import logging
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
from odoo import api, Command, fields, models, tools
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.resource.models.utils import float_to_time, HOURS_PER_DAY, Intervals
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare
from odoo.tools.misc import clean_context, format_date
from odoo.tools.translate import _
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.constrains('date_from', 'date_to', 'employee_id')
    def _check_date(self):
        if self.env.context.get('leave_skip_date_check', False):
            return
        _logger.info('hammadadadsdsd')
        all_leaves = self.search([
            ('date_from', '<', max(self.mapped('date_to'))),
            ('date_to', '>', min(self.mapped('date_from'))),
            ('employee_id', 'in', self.employee_id.ids),
            ('id', 'not in', self.ids),
            ('state', 'not in', ['cancel', 'refuse']),
            # ✅ Ignore encashed leaves globally
            ('leave_encashed_check', '=', False),
        ])

        for holiday in self:
            domain = [
                ('employee_id', '=', holiday.employee_id.id),
                ('date_from', '<', holiday.date_to),
                ('date_to', '>', holiday.date_from),
                ('id', '!=', holiday.id),
                ('state', 'not in', ['cancel', 'refuse']),
                # ✅ Ignore encashed leaves
                ('leave_encashed_check', '=', False),
            ]

            conflicting_holidays = all_leaves.filtered_domain(domain)
            _logger.info('conflicting_holidays')
            _logger.info(conflicting_holidays)
            conflicting_holidays = conflicting_holidays.filtered(lambda x:not x.leave_encashed_check)

            if conflicting_holidays and not holiday.leave_encashed_check:
                _logger.info('is conflictinng')
                conflicting_holidays_list = []
                holidays_only_have_uid = bool(holiday.employee_id)
                holiday_states = dict(conflicting_holidays.fields_get(
                    allfields=['state']
                )['state']['selection'])

                for conflicting_holiday in conflicting_holidays:
                    conflicting_holiday_data = {
                        'employee_name': conflicting_holiday.employee_id.name,
                        'date_from': format_date(self.env, conflicting_holiday.date_from),
                        'date_to': format_date(self.env, conflicting_holiday.date_to),
                        'state': holiday_states[conflicting_holiday.state],
                    }

                    if conflicting_holiday.employee_id.user_id.id != self.env.uid:
                        holidays_only_have_uid = False

                    if conflicting_holiday_data not in conflicting_holidays_list:
                        conflicting_holidays_list.append(conflicting_holiday_data)

                if not conflicting_holidays_list:
                    return

                conflicting_holidays_strings = []

                if holidays_only_have_uid:
                    for data in conflicting_holidays_list:
                        conflicting_holidays_strings.append(
                            _('from %(date_from)s to %(date_to)s - %(state)s',
                              date_from=data['date_from'],
                              date_to=data['date_to'],
                              state=data['state'])
                        )

                    raise ValidationError(_(
                        "You've already booked time off which overlaps with this period:\n%s",
                        "\n".join(conflicting_holidays_strings)
                    ))

                for data in conflicting_holidays_list:
                    conflicting_holidays_strings.append(
                        "\n" + _('%(employee_name)s - from %(date_from)s to %(date_to)s - %(state)s',
                                 employee_name=data['employee_name'],
                                 date_from=data['date_from'],
                                 date_to=data['date_to'],
                                 state=data['state'])
                    )

                raise ValidationError(_(
                    "An employee already booked time off which overlaps with this period:%s",
                    "".join(conflicting_holidays_strings)
                ))

    # def action_validate(self):
    #     res = super().action_validate()

    def action_validate(self, check_state=True):
        res = super().action_validate(check_state)

        encashed_leaves = self.filtered(lambda l: l.leave_encashed_check)

        if encashed_leaves:
            resource_leaves = self.env['resource.calendar.leaves'].search([
                ('holiday_id', 'in', encashed_leaves.ids)
            ])
            resource_leaves.unlink()

        return res
