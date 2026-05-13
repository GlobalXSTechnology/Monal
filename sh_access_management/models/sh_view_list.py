# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models


class ViewList(models.Model):
    _name = "sh.view.list"
    _description = "Holds All Available Views"

    name = fields.Char("Name")
    technical_name = fields.Char("Tech Name")
