# -*- coding: utf-8 -*-
from odoo import api, models

class ReportInternalTransfer(models.AbstractModel):
    _name = 'report.internal_transfer_report.report_internal_transfer'
    _description = 'Internal Transfer Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
        }