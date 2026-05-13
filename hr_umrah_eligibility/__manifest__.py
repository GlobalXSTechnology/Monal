{
    "name": "HR Umrah Eligibility",
    "version": "1.0",
    "depends": ["base", "hr", "hr_contract", "hr_payroll", "account"],
    "author": "Asad",
    "category": "Human Resources",
    "summary": "Manage Umrah contributions and eligibility",
    "description": "Adds contribution records and eligibility checking for Umrah package.",
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/hr_umrah_views.xml",
        "views/hr_umrah_application_view.xml",
        "wizard/umrah_eligibility_wizard.xml",
    ],
    "installable": True,
    "application": False,
}
