from odoo import models, fields, api


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    linked_partner_id = fields.Many2one('res.partner', string='Linked Partner', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Check if company_id is 12
            # vals.get('company_id') se hum check kar rahe hain ke account kis company mein ban raha hai
            current_company_id = vals.get('company_id')
            if current_company_id in [12]:
                partner_vals = {
                    'name': vals.get('name'),
                    'phone': '',
                    'customer_rank': 1,
                    # 'customer_category': False,
                    'company_id': current_company_id,
                }

                # 2. Handle 'marquee' Tag
                tag = self.env['res.partner.category'].search([('name', '=', 'NRL Functions')], limit=1)
                if not tag:
                    tag = self.env['res.partner.category'].create({'name': 'NRL Functions'})

                partner_vals['category_id'] = [(4, tag.id)]

                # 3. Create Partner
                new_partner = self.env['res.partner'].create(partner_vals)

                # 4. Link Partner ID to Analytic Account values
                vals['linked_partner_id'] = new_partner.id
            if current_company_id in [28]:
                partner_vals = {
                    'name': vals.get('name'),
                    'phone': '',
                    'customer_rank': 1,
                    # 'customer_category': False,
                    'company_id': current_company_id,
                }

                # 2. Handle 'marquee' Tag
                tag = self.env['res.partner.category'].search([('name', '=', 'Peshawar Square Functions')], limit=1)
                if not tag:
                    tag = self.env['res.partner.category'].create({'name': 'Peshawar Square Functions'})

                partner_vals['category_id'] = [(4, tag.id)]

                # 3. Create Partner
                new_partner = self.env['res.partner'].create(partner_vals)

                # 4. Link Partner ID to Analytic Account values
                vals['linked_partner_id'] = new_partner.id

        return super(AccountAnalyticAccount, self).create(vals_list)

# from odoo import models, fields, api


# class AccountAnalyticAccount(models.Model):
#     _inherit = 'account.analytic.account'

#     linked_partner_id = fields.Many2one('res.partner', string='Linked Partner', readonly=True)

#     @api.model_create_multi
#     def create(self, vals_list):
#         for vals in vals_list:
#             # 1. Partner Create Logic
#             partner_vals = {
#                 'name': vals.get('name'),
#                 'phone': '',
#                 'customer_rank': 1,
#                 'customer_category': False,
#             }

#             # 2. Handle 'Marquee' Tag (category_id in res.partner)
#             tag = self.env['res.partner.category'].search([('name', '=', 'marquee')], limit=1)
#             if not tag:
#                 tag = self.env['res.partner.category'].create({'name': 'marquee'})

#             partner_vals['category_id'] = [(4, tag.id)]

#             # 3. Create Partner
#             new_partner = self.env['res.partner'].create(partner_vals)

#             vals['linked_partner_id'] = new_partner.id

#         return super(AccountAnalyticAccount, self).create(vals_list)
