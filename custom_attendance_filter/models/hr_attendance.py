from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools.float_utils import float_compare
import logging
_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # @api.depends('worked_hours', 'check_in', 'check_out', 'out_mode')
    # def _compute_color(self):
    #     now = datetime.today()
    #     for rec in self:
    #         if rec.check_out:
    #             is_over = float_compare(rec.worked_hours, 23.59, precision_digits=2) == 1
    #             rec.color = 1 if (is_over or rec.out_mode == 'technical') else 0
    #         else:
    #             rec.color = 1 if rec.check_in and rec.check_in < (now - timedelta(days=1)) else 10

    # @api.depends('worked_hours', 'check_in', 'check_out', 'out_mode')
    def _compute_color(self):
        for attendance in self:
            _logger.info('Atttttteeendanceeeeeeeeeeeeeeeeeeeeee')
            _logger.info(attendance.worked_hours)
            _logger.info(attendance.out_mode)
            if attendance.check_out:
                _logger.info('in iffff')
                attendance.color = 1 if attendance.worked_hours > 23.99 or attendance.out_mode == 'technical' else 0
            else:
                _logger.info('elseeeeeeeee')
                attendance.color = 1 if attendance.check_in < (datetime.today() - timedelta(days=1)) else 10
