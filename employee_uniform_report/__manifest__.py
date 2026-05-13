{
    'name': "Employee Uniform Report",
    'version': '1.0',
    'author': 'Asad Noman Wattoo',
    'category': 'HR',
    'summary': "PDF Report for Employee Uniform Distribution",
    'depends': ['hr', 'stock', 'employee_uniform'],
    'data': [
        'report/uniform_report_template.xml',
        'report/uniform_report_action.xml',
    ],
    'installable': True,
    'application': False,
}
