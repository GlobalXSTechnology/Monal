# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
import logging

_logger = logging.getLogger(__name__)
from odoo import models, api, fields, _
import time
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

from odoo.tools.safe_eval import safe_eval


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.constrains('state')
    def set_adv(self):
        for slip in self:
            for line in slip.line_ids:
                records = self.env['hr.advance.salary'].search([('employee_id', '=', slip.employee_id.id),('name', '=', line.name)])
                
                for rec in records:
                    wwww = 0
                    old_line = []
                    rec.write({'amount_paid': 0})
                    rec.write({'amount_to_pay': rec.request_amount})
                    if rec.payment == 'fully':
                        rec.write({'deduction_amount': rec.request_amount})
                    else:
                        old_line = self.env['hr.advance.salary.line'].search([('skip','=',False),('hr_advance_salary_id','=',rec.id)], order='date ASC')
                        # raise UserError(old_line)
                        if old_line:
                            rec.write({'deduction_amount': old_line[0].amount})
                        else:    
                            rec.write({'deduction_amount':rec.request_amount/rec.duration_month})
                    for yi in self.env['payslip.line'].search([('advance_salary_id', '=', rec.id)]):
                        yi.write({'advance_salary_id': False})

                    get_slip_lines = self.env['hr.payslip.line'].search(
                        [('slip_id.employee_id', '=', rec.employee_id.id), ('name', '=', rec.name), ('total', '>', 0),
                         ('slip_id.state', 'in', ['done', 'paid'])])
                    atteched = rec.payslip_line_ids.mapped('payslip_id.id')
                    if rec.payment == 'partially':
                        rec.write({'state': 'paid'})
                    else:
                        if rec.bulk_paid:
                            pass
                        elif rec.advance_type == 'final_bank_salary':   
                            rec.write({'state': 'gm_finance'})
                        else:
                            rec.write({'state': 'paid'})
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

    def _generate_pdf(self):
        filtered_payslips = self.filtered(lambda a: a.state == 'paid')
        mapped_reports = filtered_payslips._get_pdf_reports()
        generic_name = _("Payslip")
        template = self.env.ref('hr_payroll.mail_template_new_payslip', raise_if_not_found=False)
        for report, payslips in mapped_reports.items():
            for payslip in payslips:
                pdf_content, dummy = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report, payslip.id)
                if report.print_report_name:
                    pdf_name = safe_eval(report.print_report_name, {'object': payslip})
                else:
                    pdf_name = generic_name
                attachments_vals_list = {
                    'name': f"{pdf_name}.pdf",
                    'type': 'binary',
                    'raw': pdf_content,
                    'res_model': payslip._name,
                    'res_id': payslip.id
                }

                # Send email to employees
                attachment_id = self.env['ir.attachment'].sudo().create(attachments_vals_list)
                if template:
                    email_send = template.send_mail(payslip.id, email_layout_xmlid='mail.mail_notification_light')
                    send_email = self.env['mail.mail'].search([('id', '=', email_send)])
                    send_email.write({'unrestricted_attachment_ids': attachment_id.ids})
                    send_email.send()

    def action_payslip_done(self):
        print('action_payslip_done')
        res = super(HrPayslip, self.with_context(payslip_generate_pdf_direct=False)).action_payslip_done()
        payslip_line_obj = self.env['payslip.line']
        slip_line_obj = self.env['hr.payslip.line']
        skip_installment_obj = self.env['hr.skip.installment']
        for payslip in self:
            advance_salary_ids = self.env['hr.advance.salary'].search(
                ['|', '&', ('payment_start_date', '>=', payslip.date_from),
                 ('payment_start_date', '<=', payslip.date_to),
                 ('payment_start_date', '<=', payslip.date_from),
                 ('advance_type','!=','final_bank_salary'),
                 ('employee_id', '=', payslip.employee_id.id),
                 ('state', '=', 'paid')])

            advance_salary_ids2 = self.env['hr.advance.salary'].search(
                ['|', '&', ('payment_start_date', '>=', payslip.date_from),
                 ('payment_start_date', '<=', payslip.date_to),
                 ('advance_type','=','final_bank_salary'),
                 ('payment_start_date', '<=', payslip.date_from),
                 ('employee_id', '=', payslip.employee_id.id),
                 ('state', 'in', ['gm_finance','paid'])
                ])
            advance_salary_ids = advance_salary_ids + advance_salary_ids2

            for rec in advance_salary_ids:
                skip_installment_ids = skip_installment_obj.search(
                    [('advance_salary_id', '=', rec.id), ('state', '=', 'approve'), ('date', '>=', payslip.date_from),
                     ('date', '<=', payslip.date_to)])
                if skip_installment_ids:
                    due_date = rec.payment_end_date + relativedelta(months=1)
                    rec.write({'payment_end_date': due_date})
                else:
                    if rec.payment == 'fully':
                        if rec.advance_type == 'bank':
                            slip_line_ids = slip_line_obj.search([('slip_id', '=', payslip.id),
                                                              ('code', '=', 'ADV/BNK' + str(rec.id))])
                        elif rec.advance_type == 'cash':
                            slip_line_ids = slip_line_obj.search([('slip_id', '=', payslip.id),
                                                              ('code', '=', 'ADV/CSH' + str(rec.id))])
                        elif rec.advance_type == 'final_bank_salary':
                            slip_line_ids = slip_line_obj.search([('slip_id', '=', payslip.id),
                                                              ('code', '=', 'ADV/FBNK' + str(rec.id))])
                    else:
                        if rec.loan_type == 'educational':

                            slip_line_ids = slip_line_obj.search([('slip_id', '=', payslip.id),
                                                                  ('code', '=', 'LOAN/EDU' + str(rec.id))])
                        elif rec.loan_type == 'medical':

                            slip_line_ids = slip_line_obj.search([('slip_id', '=', payslip.id),
                                                                  ('code', '=', 'LOAN/MED' + str(rec.id))])


                    # duplicate_remove = payslip_line_obj.search([('payslip_id', '=', payslip.id)])
                    if slip_line_ids:
                        amount = slip_line_ids.read(['total'])[0]['total']
                        payslip_line_data = {
                            'advance_salary_id': rec.id,
                            'payslip_id': payslip.id,
                            'employee_id': payslip.employee_id.id,
                            'amount': amount if payslip.credit_note else abs(amount),
                            'date': time.strftime('%Y-%m-%d')
                        }
                        payslip_line_obj.create(payslip_line_data)
                        rec.amount_paid += abs(amount)
                        if rec.amount_paid == rec.request_amount:
                            rec.write({'state': 'done'})

        return res

    @api.model
    def _cron_generate_pdf(self, batch_size=False):
        payslips = self.search([
            ('state', 'in', ['paid']),
            ('queued_for_pdf', '=', True),
        ])
        if payslips:
            return super(HrPayslip, payslips)._cron_generate_pdf(batch_size)
        return False

    def advance_salary_deduction(self):

        slip_line_obj = self.env['hr.payslip.line']
        skip_installment_obj = self.env['hr.skip.installment']
        for payslip in self:
            duplicate_remove = self.env['payslip.line'].search(
                [('payslip_id', '=', payslip.id), ('advance_salary_id', '!=', False)])
            print(duplicate_remove)
            for f in duplicate_remove:
                f.advance_salary_id.amount_to_pay += f.amount
                f.advance_salary_id.amount_paid -= f.amount
                f.advance_salary_id.deduction_amount = f.amount
                f.advance_salary_id.state = 'paid'
                f.sudo().unlink()

            advance_salary_ids = self.env['hr.advance.salary'].search([
                ('amount_to_pay', '!=', 0.0),
                ('advance_type','!=','final_bank_salary'),
                ('payment_start_date', '<=', payslip.date_to),
                ('employee_id', '=', payslip.employee_id.id),
                ('state', '=', 'paid')])

            advance_salary_ids2 = self.env['hr.advance.salary'].search([
                ('amount_to_pay', '!=', 0.0),
                ('advance_type','=','final_bank_salary'),
                ('payment_start_date', '<=', payslip.date_to),
                ('employee_id', '=', payslip.employee_id.id),
                ('state', 'in', ['gm_finance','paid'])])
            advance_salary_ids = advance_salary_ids + advance_salary_ids2

            oids = slip_line_obj.search([('slip_id', '=', payslip.id), ('code', 'in', ['LOAN/EDU', 'LOAN/MED', 'LOAN/SAL333', 'ADV/CSH', 'ADV/BNK', 'ADV/SAL333','ADV/FBNK'])])
            if oids:
                oids.unlink()
            for rec in advance_salary_ids:
                rule = 0
                if rec.payment == 'partially':
                    if rec.loan_type == 'educational':
                        rule = self.env['hr.salary.rule'].search(
                            [('code', '=', 'LOAN/EDU'), ('struct_id', '=', self.struct_id.id)])
                        code = 'LOAN/EDU'
                    else:
                        rule = self.env['hr.salary.rule'].search(
                            [('code', '=', 'LOAN/MED'), ('struct_id', '=', self.struct_id.id)])
                        code = 'LOAN/MED'

                else:
                    if rec.advance_type == 'bank':
                        rule = self.env['hr.salary.rule'].search(
                            [('code', '=', 'ADV/BNK'), ('struct_id', '=', self.struct_id.id)])
                        code = 'ADV/BNK'
                    elif rec.advance_type == 'cash':
                        rule = self.env['hr.salary.rule'].search(
                            [('code', '=', 'ADV/CSH'), ('struct_id', '=', self.struct_id.id)])
                        code = 'ADV/CSH'
                    elif rec.advance_type == 'final_bank_salary':
                        rule = self.env['hr.salary.rule'].search(
                            [('code', '=', 'ADV/FBNK'), ('struct_id', '=', self.struct_id.id)])
                        code = 'ADV/FBNK'
                skip_installment_ids = skip_installment_obj.search(
                    [('advance_salary_id', '=', rec.id), ('state', '=', 'approve'), ('date', '>=', payslip.date_from),
                     ('date', '<=', payslip.date_to)])
                if not skip_installment_ids and rule != 0:
                    if rec.payment == 'partially':
                        amount = rec.advance_salary_line_ids.filtered(
                            lambda a: payslip.date_from <= a.date <= payslip.date_to).amount
                    else:
                        amount = rec.amount_to_pay
                    slip_line_data = {
                        'slip_id': payslip.id,
                        'salary_rule_id': rule.id,
                        'contract_id': payslip.contract_id.id,
                        'name': rec.name,
                        'code': f"{code}{rec.id}",
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'amount': amount,
                        'total': amount,
                        'employee_id': payslip.employee_id.id,
                    }
                    if abs(slip_line_data['amount']) > rec.amount_to_pay:
                        slip_line_data.update({'amount': rec.amount_to_pay})

                    slip_line = slip_line_obj.create(slip_line_data)
                    net_ids = slip_line_obj.search([('slip_id', '=', payslip.id), ('code', '=', 'NET')])

                    if net_ids:
                        net_record = net_ids[0]
                        net_ids.write({'amount': net_record.amount - slip_line_data['amount'],
                                       'total': net_record.amount - slip_line_data['amount']})

    def compute_sheet(self):
        """
            Override method for calculate advance salary on payslip calculation time
        """
        res = super(HrPayslip, self).compute_sheet()

        for payslip in self:
            if not payslip.struct_id.x_studio_allowance_structure:
                payslip.advance_salary_deduction()
        return res
