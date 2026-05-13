# -*- coding: utf-8 -*-
# Part of Odoo, Aktiv Software PVT. LTD.
# See LICENSE file for full copyright & licensing details.

# Author: Aktiv Software PVT. LTD.
# mail: odoo@aktivsoftware.com
# Copyright (C) 2015-Present Aktiv Software PVT. LTD.
# Contributions:
#   Aktiv Software:
#      - Dinesh
#      - Muthaiyan Selvam
#      - Dhara Solanki
#      - Riya Pal

{
    "name": "Mass Clean Data (Clear Data)",
    "author": "Aktiv Software",
    "website": "http://www.aktivsoftware.com/",
    "summary": """
        This module allows to user clear the unwanted data using wizard.
        """,
    "description": """
        Title: Mass Clean Data \n
        Author: Aktiv Software \n
        mail: odoo@aktivsoftware.com \n
        Copyright (C) 2015-Present Aktiv Software PVT. LTD. \n
        Contributions: Aktiv Software
    """,
    "license": "OPL-1",
    "version": "18.0.1.0.0",
    "data": ["security/ir.model.access.csv", "wizard/clean_data_view.xml"],
    "images": ["static/description/Mass_Clean_Data_Banner_2.jpg"],
    "installable": True,
    "auto_install": False,
    "application": False,
    "currency": "EUR",
    "price": 7.00,
}
