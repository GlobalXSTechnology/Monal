from odoo import models, fields, api
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip.run'

    def action_payslip_done(self):
        # Add context to skip validation
        self = self.with_context(skip_advance_lock_check=True)
        return super().action_payslip_done()

    def action_hr_approval(self):
        return super(HrPayslip, self.with_context(
            skip_advance_lock_check=True
        )).action_hr_approval()

    def action_confirm(self):
        return super(HrPayslip, self.with_context(
            skip_advance_lock_check=True
        )).action_confirm()

    def action_draft(self):
        return super(HrPayslip, self.with_context(
            skip_advance_lock_check=True
        )).action_draft()

    def action_audit_approval(self):
        return super(HrPayslip, self.with_context(
            skip_advance_lock_check=True
        )).action_audit_approval()

    def create(self, vals):
        vals_list = vals if isinstance(vals, list) else [vals]
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.env.company.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            for val in vals_list:
                date = val.get('date_start')
                if date:
                    date_in = fields.Date.to_date(date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Batches cannot be created before lock date {lock_date.lock_date}")

        return super().create(vals_list)

    def write(self, vals):
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.company_id.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date and not vals.get('state'):
            for rec in self:
                if rec.date_start and rec.date_start < lock_date.lock_date:
                    raise UserError(f"Batches before {lock_date.lock_date} cannot be modified.")
        return super().write(vals)

    def unlink(self):
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.company_id.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.date_start and rec.date_start < lock_date.lock_date:
                    raise UserError(f"Batches before {lock_date.lock_date} cannot be deleted.")
        return super().unlink()


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        # We wrap the call in with_context to pass the bypass flag
        # to any 'write' calls triggered during payslip generation
        return super(HrPayslipEmployees, self.with_context(skip_advance_lock_check=True)).compute_sheet()
