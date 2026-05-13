
from odoo import api, fields, models
 


class AttendanceDevice(models.Model):
    _inherit = "hr.attendance"
    date = fields.Date(string='date')

    # @api.onchange('check_in')
    # def date_id(self):
    #
    #     date = datetime.strftime(self.check_in, '%m-%d-%Y')
    #     self.date = date