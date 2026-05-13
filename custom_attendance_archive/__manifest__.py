{
    'name': 'Attendance Archive',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Add active field to hr.attendance for archiving',
    'depends': ['hr_attendance'],
    'data': [
        'views/hr_attendance_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}