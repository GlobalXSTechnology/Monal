from odoo import models, fields, api
from odoo.exceptions import UserError

class HrPayslip(models.Model):
    _inherit = 'emp.attendance.deduction'


    def create(self, vals):
        vals_list = vals if isinstance(vals, list) else [vals]
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.env.company.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            for val in vals_list:
                date = val.get('date')
                if date:
                    date_in = fields.Date.to_date(date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Records before {lock_date.lock_date} cannot be created.")

        return super().create(vals_list)

    def write(self, vals):
        lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.env.company.id)], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.date:
                    date_in = fields.Date.to_date(rec.date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Records before {lock_date.lock_date} cannot be modified.")
        return super().write(vals)

    def unlink(self):
        lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.env.company.id)], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.date:
                    date_in = fields.Date.to_date(rec.date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Records before {lock_date.lock_date} cannot be deleted.")
        return super().unlink()