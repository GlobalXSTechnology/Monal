{
    'name': "update Advance Loan",
    'author': 'GlobalXS technology Solutions',
    'category': 'CRM',
    'license': 'AGPL-3',
    'website': 'http://www.globalxs.co',
    'description': """
""",
    'version': '18.0',
    'depends': ['sync_employee_advance_salary'],
    'data': [
        'security/ir.model.access.csv',

        'views/views.xml',

        ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
