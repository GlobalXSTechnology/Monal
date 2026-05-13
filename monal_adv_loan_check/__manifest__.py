{
    'name': "Skans Advance Loan/Salary",
    'author': 'Hammad Asghar',
    'category': 'Payroll',
    'license': 'AGPL-3',
    'website': 'http://www.globalxs.co',
    'description': """Advance Loan Check""",
    'version': '18.0',
    'depends': ['sync_employee_advance_salary'],
    'data': [
        'security/ir.model.access.csv',
        'views/loan_budget.xml',
        'views/view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
