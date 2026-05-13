# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models

class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    sh_child_menu = fields.Many2one("ir.ui.menu", string="Hide Menu")
    @api.returns('self')
    def _filter_visible_menus(self):
        # self.env['ir.ui.menu'].sudo().clear_caches()
        # self.env.registry.clear_cache()
        self.env.registry.clear_cache('routing')
        self.env.registry.clear_cache('assets')
        self.env.registry.clear_cache('templates')
        res = super(IrUiMenu, self)._filter_visible_menus()
        if res and self.env.user:
            domain = [('active_rule', '=', True),('responsible_user_ids', 'in', self.env.user.ids),('company_id', '=', self.env.company.id)]
            access_records = self.env['sh.access.manager'].sudo().search(domain)
            if access_records:
                menu_ids = access_records.mapped('sh_hide_menu_ids').ids
                return res.filtered(lambda m: m.id not in menu_ids)
        return res
