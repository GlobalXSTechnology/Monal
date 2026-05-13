from odoo import models, fields, api
from odoo.exceptions import UserError

class HrPayslip(models.Model):
    _inherit = 'hr.leave.allocation'

    def create(self, vals):
        vals_list = vals if isinstance(vals, list) else [vals]
        lock_date = self.env['lock.date'].search([('state', '=', 'done'), ('company_id', '=', self.env.company.id)],
                                                 limit=1, order='lock_date desc')
        if lock_date:
            for val in vals_list:
                # date = val.get('date_from')
                allocation_date = val.get('month_start_date') or val.get('date_from')
                if allocation_date:
                    date_in = fields.Datetime.to_datetime(allocation_date).date()
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Allocations before {lock_date.lock_date} cannot be created.")

        return super().create(vals_list)


    @api.constrains('date_from')
    def constrains_date_from(self):
        lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.env.company.id)], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                # if rec.date_from:
                allocation_date = rec.month_start_date or rec.date_from
                if allocation_date:
                    date_in = fields.Date.to_date(allocation_date)
                    # date_in = fields.Date.to_date(rec.date_from)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Allocations before {lock_date.lock_date} cannot be modified.")

    # def write(self, vals):
    #     lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.env.company.id)], limit=1, order='lock_date desc')
    #     if lock_date:
    #         for rec in self:
    #             if rec.date_from:
    #                 date_in = fields.Date.to_date(rec.date_from)
    #                 if date_in < lock_date.lock_date:
    #                     raise UserError(f"Allocations before {lock_date.lock_date} cannot be modified.")
                    
        # return super().write(vals)

    def unlink(self):
        lock_date = self.env['lock.date'].search([('state','=','done'),('company_id','=', self.env.company.id)], limit=1, order='lock_date desc')
        if lock_date:
            for rec in self:
                if rec.employee_id.bypass_allocation_lock:
                    continue
                # if rec.date_from:
                #     date_in = fields.Date.to_date(rec.date_from)
                allocation_date = rec.month_start_date or rec.date_from

                if allocation_date:
                    date_in = fields.Date.to_date(allocation_date)
                    if date_in < lock_date.lock_date:
                        raise UserError(f"Allocations before {lock_date.lock_date} cannot be deleted.")
        return super().unlink()


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    bypass_allocation_lock = fields.Boolean(default=False)

    def write(self, vals):
        if 'active' in vals:
            if vals['active'] is False:
                vals['bypass_allocation_lock'] = True
            else:
                vals['bypass_allocation_lock'] = False

        return super().write(vals)