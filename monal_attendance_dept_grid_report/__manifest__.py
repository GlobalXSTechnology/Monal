
{
    'name': 'Monal Employee Att Reg Report',
    'version': '18.0.1.0.0',
    'summary': 'Employee Att Reg Report',
    'author': 'Asad Noman Wattoo',
    'depends': ['base', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/attendance_dept_grid_wizard.xml',
        'report/attendance_dept_grid_report.xml',
        'report/attendance_dept_grid_template.xml',
    ],
    'installable': True,
    'application': False,
}
