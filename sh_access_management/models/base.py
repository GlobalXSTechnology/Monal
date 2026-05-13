# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, _, api
from lxml import etree
import json

class Model(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options)
        self.env.registry.clear_cache()

        model_name = None
        for value in res.get("views", {}).values():
            if isinstance(value, dict) and "model" in value:
                model_name = value["model"]
                break

        if not model_name or not res.get('views'):
            return res

        # Identify One2many Fields in the Parent Model
        one2many_fields = {}
        for view_data in res['views'].values():
            if 'arch' in view_data:
                root = etree.fromstring(view_data['arch'])
                for field_elem in root.iter('field'):
                    field_name = field_elem.attrib.get('name')
                    field_info = self.env[model_name]._fields.get(field_name)
                    if field_info and field_info.type == 'one2many':
                        one2many_fields[field_name] = field_info.comodel_name

        models_to_check = [model_name] + list(one2many_fields.values())

        domain = [
            ('access_manager_id.active_rule', '=', True),
            ('access_manager_id.company_id', '=', self.env.company.id),
            ('model_id.model', 'in', models_to_check),
            ('access_manager_id.responsible_user_ids', 'in', self.env.user.ids)
        ]

        find_field_access = self.env['sh.field.access'].sudo().search(domain)

        field_access_rules = {
            (access.model_id.model, field.name): access
            for access in find_field_access
            for field in access.field_ids
        }

        for view_type, view_data in res['views'].items():
            if 'arch' in view_data:
                root = etree.fromstring(view_data['arch'])

                is_tree_view = view_type in ['list', 'tree']

                # Parent fields
                for field_elem in root.xpath(".//field[not(ancestor::field)]"):
                    field_name = field_elem.attrib.get('name')
                    access_rule = field_access_rules.get((model_name, field_name))
                    if access_rule:
                        if access_rule.invisible:
                            field_elem.set("invisible", "1")
                            if is_tree_view:
                                field_elem.set("column_invisible", "1")
                        if access_rule.readonly:
                            field_elem.set("readonly", "1")
                        if access_rule.required:
                            field_elem.set("required", "1")
                        if access_rule.sh_hide_external_links:
                            options_attr = field_elem.attrib.get('options', "{}")
                            try:
                                options_dict = json.loads(options_attr.replace("'", '"'))
                            except json.JSONDecodeError:
                                options_dict = {}
                            options_dict.update({"no_edit": True, "no_create": True, "no_open": True})
                            field_elem.attrib['options'] = json.dumps(options_dict)

                # Child (One2many) fields
                for parent_field, child_model in one2many_fields.items():
                    for child_field_elem in root.xpath(f".//field[@name='{parent_field}']//field"):
                        child_field_name = child_field_elem.attrib.get('name')
                        child_access_rule = field_access_rules.get((child_model, child_field_name))
                        if child_access_rule:
                            if child_access_rule.invisible:
                                child_field_elem.set("column_invisible", "1")
                                child_field_elem.set("invisible", "1")
                            if child_access_rule.readonly:
                                child_field_elem.set("readonly", "1")
                            if child_access_rule.required:
                                child_field_elem.set("required", "1")
                            if child_access_rule.sh_hide_external_links:
                                options_attr = child_field_elem.attrib.get('options', "{}")
                                try:
                                    options_dict = json.loads(options_attr.replace("'", '"'))
                                except json.JSONDecodeError:
                                    options_dict = {}
                                options_dict.update({"no_edit": True, "no_create": True, "no_open": True})
                                child_field_elem.attrib['options'] = json.dumps(options_dict)

                                # Force widget to many2one if missing
                                if child_field_elem.attrib.get('widget') is None:
                                    field_info = self.env[child_model]._fields.get(child_field_name)
                                    if field_info and field_info.type == 'many2one':
                                        child_field_elem.attrib['widget'] = 'many2one'

                # Update the view data with the modified XML
                view_data['arch'] = etree.tostring(root, encoding='unicode').replace('\t', '')

        self.env.registry.clear_cache()
        return res
