from odoo import models, fields, api


class StockLocationInherit(models.Model):
    _inherit = 'stock.location'

    source_location = fields.Boolean(
        string='Uniform Source Location',
        default=False,
        help="This location can be used as a source for transfers"
    )

    destination_location = fields.Boolean(
        string='Uniform Destination Location',
        default=False,
        help="This location can be used as a destination for transfers"
    )


class EmployeeUniformInherit(models.Model):
    _inherit = 'employee.uniform'

    source_location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        required=True,
        domain="[('usage', '=', 'internal'), ('source_location', '=', True), ('company_id', '=', company_id)]"
    )

    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=True,
        domain="[('usage', '=', 'inventory'), ('destination_location', '=', True), ('company_id', '=', company_id)]"
    )

    @api.constrains('source_location_id', 'destination_location_id')
    def _check_valid_locations(self):
        for record in self:
            if record.source_location_id and not record.source_location_id.source_location:
                raise ValidationError(_("Selected source location is not allowed for uniform distributions."))

            if record.destination_location_id and not record.destination_location_id.destination_location:
                raise ValidationError(_("Selected destination location is not allowed for uniform distributions."))

    @api.onchange('company_id')
    def _onchange_company_id_locations(self):
        domain = {}
        if self.company_id:
            source_domain = [
                ('usage', '=', 'internal'),
                ('source_location', '=', True),
                ('company_id', '=', self.company_id.id)
            ]

            dest_domain = [
                ('usage', '=', 'internal'),
                ('destination_location', '=', True),
                ('company_id', '=', self.company_id.id)
            ]

            return {
                'domain': {
                    'source_location_id': source_domain,
                    'destination_location_id': dest_domain,
                }
            }
        return domain


class ProductCategoryInherit(models.Model):
    _inherit = 'product.category'

    uniform_category = fields.Boolean(
        string='Uniform Category',
        default=False,
        help="Products from this category will be available for uniform distribution"
    )


class EmployeeUniformLines(models.Model):
    _inherit = 'employee.uniform.line'
    _description = 'Employee Uniform Line'

    product_id = fields.Many2one(
        'product.product',
        string='Uniform Product',
        required=True,
        domain="[('categ_id.uniform_category', '=', True)]"
        
    )
