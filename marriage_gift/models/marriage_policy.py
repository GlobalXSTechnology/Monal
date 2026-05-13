from odoo import models, fields, api



class MarriagePolicy(models.Model):
    _name = 'marriage.policy'

    type = fields.Selection([('company', 'Company'), ('department', 'Department')], default='company', string='Company/Department')
    company_id = fields.Many2one("res.company", string='Company')
    department_id = fields.Many2one("hr.department", string='Department')
    minimum_salary = fields.Float(string='Salary')
    service_length = fields.Selection([('one', '1 Year'), ('two', '2 Years'), ('three', '3 Years'), ('four', '3+ Years')], string='Service Length')




