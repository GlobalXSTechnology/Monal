
{
    'name': 'Monal P&L Report',
    'version': '18.0',
    'category': 'Invoice',
    'summary': """ 
             Monal P&L Report
    """,
    'author': 'Global XS Technology Solutions',
    'license': 'AGPL-3',
    'website': 'https://www.globalxs.co',
    'depends': ['account_reports'],
    'data': ['data/pdf_export_templates.xml',],
    'assets': {
        'web.assets_backend': [
            'monal_profit_loss/static/src/components/**/*',

        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
