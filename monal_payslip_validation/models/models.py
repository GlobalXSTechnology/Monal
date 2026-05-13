from odoo import models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.constrains('employee_id', 'date_from', 'struct_id')
    def _check_duplicate_payslip(self):
        for slip in self:
            if not slip.employee_id or not slip.date_from or not slip.struct_id:
                continue

            month_start = slip.date_from.replace(day=1)
            month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)

            slips = self.search([
                ('id', '!=', slip.id),
                ('employee_id', '=', slip.employee_id.id),
                ('state', '!=', 'cancel'),
                ('date_from', '>=', month_start),
                ('date_to', '<=', month_end),
            ])

            allowance_slips = slips.filtered(
                lambda s: 'Allowance Structure' in s.struct_id.name
            )
            non_allowance_slips = slips.filtered(
                lambda s: 'Allowance Structure' not in s.struct_id.name
            )

            if 'Allowance Structure' in slip.struct_id.name and allowance_slips:
                existing = allowance_slips[0]
                raise ValidationError(_(
                    "An Allowance Structure payslip ('%s') for employee '%s' already exists "
                    "for this month (%s - %s)."
                ) % (
                                          existing.struct_id.name,
                                          slip.employee_id.name,
                                          existing.date_from,
                                          existing.date_to
                                      ))

            if 'Allowance Structure' not in slip.struct_id.name and non_allowance_slips:
                existing = non_allowance_slips[0]
                raise ValidationError(_(
                    "A payslip with structure '%s' for employee '%s' already exists "
                    "for this month (%s - %s)."
                ) % (
                                          existing.struct_id.name,
                                          slip.employee_id.name,
                                          existing.date_from,
                                          existing.date_to
                                      ))

            if len(slips) >= 2:
                raise ValidationError(_(
                    "Multiple payslips are not allowed for employee '%s' in the same month "
                    "(%s - %s). Only one Allowance payslip and one additional payslip "
                    "with a different structure can be created."
                ) % (
                                          slip.employee_id.name,
                                          month_start,
                                          month_end
                                      ))
