{
    "name": "Issuance and Consumption",
    "version": "18.0",
    'author': 'Asad',
    "category": "inventory",
    "depends": ["stock","stock_account","purchase_stock"],
    'website': 'https://www.globalxs.co',
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/consumption_view.xml",
        "views/stock_views.xml"

    ],
    'images': ['static/description/icon.png'],
    "installable": True,
    "application": True,
}
