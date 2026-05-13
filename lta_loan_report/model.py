from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.advance.salary'



    def get_first_referral_info(self):
        # print('rrrrrrrrrrrrrrrrrrrrrrrrrr')
        if not self.x_studio_referral_1:
            return {}

        badge = self.x_studio_referral_1.badge_id
        # print('rrrrrrrrrrrrrrrrrrrrrrrrrr11111',badge)

        employee = self.env['hr.employee'].search(
            [('barcode', '=', badge)],
            limit=1
        )
        # print('rrrrrrrrrrrrrrrrrrrrrrrrrr1111111111',employee)
        # _logger.info('Grt 1st referral Deeeeeeeeeeeeeeetailsssssssssssssssssssssss')
        # _logger.info('Grt 1st referral Deeeeeeeeeeeeeeetailsssssssssssssssssssssss')
        # _logger.info('Grt 1st referral Deeeeeeeeeeeeeeetailsssssssssssssssssssssss')
        # _logger.info('Grt 1st referral Deeeeeeeeeeeeeeetailsssssssssssssssssssssss')
        # _logger.info('Grt 1st referral Deeeeeeeeeeeeeeetailsssssssssssssssssssssss')
        # _logger.info(employee.name)
        # _logger.info(employee.identification_id)
        # _logger.info(employee.department_id.name)
        # _logger.info(employee.job_id.name)
        # _logger.info(employee.private_street)
        # _logger.info(employee.work_phone)

        return {
            'name': employee.name,
            'identification_id': employee.identification_id,
            'dept': employee.department_id.name,
            # 'job': employee.job_id.name,
            # 'address': employee.private_street,
            'phone': employee.work_phone,
        }

    def get_second_referral_info(self):
        # print('rrrrrrrrrrrrrrrrrrrrrrrrrr22222222')
        if not self.x_studio_referral_2:
            return {}

        badge = self.x_studio_referral_2.badge_id
        # print('rrrrrrrrrrrrrrrrrrrrrrrrrr',badge)

        employee = self.env['hr.employee'].search(
            [('barcode', '=', badge)],
            limit=1
        )
        # print('rrrrrrrrrrrrrrrrrrrrrrrrrr',employee)

        return {
            'name': employee.name,
            'identification_id': employee.identification_id,
            'dept': employee.department_id.name,
            # 'job': employee.job_id.name,
            # 'address': employee.private_street,
            'phone': employee.work_phone,
        }

    def action_print_advance(self):
        return self.env.ref('lta_loan_report.action_report_lta_print_view').report_action(self)