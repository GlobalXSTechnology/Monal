{
	'name': "Monal Product Issues Restriction",
	'author': 'Abdul Rehman Ghani (GXS)',
	'category': 'studio',
	'license': 'AGPL-3',
	'website': 'http://www.globalxs.co',
	'description': """Monal Product Issues Restriction
""",
	
	'summary': """Monal Product Issues Restriction
""",
	'version': '1.0',
	'depends': ['stock', 'mail', 'point_of_sale', 'consumption'],
	'data': [
		'security/ir.model.access.csv',
		'views/views.xml'
	],
	'installable': True,
	'application': True,
	'auto_install': False,
}
