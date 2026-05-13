from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class HRDepartment(models.Model):
    _inherit = 'hr.employee'

    referral_1 = fields.Many2one('hr.employee', string="First Referral", store=True, tracking=True)
    referral_2 = fields.Many2one('hr.employee', string="Second Referral", store=True, tracking=True)
    external_ref = fields.Char(string='External Referral', tracking=True)
    emp_first_referral = fields.Selection(
        selection=lambda self: self._emp_first_selection_1(),
        string="Referral 1",
        help="Destination Stock Location.",
        required=True
    )
    emp_second_referral_ = fields.Selection(
        selection=lambda self: self._emp_second_selection_2(),
        string="Referral 2",
        help="Destination Stock Location.",
        required=True
    )

    def _emp_first_selection_1(self):
        employees = self.env['hr.employee'].sudo().search([('active', '=', True)])  # fetch all employees globally

        return [
            (str(emp.id), f"{emp.barcode}-{emp.name} ({emp.company_id.name})")
            for emp in employees
        ]

    def _emp_second_selection_2(self):
        employees = self.env['hr.employee'].sudo().search([('active', '=', True)])  # fetch all employees globally


        if self.emp_first_referral:
            employees = employees.filtered(lambda e: str(e.id) != self.emp_first_referral)
        return [
            (str(emp.id), f"{emp.barcode}-{emp.name} ({emp.company_id.name})")
            for emp in employees
        ]

    @api.onchange('emp_first_referral', 'emp_second_referral_')
    def _check_referrals(self):
        for rec in self:
            if rec.emp_first_referral and rec.emp_second_referral_ and rec.emp_first_referral == rec.emp_second_referral_:
                raise ValidationError("Referral 1 and Referral 2 cannot be the same employee.")

            # if rec.emp_referral_1 and str(rec.employee_id.id) == rec.emp_referral_1:
            #     raise ValidationError("Referral 1 cannot be the same as the main employee.")
            #
            # if rec.emp_referral_2 and str(rec.employee_id.id) == rec.emp_referral_2:
            #     raise ValidationError("Referral 2 cannot be the same as the main employee.")
