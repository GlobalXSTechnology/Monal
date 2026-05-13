from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)



class DepartmentGroup(models.Model):
    _name = 'department.group'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Department Group'

    name = fields.Char('Name', store=True, tracking=True)
    department_id = fields.Many2many('hr.department',string='Department', store=True, tracking=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id, store=True,
                                 tracking=True)

    def _onchange_department_id(self):
        for rec in self:
            _logger.info("onchange department_group id: %s", rec.id)

            if not rec.id:
                continue

            # Departments that were previously linked but now removed
            old_depts = self.env['hr.department'].search([
                ('department_group_ids', 'in', rec.id),
                ('id', 'not in', rec.department_id.ids or [])
            ])

            if old_depts:
                old_depts.write({
                    'department_group_ids': [(3, rec.id)]
                })

            # Add group to selected departments
            if rec.department_id:
                rec.department_id.write({
                    'department_group_ids': [(4, rec.id)]
                })

    def create(self, vals):
        rec = super().create(vals)

        if rec.department_id:
            rec.department_id.write({
                'department_group_ids': [(4, rec.id)]
            })

        return rec

    def write(self, vals):
        res = super().write(vals)

        for rec in self:

            # Find departments where this group exists but now removed
            old_depts = self.env['hr.department'].search([
                ('department_group_ids', 'in', rec.id),
                ('id', 'not in', rec.department_id.ids or [])
            ])

            if old_depts:
                old_depts.write({
                    'department_group_ids': [(3, rec.id)]
                })

            # Add this group to selected departments
            if rec.department_id:
                rec.department_id.write({
                    'department_group_ids': [(4, rec.id)]
                })

        return res


    # @api.onchange('department_id')
    # def _onchange_department_id(self):
    #     for rec in self:
    #         _logger.info("onchange department_group id: %s", rec.id)
    #         if not rec.id:
    #             _logger.info("record not saved yet, skipping DB write in onchange")
    #             continue
    #
    #         old_depts = self.env['hr.department'].search([
    #             ('department_group', '=', rec.id),
    #             ('id', 'not in', rec.department_id.ids or [])
    #         ])
    #         if old_depts:
    #             old_depts.write({'department_group': False})
    #
    #         if rec.department_id:
    #             rec.department_id.write({'department_group': rec.id})

    # def create(self, vals):
    #     rec = super().create(vals)
    #     if rec.department_id:
    #         self.env['hr.department'].search([
    #             ('department_group', '=', rec.id),
    #             ('id', 'not in', rec.department_id.ids or [])
    #         ]).write({'department_group': False})
    #         rec.department_id.write({'department_group': rec.id})
    #     return rec

    # def write(self, vals):
    #     res = super().write(vals)
    #     for rec in self:
    #         self.env['hr.department'].search([
    #             ('department_group', '=', rec.id),
    #             ('id', 'not in', rec.department_id.ids or [])
    #         ]).write({'department_group': False})
    #         if rec.department_id:
    #             rec.department_id.write({'department_group': rec.id})
    #     return res



class HrDepartment(models.Model):
    _inherit = 'hr.department'

    department_group = fields.Many2one('department.group', string='Department Group', store=True, tracking=True)
    department_group_ids = fields.Many2many('department.group', string='Department Groups', store=True, tracking=True)
