# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RejectionReason(models.Model):
	_name = "rejection.reason"
	_description = "Rejection Reason"


	name = fields.Char(string="Name")
	
	
	
class StockPicking(models.Model):
	_inherit = "stock.picking"


	rejection_reason_id = fields.Many2one('rejection.reason',string="Rejection Reason")
	
class QualityCheckWizard(models.TransientModel):
	_inherit = "quality.check.wizard"


	rejection_reason_id = fields.Many2one('rejection.reason',string="Rejection Reason")
	
	def do_fail(self):
		if not self.rejection_reason_id:
			raise UserError(_("Rejection Reason is Empty."))
		result = super(QualityCheckWizard, self).do_fail()
		self.current_check_id.write({
			'rejection_reason_id': self.rejection_reason_id.id
		})
		return result
	
class QualityCheck(models.Model):
	_inherit = "quality.check"


	rejection_reason_id = fields.Many2one('rejection.reason',string="Rejection Reason")
	
	def do_fail(self):
		if not self.rejection_reason_id:
			raise UserError(_("Rejection Reason is Empty."))
		result = super(QualityCheck, self).do_fail()
		return result

	