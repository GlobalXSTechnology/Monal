from odoo import api, fields, models, _


class BtCon(models.Model):
    _name = "bt.con"
    _description = "Configuration"
    _rec_name = "Model_na"
    Model_na = fields.Char(string='Model')