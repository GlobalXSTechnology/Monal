# -*- coding: utf-8 -*-
{
	'name': 'Monal Employee Attendance Report',
	'version': '18.0',
	'Summary': 'Monal Employee Attendance Report',
	'description': """Monal Employee Attendance Report""",
	'author': "Asad",
	'website': "",
	'Maintainer': 'Global XS Technology Solutions',
	'category': 'Studio',
    'depends': ['base', 'hr_attendance','softatt_attendance_zk_extension'],
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
