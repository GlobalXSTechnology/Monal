{
    "name": "Employee Uniform",
    "version": "1.0",
    "category": "Human Resources",
    "summary": "Manage employee uniforms",
    "author": "Asad Noman Wattoo",
    "depends": ["base", "hr", "product", "stock", "hr_contract"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/employee_uniform_views.xml",
        "views/issue_details_view.xml"
    ],
    'images': ['static/description/uniform1.png'],

    "installable": True,
    "application": False
}
# stock_location_inherit_custom location check