from odoo import models, fields





class BiometricEnrollmentWizard(models.TransientModel):
    _name = 'biometric.enrollment.wizard'
    _description = 'Biometric Enrollment Wizard'

    bio_type = fields.Selection([
        ('0', 'General Template'),
        ('1', 'Fingerprint'),
        ('2', 'Face'),
        ('3', 'Voice'),
        ('4', 'Iris'),
        ('5', 'Retina'),
        ('6', 'Palm Vein'),
        ('7', 'Finger Vein'),
        ('8', 'Palm Print'),
        ('9', 'Visible Light Face'),
    ], string="Biometric Type", required=True, default='1')

    finger_id = fields.Selection([
        ('0', '0 - Left Thumb'),
        ('1', '1 - Left Index Finger'),
        ('2', '2 - Left Middle Finger'),
        ('3', '3 - Left Ring Finger'),
        ('4', '4 - Left Little Finger'),
        ('5', '5 - Right Thumb'),
        ('6', '6 - Right Index Finger'),
        ('7', '7 - Right Middle Finger'),
        ('8', '8 - Right Ring Finger'),
        ('9', '9 - Right Little Finger'),
    ], string="Finger", help="Select the finger for fingerprint enrollment")

    user_id = fields.Many2one('sa.biometric.device.user', string="User", required=True)
    device_id = fields.Many2one(related='user_id.device_id', string="Device", readonly=True)

    def action_confirm(self):
        """Run the enrollment command based on user selection."""
        for wizard in self:
            fid = wizard.finger_id if wizard.bio_type == '1' else 6  # Default FID is 6 unless fingerprint
            wizard.user_id.enroll_userbio_command(bio_type=wizard.bio_type, fid=fid)
