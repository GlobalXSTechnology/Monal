{
    'name': 'Product Approval Workflow',
    'version': '18.0',
    'summary': 'Adds stage approval for product creation',
    'category': 'Inventory',
    'author': 'Asad',
    'depends': ['base', 'product', 'sale'],
    'data': [
        'security/product_approval_groups.xml',
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
}
