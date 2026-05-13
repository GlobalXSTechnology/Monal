from odoo import models, fields, api


class SABiometricLogWizard(models.TransientModel):
    _name           = 'sa.biometric.log.wizard'
    _description    = 'Biometric Log Wizard'
    
    date_from       = fields.Datetime(string='Date From', required=True, default=fields.Datetime.now())
    date_to         = fields.Datetime(string='Date To', required=True, default=fields.Datetime.now())    
    device_id       = fields.Many2one('sa.biometric.device', string='Device', required=True)

    def action_confirm(self):
        # Call the _custom_attlog method on the selected device
        if self.device_id:
            self.device_id._custom_log(self.date_from, self.date_to)