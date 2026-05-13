# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime,date
import odoo.addons.decimal_precision as dp
from dateutil import relativedelta
import logging

_logger = logging.getLogger(__name__)


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure", required=False)


class EmployeeAdvanceSalary(models.Model):
    _name = "hr.advance.salary"
    _description = "Advance Salary Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Reference', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  )
    job_id = fields.Many2one('hr.job', string='Job Title', related='employee_id.job_id', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    readonly=True)
    request_date = fields.Datetime(string='Request Date', required=True, default=datetime.today(), tracking=True)
    request_amount = fields.Float(string='Request Amount', compute='_compute_employee_wage_get', store=True)
    currency_id = fields.Many2one('res.currency', related='employee_id.company_id.currency_id', string='Currency',
                                  readonly=True)
    confirm_date = fields.Datetime(string='Confirmed Date', readonly=True, copy=False)
    confirm_by = fields.Many2one('res.users', string='Confirm By', readonly=True, copy=False)
    approved1_date = fields.Datetime(string='Approved Date(HR)', readonly=True, copy=False)
    approved1_by = fields.Many2one('res.users', string='Approved By(HR)', readonly=True, copy=False)
    approved2_date = fields.Datetime(string='Approved Date(Payroll)', readonly=True, copy=False)
    approved2_by = fields.Many2one('res.users', string='Approved By(Payroll)', readonly=True, copy=False)
    paid_date = fields.Datetime(string='Paid Date', readonly=True)
    paid_by = fields.Many2one('res.users', string='Paid By', readonly=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company)
    payment_id = fields.Many2one('account.payment', string='Payment', readonly=True)
    paid_amount = fields.Float(string='Paid Amount', readonly=True, copy=False)
    payslip_line_ids = fields.One2many('payslip.line', 'advance_salary_id')
    user_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user)
    reason = fields.Text('Reason for Advance', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('approve1', 'Approve'),
        ('approve2', 'Approve'),
        ('paid', 'Paid'),
        ('done', 'Done'),
        ('refuse', 'Refuse'),
    ], default="draft", track_visibility='always')
    payment = fields.Selection([('partially', 'Loan'), ('fully', 'Advance Salary')], string='Payment based on ',
                               default='fully')
    duration_month = fields.Integer('Payment Duration(month)', copy=False)
    amount_paid = fields.Float('Amount Paid', copy=False)
    amount_to_pay = fields.Float('Amount to pay', compute='_compute_amount_to_pay', copy=False, store=True)
    deduction_amount = fields.Float('Deduction Amount', digits=dp.get_precision('Account'), copy=False)
    payment_start_date = fields.Datetime('Payment Start Date', copy=False)
    payment_end_date = fields.Datetime('Payment End Date', copy=False)
    advance_salary_line_ids = fields.One2many('hr.advance.salary.line', 'hr_advance_salary_id', string="Loan line ids")
    loan_calculation = fields.Selection([('auto', 'Auto'), ('manual', 'Manual')], string="Loan Calculation")

    @api.constrains('state')
    def set_adv_function(self):
        for rec in self:
            if rec.state in ['paid','gm_finance']:
                wwww = 0
                old_line = []
                rec.write({'amount_paid': 0})
                rec.write({'amount_to_pay': rec.request_amount})
                if rec.payment == 'fully':
                    rec.write({'deduction_amount': rec.request_amount})
                else:
                    old_line = self.env['hr.advance.salary.line'].search(
                        [('skip', '=', False), ('hr_advance_salary_id', '=', rec.id)], order='date ASC')
                    # raise UserError(old_line)
                    if old_line:
                        rec.write({'deduction_amount': old_line[0].amount})
                    else:
                        rec.write({'deduction_amount': rec.request_amount / rec.duration_month})
                for yi in self.env['payslip.line'].search([('advance_salary_id', '=', rec.id)]):
                    yi.write({'advance_salary_id': False})

                get_slip_lines = self.env['hr.payslip.line'].search(
                    [('slip_id.employee_id', '=', rec.employee_id.id), ('name', '=', rec.name), ('total', '>', 0),
                     ('slip_id.state', 'in', ['done', 'paid'])])
                atteched = rec.payslip_line_ids.mapped('payslip_id.id')
                # rec.write({'state': 'paid'})
                for payslip in get_slip_lines:
                    if payslip.slip_id.id not in atteched:
                        amount = payslip.total
                        if not self.env['payslip.line'].search(
                                [('advance_salary_id', '=', rec.id), ('payslip_id', '=', payslip.slip_id.id)]):
                            payslip_line_data = {
                                'advance_salary_id': rec.id,
                                'payslip_id': payslip.slip_id.id,
                                'employee_id': payslip.slip_id.employee_id.id,
                                'amount': amount,
                                'date': payslip.slip_id.date_from
                            }
                            self.env['payslip.line'].create(payslip_line_data)
                            # rec.amount_paid += (amount)
                            if wwww < len(old_line):
                                rec.write({'deduction_amount': old_line[wwww].amount})
                            rec.write({'amount_paid': rec.amount_paid + amount})
                            if rec.amount_paid == rec.request_amount:
                                rec.write({'state': 'done'})
                            # if rec.amount_paid != rec.request_amount and rec.state == 'done':
                            #     rec.write({'state': 'paid'})

    def name_get(self):
        """
        name_get that supports displaying location name and model as prefix
        """
        result = []
        for rec in self:
            name = "%s - %s - %s" % (rec.name, rec.employee_id.name, rec.request_date.date())
            result.append((rec.id, name))
        return result
    # @api.depends('employee_id')
    # def _compute_employee_wage_get(self):
    #     for record in self:
    #         if record.payment == 'partially':
    #             record.request_amount = record.employee_id.contract_id.wage * 2

    @api.depends('request_amount', 'amount_paid', 'payslip_line_ids', 'payslip_line_ids.amount')
    def _compute_amount_to_pay(self):
        for rec in self:
            rec.amount_to_pay = rec.request_amount - rec.amount_paid

    # def action_confirm(self):
    #     if not self.request_amount:
    #         raise ValidationError(_("Requested amount must be greater than 0"))
    #     if self.request_amount:
    #         # advance_salary_id = self.search([('employee_id', '=', self.employee_id.id),
    #         #                                  ('id', '!=', self.id),
    #         #                                  ('state', 'not in', ['done', 'refuse', 'paid', 'write_off'])
    #         #                                  ])
    #         # if advance_salary_id:
    #         #     raise ValidationError(_('You already generate advance salary request which is in process.'))
    #         wage = self.env['hr.contract'].sudo().search([('employee_id', '=', self.employee_id.id),
    #                                                       ('state', '=', 'open')], limit=1).wage
    #         limit = self.sudo().job_id.advance_salary_limit
    #         if self.request_amount > 0:
    #             self.write({'state': 'confirm',
    #                         'confirm_date': datetime.today(),
    #                         'confirm_by': self.env.uid})
    #         else:
    #             raise ValidationError(_("Requested amount must e greater than 0."))

    def action_approve1(self):
        self.write({'state': 'approve1',
                    'approved1_date': datetime.today(),
                    'approved1_by': self.env.uid
                    })

    def action_approve2(self):
        self.write({'state': 'approve2',
                    'approved2_date': datetime.today(),
                    'approved2_by': self.env.uid})

    def action_paid(self):
        """
        Sent the status of generating request in 'paid' state
        """
        context = dict(self.env.context or {})
        context.update({
            'default_advance_salary_id': self.id,
            'default_partner_id': self.employee_id.work_contact_id.id,
            'default_amount': self.request_amount,
            'default_payment_type': 'outbound',
            'default_ref': self.reason,
            'default_date': self.payment_start_date.date(),
        })

        return {
            'name': 'Advance Salary',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'context': context,
            'state': 'paid',
        }

    # def action_paid(self):
    #     """
    #         sent the status of generating request in 'paid' state
    #     """
    #     print(self.employee_id)
    #     context = dict(self.env.context or {})
    #     context['advance_salary_id'] = self.id
    #     context['partner_id'] = self.employee_id.work_contact_id.id

    #     return {'name': 'Advance Salary',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'account.payment',
    #             'type': 'ir.actions.act_window',
    #             'context': context,
    #             'state': 'paid',
    #             }

    def action_refuse(self):
        self.state = 'refuse'


    def action_draft(self):
        self.state = 'draft'
        # self.action_mail_send()

    @api.model
    def create(self, values):
        """
        Create a new record
        :return: Newly created record ID
        """
        # Resolve company_id reliably — fallback to current user's company
        company_id = values.get('company_id') or self.env.company.id
    
        # Assign sequence based on payment type
        payment = values.get('payment')
        if payment == 'fully':
            values['name'] = (
                self.env['ir.sequence']
                .with_context(force_company=company_id)
                .next_by_code('advance_salary') or _('New')
            )
        elif payment == 'partially':
            values['name'] = (
                self.env['ir.sequence']
                .with_context(force_company=company_id)
                .next_by_code('loan_salary') or _('New')
            )
        else:
            # Fallback so name is never empty
            values['name'] = (
                self.env['ir.sequence']
                .with_context(force_company=company_id)
                .next_by_code('advance_salary') or _('New')
            )
    
        # Derive payment_start_date from month selection (format: "YYYY-MM")
        month_str = values.get('month')
        if month_str:
            try:
                year, month = map(int, month_str.split('-'))
                values['payment_start_date'] = date(year, month, 1)
            except (ValueError, AttributeError):
                pass  # Leave payment_start_date untouched if parsing fails
    
        res = super(EmployeeAdvanceSalary, self).create(values)
        _logger.info(res)
        return res
    # def create(self, values):
    #     """
    #         Create a new record
    #         :return: Newly created record ID
    #     """
    #     res = super(EmployeeAdvanceSalary, self).create(values)
    #     _logger.info(res)
    #     if 'company_id' in values and values.get('payment') == "fully":
    #         res['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
    #             'advance_salary') or _('New')
    #         # print("Not")
    #     elif 'company_id' in values and values.get('payment') == "partially":
    #         res['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
    #             'loan_salary') or _('New')
    #         # print("DOne")
    #     # else:
    #     #     res['name'] = self.env['ir.sequence'].next_by_code('advance_salary') or _('New')

    #     return res

    # def action_mail_send(self, position=None):
    #     """
    #     This function compose an email by default
    #     """
    #     self.ensure_one()
    #     ir_model_data = self.env['ir.model.data']
    #     try:
    #         if self.state == 'done':
    #             template_id = ir_model_data.get_object_reference('sync_employee_advance_salary',
    #                                                              'email_template_advance_salary_request_done')[1]
    #         elif self.state == 'refuse':
    #             template_id = ir_model_data.get_object_reference('sync_employee_advance_salary',
    #                                                              'email_template_advance_salary_request_refuse')[1]
    #     except ValueError:
    #         template_id = False
    #     if template_id:
    #         template = self.env['mail.template'].browse(template_id)
    #         template.send_mail(self.id, force_send=True, raise_exception=False, email_values=None)
    #     return True

    def action_get_payment(self):
        """
            open a payment form
        """
        return {
            'name': 'Advance Salary',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'domain': [('advance_salary_id', '=', self.id)],
        }

    def calculate_button_action(self):
        if self.payment == 'partially':
            deducted_amount = 0
            total_installments = 0
            vals = []
            self.advance_salary_line_ids = [(5, 0, 0)]
            if self.loan_calculation == 'manual':
                if self.request_amount == 0:
                    raise ValidationError(_('Please enter Request Amount'))
                duration_month_rem = self.request_amount % self.deduction_amount
                if duration_month_rem > 0:
                    self.duration_month = int(self.request_amount / self.deduction_amount) + 1
                else:
                    self.duration_month = int(self.request_amount / self.deduction_amount)

                if  not self.special_approval and  self.duration_month > 10:
                    raise ValidationError(_('Installments Cannot Exceed more than 10'))


                for rec in range(self.duration_month):
                    total_installments += 1
                    deducted_amount += self.deduction_amount
                    if deducted_amount < self.request_amount and total_installments != self.duration_month:
                        vals.append((0, 0, {
                            'amount': self.deduction_amount,
                            'date': self.payment_start_date + relativedelta.relativedelta(months=rec),
                            'name': f"{self.name}",
                        }))
                    else:
                        deduction_amount = self.request_amount - (self.deduction_amount * (total_installments - 1))
                        vals.append((0, 0, {
                            'amount': deduction_amount,
                            'date': self.payment_start_date + relativedelta.relativedelta(months=rec),
                            'name': f"{self.name}",
                        }))
                        break

            # elif self.loan_calculation == 'auto':
            #     if self.duration_month == 0:
            #         raise ValidationError(_('Please enter proper value for Payment Duration'))
            #
            #     if self.duration_month < 2:
            #         raise ValidationError(
            #             _('Duration must be at least 2 months to split payment into one half and equal parts.'))
            #
            #     # First installment is half, rest divided equally
            #     half_amount = self.request_amount / 2
            #     remaining_installments = self.duration_month - 1
            #     remaining_amount = self.request_amount - half_amount
            #     per_month_amount = remaining_amount / remaining_installments
            #     for rec in range(self.duration_month):
            #         if rec == 0:
            #             installment_amount = half_amount
            #         elif rec < self.duration_month - 1:
            #             installment_amount = per_month_amount
            #         else:
            #             # last installment: handle rounding issues
            #             installment_amount = self.request_amount - deducted_amount
            #
            #         vals.append((0, 0, {
            #             'amount': round(installment_amount, 2),
            #             'date': self.payment_start_date + relativedelta.relativedelta(months=rec),
            #             'name': f"{self.name}",
            #         }))
            #         deducted_amount += installment_amount
            #
            #     self.deduction_amount = half_amount  # Set default deduction
            #     self.write({
            #         'payment_end_date': self.payment_start_date + relativedelta.relativedelta(
            #             months=self.duration_month - 1),
            #         'advance_salary_line_ids': vals,
            #     })

            elif self.loan_calculation == 'auto':
                if self.duration_month == 0:
                    raise ValidationError(_('Please enter proper value for Payment Duration'))

                self.deduction_amount = round(self.request_amount / self.duration_month, 0)
                if  not self.special_approval and  self.duration_month > 10:
                    raise ValidationError(_('Installments Cannot Exceed more than 10'))

                for rec in range(self.duration_month):
                    total_installments += 1
                    deducted_amount += self.deduction_amount
                    if deducted_amount < self.request_amount and total_installments != self.duration_month:
                        vals.append((0, 0, {
                            'amount': self.deduction_amount,
                            'date': self.payment_start_date + relativedelta.relativedelta(months=rec),
                            'name': f"{self.name}",
                        }))
                    else:
                        deduction_amount = self.request_amount - (self.deduction_amount * (total_installments - 1))
                        vals.append((0, 0, {
                            'amount': deduction_amount,
                            'date': self.payment_start_date + relativedelta.relativedelta(months=rec),
                            'name': f"{self.name}",
                        }))
                        break

            self.write({
                'payment_end_date': self.payment_start_date + relativedelta.relativedelta(
                    months=total_installments - 1),
                'advance_salary_line_ids': vals,
            })

    # @api.constrains('duration_month')
    # def _onchange_duration_month(self):
    #     if self.duration_month:
    #         if self.duration_month > 24:
    #             raise ValidationError("Installment's cannot be more than 24.")


class HRAdvanceLoanLines(models.Model):
    _name = 'hr.advance.salary.line'
    _description = 'HR Advance Salary Lines'

    name = fields.Char('Name')
    date = fields.Date(string="Payment Date")
    hr_advance_salary_id = fields.Many2one('hr.advance.salary', string="Advance Salary")
    employee_id = fields.Many2one('hr.employee', related="hr_advance_salary_id.employee_id", string="Employee",
                                  readonly=True)
    amount = fields.Float('Amount')
    skip = fields.Boolean('Skipped')


class PayslipLine(models.Model):
    _name = 'payslip.line'
    _description = 'Payslip Line'

    advance_salary_id = fields.Many2one('hr.advance.salary')
    payslip_id = fields.Many2one('hr.payslip', 'Payslip', required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    date = fields.Date('Date', required=True)
    amount = fields.Float('Deduction Amount', digits=dp.get_precision('Account'), required=True)
