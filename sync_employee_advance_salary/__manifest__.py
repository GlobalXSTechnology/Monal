# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': 'HR Employee Advance Salary and Loan',
    'version': '18.0',
    'category': 'Studio',
    'license': "OPL-1",
    'summary': 'Workflow of Employee request for advance salary.',
    'description': """Workflow of Employee request for advance salary.
    Employee
    advance salary
    salary
    payroll
    payslip
    employee advance salary
    skip
    skip installment
    contract
    leaves
    expense    
    HR employee advance salary
employee
employee admin
employee management
human resource admin
advance salary
advance salary request
advance salary installment
advance salary payslip
employee job position
salary deduction
advance salary deduction
salary installment
advance salary limit
salary structure
employee salary structure

hr
hr manager
hr administration
human resource
admin
administration
admin manager
Employee grade
job position
hrm
grade
payslip
salary
timesheet
calendar
Attendance
Appraisal
Employee Letter
Passport Management
Payroll
assessments employees
employees assessments
designation
key area
strength
review
development
evolution
assessment
monitor timeline
employee expense
expense
reimbursement
employee expense reimbursement
employee travel bill reimbursement
register employee expense
employee expense on payslip
Amount refunded for costs incurred
payroll manager
monthly salary
Employee Expense Reimburse
Expense Manager
Post Journal Entries
Payslip Calculation
reimburse
airfare reimbursement
flight ticket
flight ticket reimbursement
airfare allowance
automating
advance recovery
recover salary advances
employee's job position
human resource manager
installment
Configure advance salary limit
partial payment
full payment
Repayment 
Confirmation
Approval
Generate Payment
Installment Deduction in Payslip
Skip Installment
    """,
    'author': 'GlobalXS Technology Solutions',
    'website': 'www.globalxs.com',
    'depends': ['account', 'hr_payroll', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_security.xml',
        'data/advance_salary.xml',
        # 'data/mail_template.xml',
        'data/hr_payroll_data.xml',
        'views/hr_view.xml',
        'views/hr_advance_salary_view.xml',
        'views/hr_skip_installment_view.xml',
        # 'report/advance_salary.xml',
        'report/advance_salary_template.xml',
    ],
    'qweb': [],
    'demo': [],
    'images': [
        'static/description/main_screen.jpg',
    ],
    'price': 25.0,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
