from odoo import models, fields


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Hr Payslip'

    final_settlement_id = fields.Many2one('employee.final.settlement', string="Final Settlement")
    emp_bank_name = fields.Char(string='Employee Bank Nam', readonly=True)
    emp_acc_no = fields.Char(string='Account #', readonly=True)
    last_work_date = fields.Date(string='Last Working Date', readonly=True)
    count_days = fields.Integer(string='Worked Days', readonly=False)

    def action_payslip_paid(self):
        for payslip in self:
            payslip.state = 'paid'
            if payslip.final_settlement_id and payslip.final_settlement_id.state == 'final_appr':
                payslip.final_settlement_id.write({'state': 'paid'})
        return True
