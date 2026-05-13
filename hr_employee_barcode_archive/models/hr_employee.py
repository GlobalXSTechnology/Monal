from odoo import models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def write(self, vals):
        if 'active' in vals:
            for rec in self:
                if vals.get('active') is False:
                    if rec.barcode and not rec.barcode.startswith('R'):
                        rec.barcode = rec.barcode + 'R'
                # else:
                #     if rec.barcode and rec.barcode.startswith('R'):
                #         rec.barcode = rec.barcode[1:]
        return super().write(vals)
