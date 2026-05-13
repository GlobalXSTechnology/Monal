from odoo import models, fields, api
from odoo.exceptions import UserError

class HrPayslip(models.Model):
    _inherit = 'hr.attendance'


    def create(self, vals):
        vals_list = vals if isinstance(vals, list) else [vals]
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.env.company.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            for val in vals_list:
                date = val.get('check_in')
                if date:
                    date_in = fields.Datetime.to_datetime(date).date()
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Attendances before {lock_date.lock_date} cannot be created.")

        return super().create(vals_list)

    @api.constrains('check_in')
    def check_in_constrains(self):
        lock_date = self.env['lock.date'].search(
            [('state', '=', 'done'), ('company_id', '=', self.env.company.id)],
            limit=1, order='lock_date desc'
        )
        if lock_date:
            for rec in self:
                date_in = rec.check_in.date()
                if date_in < lock_date.lock_date:
                    raise UserError(f"Attendances before {lock_date.lock_date} cannot be modified.")

    # def write(self, vals):
    #     lock_date = self.env['lock.date'].search(
    #         [('state', '=', 'done'), ('company_id', '=', self.env.company.id)],
    #         limit=1, order='lock_date desc'
    #     )
    #     if lock_date:
    #         for rec in self:
    #             new_check_in = vals.get('check_in') if 'check_in' in vals else rec.check_in
    #             if new_check_in:
    #                 date_in = fields.Datetime.to_datetime(new_check_in).date()
    #                 if date_in < lock_date.lock_date:
    #                     raise UserError(f"Attendances before {lock_date.lock_date} cannot be modified.")
    #     return super().write(vals)

    def unlink(self):
        lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.env.company.id)], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.check_in:
                    date_in = fields.Date.to_date(rec.check_in)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Attendances before {lock_date.lock_date} cannot be deleted.")
        return super().unlink()
