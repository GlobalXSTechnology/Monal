from odoo import models, fields, api
from odoo.exceptions import UserError

class AdvanceSalary(models.Model):
    _inherit = 'employee.increment'

    def create(self, vals):
        vals_list = vals if isinstance(vals, list) else [vals]
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.env.company.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            for val in vals_list:
                date = val.get('request_date')
                if date:
                    date_in = fields.Date.to_date(date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Increment records before {lock_date.lock_date} cannot be created.")

        return super().create(vals_list)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     lock_date = self.env['lock.date'].search([('state','=','done')], limit=1, order='lock_date desc')
    #     if lock_date:
    #         for vals in vals_list:
    #             if vals.get('request_date'):
    #                 date_in = fields.Date.to_date(vals['request_date'])
    #                 if date_in < lock_date.lock_date:
    #                     raise UserError(
    #                         f"Advances cannot be created before lock date {lock_date.lock_date}"
    #                     )
    #     return super().create(vals_list)

    def write(self, vals):
        lock_date = self.env['lock.date'].search([('state','=','done')], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.request_date:
                    date_in = fields.Date.to_date(rec.request_date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Increment records  before {lock_date.lock_date} cannot be modified.")
        return super().write(vals)

    def unlink(self):
        lock_date = self.env['lock.date'].search([('state','=','done')], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.request_date:
                    date_in = fields.Date.to_date(rec.request_date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Increment records  before {lock_date.lock_date} cannot be deleted.")
        return super().unlink()