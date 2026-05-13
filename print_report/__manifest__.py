{
    'name': 'Monal Settlement Print Report',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Custom Final Settlement Print Report for Odoo 18',
    'depends': ['hr_payroll', 'hr','monal_employee_final_settelment'],
    'data': [

        'views/report_action.xml',
        'views/report_template.xml',
    ],
    'installable': True,
    'application': False,
}