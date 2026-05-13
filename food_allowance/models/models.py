from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError
import calendar


class FoodAllowance(models.Model):
    _name = 'food.allowances'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    food_line_template = fields.One2many('food.allowances.line', 'food_template', string='Food Allowance Line Template')
    food_subline_template = fields.Many2one('food.allowances.subline', string='Food Allowance Subline Template')

    name = fields.Char(string='Name', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, tracking=True, readonly=True,
                                 default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', string='Department', tracking=True)
    date = fields.Date(string='Date', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='State', default='draft', tracking=True)

    month = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string="Month",
        required=True,
        tracking=True
    )
    month_start_date = fields.Date(string='Month start Date ', tracking=True)
    month_end_date = fields.Date(string='Month End Date', tracking=True)

    def _get_month_selection(self):
        months = [
            ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
            ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        month_selection = []
        for year in range(2025, 2041):
            for code, name in months:
                month_selection.append((f'{year}-{code}', f'{name} {year}'))
        return month_selection

    @api.onchange('month')
    def _onchange_month(self):
        if self.month:
            year, month = map(int, self.month.split('-'))
            self.month_start_date = f'{year}-{month:02d}-01'
            self.date = self.month_start_date
            last_day = calendar.monthrange(year, month)[1]
            self.month_end_date = f'{year}-{month:02d}-{last_day}'

    def fetch_employees(self):
        for rec in self:
            if not rec.company_id:
                raise ValidationError('Please Select Company')

            # domain = [('company_id', '=', rec.company_id.id)]
            contract_domain = [
            ('company_id', '=', rec.company_id.id),
            ('state', '=', 'open'),  # only running contracts
            ('x_studio_allow_food_allowance', '=', True),]
                
            if rec.department_id:
                contract_domain.append(('department_id', '=', rec.department_id.id))
            contracts = self.env['hr.contract'].search(contract_domain)

            # employees = self.env['hr.employee'].search(domain)
            employees = contracts.mapped('employee_id')
            rec.food_line_template.unlink()
            for index, emp in enumerate(employees, start=1):
                self.env['food.allowances.line'].create({
                    'food_template': rec.id,
                    'employee_id': emp.id,
                    'sr_no': str(index),
                })
            # for emp in employees:
            #     self.env['food.allowances.line'].create({
            #         'food_template': rec.id,
            #         'employee_id': emp.id,
            #     })
            rec.message_post(
                body=f"Employees fetched successfully: {len(employees)} employees are fetched.",
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

    def done_button(self):
        self.state = 'done'

    def create(self, vals):
        if isinstance(vals, list):
            for val in vals:
                if not val.get('name'):
                    val['name'] = self.env['ir.sequence'].next_by_code('seq.food.allowance') or '/'
        else:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('seq.food.allowance') or '/'
        return super(FoodAllowance, self).create(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("You can only delete Food Allowances in Draft state.")

        return super(FoodAllowance, self).unlink()


class FoodAllowanceLine(models.Model):
    _name = 'food.allowances.line'

    food_template = fields.Many2one('food.allowances', string='Food Allowance Template', ondelete='cascade')
    food_subline_template = fields.One2many('food.allowances.subline', 'food_line_template',
                                            string='Food Allowance Subline Template', ondelete='cascade')
    sr_no = fields.Char(string='Sr No', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    total_amount = fields.Float(string='Total', compute='get_total_allowances')
    state = fields.Selection(related='food_template.state', store=True, readonly=True)

    @api.depends('food_subline_template.rest_amount')
    def get_total_allowances(self):
        for rec in self:
            rec.total_amount = sum(rec.food_subline_template.mapped('rest_amount'))

    def open_line_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Food Allowance Line',
            'view_mode': 'form',
            'res_model': 'food.allowances.line',
            'res_id': self.id,
            'target': 'new',
        }


class FoodAllowanceSubline(models.Model):
    _name = 'food.allowances.subline'

    food_template = fields.Many2one('food.allowances', string='Food Allowance Template', ondelete='cascade')
    food_line_template = fields.Many2one('food.allowances.line', string='Food Allowance Line Template',
                                         ondelete='cascade')

    rest_id = fields.Many2one('restaurant.list', string='Restaurant', required=True)
    rest_amount = fields.Float(string='Amount', required=True)


class AllowanceData(models.Model):
    _name = 'restaurant.list'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
