{
    'name': 'Employee Increment Report',
    'version': '1.0',
    'author': 'Asad',
    'category': 'Human Resources',
    'summary': 'Generate employee increment reports with filters and totals',
    'depends': ['hr', 'base', 'web', 'employee_increment'],
    'data': [
        'security/ir.model.access.csv',
        'report/employee_increment_report_template.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
