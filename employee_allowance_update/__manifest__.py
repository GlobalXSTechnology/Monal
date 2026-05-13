{
    'name': 'Employee Allowance Update',
    'version': '1.0',
    'author': 'Asad Noman',
    'category': 'Human Resources',
    'summary': 'Update employee allowances in bulk',
    'description': 'A wizard to update multiple employee allowances with filtering by company, department, and employee.',
    'depends': ['hr', 'base', 'hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'security/employee_allowance_update_security.xml',
        'views/employee_allowance_update_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
