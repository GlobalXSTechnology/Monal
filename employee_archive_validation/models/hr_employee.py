from odoo import models, api, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def write(self, vals):
        if 'active' in vals and vals.get('active') is False:
            for employee in self:
                running_contract = self.env['hr.contract'].search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'open')
                ], limit=1)

                if running_contract:
                    raise ValidationError(_(
                        "You cannot Archive employee '%s' because they have a running contract. "
                        "Please expire or cancel the contract first."
                    ) % employee.name)

                settlement = self.env['employee.final.settlement'].search([
                    ('name', '=', employee.id)
                ], order='id desc', limit=1)

                if settlement:
                    if settlement.state != 'paid':
                        state_labels = dict(self.env['employee.final.settlement']._fields['state'].selection)
                        current_state = state_labels.get(settlement.state, settlement.state)

                        raise ValidationError(_(
                            "You cannot Archive employee '%s' because their Final Settlement "
                            "status is '%s'. It must be 'Paid' to proceed."
                        ) % (employee.name, current_state))
                else:
                    raise ValidationError(_(
                        "No Final Settlement record found for '%s'. "
                        "Please create and pay the settlement before archiving."
                    ) % employee.name)

        return super(HrEmployee, self).write(vals)

class AttendanceEmployeeCode(models.Model):
    _inherit = 'sa.attendance.employee.code'

    @api.constrains('device_id', 'code')
    def _check_badge_id_alignment(self):
        for record in self:
            employee = record.employee_id
            device = record.device_id

            if employee:
                # if device and device.company_id != employee.company_id:
                #     raise ValidationError(_(
                #         "Company Mismatch! The device company (%s) must match the employee's company (%s)."
                #     ) % (device.company_id.name, employee.company_id.name))

                emp_barcode = employee.barcode or ''
                input_code = record.code or ''

                if input_code != emp_barcode:
                    raise ValidationError(_(
                        "Badge ID Mismatch! The entered code (%s) does not match the Employee's Badge ID (%s)."
                    ) % (input_code, emp_barcode))