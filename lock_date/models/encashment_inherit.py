from odoo import models, fields, api
from odoo.exceptions import UserError

class HrPayslip(models.Model):
    _inherit = 'leave.encashment'

    def create(self, vals):
        vals_list = vals if isinstance(vals, list) else [vals]
        lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.env.company.id)], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.month_start_date:
                    date_in = fields.Date.to_date(rec.month_start_date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Encashments before {lock_date.lock_date} cannot be modified.")

        # if lock_date:
        #     for val in vals_list:
        #         period_id = val.get('month') or val.get('period_id')
        #         print(period_id)
        #         if period_id:
        #             period = self.env['monal.evaluation.period'].browse(period_id)
        #             print(period)
        #             if period and period.period_start_date:
        #                 print(period.period_start_date)
        #                 date_in = fields.Date.to_date(period.period_start_date)
        #                 if date_in < lock_date.lock_date:
        #                     raise UserError(
        #                         f"Encashments cannot be created before lock date {lock_date.lock_date}"
        #                     )
        return super().create(vals_list)

    def write(self, vals):
        lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.env.company.id)], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.month_start_date:
                    date_in = fields.Date.to_date(rec.month_start_date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Encashments before {lock_date.lock_date} cannot be modified.")
        return super().write(vals)

    def unlink(self):
        lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.env.company.id)], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.month_start_date:
                    date_in = fields.Date.to_date(rec.month_start_date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Encashments before {lock_date.lock_date} cannot be deleted.")
        return super().unlink()
