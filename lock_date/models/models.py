from odoo import models, fields, api
from odoo.exceptions import UserError



class LockDate(models.Model):
    _name = 'lock.date'
    _inherit = ['mail.thread']


    lock_date = fields.Date(string='Date', tracking=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', tracking=True, default=lambda self:self.env.company.id)
    state = fields.Selection([('draft','Draft'),('done','Done')], string='State', tracking=True, default='draft')

    def done_button(self):
        for rec in self:
            rec.state = 'done'

    def reset_button(self):
        for rec in self:
            rec.state = 'draft'

    @api.constrains('company_id')
    def _check_unique_company(self):
        for rec in self:
            existing = self.search([
                ('company_id', '=', rec.company_id.id),
                ('id', '!=', rec.id)
            ], limit=1)
            if existing:
                raise UserError(f"A lock date already exists for company {rec.company_id.name} 🧱")

