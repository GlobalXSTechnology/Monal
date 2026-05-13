from odoo import models,fields,api

class ResourceCalendarInherit(models.Model):
    _inherit = 'resource.calendar'

    start_check = fields.Float('Check-in Start Time',store=True)
    end_check = fields.Float('Check-out End Time',store=True)