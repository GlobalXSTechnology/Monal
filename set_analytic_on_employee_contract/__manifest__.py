{
    'name': 'Set Analytic On Employee',
    'version': '18.0',
    'category': 'Extra Tools',
    'summary': 'Set Analytic On Employee',
    'sequence': '-1000',
    'license': 'AGPL-3',
    'author': ' Hammad Asghar,',
    'Maintainer': 'Odoo Mates',
    'website': 'odoomates.com',
    'depends': ['hr','hr_contract','hr_payroll_account'],
    'demo': [],
    'data': [
        'views/employee_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto install': False,
}
