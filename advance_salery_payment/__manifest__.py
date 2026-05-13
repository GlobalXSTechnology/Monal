{
    'name': 'Advance Salary Payment WEJ',
    'version': '18.0',
    'category': 'Extra Tools',
    'summary': 'Advance Salary Payment',
    
    'license': 'AGPL-3',
    'author': 'Abdul Rehman Ghani',
    
    'website': 'odoo.arg.com',
    'depends': [
    'sync_employee_advance_salary', 
    'monal_adv_loan_check',
    ],
    'demo': [],
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto install': False,
}
