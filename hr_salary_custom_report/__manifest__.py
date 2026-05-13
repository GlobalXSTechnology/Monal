{
    'name': 'HR Salary Reports',
    'version': '1.0',
    'summary': 'Salary Sheet Report',
    'category': 'Human Resources',
    'author': 'Asad Noman Wattoo',
    'depends': ['hr', 'hr_payroll', 'account', 'sync_employee_advance_salary'],
    'data': [
        'security/ir.model.access.csv',
        'views/salary_report_wizard_views.xml',
        'reports/salary_sheet_report.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}