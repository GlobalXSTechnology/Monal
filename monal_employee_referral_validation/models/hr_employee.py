from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date




class HRContract(models.Model):
    _inherit = "hr.contract"

    def write(self, vals):
        if 'date_end' in vals and vals.get('date_end'):
            for contract in self:
                emp = contract.employee_id
                if not emp or not emp.barcode:
                    continue

                badge = emp.barcode
                messages = []
                referred_employees = self.env['hr.employee'].sudo().search([
                    '|',
                    ('x_studio_referral_1.badge_id', '=', badge),
                    ('x_studio_referral_2.badge_id', '=', badge),
                ])

                if referred_employees:
                    details = "\n".join(
                        f"- {e.name} | Badge: {e.barcode} | Company: {e.company_id.name}"
                        for e in referred_employees
                    )
                    messages.append(
                        "🔹 Employee Referrals:\n" + details
                    )

                all_company_ids = self.env['res.company'].sudo().search([]).ids

                referred_advances = (
                    self.env['hr.advance.salary']
                    .sudo()
                    .with_context(allowed_company_ids=all_company_ids)
                    .search([
                        '&',
                        '|',
                        ('x_studio_referral_1.badge_id', '=', badge),
                        ('x_studio_referral_2.badge_id', '=', badge),
                        ('state', 'not in', ['done', 'refuse']),
                    ])
                )

                if referred_advances:
                    details = "\n".join(
                        f"- {a.name} | Employee: {a.employee_id.name} | Company: {a.company_id.name}"
                        for a in referred_advances
                    )
                    messages.append(
                        "🔹 Advance / Loan Referrals:\n" + details
                    )

                if messages:
                    raise ValidationError(
                        "You cannot set End Date for this employee because it is used as a referral in the following records:\n\n"
                        + "\n\n".join(messages)
                    )
                # UniformLine = self.env['employee.uniform.line'].sudo()
                #
                # issue_lines = UniformLine.search([
                #     ('employee_id', '=', emp.id),
                #     ('check_filter', '=', 'used'),
                #     ('uniform_id.distribution_date', '!=', False),
                # ])
                #
                # for issue in issue_lines:
                #     issue_date = fields.Date.to_date(issue.uniform_id.distribution_date)
                #
                #     # 🔥 IMPORTANT FIX: search return ANYWHERE (not same uniform)
                #     returned = UniformLine.search_count([
                #         ('employee_id', '=', emp.id),
                #         ('check_filter', 'in', ('return', 'new')),
                #         ('uniform_id.distribution_date', '>=', issue.uniform_id.distribution_date),
                #     ])
                #
                #     if returned:
                #         continue  # returned → OK
                #
                #     # 6 months rule
                #     allowed_date = issue_date + relativedelta(months=6)
                #     today = date.today()
                #     if today <= allowed_date:
                #         raise ValidationError(
                #             f"❌ Employee {emp.name} has not returned the issued uniform.\n\n"
                #             f"Issue Date: {issue_date}\n"
                #             f"Uniform must be returned within 6 months."
                #         )

                # Asset = self.env['account.asset'].sudo()  # adjust model if needed
                #
                # allocated_assets = Asset.search([
                #     ('asset_loc_id', '=', emp.id),
                #     ('state', 'not in', ('returned', 'disposed', 'cancel')),  # adjust states
                # ])
                #
                # if allocated_assets:
                #     asset_details = "\n".join(
                #         f"- {a.name} | Status: {a.state}"
                #         for a in allocated_assets
                #     )
                #
                #     raise ValidationError(
                #         "❌ You cannot set End Date for this employee because the following assets are still allocated:\n\n"
                #         + asset_details
                #     )


        return super().write(vals)

