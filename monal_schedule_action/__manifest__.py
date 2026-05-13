{
    'name': 'Monal Schedule Action',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Wizard for scheduling attendance actions with date and multiple companies.',
    'depends': ['hr_attendance', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}