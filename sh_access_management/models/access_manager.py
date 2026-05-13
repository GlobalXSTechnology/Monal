# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, api, exceptions, _


class AccessManager(models.Model):
    _name = "sh.access.manager"
    _description = "Access Management"

    name = fields.Char("Name")
    # responsible_user_ids = fields.Many2many("res.users", string="Users")
    responsible_user_ids = fields.Many2many(
    'res.users', 
    'sh_access_manager_responsible_user_rel', 
    'sh_access_manager_id', 
    'responsible_user_id', 
    string="Users")
    
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    created_by = fields.Many2one("res.users", string="Created By")
    active_rule = fields.Boolean("Active", default="True")
    sh_readonly = fields.Boolean("Readonly")
    sh_disable_developer_mode = fields.Boolean("Disable Developer Mode")

    sh_global_hide_full_chatter = fields.Boolean("Full Chatter")
    sh_disable_user_login = fields.Boolean("Disable Login")
    
    # pages
    sh_hide_menu_ids = fields.Many2many(
        comodel_name="ir.ui.menu", string="Hide Menu")
    sh_access_model_line = fields.One2many(
        "sh.access.model", 'access_manager_id', string="Access Model")
    sh_field_access_line = fields.One2many(
        "sh.field.access", 'access_manager_id', string="Field Access")
    sh_navbar_button_line = fields.One2many(
        'sh.navbar.buttons.access', 'access_manager_id', 'Navbar Button Access')
    sh_hide_chatter_line = fields.One2many(
        "sh.hide.chatter", 'access_manager_id', string="Hide Chatter")
    sh_hide_filter_line = fields.One2many(
        "sh.filter.access", 'access_manager_id', string="Field Access")
    @api.model
    def create(self, vals):
        """
        Prevent adding admin users in `responsible_user_ids` during record creation.
        """
        if 'responsible_user_ids' in vals:
            admin_users = self.env.ref('base.group_system').users
            new_user_ids = set()

            for operation in vals['responsible_user_ids']:
                if operation[0] == 6:  # Replace all users
                    new_user_ids.update(operation[2])  # Extract list of IDs
                elif operation[0] == 4:  # Add single user
                    new_user_ids.add(operation[1])

            # Check if any admin users are being added
            restricted_admins = admin_users.filtered(lambda u: u.id in new_user_ids)
            if restricted_admins:
                raise exceptions.UserError(
                    _("You cannot add an administrator to the Restricted Users list.")
                )

        return super(AccessManager, self).create(vals)

    def write(self, vals):
        """
        Prevent adding admin users in `responsible_user_ids` during record updates.
        """
        if 'responsible_user_ids' in vals:
            admin_users = self.env.ref('base.group_system').users

            for record in self:
                new_user_ids = set()

                for operation in vals['responsible_user_ids']:
                    if operation[0] == 6:  # Replace all users
                        new_user_ids.update(operation[2])  # Extract list
                    elif operation[0] == 4:  # Add single user
                        new_user_ids.add(operation[1])

                restricted_admins = admin_users.filtered(lambda u: u.id in new_user_ids)

                if restricted_admins:
                    raise exceptions.UserError(
                        _("You cannot add an Administrator to the Restricted Users list.")
                    )

        self.env.registry.clear_cache()
        return super(AccessManager, self).write(vals)

    def unlink(self):
        """ Clear related records on delete """
        self.sh_navbar_button_line.unlink()
        return super(AccessManager, self).unlink()

    # @api.model
    # def get_access_restrictions(self, kwargs):
    #     """
    #     Dynamically prepare and return access restrictions for the user.
    #     Args:
    #         kwargs (dict): Contains user_id and optional company_id.
    #     Returns:
    #         dict: Restrictions based on user-specific and global rules.
    #     """
    #     user_id = kwargs.get("user_id")
    #     company_id = kwargs.get("company_id") or self.env.company.id

    #     if not user_id:
    #         raise ValueError("User ID is required.")

    #     domain = [
    #         ('responsible_user_ids', 'in', [user_id]),
    #         ('active_rule', '=', True),
    #     ]

    #     if company_id:
    #         domain.append(('company_id', '=', company_id))

    #     # Search for matching records
    #     access_records = self.search(domain)

    #     # Prepare restrictions dictionary
    #     restrictions = {
    #         "disable_developer_mode": any(record.sh_disable_developer_mode for record in access_records),
    #         "global_hide_full_chatter": any(record.sh_global_hide_full_chatter for record in access_records),
    #     }
    #     return {"model_restrictions": restrictions}

    @api.model
    def get_access_restrictions(self, kwargs):
        """
        Dynamically prepare and return access restrictions for the user.
        Args:
            kwargs (dict): Contains user_id and optional company_id.
        Returns:
            dict: Restrictions based on user-specific and global rules.
        """
        user_id = kwargs.get("user_id")
        company_id = kwargs.get("company_id") or self.env.company.id

        if not user_id:
            raise ValueError("User ID is required.")

        domain = [
            ('responsible_user_ids', 'in', [user_id]),
            ('active_rule', '=', True),
        ]

        if company_id:
            domain.append(('company_id', '=', company_id))

        disable_developer_mode = self.search_count(domain + [('sh_disable_developer_mode', '=', True)]) > 0
        global_hide_full_chatter = self.search_count(domain + [('sh_global_hide_full_chatter', '=', True)]) > 0
        sh_readonly = self.search_count(domain + [('sh_readonly', '=', True)]) > 0

        return {
            "model_restrictions": {
                "disable_developer_mode": disable_developer_mode,
                "global_hide_full_chatter": global_hide_full_chatter,
                "sh_readonly": sh_readonly,
            }
        }
