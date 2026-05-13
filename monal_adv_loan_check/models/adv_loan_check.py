from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging
from dateutil.relativedelta import relativedelta

from odoo.addons.stock.report.stock_traceability import autoIncrement

# from odoo.odoo.api import ondelete

_logger = logging.getLogger(__name__)


class IRAttachment(models.Model):
    _inherit = 'ir.attachment'

    rev_bank_cheque = fields.Many2one('hr.advance.salary', string="Rev Bank Cheque")
    rev_affidavit = fields.Many2one('hr.advance.salary', string="Rev Affidavit")


class HrAdvanceSalary(models.Model):
    _inherit = 'hr.advance.salary'

    first_referral = fields.Many2one('hr.employee', string='First Referral', store=True, tracking=True)
    second_referral = fields.Many2one('hr.employee', string='Second Referral', store=True, tracking=True)
    special_approval = fields.Boolean(string='Special Approval', default=False, store=True)
    loan_type = fields.Selection([
        ('educational', 'Educational'),
        ('medical', 'Medical'),
    ], default=False, track_visibility='always', string="Loan Type")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        # ('gm', 'GM'),
        ('gm_hr', 'GM HR'),
        ('gm_finance', 'GM Finance'),
        ('audit', 'Audit'),
        ('finance', 'Finance'),
        ('deputy_cfo', 'Deputy CFO'),
        ('ceo', 'CEO'),
        ('paid', 'Paid'),
        ('done', 'Done'),
        ('write_off', 'Write Off'),
        ('refuse', 'Cancel'),
    ], default="draft", track_visibility='always')
    gm_hr_approved = fields.Boolean(string='GM‑HR ok', tracking=True)
    audit_approved = fields.Boolean(string='Audit ok', tracking=True)
    finance_approved = fields.Boolean(string='Finance ok', tracking=True)
    deputy_cfo_approved = fields.Boolean(string='Deputy‑CFO ok', tracking=True)
    last_approval_date = fields.Datetime("Last Approval Date", readonly=True)
    budget_adjusted = fields.Boolean('Budget Adjusted', default=False, copy=False)
    # affidavit = fields.Binary(string='Affidavit')
    # bank_cheque = fields.Binary(string='Bank Cheque')
    bank_cheque_attachment_ids = fields.One2many(
        'ir.attachment', 'rev_bank_cheque',
        string='Bank Cheque', store=True,
    )
    affidavit_attachment_ids = fields.One2many(
        'ir.attachment', 'rev_affidavit',
        string='Affidavit', store=True,
    )
    emp_referral_1 = fields.Selection(
        selection=lambda self: self._emp_selection_1(),
        string="Referral 1",
        help="Destination Stock Location.",
    )
    emp_referral_2 = fields.Selection(
        selection=lambda self: self._emp_selection_2(),
        string="Referral 2",
        help="Destination Stock Location.",
    )

    def _emp_selection_1(self):
        emp_id = self.employee_id.id if self.employee_id else False
        employees = self.env['hr.employee'].sudo().search([('active', '=', True)])  # fetch all employees globally
        if emp_id:
            employees = employees.filtered(lambda e: e.id != emp_id)

        return [
            (str(emp.id), f"{emp.barcode}-{emp.name} ({emp.company_id.name})")
            for emp in employees
        ]

    def _emp_selection_2(self):
        emp_id = self.employee_id.id if self.employee_id else False
        employees = self.env['hr.employee'].sudo().search([('active', '=', True)])  # fetch all employees globally

        if emp_id:
            employees = employees.filtered(lambda e: e.id != emp_id)

        if self.emp_referral_1:
            employees = employees.filtered(lambda e: str(e.id) != self.emp_referral_1)
        return [
            (str(emp.id), f"{emp.barcode}-{emp.name} ({emp.company_id.name})")
            for emp in employees
        ]

    @api.onchange('emp_referral_1', 'emp_referral_2', 'employee_id')
    def _check_referrals(self):
        for rec in self:
            if rec.emp_referral_1 and rec.emp_referral_2 and rec.emp_referral_1 == rec.emp_referral_2:
                raise ValidationError("Referral 1 and Referral 2 cannot be the same employee.")

            if rec.emp_referral_1 and str(rec.employee_id.id) == rec.emp_referral_1:
                raise ValidationError("Referral 1 cannot be the same as the main employee.")

            if rec.emp_referral_2 and str(rec.employee_id.id) == rec.emp_referral_2:
                raise ValidationError("Referral 2 cannot be the same as the main employee.")

    @api.constrains('bank_cheque_attachment_ids', 'affidavit_attachment_ids')
    def _check_attachments_required(self):
        for b in self.bank_cheque_attachment_ids:
            b.write({'public':True})
        for a in self.affidavit_attachment_ids:
            a.write({'public':True})
        _logger.info('Constrainssssssssssssssssssssssssssssss')
        _logger.info('Constrainssssssssssssssssssssssssssssss')
        _logger.info('Constrainssssssssssssssssssssssssssssss')
        _logger.info('Constrainssssssssssssssssssssssssssssss')
        # self.env.cr.commit()
        _logger.info(len(self.bank_cheque_attachment_ids))
        _logger.info(len(self.affidavit_attachment_ids))

        for record in self:
            if len(record.bank_cheque_attachment_ids) > 1:
                raise ValidationError("You must upload exactly one Bank Cheque document.")
            if len(record.affidavit_attachment_ids) > 1:
                raise ValidationError("You must upload exactly one Affidavit document.")

    @api.onchange('first_referral', 'second_referral')
    def _onchange_referral_employees(self):
        if self.first_referral and self.second_referral and \
                self.first_referral.id == self.second_referral.id:
            raise ValidationError("First and Second Referrals cannot be the same employee!")

    def write(self, vals):
        # res = super().write(vals)
        has_group = self.env.user.has_group('monal_adv_loan_check.group_gm_hr')
        if has_group:
            _logger.info('startttttttttttttttttttttttttttt')
            _logger.info('startttttttttttttttttttttttttttt')
            _logger.info(vals)
            _logger.info(vals.get('state'))
            _logger.info(self.state)
            r = []
            for i in vals:
                r.append(i)

            # if self.state == 'draft' and vals.get('state')  != 'draft':
            if self.state == 'draft' and vals.get('state') == None:
                if vals.get('display_name'):
                    if len(r) > 1:
                        vals['audit_approved'] = False
                        vals['finance_approved'] = False
                        vals['deputy_cfo_approved'] = False
                else:
                    vals['audit_approved'] = False
                    vals['finance_approved'] = False
                    vals['deputy_cfo_approved'] = False

            _logger.info(vals)
            _logger.info('Enddddddddddddddddddddddddddddd')
            _logger.info('Enddddddddddddddddddddddddddddd')
            _logger.info('Enddddddddddddddddddddddddddddd')
            # rec. = False
            # rec. = False
        #     autoIncrement()
        return super().write(vals)

    # def action_gm_approve(self):
    #     self.write({'state': 'gm'})

    def action_approve1(self):
        self.write({'state': 'gm_hr'})
        self.gm_hr_approved = True
        for rec in self:
            # if rec.write_date and rec.last_approval_date and rec.write_date > rec.last_approval_date:
            #     Form was modified - skip additional approvals
            # continue
            if not rec.special_approval:
                if rec.audit_approved:
                    rec.action_approve2()
                if rec.audit_approved and rec.finance_approved:
                    rec.action_approve2()
                    rec.action_finance_approve()

    def action_approve2(self):
        self.write({'state': 'audit'})
        self.audit_approved = True
        # self._move_to_next_stage()

    #
    def action_finance_approve(self):
        self.write({'state': 'finance'
                    })
        self.finance_approved = True
        # self._move_to_next_stage()

    def action_gm_finance_approve(self):
        self.write({'state': 'gm_finance'
                    })

    def action_deputy_cfo(self):
        self.write({'state': 'deputy_cfo',
                    })
        self.deputy_cfo_approved = True
        # self._move_to_next_stage()

    def action_ceo_approval(self):
        self.write({'state': 'ceo'
                    })

    def action_draft(self):
        self.state = 'draft'
        self.special_approval = False
        self.gm_hr_approved = False
        self.audit_approved = False
        self.finance_approved = False
        self.deputy_cfo_approved = False
        # self.loan_type = False

    def action_refuse(self):
        for request in self:
            if request.budget_adjusted:

                budget_config = self.env['employee.loan.budget'].search([
                    ('department_id', '=', request.department_id.id),
                    ('id', '!=', request.id),
                ], limit=1)

                if budget_config:
                    budget_config.write({
                        'consumed_budget': budget_config.consumed_budget - request.request_amount
                    })
                    request.budget_adjusted = False
            self.state = 'refuse'

    def action_refuse_2(self):
        self.state = 'draft'

    def action_write_off(self):
        self.write({'state': 'write_off'
                    })

    @api.constrains('payment', 'loan_type', 'state')
    def _check_loan_type_required(self):
        for rec in self.filtered(lambda r: r.state != 'draft'):
            if rec.payment == 'partially' and not rec.loan_type:
                raise ValidationError("Loan Type is required In Loan Case")

    def action_confirm(self):
        for rec in self:
            rec.display_name = rec.name
            rec.state = 'confirm'
            if rec.payment == 'fully':
                if rec.request_amount <= 0:
                    raise ValidationError('Advance amount must be greater than zero.')

                wage = rec.employee_id.contract_id.wage or 0.0
                if not wage:
                    raise ValidationError('The employee has no active contract with a wage.')

                today_date = date.today()
                day_of_month = today_date.day
                # user = self.env['res.groups'].search([('name', '=', 'Special Approval')]).users

                # if self.env.user.id in user.ids:
                #     user = user
                # else:
                #     user = False
                # previous_advance = self.env['hr.advance.salary'].search([
                #     ('employee_id', '=', rec.employee_id.id),
                #     ('id', '!=', rec.id),  # Exclude the current record
                #     ('amount_to_pay', '>', 0),
                #     ('state', 'not in', ['write_off', 'refuse']),
                # ], limit=1)
                # if previous_advance:
                #     raise ValidationError(
                #         f'Employee already has a pending advance salary (Remaining Amount: {previous_advance.amount_to_pay}). Please clear it before applying for a new advance.'
                #     )

                # req_date = rec.request_date or fields.Date.today()
                # month_start = req_date.replace(day=1)
                # month_end = month_start + relativedelta(months=1, days=-1)
                #
                # domain_month = [
                #     ('id', '!=', rec.id),
                #     ('employee_id', '=', rec.employee_id.id),
                #     ('request_date', '>=', month_start),
                #     ('request_date', '<=', month_end),
                #     ('state', 'not in', ['write_off', 'refuse']),
                # ]
                #
                # previous_sum = sum(self.search(domain_month).mapped('request_amount'))
                # remaining_allowance = wage - previous_sum
                #
                # if remaining_allowance <= 0:
                #     raise ValidationError(
                #         f'Employee has already reached the monthly advance limit '
                #         f'of {wage:.0f}. No further advance is allowed this month.'
                #     )
                #
                # if rec.request_amount > remaining_allowance:
                #     raise ValidationError(
                #         f'Employee can still request at most {remaining_allowance:.0f} '
                #         f'this month. Current request ({rec.request_amount:.0f}) exceeds it.'
                #     )

                # if rec.request_amount > wage:
                #     raise ValidationError(
                #         f"Employee can avail advance salary only up to 1 month wage. Employee's wage is {wage}"
                #     )
                # request_count = len(self.search(domain_month))
                # rec.special_approval = request_count >= 2
            else:
                if rec.payment == 'partially':
                    contract_start_date = rec.employee_id.contract_id.date_start
                    if not contract_start_date:
                        raise ValidationError('Employee\'s joining date is not defined.')
                    today_date = date.today()
                    if not rec.special_approval and today_date < contract_start_date + relativedelta(months=6):
                        raise ValidationError(
                            'Only employees who have completed at least 6 months of service '
                            'can apply for a loan.'
                        )
                    date_1 = (today_date - contract_start_date).days
                    previous_loans = self.env['hr.advance.salary'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('id', '!=', rec.id),
                        ('amount_to_pay', '>', 0),
                        ('state', 'not in', ['write_off', 'refuse']),
                    ], limit=1, order="id desc")

                    previous_loans_after = self.env['hr.advance.salary'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('id', '!=', rec.id),
                        ('amount_to_pay', '=', 0),
                        ('state', 'not in', ['write_off', 'refuse']),
                    ], limit=1, order="id desc")
                    _logger.info('Starttttttttttttttttttttttttttt')
                    _logger.info('Starttttttttttttttttttttttttttt')
                    _logger.info(previous_loans)
                    _logger.info(previous_loans_after)
                    # for loan in previous_loans:
                    #     if loan.amount_to_pay > 0:
                    #         raise ValidationError(
                    #             f'Employee already has a pending loan (Remaining Amount: {loan.amount_to_pay}). Please clear it before applying for a new loan.'
                    #         )
                    # for loann in previous_loans_after:
                    #     if loann.state == 'done' and loann.payment_end_date:  # Assuming 'paid' indicates fully paid
                    #         last_payment_date = loann.payment_end_date.date()
                    #         _logger.info(last_payment_date)
                    #         if today_date < last_payment_date + relativedelta(months=12):
                    #             raise ValidationError(
                    #                 f'Employee can apply for a new loan 1 Year after fully repaying the previous loan (Last loan cleared on: {last_payment_date}).'
                    #             )
                    budget_config = self.env['employee.loan.budget'].search([
                        ('company_id', '=', rec.employee_id.company_id.id),
                        ('department_id', '=', rec.employee_id.department_id.id)
                    ], limit=1)
                    _logger.info(budget_config)
                    if not rec.budget_adjusted:
                        if budget_config:
                            total_budget = budget_config.remaining_budget
                            # rec.budget_adjusted = True
                            if not rec.special_approval and rec.request_amount > total_budget:
                                raise ValidationError(
                                    f'Employee cannot avail loan more than Budget, Allowed Bugdet is {total_budget}'
                                )
                                # rec.special_approval = True
                            budget_config.write({
                                'consumed_budget': budget_config.consumed_budget + rec.request_amount
                            })
                            _logger.info(total_budget)

                    if rec.request_amount <= 0:
                        raise ValidationError('Advance amount must be greater than zero.')

                    wage = rec.employee_id.contract_id.wage
                    if not rec.special_approval and not wage:
                        raise ValidationError('Employees Wage is not defined.')
                    max_advance_allowed = wage * 2

                    if not rec.special_approval and rec.request_amount > max_advance_allowed:
                        raise ValidationError(
                            f"Employee Can Avail Loan Upto 2 Month Salary Only. Max Allowed Loan is {max_advance_allowed} ")
                        # rec.special_approval = True
                    if not rec.special_approval and rec.duration_month == False:
                        raise ValidationError(_('Please enter proper value for Payment Duration'))


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        res = super().action_post()
        for payment in self:
            payment.state = 'paid'  # Custom state value (if you have a custom state)
        return res
