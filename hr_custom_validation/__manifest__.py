{
    'name': 'HR Employee Unarchive Validation',
    'version': '1.0',
    'category': 'Human Resources',
    'author': 'Nouman Mustafa ',
    'summary': 'Restrict unarchive action to specific user group',
    'depends': ['hr'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}