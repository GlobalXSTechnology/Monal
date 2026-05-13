# -*- coding: utf-8 -*-
{
	'name': 'Monal Employee Attendance Report With Break',
	'version': '18.0',
	'Summary': 'Monal Employee Attendance Report With Break',
	'description': """Monal Employee Attendance Report With Break""",
	'author': "ABDUL REHMAN GHANI (GXS)" "Asad",
	# 'website': "http://www.globalxs.co/abdul.rehman@globalxs.co",
	'Maintainer': 'Global XS Technology Solutions',
	'category': 'Studio',
    'depends': ['base', 'hr_attendance'],
    'license': 'AGPL-3',
    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'views/report_views.xml',
        'security/ir.model.access.csv',
    ],

    "application": True,
    "installable": True,
}
