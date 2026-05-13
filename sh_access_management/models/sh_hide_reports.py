# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from collections import defaultdict
from odoo import fields, models, _, api, tools
from odoo.exceptions import MissingError, AccessError
from types import MappingProxyType as frozendict

class ReportActions(models.Model):
    _inherit = 'ir.actions.actions'

    # @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'model_name', 'debug')

    @tools.ormcache('model_name', 'self.env.lang')
    def _get_bindings(self, model_name, debug=False):
        """ Retrieve the list of actions bound to the given model.

           :return: a dict mapping binding types to a list of dict describing
                    actions, where the latter is given by calling the method
                    ``read`` on the action record.
        """
        cr = self.env.cr
        IrModelAccess = self.env['ir.model.access']

        result = defaultdict(list)
        user_groups = self.env.user.groups_id
        if not debug:
            user_groups -= self.env.ref('base.group_no_one')

        self.env.flush_all()
        cr.execute("""
            SELECT a.id, a.type, a.binding_type
              FROM ir_actions a
              JOIN ir_model m ON a.binding_model_id = m.id
             WHERE m.model = %s
          ORDER BY a.id
        """, [model_name])

        for action_id, action_model, binding_type in cr.fetchall():
            try:
                action = self.env[action_model].sudo().browse(action_id)
                action_groups = getattr(action, 'groups_id', ())
                action_model_name = getattr(action, 'res_model', False)
                if action_groups and not action_groups & user_groups:
                    continue
                if action_model_name and not IrModelAccess.sudo().check(action_model_name, mode='read', raise_exception=False):
                    continue
                fields_to_read = ['name', 'binding_view_types']
                if 'sequence' in action._fields:
                    fields_to_read.append('sequence')
                result[binding_type].append(action.read(fields_to_read)[0])
            except (AccessError, MissingError):
                continue

        if result.get('action'):
            result['action'] = sorted(result['action'], key=lambda vals: vals.get('sequence', 0))

        allowed_reports = result.get('report', [])
        allowed_actions = result.get('action', [])

        if allowed_actions or allowed_reports:
            domain = [
                ('active_rule', '=', True),
                ('responsible_user_ids', 'in', self.env.user.ids),
                ('company_id', '=', self.env.company.id)
            ]
            find_access = self.env['sh.access.manager'].sudo().search(domain)

            temp_report = []
            temp_action = []
            hide_all_actions = False
            hide_all_reports = False

            if find_access:
                for model_access in find_access.sh_access_model_line:
                    if model_access.model_id.model == model_name:
                        if model_access.sh_hide_action:
                            hide_all_actions = True
                        if model_access.sh_hide_print:
                            hide_all_reports = True

                        for allowed in allowed_reports:
                            for report in model_access.report_ids:
                                if allowed['id'] == report.id:
                                    temp_report.append(report.id)
                        for allowed_action in allowed_actions:
                            if allowed_action['id'] == model_access.action_id.id:
                                temp_action.append(model_access.action_id.id)

            if hide_all_actions:
                result['action'] = []
            else:
                result['action'] = [action_dic for action_dic in allowed_actions if action_dic['id'] not in temp_action]

            if hide_all_reports:
                result['report'] = []
            else:
                result['report'] = [item_dic for item_dic in allowed_reports if item_dic['id'] not in temp_report]

        return frozendict(result)
    