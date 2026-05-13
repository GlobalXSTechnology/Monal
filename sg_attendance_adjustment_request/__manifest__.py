# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "SG Attendance Adjust Request",
    'summary': """ SG Attendance Adjust Request """,
    'description': """

    """,
    'category': '',
    'version': '18.0.0.1',
    'depends': ['hr', 'hr_attendance', 'base','portal','website'],
    'data': [
        'security/ir.model.access.csv',
        'security/data.xml',
        #'views/assets.xml',
        'views/my_views.xml',
        #'views/website_form.xml',
        #'views/attendance_view.xml',
        'views/mail_activity_views.xml',
        'views/mail_data.xml',
    ],
    'demo': [

    ],
    'qweb': [

    ],
    'js': ['static/src/js/attendance_adjustment.js'],

    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
