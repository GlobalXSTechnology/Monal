from odoo import models, fields, api, _
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
import odoo.addons.decimal_precision as dp
from dateutil import relativedelta

_logger = logging.getLogger(__name__)


class EmployeeAdvanceSalary(models.Model):
    _inherit = "hr.advance.salary"

    duration_month = fields.Integer('Payment Duration(month)', copy=False, tracking=True)

    def open_wizard_for_installments(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Change Installments",
            "res_model": "sync.adv.loan.update",
            "view_mode": "form",
            "view_type": "form",
            "target": "new",
            "context": {
                "salary_id": self.id, 'amount_to_pay': self.amount_to_pay}
        }


class ReworksJobCard(models.TransientModel):
    _name = 'sync.adv.loan.update'
    _description = 'sync.adv.loan.update'

    salary_id = fields.Many2one('hr.advance.salary', string='Advance/Loan')
    amount = fields.Integer(string='Installment Amount')
    amount_to_pay = fields.Integer(string='Amount To Pay')
    installments = fields.Integer('Number of Installments')
    start_date = fields.Date(string='Start From Date',
                             help="Installments will be recalculated starting from this date.")

    def by_amount(self):
        if not self.start_date:
            raise ValidationError("Please select a Start From Date first.")
        if self.amount == 0:
            raise ValidationError('Kindly select any amount')
        if self.amount > self.salary_id.amount_to_pay:
            raise ValidationError('The entered amount is greater than the amount to pay')

        # Compute installments
        self.installments = int(self.salary_id.amount_to_pay / self.amount)
        if self.salary_id.amount_to_pay % self.amount != 0:
            self.installments += 1

        # Remove old installments after the new start date
        self.salary_id.advance_salary_line_ids.filtered(lambda x: x.date >= self.start_date).unlink()

        # Start creating installments
        current_date = self.start_date
        remaining_amount = self.salary_id.amount_to_pay
        amount_sum = 0

        for i in range(self.installments):
            if amount_sum + self.amount < self.salary_id.amount_to_pay:
                inst_amount = self.amount
            else:
                inst_amount = self.salary_id.amount_to_pay - amount_sum

            self.env['hr.advance.salary.line'].create({
                'hr_advance_salary_id': self.salary_id.id,
                'date': current_date,
                'amount': inst_amount,
                'employee_id': self.salary_id.employee_id.id
            })

            amount_sum += inst_amount
            current_date += relativedelta.relativedelta(months=1)

        # Update fields on main salary record
        self.salary_id.write({
            'duration_month': self.installments,
            'deduction_amount': self.amount
        })

        # -------------------------------
        # ACTION METHOD (BY INSTALLMENTS)
        # -------------------------------

    def action(self):
        if not self.start_date:
            raise ValidationError("Please select a Start From Date first.")
        if self.installments <= 0:
            raise ValidationError("Number of installments must be greater than zero.")

        # Remove old installments after the selected date
        self.salary_id.advance_salary_line_ids.filtered(lambda x: x.date >= self.start_date).unlink()

        # Calculate installment amount
        inst_amount = self.salary_id.amount_to_pay / self.installments
        current_date = self.start_date

        # Create new schedule from the selected date
        for i in range(self.installments):
            self.env['hr.advance.salary.line'].create({
                'hr_advance_salary_id': self.salary_id.id,
                'date': current_date,
                'amount': inst_amount,
                'employee_id': self.salary_id.employee_id.id
            })
            current_date += relativedelta.relativedelta(months=1)

        self.salary_id.write({
            'duration_month': self.installments,
            'deduction_amount': inst_amount
        })

    # def by_amount(self):
    #     if not self.start_date:
    #         raise ValidationError("Please select a Start From Date first.")
    #     if self.amount == 0:
    #         raise ValidationError('kindly select any amount')
    #     if self.amount > self.salary_id.amount_to_pay:
    #         raise ValidationError('The enter amount is grater then amount to pay')
    #     number = 0
    #     amount_to_pay = self.salary_id.amount_to_pay - self.amount
    #     if self.amount > 0:
    #         self.installments = (self.salary_id.amount_to_pay / self.amount) + 1
    #
    #     payslip_ids = self.salary_id.payslip_line_ids.sorted(key=lambda a: a.date, reverse=True)
    #     date_payslip = date.today()
    #     st_date = self.salary_id.payment_start_date + timedelta(hours=5)
    #     st_date = st_date.date()
    #     if not payslip_ids:
    #         self.salary_id.advance_salary_line_ids.unlink()
    #         date_payslip = st_date
    #     if payslip_ids:
    #
    #         date_payslip = payslip_ids[0].payslip_id.date_to
    #         for ii in payslip_ids:
    #             if date_payslip < ii.payslip_id.date_to:
    #                 date_payslip = ii.payslip_id.date_to
    #     paid_installments = len(self.salary_id.advance_salary_line_ids.filtered(lambda a: a.date <= date_payslip))
    #     # if self.installments <= paid_installments and paid_installments > 0:
    #     #     raise ValidationError("Total number of installment must grater than paid installments.")
    #     installment_ids = self.salary_id.advance_salary_line_ids.filtered(lambda x: x.date > date_payslip)
    #     installment_ids.unlink()
    #     if paid_installments == 0:
    #         self.salary_id.advance_salary_line_ids.unlink()
    #         date_payslip = st_date
    #     r = self.salary_id.advance_salary_line_ids
    #     x = 1
    #     _logger.info(f'{r}/////////////////{st_date}')
    #     max = self.installments
    #
    #     amount_sum = 0
    #     num = 0
    #     for i in range(self.installments):
    #         num += 1
    #         print(i)
    #         if amount_sum < self.salary_id.amount_to_pay:
    #             payment_date = r[-1].date + relativedelta.relativedelta(
    #                 months=x) if r else st_date + relativedelta.relativedelta(months=i)
    #             if num  == max:
    #                 amount =  self.salary_id.amount_to_pay - amount_sum
    #             else:
    #                 amount = self.amount
    #                 amount_sum += self.amount
    #             self.env['hr.advance.salary.line'].create({
    #                 'hr_advance_salary_id': self.salary_id.id,
    #                 'date': payment_date,
    #                 'amount': amount,
    #                 'employee_id': self.salary_id.employee_id.id
    #             })
    #             x += 1
    #         else:
    #             self.installments = self.installments - 1
    #     self.salary_id.write({'duration_month': self.installments + len(self.salary_id.payslip_line_ids),'deduction_amount':self.amount})
    #
    # def action(self):
    #     payslip_ids = self.salary_id.payslip_line_ids.sorted(key=lambda a:a.date, reverse=True)
    #     date_payslip = date.today()
    #     st_date = self.salary_id.payment_start_date + timedelta(hours=5)
    #     st_date = st_date.date()
    #     if not payslip_ids:
    #
    #         self.salary_id.advance_salary_line_ids.unlink()
    #         date_payslip = st_date
    #     if payslip_ids:
    #         date_payslip = payslip_ids[0].payslip_id.date_to
    #         for ii in payslip_ids:
    #             if date_payslip < ii.payslip_id.date_to:
    #                 date_payslip = ii.payslip_id.date_to
    #     paid_installments = len(self.salary_id.advance_salary_line_ids.filtered(lambda a: a.date <= date_payslip))
    #     if self.installments <= paid_installments and paid_installments > 0:
    #         raise ValidationError("Total number of installment must grater than paid installments.")
    #     installment_ids = self.salary_id.advance_salary_line_ids.filtered(lambda x: x.date > date_payslip)
    #     installment_ids.unlink()
    #     if paid_installments == 0:
    #         self.salary_id.advance_salary_line_ids.unlink()
    #         date_payslip = st_date
    #     r = self.salary_id.advance_salary_line_ids
    #     x = 1
    #     _logger.info(f'{r}/////////////////{st_date}')
    #     for i in range(self.installments - paid_installments):
    #         payment_date = r[-1].date + relativedelta.relativedelta(months=x) if r else st_date  + relativedelta.relativedelta(months=i)
    #         self.env['hr.advance.salary.line'].create({
    #             'hr_advance_salary_id': self.salary_id.id,
    #             'date': payment_date,
    #             'amount': (self.salary_id.amount_to_pay / (self.installments - paid_installments)),
    #             'employee_id': self.salary_id.employee_id.id
    #         })
    #         x+=1
    #     self.salary_id.write({'duration_month':self.installments})
