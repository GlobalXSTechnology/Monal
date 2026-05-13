{
    'name': 'Monal Bulk Advance Loan Payments',
	'version': '18.0',
	'Summary': 'Monal Bulk Advance Loan Payments',
	'description': """Monal Bulk Advance Loan Payments""",
	'author': "ABDUL REHMAN GHANI (GXS)",
	'website': "http://www.globalxs.co/abdul.rehman@globalxs.co",
	'Maintainer': 'Global XS Technology Solutions',
	'category': 'Studio',
    'depends': ['hr','account','sync_employee_advance_salary'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/bulk_advance_payments.xml',
        'wizard/bulk_loan_payments.xml',
        'wizard/account_journal_inherit.xml',

    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}







