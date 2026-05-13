from odoo import models, api, _
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.constrains('location_id', 'location_dest_id')
    def _check_locations_not_equal(self):
        for record in self:
            # Hum sirf Internal Transfers (INT) ke liye check kar rahe hain
            if record.picking_type_code == 'internal':
                if record.location_id == record.location_dest_id:
                    raise ValidationError(_(
                        "Error: The Source Location and Destination Location are identical! Please select different locations for the internal transfer."
                    ))