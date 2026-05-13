# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Global Inputs Solutions",
    'summary': """ Add manual inputs without going into payslips""",
    'description': """FOR MONAL

    """,
    'category': 'Other',
    'version': '18.0',
    'module_type': 'official',
    'depends': ['mail','hr_payroll','hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/department_group.xml',
        'views/global_inputs.xml',
        'views/employee_global_inputs.xml',
    ],
    'demo': [

    ],
    'qweb': [

    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
