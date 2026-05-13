from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class GlobalInputs(models.Model):
	_name = 'global.input'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Global Input'
	
	name = fields.Char('Name', store=True)
	date_to = fields.Date(string='Date To', required=True)
	date_from = fields.Date(string='Date From', required=True)
	apply_by = fields.Selection([
		('batch', "Batch"),
		('dpt', "Department"),
		('comp', "Company"),
		('emp', "Employees"),
	], string="Apply Inputs By", default='batch')
	state = fields.Selection([
		('draft', 'Draft'),
		('done', 'Done'), ], )
	batch_id = fields.Many2one('hr.payslip.run', 'Batch')
	department_id = fields.Many2one('hr.department', 'Department')
	company_id = fields.Many2one('res.company', 'Company')
	is_emp = fields.Boolean('By Employee', compute='set_emp', store=True)
	is_service = fields.Boolean('Service')
	amount = fields.Float('Amount')
	input_line_ids = fields.One2many(
		'global.input.line', 'input_id', string='Payslip Inputs', store=True,
		readonly=False)
	input_type_id = fields.Many2one('hr.payslip.input.type', string='Type')
	
	
	def set_draft(self):
		self.write({'state': 'draft'})
	
	@api.depends('apply_by')
	def set_emp(self):
		if self.apply_by == 'emp':
			self.is_emp = True
		else:
			self.is_emp = False
	
	@api.onchange('apply_by')
	def onchangeapply(self):
		# self.employee = None
		self.company_id = None
		self.batch_id = None
		self.department_id = None
	
	def add_inputs(self):
		list = []
		input_list = {}
		if self.batch_id:
			batch_payslip = self.env['hr.payslip'].search(
				[('payslip_run_id', '=', self.batch_id.id), ('date_to', '<=', self.date_to),
				 ('date_from', '>=', self.date_from),
				 ('state', 'not in', ['done', 'refuse', 'paid'])])
			print(batch_payslip)
			for rec in self.input_line_ids:
				input_list = \
					(0, 0, {
						"name": rec.name,
						"input_type_id": rec.input_type_id.id,
						"sequence": rec.sequence,
						"code": rec.code,
						"amount": rec.amount
						
					})
				list.append(input_list)
			print(list)
			for slips in batch_payslip:
				print(slips)
				slips.write({"input_line_ids": list})
				slips.compute_sheet()
			self.state = 'done'
		
		elif self.company_id:
			cop_payslip = self.env['hr.payslip'].search(
				[('company_id', '=', self.company_id.id), ('state', '=', 'verify')])
			for rec in self.input_line_ids:
				input_list = \
					(0, 0, {
						"name": rec.name,
						"input_type_id": rec.input_type_id.id,
						"sequence": rec.sequence,
						"code": rec.code,
						"amount": rec.amount
						
					})
				list.append(input_list)
			print(list)
			for slips in cop_payslip:
				print(slips)
				slips.write({"input_line_ids": list})
				slips.compute_sheet()
			self.state = 'done'
		
		
		elif self.department_id:
			dep_payslip = self.env['hr.payslip'].search(
				[('department_id', '=', self.contract_id.department_id.id), ('state', '=', 'verify')])
			for rec in self.input_line_ids:
				input_list = \
					(0, 0, {
						"name": rec.name,
						"input_type_id": rec.input_type_id.id,
						"sequence": rec.sequence,
						"code": rec.code,
						"amount": rec.amount
						
					})
				list.append(input_list)
			print(list)
			for slips in dep_payslip:
				print(slips)
				slips.write({"input_line_ids": list})
				slips.compute_sheet()
			self.state = 'done'
		
		elif self.apply_by == 'emp':
			for rec in self.input_line_ids:
				emp_payslip = self.env['hr.payslip'].search(
					[('employee_id', '=', rec.employee_id.id), ('state', '=', 'verify')])
				my_list = []
				print(emp_payslip)
				if emp_payslip:
					input_list = \
						(0, 0, {
							"name": rec.name,
							"input_type_id": rec.input_type_id.id,
							"sequence": rec.sequence,
							"code": rec.code,
							"amount": rec.amount
							
						})
					my_list.append(input_list)
					for slip in emp_payslip:
						slip.write({"input_line_ids": my_list})
						slip.compute_sheet()
				else:
					continue
			self.state = 'done'
		
		else:
			raise ValidationError(_('Unable to find any payslip to perform action on.'))
	
	def name_get(self):
		"""
		name_get that supports displaying location name and model as prefix
		"""
		result = []
		for rec in self:
			if rec.company_id == 1:
				if rec.customer_rank > 0 or rec.supplier_rank > 0:
					# result.append((rec.id , + rec.product_category_code))
					name = "%s - %s" % (rec.product_category_code, rec.name)
					result.append((rec.id, name))
				else:
					name = "%s" % (rec.name)
					result.append((rec.id, name))
			else:
				name = "%s" % (rec.name)
				result.append((rec.id, name))
		print(result)
		return result
	
	@api.onchange('batch_id', 'amount', 'date_from', 'date_to')
	def _onchange_batch_summary(self):
		if self.apply_by != 'batch':
			return
		
		if not (self.batch_id and self.date_from and self.date_to and self.amount):
			self.input_line_ids = [(5, 0, 0)]
			return
		
		payslips = self.env['hr.payslip'].search([
			('payslip_run_id', '=', self.batch_id.id),
			('date_from', '>=', self.date_from),
			('date_to', '<=', self.date_to),
		])
		
		emp_records = payslips.mapped('employee_id')
		if not emp_records:
			raise ValidationError(_('No payslip employees found for selected batch.'))
		
		attendance_obj = self.env['hr.attendance']
		employee_attendance_map = {}
		total_attendance_days = 0
		
		for emp in emp_records:
			records = attendance_obj.search([
				('employee_id', '=', emp.id),
				('check_in', '>=', self.date_from),
				('check_in', '<=', self.date_to),
			])
			unique_days = set(att.check_in.date() for att in records if att.check_in)
			attendance_count = len(unique_days)
			employee_attendance_map[emp.id] = attendance_count
			total_attendance_days += attendance_count
		
		if total_attendance_days == 0:
			raise ValidationError(_('Total attendance days is zero.'))
		
		amount_per_day = self.amount / total_attendance_days
		
		total_distributed_amount = 0.0
		for emp_id, days in employee_attendance_map.items():
			total_distributed_amount += days * amount_per_day
		
		self.input_line_ids = [(5, 0, 0), (0, 0, {
			'employee_id': False,
			'attendance': total_attendance_days,
			'amount': round(total_distributed_amount, 2),
			'name': _('Batch %s', self.batch_id.name),
			'input_type_id': self.input_type_id.id if self.input_type_id else False,
		})]
	
	@api.onchange('department_id', 'amount', 'date_from', 'date_to')
	def _onchange_department_id_or_amount(self):
		if self.apply_by != 'dpt' or not self.department_id or not self.amount:
			self.input_line_ids = [(5, 0, 0)]
			return
		
		if not self.date_from or not self.date_to:
			raise ValidationError(_('Please set the date range first.'))
		
		payslips = self.env['hr.payslip'].search([
			('department_id', '=', self.department_id.id),
			('date_from', '>=', self.date_from),
			('date_to', '<=', self.date_to),
		])
		
		employee_ids = list(set(payslips.mapped('employee_id')))
		if not employee_ids:
			raise ValidationError(_('No payslips found for this department and date range.'))
		
		attendance_obj = self.env['hr.attendance']
		employee_attendance_map = {}
		total_attendance_days = 0
		
		for emp in employee_ids:
			attendances = attendance_obj.search([
				('employee_id', '=', emp.id),
				('check_in', '>=', self.date_from),
				('check_in', '<=', self.date_to)
			])
			unique_days = set(att.check_in.date() for att in attendances if att.check_in)
			attendance_count = len(unique_days)
			employee_attendance_map[emp.id] = attendance_count
			total_attendance_days += attendance_count
		
		if total_attendance_days == 0:
			raise ValidationError(_('Total attendance days is zero.'))
		
		amount_per_day = self.amount / total_attendance_days
		
		total_distributed_amount = 0.0
		for days in employee_attendance_map.values():
			total_distributed_amount += days * amount_per_day
		
		self.input_line_ids = [(5, 0, 0), (0, 0, {
			'employee_id': False,
			'attendance': total_attendance_days,
			'amount': round(total_distributed_amount, 2),
			'name': _('Department %s', self.department_id.name),
			'input_type_id': self.input_type_id.id if self.input_type_id else False,
		})]
	
	@api.onchange('apply_by', 'company_id', 'date_from', 'date_to', 'amount')
	def _onchange_company_apply(self):
		if self.apply_by != 'comp' or not (self.company_id and self.date_from and self.date_to and self.amount):
			self.input_line_ids = [(5, 0, 0)]
			return
		
		payslips = self.env['hr.payslip'].search([
			('company_id', '=', self.company_id.id),
			('date_from', '>=', self.date_from),
			('date_to', '<=', self.date_to),
		])
		
		employee_ids = payslips.mapped('employee_id')
		if not employee_ids:
			raise ValidationError("No employee payslips found for selected company and date range.")
		
		attendance_obj = self.env['hr.attendance']
		employee_attendance_map = {}
		total_attendance_days = 0
		
		for emp in employee_ids:
			records = attendance_obj.search([
				('employee_id', '=', emp.id),
				('check_in', '>=', self.date_from),
				('check_in', '<=', self.date_to),
			])
			unique_days = set(att.check_in.date() for att in records if att.check_in)
			attendance_count = len(unique_days)
			employee_attendance_map[emp.id] = attendance_count
			total_attendance_days += attendance_count
		
		if total_attendance_days == 0:
			raise ValidationError("Total attendance days is zero for selected employees.")
		
		amount_per_day = self.amount / total_attendance_days
		
		total_distributed_amount = 0.0
		for days in employee_attendance_map.values():
			total_distributed_amount += days * amount_per_day
		
		self.input_line_ids = [(5, 0, 0), (0, 0, {
			'employee_id': False,
			'attendance': total_attendance_days,
			'amount': round(total_distributed_amount, 2),
			'name': _('Company %s', self.company_id.name),
			'input_type_id': self.input_type_id.id if self.input_type_id else False,
		})]
	
	@api.onchange('amount', 'input_line_ids')
	def _onchange_distribute_amount(self):
		total_attendance = sum(line.attendance for line in self.input_line_ids if line.attendance)
		if total_attendance > 0:
			per_day_amount = self.amount / total_attendance
			for line in self.input_line_ids:
				line.amount = line.attendance * per_day_amount
		else:
			for line in self.input_line_ids:
				line.amount = 0.0


class GlobalInputLine(models.Model):
	_name = 'global.input.line'
	
	name = fields.Char(string="Description")
	input_id = fields.Many2one('global.input', string='Global Input', ondelete='cascade', index=True)
	sequence = fields.Integer(required=True, index=True, default=10)
	input_type_id = fields.Many2one('hr.payslip.input.type', string='Type', required=True, )
	# _allowed_input_type_ids = fields.Many2many('hr.payslip.input.type',
	#                                            related='payslip_id.struct_id.input_line_type_ids')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	attendance = fields.Integer(string='Attendance')
	code = fields.Char(related='input_type_id.code', required=True,
	                   help="The code that can be used in the salary rules")
	
	amount = fields.Float(
		string="Count",
		help="It is used in computation. E.g. a rule for salesmen having 1%% commission of basic salary per product can defined in expression like: result = inputs.SALEURO.amount * contract.wage * 0.01.")
	
	
	
	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if self.employee_id and self.input_id.date_from and self.input_id.date_to and self.input_id.is_service:
			attendances = self.env['hr.attendance'].search([
				('employee_id', '=', self.employee_id.id),
				('check_in', '>=', self.input_id.date_from),
				('check_in', '<=', self.input_id.date_to)
			])
			unique_days = set(att.check_in.date() for att in attendances if att.check_in)
			self.attendance = len(unique_days)
			self.input_id._onchange_distribute_amount()
	
	
	@api.model
	def create(self, vals):
		if not vals.get('input_type_id') and vals.get('input_id'):
			parent = self.env['global.input'].browse(vals['input_id'])
			if parent.apply_by == 'emp' and parent.is_service and parent.input_type_id:
				vals['input_type_id'] = parent.input_type_id.id
		return super().create(vals)
	
	@api.onchange('input_id')
	def _onchange_input_id(self):
		if self.input_id and self.input_id.input_type_id and self.input_id.apply_by == 'emp' and self.input_id.is_service:
			if not self.input_type_id:
				self.input_type_id = self.input_id.input_type_id
