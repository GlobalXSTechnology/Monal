{
    'name': 'Deduction Type Wise Report',
    'category': 'Reporting',
    'summary': 'Deduction Type Wise Report',
    'description': 'Deduction Type Wise Report',
    'version': "18.0",
    'author': 'Khalid(Gxs)',
    'license': 'LGPL-3',
    'company': 'GlobalXs & Solution',

    'depends': ['hr_payroll'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
