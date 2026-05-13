{
    'name': 'Employee Final Settlement',
    'version': '18.0',
    'category': 'Extra Tools',
    'summary': 'Module for manging Employee Final Settlement',
    'sequence': '-10008',
    'license': 'AGPL-3',
    'author': 'Hammad Asghar',
    'Maintainer': 'Odoo Mates',
    'website': '',
    'depends': [
        'hr',
        'hr_payroll',
        'mail',
    ],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/empl_final_settlement.xml',
        'views/final_settlement_print.xml',
        'views/payslip_inherit.xml',
        'views/rules.xml',

    ],
    'installable': True,
    'application': True,
    'auto install': False,
}
