from odoo import models, api, fields
from datetime import date, timedelta, datetime, date
from calendar import monthrange
import calendar
from odoo.exceptions import ValidationError
import math
import logging

_logger = logging.getLogger(__name__)

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('identification_id')
    def _check_unique_cnic(self):
        for rec in self:
            if rec.identification_id:
                current_cnic = rec.identification_id.replace('-', '').replace(' ', '')
                employees = self.search([
                    ('id', '!=', rec.id),
                    ('identification_id', '!=', False)
                ])

                duplicate = employees.filtered(
                    lambda e: e.identification_id.replace('-', '').replace(' ', '') == current_cnic
                )
                if duplicate:
                    raise ValidationError(
                        f"Employee with CNIC {rec.identification_id} already exists: {duplicate[0].name}"
                    )

    # @api.constrains('identification_id')
    # def _check_unique_cnic(self):
    #     for rec in self:
    #         if rec.identification_id:
    #             duplicate = self.search([
    #                 ('id', '!=', rec.id),
    #                 ('identification_id', '=', rec.identification_id)
    #             ], limit=1)
    #             if duplicate:
    #                 raise ValidationError(
    #                     f"Employee with CNIC {rec.identification_id} already exists: {duplicate.name}"
    #                 )