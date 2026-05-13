# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Employees Master',
    'version': '1.0',
    'category': 'costing',
    'author': 'Mr Hamza',
    'sequence': -150,
    'summary': 'human resources',
    'description': """human resources""",
    'depends': ['hr','hr_contract'],
    'data': [
        'views/employee_batch_view.xml',
        'security/ir.model.access.csv',

    ],
    'demo': [],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
