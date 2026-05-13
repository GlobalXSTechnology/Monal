from odoo import models, api, exceptions, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def action_unarchive(self):
        group_xml_id = 'hr_custom_validation.group_hr_unarchive_validator'

        if not self.env.user.has_group(group_xml_id):
            raise exceptions.UserError(
                _("You are not authorise to unarchive the records. Contact to your administration!"))

        return super(HrEmployee, self).action_unarchive()

    def action_archive(self):
        # Archive logic: active field False ho jati hai
        return super(HrEmployee, self).action_archive()