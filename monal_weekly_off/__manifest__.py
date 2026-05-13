{
    'name': "Monal Weekly Off",
    'author': 'Hammad Asghar',
    'category': 'TimeOff',
    'license': 'AGPL-3',
    'website': 'http://www.globalxs.co',
    'description': """Weekly Leave""",
    'version': '18.0',
    'depends': ['hr_holidays','hr'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/loan_budget.xml',
        'views/employee_inherit.xml',
        'wizard/schedule_action_wizard_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
