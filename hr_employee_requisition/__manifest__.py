# -*- coding: utf-8 -*-
{
    'name': "Employee Requisition",
    'summary': """Employee Requisition""",
    'description': """Employee Requisition""",
    'author': "Mohsan Raza",
    'website': "https://www.globalxs.co",
    'category': 'Studio',
    'module_type': 'official',
    'version': '18.0',
    'depends': [
        'hr',
    ],
    'demo': [],
    'data': [
        'data/sequence.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/hr_department.xml',
        'views/hr_employee_requisition.xml',
        'views/menus.xml',

    ],
    'installable': True,
    'application': True,
    'auto install': False,
}
