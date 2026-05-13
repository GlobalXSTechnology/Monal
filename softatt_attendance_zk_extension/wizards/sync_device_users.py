from odoo import models, fields



class SyncBiometricUserDeviceWizard(models.TransientModel):
    _name = 'sync.biometric.user.device.wizard'
    _description = 'Sync Biometric User Info Across Devices'

    device_ids = fields.Many2many('sa.biometric.device', string='Devices', required=True)
    user_ids = fields.Many2many('sa.biometric.device.user', string='Users', required=True)

    def action_confirm(self):
        """Loop through the selected devices and users, and call the update_userinfo_command method."""
        for device in self.device_ids:
            self.user_ids.update_userinfo_command(device_id=device)
        return {'type': 'ir.actions.act_window_close'}
