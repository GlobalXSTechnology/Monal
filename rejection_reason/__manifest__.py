{
	'name': "Monal Rejection Reason",
	'author': 'Abdul Rehman Ghani (GXS)',
	'category': 'studio',
	'license': 'AGPL-3',
	'website': 'http://www.globalxs.co',
	'description': """Monal Rejection Reason
""",
	
	'summary': """ Monal Rejection Reason
""",
	'version': '1.0',
	'depends': ['stock','quality_control'],
	'data': [
		'security/ir.model.access.csv',
		'views/stock.xml',
		'views/views.xml',
	],
	'installable': True,
	'application': True,
	'auto_install': False,
}
