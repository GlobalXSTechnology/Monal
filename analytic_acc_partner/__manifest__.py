{
    'name': 'Analytic Account Partner Link',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Creates a partner automatically when an analytic account is created',
    'depends': ['analytic', 'account', 'base'],
    'data': [
        'views/analytic_account_view.xml',
    ],
    'installable': True,
    'application': False,
}