from odoo import models, fields, api
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        # Add context to skip validation
        self = self.with_context(skip_advance_lock_check=True)
        return super().action_payslip_done()
    def action_payslip_cancel(self):
        # Add context to skip validation
        self = self.with_context(skip_advance_lock_check=True)
        return super().action_payslip_cancel()
    def action_payslip_draft(self):
        # Add context to skip validation
        self = self.with_context(skip_advance_lock_check=True)
        return super().action_payslip_draft()
    def action_payslip_paid(self):
        # Add context to skip validation
        self = self.with_context(skip_advance_lock_check=True)
        return super().action_payslip_paid()

    def payslip_hr_approval(self):
        return super(HrPayslip, self.with_context(
            skip_advance_lock_check=True
        )).payslip_hr_approval()

    def payslip_audit_approval(self):
        return super(HrPayslip, self.with_context(
            skip_advance_lock_check=True
        )).payslip_audit_approval()

    def create(self, vals):
        vals_list = vals if isinstance(vals, list) else [vals]
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.env.company.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            for val in vals_list:
                date = val.get('date_from')
                if date:
                    date_in = fields.Date.to_date(date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Payslips before {lock_date.lock_date} cannot be created.")

        return super().create(vals_list)

    # @api.constrains('date_from')
    # def constrains_date_from(self, vals):
    #     lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.company_id.id)], limit=1, order='lock_date desc')
    #     if lock_date:
    #         for rec in self:
    #             if rec.date_from and rec.date_from < lock_date.lock_date:
    #                 raise UserError(f"Payslips before {lock_date.lock_date} cannot be modified.")

    def write(self, vals):
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.company_id.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date and not vals.get('state'):
            for rec in self:
                if rec.date_from and rec.date_from < lock_date.lock_date:
                    raise UserError(f"Payslips before {lock_date.lock_date} cannot be modified.")
        return super().write(vals)

    def unlink(self):
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.company_id.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.date_from and rec.date_from < lock_date.lock_date:
                    raise UserError(f"Payslips before {lock_date.lock_date} cannot be deleted.")
        return super().unlink()
