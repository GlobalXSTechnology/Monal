{
    'name': "Skans Advance Loan/Salary Changes",
    'author': 'Gxs',
    'category': 'Payroll',
    'license': 'AGPL-3',
    'website': 'http://www.globalxs.co',
    'description': """Advance Loan Check Changes""",
    'version': '18.0',
    'depends': ['sync_employee_advance_salary','emp_fine_deduction','food_allowance','payroll_overtime_inputs'],
    'data': [
        'views/food_allowance.xml',
        'views/views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
