{
    'name': 'HR Mis Leaves Report',
    'version': '1.0',
    'author': 'Asad',
    'category': 'Human Resources',
    'summary': '',
    'depends': ['hr', 'hr_attendance', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/attendance_report_wizard_view.xml',
        # 'report/attendance_report.xml',
    ],
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
}
