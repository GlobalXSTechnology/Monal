{
    'name': 'Consumption Month Comparison Report',
    'version': '1.0',
    'summary': 'Multi-Month Consumption Comparison Report (Qty, Amount, Cost)',
    'category': 'Inventory/Reporting',
    'author': 'Asad',
    "depends": ["base", "stock", "consumption","report_xlsx"],
    'data': [
        'security/ir.model.access.csv',
        'views/month_comparison_report_wizard.xml',
        'report/multi_month_comparison_template.xml',
        'report/debit_credit_comparison_template.xml',
        'report/report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}