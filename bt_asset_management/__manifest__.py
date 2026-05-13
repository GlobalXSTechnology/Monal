# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 BroadTech IT Solutions Pvt Ltd 
#    (<http://broadtech-innovations.com>)s
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Asset Management',
    'version': '0.1',
    'category': 'custom',
    'summary': 'Asset Management',
    'license': 'AGPL-3',
    'description': """
     A simple system to manage assets owned by an organization.
""",
    'author': 'Global XS Technology Solutions',
    'website': 'http://www.globalxs.co',
    'depends': ['base', 'mail', 'stock', 'account_asset', 'account','hr'],
    'images': ['static/description/banner.jpg'],
    'data': [
        'data/sequence.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/asset_sequence.xml',
        'views/asset_view.xml',
        'views/hr_employee_inherit.xml',
        'views/asset_move_view.xml',
        'views/stock_data.xml',
        'views/asset_confi.xml',
        'views/Xpath_check_field.xml',
        'views/asset_minor_action.xml',
        'views/asset_type_action.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=2:softtabstop=2:shiftwidth=2:
