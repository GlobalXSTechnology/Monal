from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import calendar

_logger = logging.getLogger(__name__)


class BulkAdvanceLoanPayment(models.Model):
	_name = 'bulk.loan.payments'

	name = fields.Char('Name')

	journal_id = fields.Many2one("account.journal", string="Journal",domain="[('journal_idd', '=', True)]")
	line_ids = fields.One2many("bulk.loan.payments.line", "loan_payment_id", string="Payment Lines Ids")
	advance_type = fields.Selection([('bank', 'Bank'), ('cash', 'Cash'), ('final_bank_salary', 'Final Bank Salary')],
									string='Type', default=False)
	date = fields.Date(string="Date", default=fields.Date.today)

	available_journal_ids = fields.Many2many(
		"account.journal",
		string="Available Journals",
		readonly=True
	)


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
			last_day = calendar.monthrange(year, month)[1]
			self.month_end_date = f'{year}-{month:02d}-{last_day}'

	# @api.onchange('advance_type')
	# def _onchange_advance_type(self):
	# 	domain = [('journal_idd', '=', True)]
	#
	# 	if self.advance_type == 'cash':
	# 		domain.append(('type', '=', 'cash'))
	# 	elif self.advance_type in ('bank', 'final_bank_salary'):
	# 		domain.append(('type', '=', 'bank'))
	#
	# 	journals = self.env['account.journal'].search(domain)
	#
	# 	self.available_journal_ids = journals
	# 	self.journal_id = False


	@api.onchange('month')
	def _onchange_period(self):
		if not self.month:
			return

		year, month = map(int, self.month.split('-'))
		self.month_start_date = f'{year}-{month:02d}-01'
		last_day = calendar.monthrange(year, month)[1]
		self.month_end_date = f'{year}-{month:02d}-{last_day}'
		self.line_ids = [(5, 0, 0)]


		domain = [
			('payment_start_date', '>=', self.month_start_date),
			('payment_start_date', '<=', self.month_end_date),
			('payment', '=', 'partially'),
			('state', 'in', ['deputy_cfo','ceo']),
		]

		advances = self.env['hr.advance.salary'].search(domain)
		_logger.info(f"advancesssssssssssssssssssss{advances}")
		_logger.info(self.month)
		_logger.info(self.advance_type)

		lines = []
		for adv in advances:
			lines.append((0, 0, {
				'employee_id': adv.employee_id.id,
				'amount_pay': adv.request_amount,
				# 'payment_date': fields.Datetime.now(),
			}))

		self.line_ids = lines



	def action_loan_payments(self):
		if not self.journal_id:
			raise ValidationError(_("Please select a Journal."))

		journal = self.journal_id

		if not journal.default_account_id:
			raise ValidationError(_("Selected journal has no Default Account."))

		move_lines = []
		total_credit = 0.0

		for line in self.line_ids:
			if line.amount_pay <= 0:
				continue

			employee = line.employee_id
			partner = employee.work_contact_id

			if not partner:
				raise ValidationError(
					_("Missing Home Address for employee %s") % employee.name
				)

			hr_advance = self.env['hr.advance.salary'].search([
				('employee_id', '=', employee.id),
				('payment', '=', 'partially'),
				('state', 'in', ['deputy_cfo','ceo'])
			], limit=1)

			if not hr_advance:
				continue

			debit_account = partner.loan_receivable_pf
			if not debit_account:
				raise ValidationError(
					_("Loan Receivable account not set for %s") % employee.name
				)
			advance_ref = hr_advance.name or ''
			line_name = f"{employee.name} - {advance_ref}"

			# Debit line per employee
			move_lines.append((0, 0, {
				'name': line_name,
				'partner_id': partner.id,
				'account_id': debit_account.id,
				'debit': line.amount_pay,
				'credit': 0.0,
			}))

			total_credit += line.amount_pay

			# Update advance salary
			hr_advance.write({
				'state': 'paid',
				'amount_paid': hr_advance.amount_paid + line.amount_pay,
				# 'amount_to_pay': line.amount_pay,
			})

		if not move_lines:
			return True


		# SINGLE credit line
		move_lines.append((0, 0, {
			'name': self.name or 'Bulk Advance Salary Payment',
			'account_id': journal.default_account_id.id,
			'debit': 0.0,
			'credit': total_credit,
		}))

		move_vals = {
			'ref': self.name or 'Bulk Advance Salary Payment',
			'date': self.date,
			'journal_id': journal.id,
			'line_ids': move_lines,
		}

		move = self.env['account.move'].create(move_vals)
		move.action_post()

		return {
			'name': _('Accounting Entry'),
			'type': 'ir.actions.act_window',
			'res_model': 'account.move',
			'res_id': move.id,
			'view_mode': 'form',
			'target': 'current',
		}
	class BulkLoanPaymentLines(models.Model):
		_name = 'bulk.loan.payments.line'

		loan_payment_id = fields.Many2one("bulk.loan.payments", string="Loan Payments")
		employee_id = fields.Many2one("hr.employee", string="Employees")
		batch_id = fields.Char(string="Batch ID", related="employee_id.barcode")
		amount_pay = fields.Float(string="Payment Amount")
		payment_date = fields.Datetime(string="Payment Date", default=datetime.now())
