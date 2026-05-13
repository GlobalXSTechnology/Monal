from odoo import models,fields,api
from datetime import datetime


class AttendnceFields(models.Model):
    _inherit = 'hr.attendance'

    @api.depends('check_in')
    def new_date(self):
        for rec in self:
            rec.attend_check_in = datetime.strftime(rec.check_in, '%Y-%m-%d')

    attend_check_in = fields.Date('Hide this check in',compute='new_date',store=True)

