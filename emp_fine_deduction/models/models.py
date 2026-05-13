import calendar
from odoo import api, models, _, fields
from odoo.exceptions import ValidationError

class EmpAttDeduction(models.Model):
	_name = 'emp.fine.deduction'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Fine Deductions'
	
	name = fields.Char(string="Name")
	employee_id = fields.Many2one("hr.employee", string="Employee")
	date = fields.Date(string="Date")
	amount = fields.Float(string="Amount")
	state = fields.Selection([('draft', 'Draft'), ('approve', 'Approved'), ('refused', 'Refused')], string='Status',
	                         default='draft')
	
	month = fields.Selection(
		selection=lambda self: self._get_month_selection(),
		string="Month",
		required=True,
		tracking=True
	)
	month_start_date = fields.Date(string="Month start Date", readonly=True)
	month_end_date = fields.Date(string="Month end Date", readonly=True)
	
	def _get_month_selection(self):
		months = [
			('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
			('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
			('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
		]
		month_selection = []
		for year in range(2025, 2050):
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
	
	def action_draft(self):
		self.state = 'draft'
		
	def action_approved(self):
		self.state = 'approve'
		
	def action_refused(self):
		self.state = 'refused'
	
	# @api.constrains('employee_id', 'month')
	# def _check_duplicate_month(self):
	# 	for record in self:
	# 		if record.employee_id and record.month:
	# 			domain = [
	# 				('employee_id', '=', record.employee_id.id),
	# 				('month', '=', record.month),
	# 				('id', '!=', record.id)
	# 			]
	# 			duplicate = self.env['emp.fine.deduction'].search_count(domain)
	# 			if duplicate:
	# 				raise ValidationError(
	# 					_('A deduction record already exists for %s for month %s.')
	# 					% (record.employee_id.name, record.month)
	# 				)

