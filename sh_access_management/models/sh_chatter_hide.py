# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, api


class SmartButtonList(models.Model):
    _name = "sh.hide.chatter"
    _description = "Smart Button List"

    name = fields.Char("Navbar Name")
    model_ids = fields.Many2many('ir.model', string="Model")
    access_manager_id = fields.Many2one(
        "sh.access.manager", string="Access Manager")

    hide_full_chatter = fields.Boolean("Full Chatter")
    hide_send_msg = fields.Boolean("Send Message")
    hide_log_notes = fields.Boolean("Log Notes")
    hide_activity = fields.Boolean("Activity")
    hide_followers = fields.Boolean("Followers")
    hide_attachments = fields.Boolean("Attachments")

    @api.model
    def sh_checkhide_chatter(self, kwargs):
        user_id = kwargs.get('user_id')
        if not user_id:
            return {
                "model_restrictions": {}
            }

        # Add domain for global restrictions
        global_domain = [
            ('active_rule', '=', True),
            ('responsible_user_ids', 'in', [int(user_id)]),
            ('sh_global_hide_full_chatter', '=', True),
            ('company_id', '=', self.env.company.id)
        ]
        global_restriction = self.env['sh.access.manager'].sudo().search(global_domain, limit=1)

        domain = [
            ('access_manager_id.active_rule', '=', True),
            ('access_manager_id.responsible_user_ids', 'in', [int(user_id)]),
            ('access_manager_id.company_id', '=', self.env.company.id)
        ]
        find_records = self.env['sh.hide.chatter'].sudo().search(domain)

        model_restrictions = {}
        for record in find_records:
            for model in record.sudo().model_ids:
                model_name = model.model
                # Add Model Wise Restrictions
                if model_name not in model_restrictions:
                    model_restrictions[model_name] = {
                        "hide_full_chatter": record.hide_full_chatter,
                        "hide_send_msg": record.hide_send_msg,
                        "hide_log_notes": record.hide_log_notes,
                        "hide_activity": record.hide_activity,
                        "hide_followers": record.hide_followers,
                        "hide_attachments": record.hide_attachments,
                    }
                else:
                    model_restrictions[model_name]["hide_full_chatter"] |= record.hide_full_chatter
                    model_restrictions[model_name]["hide_send_msg"] |= record.hide_send_msg
                    model_restrictions[model_name]["hide_log_notes"] |= record.hide_log_notes
                    model_restrictions[model_name]["hide_activity"] |= record.hide_activity
                    model_restrictions[model_name]["hide_followers"] |= record.hide_followers
                    model_restrictions[model_name]["hide_attachments"] |= record.hide_attachments

        # Apply global restriction if found
        if global_restriction:
            model_restrictions["global"] = {"sh_global_hide_full_chatter": True}

        return {
            "model_restrictions": model_restrictions
        }
