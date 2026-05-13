{
    "name": "Employee Uniform To Issuance",
    "version": "18.0",
    "category": "Human Resources",
    "summary": "Manage employee uniforms",
    "author": "Asad Noman Wattoo",
    "depends": ["base", "hr", "product", "stock", "hr_contract",'employee_uniform','consumption'],
    "data": [
        # "security/ir.model.access.csv",
        # "security/ir_rule.xml",
        "views/empl_uniform_inherit.xml",
        # "views/issue_details_view.xml"
    ],
    'images': ['static/description/uniform1.png'],

    "installable": True,
    "application": False
}
# stock_location_inherit_custom location check