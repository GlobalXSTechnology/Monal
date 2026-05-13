{
    'name': "Monal Butchery Manufacturing report",
    'author': 'Hammad Asghar',
    'category': 'HR',
    'license': 'AGPL-3',
    'website': 'http://www.globalxs.co',
    'description': """Monal Butchery Manufacturing report""",
    'version': '18.0',
    'depends': ['butcher_unbuild','base','mail'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/butchery_manufacturing_report_template.xml',
        'wizard/butchery_manufacturing_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
