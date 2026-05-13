from odoo import models, fields, api




class ContractFields(models.Model):
    _inherit = 'hr.contract'

    @api.constrains('employee_id')
    def get_job_dept(self):
        for rec in self:
            if rec.employee_id:
                rec.job_id = rec.employee_id.job_id
                rec.department_id = rec.employee_id.department_id
                rec.analytic_account_id = rec.employee_id.analytic_account_id



class EmployeeFields(models.Model):
    _inherit = 'hr.employee'

    def write(self, vals):
        res = super().write(vals)

        # prevent recursion loop
        if self.env.context.get('skip_contract_sync'):
            return res

        for rec in self:
            contract = rec.contract_id
            if not contract:
                continue

            update_vals = {}

            # job
            if 'job_id' in vals and contract.job_id.id != rec.job_id.id:
                update_vals['job_id'] = rec.job_id.id

            # department
            if 'department_id' in vals and contract.department_id.id != rec.department_id.id:
                update_vals['department_id'] = rec.department_id.id

            # working schedule (MOST IMPORTANT)
            if 'resource_calendar_id' in vals and contract.resource_calendar_id.id != rec.resource_calendar_id.id:
                update_vals['resource_calendar_id'] = rec.resource_calendar_id.id

            # write only if something actually changed
            if update_vals:
                contract.with_context(skip_employee_sync=True).write(update_vals)

        return res





