from odoo import models, fields, api, _


class EmployeeIncrement(models.Model):
    _name = 'employee.increment'
    _description = 'Employee Salary Increment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    filter_type = fields.Selection([
        ('company', 'Company'),
        ('department', 'Department'),
        ('employee', 'Employee')
    ], string="Filter Type", required=True, default="company")

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        domain=lambda self: [('id', '=', self.env.company.id)],
        required=True,
    )
    department_id = fields.Many2many(
        'hr.department',
        string="Department",
        domain=lambda self: [('company_id', '=', self.env.company.id)],
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        string="Employees",
        domain=lambda self: [('company_id', '=', self.env.company.id)],
    )

    increment_type_set = fields.Selection([
        ('overall', 'Overall'),
        ('individual', 'Individual')
    ], string="Increment Type Mode", required=True, default="overall")

    increment_type = fields.Selection([
        ('percent', 'Percentage (%)'),
        ('amount', 'Fixed Amount')
    ], string="Increment Type", required=True)

    value = fields.Float("Increment Value", required=True)

    line_ids = fields.One2many('employee.increment.line', 'increment_id', string="Increment Lines")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('applied', 'Applied Increment'),
        ('approved', 'Approved')
    ], string="Status", default='draft', tracking=True)
    total_individual_value = fields.Float(
        string="Increment Value",
        compute="_compute_total_individual_value",
        store=True
    )




    @api.onchange('increment_type','filter_type','company_id','department_id','employee_ids','increment_type_set')
    def _onchange_increment_type(self):
        if self.increment_type:
            for line in self.line_ids:
                line.increment_type = self.increment_type

    @api.depends('line_ids.value', 'increment_type_set')
    def _compute_total_individual_value(self):
        for rec in self:
            if rec.increment_type_set == 'individual':
                rec.total_individual_value = sum(rec.line_ids.mapped('value'))
            else:
                rec.total_individual_value = rec.value

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id') or self.env.company.id

        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code('employee.increment') or _(
                'New')

        return super(EmployeeIncrement, self).create(vals)

    @api.onchange('filter_type', 'company_id', 'department_id', 'employee_ids', 'increment_type_set', 'increment_type')
    def _onchange_filters(self):
        employees = self.env['hr.employee']

        if self.filter_type == 'company' and self.company_id:
            employees = employees.search([('company_id', '=', self.company_id.id)])
        elif self.filter_type == 'department' and self.department_id:
            employees = employees.search([('department_id', 'in', self.department_id.ids)])
        elif self.filter_type == 'employee' and self.employee_ids:
            employees = self.employee_ids

        # Only include employees with a valid contract
        employees = employees.filtered(lambda e: e.contract_id and e.contract_id.exists())

        self.line_ids = [(5, 0, 0)]  # clear old lines
        line_vals = []

        for emp in employees:
            if emp:
                vals = {
                    'employee_id': emp.id,
                    'old_salary': emp.contract_id.wage,
                    'increment_type': self.increment_type if self.increment_type_set == 'overall' else 'percent',
                    'value': self.value if self.increment_type_set == 'overall' else 0.0,
                }
                line_vals.append((0, 0, vals))

        if line_vals:
            self.line_ids = line_vals

    def action_apply(self):
        for rec in self:
            for line in rec.line_ids:
                if not line.employee_id or not line.employee_id.contract_id:
                    continue

                # Determine increment
                if rec.increment_type_set == 'overall':
                    inc_type = rec.increment_type
                    inc_value = rec.value
                else:
                    inc_type = line.increment_type
                    inc_value = line.value

                if inc_type == 'percent':
                    increment = (line.old_salary * inc_value) / 100
                else:
                    increment = inc_value

                new_salary = line.old_salary + increment
                line.increment_value = increment
                line.new_salary = new_salary

                contract = line.employee_id.contract_id
                contract.wage = new_salary

                # Log history
                self.env['employee.increment.history'].create({
                    'employee_id': line.employee_id.id,
                    'contract_id': contract.id,
                    'increment_id': rec.id,
                    'date': fields.Date.today(),
                    'old_salary': line.old_salary,
                    'increment_value': increment,
                    'new_salary': new_salary,
                    'note': f"Increment applied via {rec.name}"
                })

            rec.state = 'applied'

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_set_to_draft(self):
        for rec in self:
            for line in rec.line_ids:
                if line.employee_id.contract_id:
                    line.employee_id.contract_id.wage = line.old_salary
            rec.state = 'draft'


class EmployeeIncrementLine(models.Model):
    _name = 'employee.increment.line'
    _description = 'Employee Increment Line'

    increment_id = fields.Many2one('employee.increment', string="Increment Ref", required=True)
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        domain=lambda self: [('company_id', '=', self.env.company.id)]
    )
    old_salary = fields.Float("Old Salary", required=True)
    increment_type = fields.Selection([
        ('percent', 'Percentage (%)'),
        ('amount', 'Fixed Amount')
    ], string="Increment Type", required=True)
    value = fields.Float("Increment Value", required=True)
    increment_value = fields.Float("Applied Increment")
    new_salary = fields.Float("New Salary")
    increment_type_set = fields.Selection(
        related="increment_id.increment_type_set",
        store=True,
        readonly=True
    )




class EmployeeIncrementHistory(models.Model):
    _name = 'employee.increment.history'
    _description = 'Employee Increment History'
    _order = 'date desc'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    contract_id = fields.Many2one('hr.contract', string="Contract")
    increment_id = fields.Many2one('employee.increment', string="Increment Ref")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    old_salary = fields.Float("Old Salary")
    increment_value = fields.Float("Increment Amount")
    new_salary = fields.Float("New Salary")
    note = fields.Char("Notes")


class HrContract(models.Model):
    _inherit = 'hr.contract'

    class HrContract(models.Model):
        _inherit = 'hr.contract'

        increment_history_ids = fields.One2many(
            'employee.increment.history',
            'contract_id',
            string="Increment History",
            domain=[('increment_id.state', '=', 'approved')]
        )


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    increment_history_count = fields.Integer(
        string="Increment History Count",
        compute="_compute_increment_history_count"
    )

    def _compute_increment_history_count(self):
        for emp in self:
            emp.increment_history_count = self.env['employee.increment.history'].search_count([
                ('employee_id', '=', emp.id)
            ])

    def action_view_increment_history(self):
        return {
            'name': "Increment History",
            'type': 'ir.actions.act_window',
            'res_model': 'employee.increment.history',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id}
        }
