
{
    "name": "Withholding Deductions",
    "summary": "This module allows you to add withholding tax.",
    "description": """
        This module allows you to add withholding tax.
        It also allows you to add multiple deductions. 
        """,
    "version": "18.0.0.1",
    "license": "AGPL-3",
    'live_test_url':'https://youtu.be/Ah1Q1OLo02A',
    'author': 'Odolution',
    'company': 'Odolution Pvt Ltd',
    'maintainer': 'Odolution Pvt Ltd',
    'website': 'https://www.odolution.com/',
    "category": "Accounting",
    "depends": ["account"],
    'price': 100.00,
    "data": [
        "security/ir.model.access.csv",
        "views/account_payment.xml",
        "wizard/account_payment_register_views.xml",
    ],
    'images': ['static/description/demo_thumbnail.png' ],
    "installable": True,
    'application':True,
    'auto_install':False,

}
