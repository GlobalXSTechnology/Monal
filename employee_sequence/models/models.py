from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # emp_sequence = fields.Char(string='Sequence', readonly=True)

    # @api.constrains('barcode')
    # def onchange_barcode(self):
    #     for rec in self:
    #         domain = [('barcode', '=', rec.barcode)]
    #         if rec.id:
    #             domain.append(('id', '!=', rec.id))
    #         existing = self.env['hr.employee'].search(domain)
    #         if existing:
    #             raise ValidationError(f'This Sequence number is already assigned to one of the employees({existing.employee_id.name})')


    def create(self, vals_list):
        if isinstance(vals_list, list):
            for vals in vals_list:
                if not vals.get('barcode'):
                    code = self._get_unique_barcode()
                    vals['barcode'] = code
        else:
            if not vals_list.get('barcode'):
                code = self._get_unique_barcode()
                vals_list['barcode'] = code
        _logger.info('employee_sequence_module')
        _logger.info('employee_sequence_module')
        _logger.info('employee_sequence_module')
        _logger.info('employee_sequence_module')
        
        return super(HrEmployee, self).create(vals_list)

    def _get_unique_barcode(self):
        seq = self.env['ir.sequence']
        code = seq.next_by_code('emp.sequence')
        while self.search_count([('barcode', '=', code)]):
            code = seq.next_by_code('emp.sequence')
        return code
