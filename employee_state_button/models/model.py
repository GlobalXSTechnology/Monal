from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('gm_project', 'GM Project Approval'),
        ('hr_approval', 'HR Approval'),
        ('gm_hr', 'GM HR'),
    ], default='draft', tracking=True)

    is_locked = fields.Boolean(string="Locked", default=False,tracking=True)

    def action_lock(self):
        self.is_locked = True

    def action_unlock(self):
        self.is_locked = False

    def action_gm_project(self):
        for rec in self:
            rec.state = 'gm_project'

    # GM Project Approval → HR Approval
    def action_hr_approval(self):
        for rec in self:
            rec.state = 'hr_approval'

    # HR Approval → GM HR
    def action_gm_hr(self):
        for rec in self:
            rec.state = 'gm_hr'
            rec.is_locked = True

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.is_locked = False  # optional: unlock bhi kar de

    # # (Optional) Reset back to Draft
    # def action_reset_to_draft(self):
    #     for rec in self:
    #         rec.state = 'draft'
