# -*- coding: utf-8 -*-
{
	'name': 'Monal Employee Facility Register Report',
	'version': '18.0',
	'Summary': 'Monal Employee Facility Register Report',
	'description': """Monal Employee Facility Register Report""",
	'author': "ABDUL REHMAN GHANI (GXS)",
	'website': "http://www.globalxs.co/abdul.rehman@globalxs.co",
	'Maintainer': 'Global XS Technology Solutions',
	'category': 'Studio',
    'depends': ['base', 'hr_payroll'],
    'license': 'AGPL-3',
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'views/report_views.xml',
        'security/ir.model.access.csv',
    ],
    "application": True,
    "installable": True,
}
