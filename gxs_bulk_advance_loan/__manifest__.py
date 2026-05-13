# -*- coding: utf-8 -*-
{
    'name': "Bulk Advance Loan",
    'summary': """ Bulk Advance Loan """,

    'description': """ Bulk Advance Loan """,

    'author': "Global XS Technology Solutions",
    'website': "http://www.globalxs.co",
    'category': 'Uncategorized',
    'version': '18.0',

    'depends': ['hr','account','sync_employee_advance_salary'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/bulk_advance_loan.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
