{
    "name": "Butcher Unbuild",
    "version": "18.0",
    'author': 'Asad',
    "category": "Manufacturing",
    "depends": ["mrp", "account","stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/butcher_unbuild_menu.xml",
        "views/butcher_unbuild_view.xml",
        "views/mrp_bom.xml"
    ],
'assets': {

        'web.assets_backend': [
            'butcher_unbuild/static//src/x2many_list.js',

        ],},
    'images': ['static/description/icon.png'],

    "installable": True,
    "application": True,
}
