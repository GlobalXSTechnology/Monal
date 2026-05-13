from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date as delta1
from datetime import datetime


class ProductIssuesRestriction(models.Model):
    _name = 'product.issues.restriction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product Issues Restriction"
    
    date_from = fields.Date('From Date', default=lambda self: fields.Date.to_string(delta1.today()), required=True)
    date_to = fields.Date("To Date", default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()), required=True)
    company_id = fields.Many2one("res.company", string="Company", tracking=True)
    category_ids = fields.Many2many("pos.category", string="Product Category")
    location_id = fields.Many2one("stock.location", string="Location", tracking=True)
    restriction_line_ids = fields.One2many("product.issues.restriction.line", 'restriction_id', string="Restriction Lines")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string="State", default='draft')
    
    def action_done(self):
        self.state = 'done'
        
        
    def action_cancel(self):
        self.state = 'cancel'
        
        
    def action_draft(self):
        self.state = 'draft'
        
        
    @api.onchange('category_ids')
    def _onchange_category_ids(self):
        self.restriction_line_ids = False
        Product = self.env['product.product']
        selected_category_ids = self.category_ids.ids
        allowed_products = Product.search([('categ_id', 'in', selected_category_ids)])
        allowed_product_ids = allowed_products.ids
        new_lines = []
        for product in allowed_products:
            new_lines.append((0, 0, {
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_qty': 0.0,
            }))
        self.restriction_line_ids = new_lines

    
class ProductIssuesRestrictionLine(models.Model):
    _name = 'product.issues.restriction.line'
    
    restriction_id = fields.Many2one('product.issues.restriction', string="Restrictions")
    
    product_id = fields.Many2one('product.product', string="Product")
    product_uom = fields.Many2one('uom.uom', string="UOM", store=True)
    categ_id = fields.Many2one('product.category', string="Category", related='product_id.categ_id', store=True)
    product_qty = fields.Float(string="Quantity")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    