# -*- coding: utf-8 -*-
{
    'name': 'Internal Transfer Report',
    'version': '1.0.0',
    'author': 'Asad Noman',
    'license': 'LGPL-3',
    'category': 'Inventory/Reporting',
    'summary': 'Custom PDF report for Internal Transfers (stock.picking)',
    'depends': ['stock', 'consumption'],
    'data': [
        'report/internal_transfer_report_templates.xml',
    ],
    'installable': True,
    'application': False,
}