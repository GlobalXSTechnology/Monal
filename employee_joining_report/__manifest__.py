{
    'name' : 'Employee Joining Report',
    'version': '18.0',
    'category': '',
    'Summary': 'Employee Joining Report',
    'depends' : ['hr'],
    'description': """Employee Joining Report""",

    'data':[
    'security/ir.model.access.csv',
    'views/employee_joining_report.xml',
    'views/employee_joining_report_template.xml',

    ],


   'installable':True,
    'auto install':False,
}