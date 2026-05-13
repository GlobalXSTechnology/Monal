{
    "name": "Consumption Report Wizard Action",
    "version": "1.0",
    'author': "Asad",
    "category": "Inventory",
    "summary": "Button to open Consumption Report Wizard from Transfer Consumption",
    "depends": ["base", "stock","consumption"],
    "data": [
        "security/ir.model.access.csv",

        "views/transfer_consumption_inherit_view.xml"
    ],
    "installable": True,
    "application": False
}
