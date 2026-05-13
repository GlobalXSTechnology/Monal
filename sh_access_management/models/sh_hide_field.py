# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, _, api
from lxml import etree
from odoo.models import BaseModel
import odoo
import xml.etree.ElementTree as ET
import json


class AccessManager(models.Model):
    _name = "sh.field.access"
    _description = "Field Access"

    model_id = fields.Many2one('ir.model', string="Model")
    # field_ids = fields.Many2many(
    #     "ir.model.fields", domain="[('model_id','=',model_id),('required','=',False)]", string="Fields")
    
    # field_ids = fields.Many2many('ir.model.fields', 'hide_field_ir_model_fields_rel', 'hide_field_id', 'ir_field_id', string='Field')


    field_ids = fields.Many2many(
        "ir.model.fields", domain="[('model_id','=',model_id)]", string="Fields")

    readonly = fields.Boolean("Readonly")
    required = fields.Boolean("Required")
    invisible = fields.Boolean("Invisible")
    sh_hide_external_links = fields.Boolean("External Links")   
    access_manager_id = fields.Many2one(
        "sh.access.manager", string="Access Manager")

