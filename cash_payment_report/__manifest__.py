# -*- coding: utf-8 -*-
{
    'name': "Cash Payment Report",

    'summary': """Cash Payment Report""",

    'description': """Cash Payment Report""",

    'author': "Khalid",
    'version': '18.0',

    'depends': ['base','account'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/templates.xml',
        'views/views.xml',

    ],
    'installable': True,
    'application': True,
    'auto install': False,

}

