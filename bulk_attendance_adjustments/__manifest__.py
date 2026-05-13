{
    'name': "Bulk Attendance Adjustments",
    'summary': "Module for Bulk Attendance Adjustments",
    'description': """Module for Bulk Attendance Adjustments""",
    'author': 'Khalid(Gxs)',
    'category': 'Attendances',
    'license': 'AGPL-3',
    'website': 'http://www.globalxs.co',
    'version': '18.0',
    'depends': ['hr','sg_attendance_adjustment_request'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
