from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import date
from datetime import datetime, time, timedelta, date
from odoo.exceptions import UserError, ValidationError, MissingError


class AccountMove(models.Model):
    _inherit = 'account.move'

    acct_id = fields.Integer(string="Acttive Inform")
    acct_id2 = fields.Integer(string="Acttive Inform")


class UserLoanFields(models.Model):
    _inherit = 'res.partner'

    loan_receivable_pf = fields.Many2one('account.account', string='Loan Receivable', store=True)
    loan_receivable1_comp = fields.Many2one('account.account', string='Company Loan Receivable', store=True)
    loan_receivable1_vehicle = fields.Many2one('account.account', string='Vehicle Loan Receivable', store=True)
    advance_receivable1 = fields.Many2one('account.account', string='Advance Receivable', store=True)


class EmployeeAdvanceSalary(models.Model):
    _inherit = "hr.advance.salary"

    def action_paid_2(self):
        if self.payment == 'partially':
            return {
                'name': 'Advance Salary Payment',
                'type': 'ir.actions.act_window',
                'res_model': 'advance.salary.payment',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {'default_amount': self.request_amount, 'default_check': True},
            }

        if self.payment == 'fully':
            return {
                'name': 'Advance Salary Payment',
                'type': 'ir.actions.act_window',
                'res_model': 'advance.salary.payment',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {'default_amount': self.request_amount, 'default_check': True},
            }

    def action_journal_voucher(self):

        self.ensure_one()
        active_id = self._context.get('active_id')
        print(active_id, self.id, 'active_id = self._context.get(00000000)')
        return {
            'name': _('Journal Entry'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('acct_id', '=', self.id)],
        }
        
    def action_lum_sum(self):

        self.ensure_one()
        active_id = self._context.get('active_id')
        print(active_id, self.id, 'active_id = self._context.get(00000000)')
        return {
            'name': _('Journal Entry'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('acct_id2', '=', self.id)],
        }


class AdvanceSalaryPayment(models.TransientModel):
    _name = "advance.salary.payment"

    def _get_advance(self):
        print(self.env['hr.advance.salary'].browse(self.env.context['active_id']))
        return self.env['hr.advance.salary'].browse(self.env.context['active_id'])

    active_id = fields.Many2one('hr.advance.salary', string="Advance Salary", default=_get_advance, store=True)

    debit_account = fields.Many2one('account.account', string="Debit Account", compute="compute_debit_account")
    credit_account = fields.Many2one('account.account', string="Credit Account", compute="compute_debit_account")
    amount = fields.Float(string="Amount")
    account_id1 = fields.Many2one("account.journal", string="Journal", domain=[('type', 'in', ('bank', 'cash'))],
                                  required=True)
    check = fields.Boolean(string="Check", default=False)
    date = fields.Date(string="Date",  default=fields.Date.today)

    @api.depends('active_id')
    def compute_debit_account(self):
        active_record = self.env['hr.advance.salary'].browse(self._context.get('active_id'))

        payment_type = active_record.payment

        if payment_type == 'partially':
            self.debit_account = active_record.employee_id.work_contact_id.loan_receivable_pf
            self.credit_account = active_record.employee_id.work_contact_id.loan_receivable_pf

        elif payment_type == 'fully':
            self.debit_account = active_record.employee_id.work_contact_id.advance_receivable1
            self.credit_account = active_record.employee_id.work_contact_id.advance_receivable1
       
    def action_paid_3(self):

        active_record = self.env['hr.advance.salary'].browse(self._context.get('active_id'))

        if active_record.payment == 'partially':
            account_id = active_record.employee_id.work_contact_id.loan_receivable_pf.id
            
        elif active_record.payment == 'fully':
            account_id = active_record.employee_id.work_contact_id.advance_receivable1.id
            
        else:
            raise UserError(_("Invalid payment type"))
        journal_id = self.account_id1.id
        credit = self.account_id1.default_account_id.id
        debit_name = f"{active_record.name} - {active_record.employee_id.name}"

        if self.check:
            move = self.env['account.move'].create({
                'acct_id': active_record.id,
                'ref': (active_record.employee_id.name + ' ,' + active_record.payment),
                'date': self.date,
                'partner_id': active_record.employee_id.work_contact_id.id,
                'journal_id': journal_id,
                'line_ids': [
                    (0, 0, {
                        'name': debit_name,
                        'date': active_record.request_date,
                        'partner_id': active_record.employee_id.work_contact_id.id,
                        'account_id': account_id,
                        'debit': active_record.request_amount,
                    }),
                    (0, 0, {
                        'name': active_record.employee_id.name,
                        'date': active_record.request_date,
                        'partner_id': active_record.employee_id.work_contact_id.id,
                        'account_id': credit,
                        'credit': active_record.request_amount,
                    }),
                ],
            })
            move.action_post()

            active_record.write({'state': 'paid'})
        else:
            if self.amount > active_record.amount_to_pay:
                raise ValidationError(_("Amount should not be greater than Amount to Pay"))
            else:
                move = self.env['account.move'].create({
                    'acct_id2': active_record.id,
                    'ref': (active_record.employee_id.name + ' ,' + active_record.payment),
                    'date': active_record.request_date,
                    'partner_id': active_record.employee_id.work_contact_id.id,
                    'journal_id': journal_id,
                    'line_ids': [
                        (0, 0, {
                            'name': active_record.employee_id.name,
                            'date': date.today(),
                            'partner_id': active_record.employee_id.work_contact_id.id,
                            'account_id': credit,
                            'debit': self.amount,
                        }),
                        (0, 0, {
                            'name': active_record.employee_id.name,
                            'date': active_record.request_date,
                            'partner_id': active_record.employee_id.work_contact_id.id,
                            'account_id': account_id,
                            'credit': self.amount,
                        }),
                    ],
                })
                move.action_post()

                payslip_ids = active_record.payslip_line_ids.sorted(key=lambda a: a.date, reverse=True)
                date_payslip = date.today()
                st_date = active_record.payment_start_date + timedelta(hours=5)
                st_date = st_date.date()

                if not payslip_ids:
                    date_payslip = st_date

                print(date_payslip)
                if payslip_ids:
                    date_payslip = payslip_ids[0].payslip_id.date_to
                    for ii in payslip_ids:
                        if date_payslip < ii.payslip_id.date_to:
                            date_payslip = ii.payslip_id.date_to

                all_installments = active_record.advance_salary_line_ids
                unpaid_installments = all_installments.filtered(lambda l: l.date >= date_payslip)
                unpaid_installments.unlink()

                self.env["hr.advance.salary.line"].create({
                    "hr_advance_salary_id": active_record.id,
                    "display_name": active_record.name,
                    "date": date.today(),
                    "amount": self.amount,
                    "employee_id": active_record.employee_id.id,
                })
                total_lines = len(active_record.advance_salary_line_ids)
                active_record.write({'duration_month': total_lines})

                if active_record.amount_to_pay > 0:
                    active_record.write({'amount_paid': active_record.amount_paid + self.amount, 'amount_to_pay': active_record.amount_to_pay - self.amount,})
                if active_record.amount_to_pay == 0:
                    active_record.sudo().write(
                        {'state': 'done',
                         'payment_end_date': datetime.now(),
                         'lum_sum': True, }
                    )

        return {
            'name': _('Accounting Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',

        }
