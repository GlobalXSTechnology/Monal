{
    'name': 'Customer Feedback Report',
    'version': '1.0',
    'summary': 'Customer Feedback Report Wizard with Date Filtering',
    'description': """
        This module provides a wizard to generate customer feedback reports based on creation date.
        The wizard allows filtering feedback records by date range.
    """,
    'author': 'Asad Noman Wattoo',
    'depends': ['web_customer_feedback', 'point_of_sale', 'website'],
    'data': [
        "security/ir.model.access.csv",
        'views/customer_feedback_report_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
