# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, SUPERUSER_ID, _
from odoo.tools.translate import _
from lxml import etree
import ast

class ir_ui_view(models.Model):
    _inherit = 'ir.ui.view'

    def _postprocess_tag_search(self, node, name_manager, node_info):

        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_search', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_search(node, name_manager, node_info)

        all_actions = self.env['ir.actions.act_window'].sudo().search([('res_model', '=', name_manager.model._name),('search_view_id', '=', self.id)])

        # Fetch all filters and group-bys that need to be hidden for this model
        hide_filter_obj = self.env['sh.filter.access']
        hide_filter_ids = hide_filter_obj.sudo().search([
            ('model_id.model', '=', name_manager.model._name),
            ('access_manager_id.active_rule', '=', True),
            ('access_manager_id.responsible_user_ids', 'in', self._uid),
            ('access_manager_id.company_id', '=', self.env.company.id)
        ])
        hide_filters = hide_filter_ids.mapped('sh_store_filter_data_ids')
        hide_groupbys = hide_filter_ids.mapped('sh_store_groupby_data_ids')

        hidden_filter_names = hide_filters.mapped('sh_attribute_name')
        hidden_groupby_names = hide_groupbys.mapped('sh_attribute_name')

        removed_defaults_per_model = {}

        for action in all_actions:
            try:
                context_data = ast.literal_eval(action.context) if action.context else {}
            except Exception:
                context_data = {}

            sh_is_modified = False  # Flag to track if modifications happen
            removed_defaults = {}

            # Remove default filters
            for hidden_filter in hidden_filter_names:
                search_key = f"search_default_{hidden_filter}"
                if search_key in context_data:
                    removed_defaults[search_key] = context_data.pop(search_key)
                    sh_is_modified = True

            # Remove default groupbys
            if 'group_by' in context_data:
                if isinstance(context_data['group_by'], str):  # Convert single string to list
                    context_data['group_by'] = [context_data['group_by']]
                elif not isinstance(context_data['group_by'], list):  # Reset to empty list if incorrect type
                    context_data['group_by'] = []

                # Remove only the specified hidden group-by values
                context_data['group_by'] = [
                    gb for gb in context_data['group_by'] if gb not in hidden_groupby_names
                ]

                if len(context_data['group_by']) < len(hidden_groupby_names):  # If any group_by is removed
                    removed_defaults['group_by'] = hidden_groupby_names
                    sh_is_modified = True

            # If modifications happened, update the action
            if sh_is_modified:
                action.sudo().write({'context': str(context_data)})

            # Store removed defaults per model
            if removed_defaults:
                removed_defaults_per_model[action.res_model] = removed_defaults

        # Process search filters & groupbys in the view node
        for child in node:
            # Reset invisible attribute before applying conditions
            if 'invisible' in child.attrib:
                del child.attrib['invisible']

            # Hide filters
            if child.tag == 'filter':
                if child.get('name') in hidden_filter_names:
                    child.set('invisible', '1')
                    node_info['invisible'] = "1 == 1"

            # Hide groupbys inside <group>
            if child.tag == 'group':
                for group_child in child:
                    if group_child.tag == 'filter' and group_child.get('name') in hidden_groupby_names:
                        group_child.set('invisible', '1')
                        node_info['invisible'] = "1 == 1"

        # Store removed defaults per model (e.g., in `ir.config_parameter`)
        if removed_defaults_per_model:
            config_param = self.env['ir.config_parameter'].sudo()
            for model_name, removed_defaults in removed_defaults_per_model.items():
                config_param.set_param(f'hidden_defaults_{model_name}_{self.id}', str(removed_defaults))

        return None

    def _postprocess_tag_button(self, node, name_manager, node_info):
        # Hide Any Button
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_button', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_button(node, name_manager, node_info)

        hide = None
        hide_button_obj = self.env['sh.navbar.buttons.access']
        # hide_button_ids = hide_button_obj.sudo().search([('access_manager_id.company_ids','in',self.env.company.id),('model_id.model','=',name_manager.model._name),('access_manager_id.active','=',True),('access_manager_id.user_ids','in',self._uid)])
        hide_button_ids = hide_button_obj.sudo().search([('model_id.model','=',name_manager.model._name),('access_manager_id.active_rule','=',True),('access_manager_id.responsible_user_ids','in',self._uid),('access_manager_id.company_id', '=', self.env.company.id)])

        # Filtered with same env user and current model
        sh_store_btn_data_ids = hide_button_ids.mapped('sh_store_btn_data_ids')
        # translation_obj = self.env['ir.translation']
        if sh_store_btn_data_ids:
            for btn in sh_store_btn_data_ids:
                if btn.sh_attribute_name == node.get('name'):
                    if node.get('string'):
                        # if translation_obj._get_source(None, ('model_terms',), self.env.lang, btn.sh_attribute_string, None) == node.get('string'):
                        if _(btn.sh_attribute_string) == node.get('string'):
                            hide = [btn]
                            break
                    else:
                        hide = [btn]
                        break
        if hide:
            node.set('invisible', '1')
            if 'attrs' in node.attrib.keys() and node.attrib['attrs']:
                del node.attrib['attrs']
            # node_info['modifiers']['invisible'] = True
            node_info['invisible'] = "1 == 1"

        return None
    
    def _postprocess_tag_page(self, node, name_manager, node_info):
        # Hide Any Notebook Page
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_page', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_page(node, name_manager, node_info)

        hide = None
        hide_tab_obj = self.env['sh.navbar.buttons.access']
        # hide_tab_ids = hide_tab_obj.sudo().search([('access_manager_id.company_ids','in',self.env.company.id),('model_id.model','=',name_manager.model._name),('access_manager_id.active','=',True),('access_manager_id.user_ids','in',self._uid)])
        hide_tab_ids = hide_tab_obj.sudo().search([('model_id.model','=',name_manager.model._name),('access_manager_id.active_rule','=',True),('access_manager_id.responsible_user_ids','in',self._uid),('access_manager_id.company_id', '=', self.env.company.id)])
        # translation_obj = self.env['ir.translation']
        # Filtered with same env user and current model
        sh_store_page_data_ids = hide_tab_ids.mapped('sh_store_page_data_ids')
        if sh_store_page_data_ids:
            for tab in sh_store_page_data_ids:
                # query = """SELECT value FROM ir_translation WHERE lang=%s AND type in (code) AND src=%s"""
                # self._cr.execute(query, params)
                # res = self._cr.fetchone()
                
                # if translation_obj._get_source(None, ('model_terms',), self.env.lang, tab.sh_attribute_string, None) == node.get('string'):
                if _(tab.sh_attribute_string) == node.get('string'):
                    if node.get('name'):
                        if tab.sh_attribute_name == node.get('name'):
                            hide = [tab]
                            break
                    else:
                        hide = [tab]
                        break    
        if hide:
            node.set('invisible', '1')
            if 'attrs' in node.attrib.keys() and node.attrib['attrs']:
                del node.attrib['attrs']
      
            # node_info['modifiers']['invisible'] = True
            node_info['invisible'] = "1 == 1"
        return None
