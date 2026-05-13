from odoo import models, fields, api
from odoo.exceptions import UserError

class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.constrains('date_start','date_end')
    def constrains_date_start(self):
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.company_id.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            print('lock date found:', lock_date.lock_date)
            for rec in self:
                if not rec.date_end:
                    print('No End date man')
                    if rec.date_start:
                        print('Date start is there man lets goo')
                        date_in = rec.date_start
                        if date_in < lock_date.lock_date:
                            raise UserError(f"Contracts before {lock_date.lock_date} cannot be modified.")

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
                        raise UserError(f"Contracts before {lock_date.lock_date} cannot be created.")

        return super().create(vals_list)

    # def write(self, vals):
    #     res = super().write(vals)
    #     self.constrains_date_start()
    #     return res
    
    # 
    # def write(self, vals):
    #     lock_date = self.env['lock.date'].search([
    #         ('state', '=', 'done'),
    #         ('company_id', '=', self.env.company.id)
    #     ], limit=1, order='lock_date desc')
    # 
    #     if lock_date:
    #         for rec in self:
    #             new_date = vals.get('date_start') or rec.date_start

    
    #             if new_date:
    #                 date_in = fields.Date.to_date(new_date)
    #                 if date_in < lock_date.lock_date:
    #                     raise UserError(f"Contracts before {lock_date.lock_date} cannot be modified.")
    # 
    #     return super().write(vals)
    # 
    
    def unlink(self):
        lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.company_id.id)], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.date_start:
                    date_in = rec.date_start
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Contracts before {lock_date.lock_date} cannot be deleted.")
        return super().unlink()
