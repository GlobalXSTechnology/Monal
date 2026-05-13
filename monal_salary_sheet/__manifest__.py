{
    'name': "monal_salary_sheet",

    'author': "ali raza",
    'version': '18.0',
    'depends': ['hr_payroll', 'sync_employee_advance_salary', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/monal_salary_sheet.xml',
        'views/salary_sheet_template.xml',
    ],
    "installable": True,
    "application": False
}
