{
    'name': "Monal Butchery Consumption_report",
    'author': 'Hammad Asghar',
    'category': 'HR',
    'license': 'AGPL-3',
    'website': 'http://www.globalxs.co',
    'description': """Monal Butchery Consumption_report""",
    'version': '18.0',
    'depends': ['butcher_unbuild','base','mail','report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/butchery_consumption_report_template.xml',
        'wizard/butchery_consumption_wizard_view.xml',
        'wizard/butchery_consumption_summary_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
