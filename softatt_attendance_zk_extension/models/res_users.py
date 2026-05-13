from odoo import models, fields



class UserDevices(models.Model):
    _inherit = 'res.users'
    device_ids = fields.Many2many('sa.biometric.device')
    

    