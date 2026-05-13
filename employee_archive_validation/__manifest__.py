{
    'name': 'HR Employee Archive Validation',
    'version': '1.0',
    'category': 'Human Resources',
    'author': 'Nouman Mustafa',
    'summary': 'Restrict archiving employees with running contracts',
    'author': 'GXS',
    'depends': ['hr', 'hr_contract', 'monal_employee_final_settelment', 'hr_payroll', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_update.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}