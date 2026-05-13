# -*- coding: utf-8 -*-
{
    'name': 'GXS Chatter Attachment Fix',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'summary': 'Fixes attachment upload error in Chatter',
    'author': 'GlobalXS',
    'depends': ['mail', 'sh_access_management'],
    'assets': {
        'web.assets_backend': [
            'gxs_chatter_attachment_fix/static/src/xml/chatter_fix.xml',
            'gxs_chatter_attachment_fix/static/src/js/chatter_fix.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
