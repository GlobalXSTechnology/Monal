# -*- coding: utf-8 -*-
{
    'name': 'Web Customer Feedback',
    'version': '1.0',
    "category": 'Website',
    'summary': 'Web Customer Feedback with Website Snippets',
    'description': 'Web Customer Feedback with Website Snippets for displaying customer feedback forms',
    'author': 'HASNAIN JUTT(GXS)',
    'company': 'Global XS Technology Solution',
    'maintainer': 'HASNAIN JUTT(GXS)',
    'website': 'https://www.globalxs.co/',
    'depends': ['point_of_sale', 'website', 'base', 'web_editor'],
    'data': [
        'security/ir.model.access.csv',
        'views/feed_back.xml',
        'views/customer_feedback_template.xml',
        'views/feedback_snippet_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'web_customer_feedback/static/src/css/feedback_snippet.css',
            'web_customer_feedback/static/src/js/feedback_public.js',
        ],
        'website.assets_wysiwyg': [
            'web_customer_feedback/static/src/js/feedback_options.js',
            'web_customer_feedback/static/src/xml/feedback_snippet_options.xml',
        ],
        'web.assets_backend': [
            'web_customer_feedback/static/src/xml/feedback_snippet.xml',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
    'external_dependencies': {
        'python': ['qrcode'],
    },

}
