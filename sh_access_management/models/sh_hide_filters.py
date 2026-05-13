# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies Pvt. Ltd.

from odoo import fields, models, api
from lxml import etree


class ShFilterAccess(models.Model):
    _name = "sh.filter.access"
    _description = "Filter Access"

    model_id = fields.Many2one(
        'ir.model',
        string="Model",
        required=True,
        ondelete="cascade"
    )
    access_manager_id = fields.Many2one("sh.access.manager", string="Access Manager")
    sh_store_filter_data_ids = fields.Many2many(
        'sh.store.model.data',
        'sh_filter_hide_view_nodes_store_model_nodes_rel',
        'sh_hide_id', 'sh_store_id',
        string='Hide Filters',
        domain="[('model_id','=',model_id),('sh_node_option','=','filter')]"
    )
    sh_store_groupby_data_ids = fields.Many2many(
        'sh.store.model.data',
        'sh_groupby_hide_view_nodes_store_model_nodes_rel',
        'sh_hide_id', 'sh_store_id',
        string='Hide Group By',
        domain="[('model_id','=',model_id),('sh_node_option','=','groupby')]"
    )

    @api.model
    @api.onchange('model_id')
    def _get_filters_groupby(self):
        store_model_nodes_obj = self.env['sh.store.model.data']
        view_obj = self.env['ir.ui.view']

        if self.model_id:
            views = view_obj.search([
                ('model', '=', self.model_id.model),
                ('type', '=', 'search'),
            ])
            
            for view in views:
                res = self.env[self.model_id.model].sudo().get_view(view_id=view.id, view_type='search')
                doc = etree.XML(res['arch'])
                
                # Find regular filters
                filter_nodes = doc.xpath("//filter[not(parent::group)]")
                for node in filter_nodes:
                    filter_name = node.get('name')
                    filter_string = node.get('string')
                    if filter_name and filter_string:
                        domain = [
                            ('model_id', '=', self.model_id.id),
                            ('sh_node_option', '=', 'filter'),
                            ('sh_attribute_name', '=', filter_name),
                            ('sh_attribute_string', '=', filter_string)
                        ]
                        if not store_model_nodes_obj.search(domain):
                            store_model_nodes_obj.create({
                                'model_id': self.model_id.id,
                                'sh_node_option': 'filter',
                                'sh_attribute_name': filter_name,
                                'sh_attribute_string': filter_string
                            })
                
                # Find group_by options inside <group>
                groupby_nodes = doc.xpath("//group/filter")
                for node in groupby_nodes:
                    groupby_name = node.get('name')
                    groupby_string = node.get('string')
                    if groupby_name and groupby_string:
                        domain = [
                            ('model_id', '=', self.model_id.id),
                            ('sh_node_option', '=', 'groupby'),
                            ('sh_attribute_name', '=', groupby_name),
                            ('sh_attribute_string', '=', groupby_string)
                        ]
                        if not store_model_nodes_obj.search(domain):
                            store_model_nodes_obj.create({
                                'model_id': self.model_id.id,
                                'sh_node_option': 'groupby',
                                'sh_attribute_name': groupby_name,
                                'sh_attribute_string': groupby_string
                            })
