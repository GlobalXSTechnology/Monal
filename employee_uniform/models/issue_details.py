from odoo import models, fields, api, _


class EmployeeUniformIssuedWizard(models.TransientModel):
    _name = 'employee.uniform.issued.wizard'
    _description = 'Uniform Issued Wizard'

    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    new_line_ids = fields.One2many('employee.uniform.issued.line.wizard', 'wizard_id', string="New Items")
    used_line_ids = fields.One2many('employee.uniform.issued.line.wizard', 'wizard_id', string="Used / Issue Items")
    return_line_ids = fields.One2many('employee.uniform.issued.line.wizard', 'wizard_id', string="Returned Items")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('employee_id'):
            employee = self.env['hr.employee'].browse(self._context['employee_id'])
            new_lines, used_lines, return_lines = [], [], []
            for line in employee.uniform_line_ids.sorted(lambda l: l.uniform_id.distribution_date):
                vals = {
                    'product_id': line.product_id.id,
                    'quantity': line.done_quantity or line.quantity,  # Use done_quantity if available
                    'distribution_date': line.uniform_id.distribution_date,
                    'check_filter': line.check_filter,
                    'uniform_ref': line.uniform_id.name,
                }
                if line.check_filter == 'new':
                    new_lines.append((0, 0, vals))
                elif line.check_filter == 'used':
                    used_lines.append((0, 0, vals))
                elif line.check_filter == 'return':
                    return_lines.append((0, 0, vals))
            res.update({
                'employee_id': employee.id,
                'new_line_ids': new_lines,
                'used_line_ids': used_lines,
                'return_line_ids': return_lines,
            })
        return res


class EmployeeUniformIssuedLineWizard(models.TransientModel):
    _name = 'employee.uniform.issued.line.wizard'
    _description = 'Uniform Issued Wizard Line'

    wizard_id = fields.Many2one('employee.uniform.issued.wizard', string="Wizard", required=True)
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    quantity = fields.Float(string="Quantity", readonly=True)
    distribution_date = fields.Date(string="Distribution Date", readonly=True)
    check_filter = fields.Selection([
        ('new', 'Replace'),
        ('used', 'Issue'),
        ('return', 'Return'),
    ], string="Type", readonly=True)
    uniform_ref = fields.Char(string="Reference No", readonly=True)
