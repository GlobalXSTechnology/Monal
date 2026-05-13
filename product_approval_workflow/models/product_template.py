from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    approval_stage = fields.Selection([
        ('draft', 'Draft'),
        ('gm', 'Product GM'),
        ('admin', 'Product Admin'),
        ('done', 'Done'),
        ('rejected', 'Rejected'),
    ], default='draft', string='Approval Stage', tracking=True)

    def action_submit_to_gm(self):
        for rec in self:
            if rec.approval_stage == 'done':
                raise ValidationError("Approved products cannot be submitted again to GM.")
            rec.approval_stage = 'gm'

    def action_approve_by_gm(self):
        for rec in self:
            if rec.approval_stage != 'gm':
                raise ValidationError("GM can approve only products that are in GM approval stage.")
            rec.approval_stage = 'admin'

    def action_approve_by_admin(self):
        for rec in self:
            if rec.approval_stage != 'admin':
                raise ValidationError("Admin can approve only products that are approved by GM.")
            rec.approval_stage = 'done'
            rec.active = True

    def action_reject(self):
        for rec in self:
            rec.approval_stage = 'rejected'

    @api.model
    def create(self, vals):
        vals.setdefault('approval_stage', 'draft')
        vals.setdefault('active', True)
        return super().create(vals)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        args.append(('approval_stage', '=', 'done'))
        self_obj = self

        if 'search_product_product' not in self.env.context and any(term[0] == 'id' for term in args):
            self_obj = self_obj.with_context(search_product_product=False)

        return super(ProductTemplate, self_obj).name_search(name, args, operator, limit)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        args.append(('product_tmpl_id.approval_stage', '=', 'done'))
        return super().name_search(name, args, operator, limit)
