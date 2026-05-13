from odoo import models, fields, api
from odoo.exceptions import UserError


class AdvanceSalary(models.Model):
    _inherit = 'hr.advance.salary'

    def create(self, vals):
        vals_list = vals if isinstance(vals, list) else [vals]
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.env.company.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            for val in vals_list:
                request_date = val.get('request_date')
                month = val.get('month')
                if request_date:
                    date_in = fields.Date.to_date(request_date)
                    lock_month = lock_date.lock_date.strftime('%Y-%m')
                    if date_in < lock_date.lock_date or month < lock_month:
                        raise UserError(f"Advances before {lock_date.lock_date} cannot be created.")

        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('skip_advance_lock_check'):
            return super().write(vals)
        referral_fields = {'x_studio_referral_1', 'x_studio_referral_2'}
        is_only_referral_update = set(vals.keys()).issubset(referral_fields)

        if not is_only_referral_update:
            lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.company_id.id)],
                                                     limit=1, order='lock_date desc')
            if lock_date:
                for rec in self:
                    if rec.request_date:
                        date_in = fields.Date.to_date(rec.request_date)
                        lock_month = lock_date.lock_date.strftime('%Y-%m')
                        if date_in < lock_date.lock_date or rec.month < lock_month:
                            raise UserError(f"Advances before {lock_date.lock_date} cannot be modified.")
        return super().write(vals)

    def unlink(self):
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.company_id.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.request_date:
                    date_in = fields.Date.to_date(rec.request_date)
                    lock_month = lock_date.lock_date.strftime('%Y-%m')
                    if date_in < lock_date.lock_date or rec.month < lock_month:
                        raise UserError(f"Advances before {lock_date.lock_date} cannot be deleted.")
        return super().unlink()
