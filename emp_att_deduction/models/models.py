import calendar
from odoo import api, models, _, fields
from odoo.exceptions import ValidationError
from datetime import datetime, date

class EmpAttDeduction(models.Model):
	_name = 'emp.attendance.deduction'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Attendance Deductions'
	
	name = fields.Char(string="Name")
	employee_id = fields.Many2one("hr.employee", string="Employee")
	date = fields.Date(string="Date")
	amount = fields.Float(string="Amount", compute="_compute_get_emp_wage", readonly=True)
	state = fields.Selection([('draft', 'Draft'), ('approve', 'Approved'), ('refused', 'Refused')], string='Status',
	                         default='draft')
	
	def action_draft(self):
		self.state = 'draft'
		
	def action_approved(self):
		self.state = 'approve'
		
	def action_refused(self):
		self.state = 'refused'



	@api.depends('employee_id', 'date')
	def _compute_get_emp_wage(self):
		for record in self:
			if record.employee_id and record.date:
				year = record.date.year
				month = record.date.month
				days_in_month = calendar.monthrange(year, month)[1]
				
				working_days = 0
				for day in range(1, days_in_month + 1):
					current_day = date(year, month, day)
					if current_day.weekday() != 6:  # 6 = Sunday
						working_days += 1
				
				contract = self.env['hr.contract'].search([
					('employee_id', '=', record.employee_id.id),
					('state', '=', 'open'),
					('date_start', '<=', record.date),
					'|',
					('date_end', '=', False),
					('date_end', '>=', record.date)
				], limit=1)
				
				if contract and contract.wage and working_days > 0:
					record.amount = round(contract.wage / working_days, 2)
				else:
					record.amount = 0.0
			else:
				record.amount = 0.0
	
	# @api.onchange('employee_id', 'date')
	# def _compute_get_emp_wage(self):
	# 	for record in self:
	# 		if record.employee_id and record.date:
	# 			year = record.date.year
	# 			month = record.date.month
	# 			days_in_month = calendar.monthrange(year, month)[1]
				
	# 			contract = self.env['hr.contract'].search([
	# 				('employee_id', '=', record.employee_id.id),
	# 				('state', '=', 'open'),
	# 				('date_start', '<=', record.date),
	# 				'|',
	# 				('date_end', '=', False),
	# 				('date_end', '>=', record.date)
	# 			], limit=1)
				
	# 			if contract and contract.wage:
	# 				record.amount = round(contract.wage / days_in_month, 2)
	# 			else:
	# 				record.amount = 0.0
	# 		else:
	# 			record.amount = 0.0
	
	@api.constrains('employee_id', 'date')
	def _check_duplicate_date(self):
		for record in self:
			if record.employee_id and record.date:
				domain = [
					('employee_id', '=', record.employee_id.id),
					('date', '=', record.date),
					('id', '!=', record.id)
				]
				duplicate = self.env['emp.attendance.deduction'].search_count(domain)
				if duplicate:
					raise ValidationError(
						_('A deduction record already exists for %s on %s.')
						% (record.employee_id.name, record.date.strftime('%Y-%m-%d'))
					)
