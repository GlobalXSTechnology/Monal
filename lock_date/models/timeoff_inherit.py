from odoo import models, fields, api
from odoo.exceptions import UserError

class HrPayslip(models.Model):
    _inherit = 'hr.leave'


    @api.constrains('request_date_from', 'request_date_to')
    def constrains_request_date_from(self):
        lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.company_id.id)], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.date_from:
                    date_in = fields.Date.to_date(rec.date_from)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Leaves before {lock_date.lock_date} cannot be modified.")


    def create(self, vals):
        vals_list = vals if isinstance(vals, list) else [vals]
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.env.company.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            for val in vals_list:
                date = val.get('date_from')
                if date:
                    date_in = fields.Datetime.to_datetime(date).date()
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Leaves before {lock_date.lock_date} cannot be created.")

        return super().create(vals_list)

    # def write(self, vals):
    #     lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.company_id.id)], limit=1, order='lock_date desc')
    #     if lock_date:
    #         for rec in self:
    #             if rec.date_from:
    #                 date_in = fields.Date.to_date(rec.date_from)
    #                 if date_in < lock_date.lock_date:
    #                     raise UserError(f"Leaves before {lock_date.lock_date} cannot be modified. ------{rec.request_date_from}-------{rec.id}----{date_in}---{rec.employee_id.name}")
    #     return super().write(vals)

    def unlink(self):
        lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.company_id.id)], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.date_from:
                    date_in = fields.Date.to_date(rec.date_from)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Leaves before {lock_date.lock_date} cannot be deleted.")
        return super().unlink()
