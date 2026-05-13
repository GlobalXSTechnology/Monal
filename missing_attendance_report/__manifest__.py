{
    'name': 'Missing Attendance Report - Asian Wok',
    'version': '18.0.1.0',
    'category': 'Human Resources',
    'summary': 'Dynamic PDF report for missing check-in/out',
    'depends': ['base', 'hr_attendance', 'mail','sg_attendance_adjustment_request'],
    'data': [
        'security/ir.model.access.csv',
        'report/view.xml',
        'wizard/missing_attendance_wizard_view.xml',
        'report/report_action.xml',
        'report/missing_attendance_template.xml',
    ],
    'installable': True,
    'application': False,
}