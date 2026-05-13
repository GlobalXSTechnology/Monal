
from odoo import models, fields, api
# import pytz
class SaBiometricCmd(models.Model):
    _name           = 'sa.biometric.att'
    _description    = 'Attendance Log'

    device_id   = fields.Many2one('sa.biometric.device')
    punch_state = fields.Char()
    emp_code    = fields.Char()
    punch_type  = fields.Integer()
    punch_time  = fields.Datetime()
    unknown1    = fields.Integer()
    unknown2    = fields.Integer()

