{
    'name': 'LTA Loan Print View',
    'version': '18.0',
    'category': 'Human Resources',
    'summary': 'Custom Print View for Employee Loan/Advance Salary',
    'depends': ['base', 'hr','hr_payroll', 'sync_employee_advance_salary'],
    'data': [
        'reports/report_action.xml',
        'reports/lta_report_template.xml',

    ],
    'installable': True,
    'application': False,
}