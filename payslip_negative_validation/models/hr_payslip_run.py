from odoo import models
from odoo.exceptions import ValidationError


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_hr_approval(self):
        for rec in self:
            negative_slips = []

            for slip in rec.slip_ids:
                net_line = slip.line_ids.filtered(lambda l: l.code == 'NET')
                net_amount = sum(net_line.mapped('total'))

                if net_amount < 0:
                    slip_name = slip.number or slip.name or 'Unknown Slip'
                    employee = slip.employee_id.name or ''
                    negative_slips.append(f"{slip_name} - {employee}")

            if negative_slips:
                raise ValidationError(
                    "Following payslips have negative Net Salary:\n\n%s"
                    % "\n".join(negative_slips)
                )

        return super().action_hr_approval()


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def payslip_hr_approval(self):
        for slip in self:
            # Get NET salary
            net_line = slip.line_ids.filtered(lambda l: l.code == 'NET')
            net_amount = sum(net_line.mapped('total'))

            if net_amount < 0:
                raise ValidationError(
                    f"Payslip  Cannot  be Approved with  Negative Net Salary."
                )

        return super().payslip_hr_approval()
