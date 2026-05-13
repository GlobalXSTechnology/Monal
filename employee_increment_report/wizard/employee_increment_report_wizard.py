# from odoo import models, fields, api, _
# from odoo.exceptions import UserError
# from datetime import datetime
# 
# 
# class EmployeeIncrementWizard(models.TransientModel):
#     _name = 'employee.increment.report.wizard'
#     _description = 'Employee Increment Report Wizard'
# 
#     date_from = fields.Date(string='From Date', required=True, default=fields.Date.context_today)
#     date_to = fields.Date(string='To Date', required=True, default=fields.Date.context_today)
# 
#     type = fields.Selection(
#         [
#             ('department', 'Department Wise'),
#             ('company', 'Company Wise'),
#             ('employee', 'Employee Wise'),
#         ],
#         string='Report Type',
#         required=True,
#         default='company'
#     )
# 
#     company_id = fields.Many2one(
#         'res.company',
#         string="Company",
#         default=lambda self: self.env.company,
#         domain=lambda self: [('id', '=', self.env.company.id)],
#         readonly=True
# 
#     )
#     department_id = fields.Many2many(
#         'hr.department',
#         string="Department",
#         domain=lambda self: [('company_id', '=', self.env.company.id)],
#     )
#     employee_ids = fields.Many2many(
#         'hr.employee',
#         string="Employees",
#         domain=lambda self: [('company_id', '=', self.env.company.id)],
#     )
# 
# 
#     @api.onchange('date_from', 'date_to')
#     def _onchange_dates(self):
#         if self.date_from and self.date_to:
#             if self.date_from > self.date_to:
#                 return {
#                     'warning': {
#                         'title': _('Invalid Date Range'),
#                         'message': _('From Date cannot be after To Date.'),
#                     }
#                 }
# 
#     def action_generate_report(self):
#         self.ensure_one()
# 
#         # --- Validate Dates ---
#         if self.date_from > self.date_to:
#             raise UserError(_("From Date cannot be after To Date."))
# 
#         # --- Domain for search ---
#         domain = [
#             ('date', '>=', self.date_from),
#             ('date', '<=', self.date_to),
#         ]
# 
#         if self.department_id:
#             domain.append(('employee_id.department_id', 'in', self.department_id.ids))
# 
#         if self.employee_ids:
#             domain.append(('employee_id', 'in', self.employee_ids.ids))
# 
#         # Company filter through employee's company
#         if self.company_id:
#             domain.append(('employee_id.company_id', '=', self.company_id.id))
# 
#         # Access the history model
#         try:
#             increment_history = self.env['employee.increment.history'].search(domain,
#                                                                               order='employee_id, date desc, id desc')
#         except Exception as e:
#             raise UserError(_("Error accessing increment history: %s") % str(e))
# 
#         if not increment_history:
#             raise UserError(_("No increment records found for the selected criteria."))
# 
#         # --- Prepare report data - Only show latest increment per employee ---
#         report_data = []
#         processed_employees = set()
# 
#         for history in increment_history:
#             employee_id = history.employee_id.id
# 
#             # Skip if we already processed this employee (show only latest)
#             if employee_id in processed_employees:
#                 continue
# 
#             processed_employees.add(employee_id)
# 
#             employee = history.employee_id
#             report_data.append({
#                 'doc_date': history.date.strftime('%d-%m-%Y') if history.date else '-',
#                 'emp_code': employee.barcode or '-',  # Badge ID from barcode field
#                 'emp_name': employee.name,
#                 'father_name': employee.x_studio_father_name or '-',  # Studio field for father name
#                 'cnic': employee.identification_id or '-',
#                 'joining_date': employee.create_date.strftime('%d-%m-%Y') if employee.create_date else '-',
#                 'department': employee.department_id.name if employee.department_id else '-',
#                 'designation': employee.job_id.name if employee.job_id else '-',
#                 'line_type': 'Basic Salary',
#                 'before_amount': history.old_salary or 0.0,
#                 'ratio': (history.increment_value / history.old_salary * 100) if history.old_salary else 0,
#                 'increment_amount': history.increment_value or 0.0,
#                 'after_amount': history.new_salary or 0.0,
#             })
# 
#         # --- Totals ---
#         total_before = sum(item['before_amount'] for item in report_data)
#         total_increment = sum(item['increment_amount'] for item in report_data)
#         total_after = sum(item['after_amount'] for item in report_data)
#         overall_ratio = (total_increment / total_before * 100) if total_before else 0
# 
#         # Get report type display name
#         type_display = dict(self._fields['type'].selection).get(self.type)
# 
#         # Prepare data for report
#         data = {
#             'report_data': report_data,
#             'total_before': total_before,
#             'total_increment': total_increment,
#             'total_after': total_after,
#             'overall_ratio': overall_ratio,
#             'date_from': self.date_from.strftime('%d-%m-%Y'),
#             'date_to': self.date_to.strftime('%d-%m-%Y'),
#             'department_name': ', '.join(
#                 self.department_id.mapped('name')) if self.department_id else 'All Departments',
#             'company_name': self.company_id.name,
#             'print_date': fields.Date.today().strftime('%d-%m-%Y'),
#             'print_time': datetime.now().strftime('%I:%M %p'),
#             'report_type': type_display,  # Add report type name
#         }
# 
#         return self.env.ref('employee_increment_report.employee_increment_report_action').report_action(self, data=data)
# 
# 
# class EmployeeIncrementHistoryc(models.Model):
#     _inherit = 'employee.increment.history'
# 
#     company_id = fields.Many2one(
#         'res.company',
#         string="Company",
#         related='employee_id.company_id',
#         store=True,
#         readonly=True
#     )
# 
# 
# class EmployeeIncrementReport(models.AbstractModel):
#     _name = 'report.employee_increment_report.increment_report_template'
#     _description = 'Employee Increment Report'
# 
#     @api.model
#     def _get_report_values(self, docids, data=None):
#         if not data:
#             raise UserError(_("No data provided for report generation."))
# 
#         return {
#             'doc_ids': docids,
#             'doc_model': 'employee.increment.report.wizard',
#             'data': data,
#         }
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


class EmployeeIncrementWizard(models.TransientModel):
    _name = 'employee.increment.report.wizard'
    _description = 'Employee Increment Report Wizard'

    date_from = fields.Date(string='From Date', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='To Date', required=True, default=fields.Date.context_today)

    type = fields.Selection(
        [
            ('department', 'Department Wise'),
            ('company', 'Company Wise'),
            ('employee', 'Employee Wise'),
        ],
        string='Report Type',
        required=True,
        default='department'
    )

    department_id = fields.Many2many('hr.department', string='Departments')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                return {
                    'warning': {
                        'title': _('Invalid Date Range'),
                        'message': _('From Date cannot be after To Date.'),
                    }
                }

    def action_generate_report(self):
        self.ensure_one()

        # --- Validate Dates ---
        if self.date_from > self.date_to:
            raise UserError(_("From Date cannot be after To Date."))

        # --- Domain for search ---
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]

        if self.department_id:
            domain.append(('employee_id.department_id', 'in', self.department_id.ids))

        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))

        # Company filter through employee's company
        if self.company_id:
            domain.append(('employee_id.company_id', '=', self.company_id.id))

        # Access the history model
        try:
            increment_history = self.env['employee.increment.history'].search(domain)
        except Exception as e:
            raise UserError(_("Error accessing increment history: %s") % str(e))

        if not increment_history:
            raise UserError(_("No increment records found for the selected criteria."))

        # --- Prepare report data ---
        report_data = []
        for history in increment_history:
            employee = history.employee_id
            report_data.append({
                'doc_date': history.date.strftime('%d-%m-%Y') if history.date else '-',
                'emp_name': employee.name,
                'father_name': getattr(employee, 'father_name', '') or '-',
                'cnic': employee.identification_id or '-',
                'joining_date': employee.create_date.strftime('%d-%m-%Y') if employee.create_date else '-',
                'department': employee.department_id.name if employee.department_id else '-',
                'designation': employee.job_id.name if employee.job_id else '-',
                'line_type': 'Basic Salary',
                'before_amount': history.old_salary or 0.0,
                'ratio': (history.increment_value / history.old_salary * 100) if history.old_salary else 0,
                'increment_amount': history.increment_value or 0.0,
                'after_amount': history.new_salary or 0.0,
            })

        # --- Totals ---
        total_before = sum(item['before_amount'] for item in report_data)
        total_increment = sum(item['increment_amount'] for item in report_data)
        total_after = sum(item['after_amount'] for item in report_data)
        overall_ratio = (total_increment / total_before * 100) if total_before else 0

        # Prepare data for report
        data = {
            'report_data': report_data,
            'total_before': total_before,
            'total_increment': total_increment,
            'total_after': total_after,
            'overall_ratio': overall_ratio,
            'date_from': self.date_from.strftime('%d-%m-%Y'),
            'date_to': self.date_to.strftime('%d-%m-%Y'),
            'department_name': ', '.join(
                self.department_id.mapped('name')) if self.department_id else 'All Departments',
            'company_name': self.company_id.name,
            'print_date': fields.Date.today().strftime('%d-%m-%Y'),
            'print_time': datetime.now().strftime('%I:%M %p'),
        }

        return self.env.ref('employee_increment_report.employee_increment_report_action').report_action(self, data=data)
class EmployeeIncrementHistoryc(models.Model):
    _inherit = 'employee.increment.history'

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        related='employee_id.company_id',
        store=True,
        readonly=True
    )

class EmployeeIncrementReport(models.AbstractModel):
    _name = 'report.employee_increment_report.increment_report_template'
    _description = 'Employee Increment Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            raise UserError(_("No data provided for report generation."))

        return {
            'doc_ids': docids,
            'doc_model': 'employee.increment.report.wizard',
            'data': data,
        }