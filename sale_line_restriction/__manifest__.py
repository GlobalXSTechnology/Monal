{
    'name': 'Sale Order Line Delete Validation',
    'version': '1.0',
    'category': 'Sales',
    'author': 'Nouman Mustafa',
    'summary': 'Restrict sale order line deletion if state is not Quotation',
    'depends': ['sale', 'stock', 'consumption'],
    'data': [
        'views/consumption_view.xml',
        'views/sale_order_view.xml',
        'views/transfer_consumption_view.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
