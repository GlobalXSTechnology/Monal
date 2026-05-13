{
    'name': 'Employee Salary Increment',
    'version': '1.0',
    'category': 'Human Resources',
    'author': 'Asad',
    'depends': ['hr', 'hr_contract', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/increment_views.xml',
        'views/sequence.xml',
    ],
    'installable': True,
    'application': True,
}