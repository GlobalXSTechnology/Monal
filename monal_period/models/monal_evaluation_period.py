from odoo import models, api, fields
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging
from dateutil.relativedelta import relativedelta

import calendar

_logger = logging.getLogger(__name__)


class MonalEvaluationPeriod(models.Model):
    _name = 'monal.evaluation.period'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Monal Evaluation Period'
    _rec_name = 'name'


    month = fields.Selection([
        ('01', 'January'),
        ('02', 'February'),
        ('03', 'March'),
        ('04', 'April'),
        ('05', 'May'),
        ('06', 'June'),
        ('07', 'July'),
        ('08', 'August'),
        ('09', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string="Month", tracking=True)
    period_start_date = fields.Date(string="Period Start Date", compute="_compute_period_dates", store=True)
    period_end_date = fields.Date(string="Period End Date", compute="_compute_period_dates", store=True)
    name = fields.Char(string="Name", compute="_compute_name", store=True)

    @api.depends('month', 'period_start_date')
    def _compute_name(self):
        for rec in self:
            month_label = dict(self._fields['month'].selection).get(rec.month, "")
            year = rec.period_start_date.year if rec.period_start_date else date.today().year
            rec.name = f"{month_label} {year}" if month_label else "New"

    @api.depends('month')
    def _compute_period_dates(self):
        for rec in self:
            start_date = end_date = False

            if rec.month:
                year = date.today().year
                month = int(rec.month)
                start_date = date(year, month, 1)
                last_day = calendar.monthrange(year, month)[1]
                end_date = date(year, month, last_day)

            rec.period_start_date = start_date
            rec.period_end_date = end_date
