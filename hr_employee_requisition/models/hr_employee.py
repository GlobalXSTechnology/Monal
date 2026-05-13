from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class HRDepartment(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('department_id')
    def on_save_department_id(self):
        if self.department_id.head_count_employee < self.department_id.total_employee:
            raise ValidationError(
                _(f"You cannot Add this employee to Department: {self.department_id.name} \nas Head Count of this department: {self.department_id.head_count_employee} \nand Total Number of Employees in this department is {self.department_id.total_employee}."))


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.constrains('wage', 'employee_id')
    def _check_department_budget(self):
        active_states = ('draft', 'open')
        for contract in self:
            emp = contract.employee_id
            dept = emp.department_id
            if not dept or not dept.budget:
                continue  # no budget to compare

            # Sum wages of all other active contracts in the same department
            domain = [
                ('id', '!=', contract.id),
                ('state', 'in', active_states),
                ('employee_id.department_id', '=', dept.id)
            ]
            _logger.info(domain)
            total_other_wages = sum(self.search(domain).mapped('wage'))
            projected_total = total_other_wages + contract.wage
            if projected_total > dept.budget:  # tiny epsilon
                raise ValidationError(_(

                    f"You cannot exceed the budget of {dept.name} department."

                    # f"{dept.name} wage limit exceeded — budget is {dept.budget}, but total would become {projected_total}

                ))

