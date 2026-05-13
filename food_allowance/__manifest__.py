{
    'name': 'Food Allowances',
    'version': '18.0',
    'summary': 'Module for adding food allowances of employees',
    'sequence': '-1005',
    'license': 'AGPL-3',
    'author': 'Khalid (GXS)',
    'depends': ['mail', 'hr','hr_work_entry_contract_enterprise'],
    'demo': [],
    'data': [
        'data/seq.xml',
        'security/ir.model.access.csv',
        'views/allowance_views.xml',
        'views/allowances_list.xml',
        ],
    'installable': True,
    'application': True,
    'auto install': False,
}
