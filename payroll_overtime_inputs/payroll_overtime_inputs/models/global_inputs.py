from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    global_input_id = fields.Many2one('global.input', string="Global Input")

    def unlink(self):
        for rec in self:
            if rec.payslip_id and rec.payslip_id.applied_global_input_ids:
                rec.payslip_id.write({
                    'applied_global_input_ids': [(5, 0, 0)]
                })
        return super().unlink()


    def recalculate_amount_input_line(self):
        for rec in self:
            if rec.payslip_id.applied_global_input_ids:
                global_inputs = rec.payslip_id.applied_global_input_ids.input_line_ids.filtered \
                    (lambda a: a.input_type_id == rec.input_type_id)
                amount = 0
                for input in global_inputs:
                    if input.input_id.is_service:
                        amount += (rec.payslip_id.attendance_count * input.get_add_input_lines_amount())
                    else:
                        amount += input.get_add_input_lines_amount()
                _logger.info \
                    ('amountamountamountamountamountamountamountamountamountamountamountamountamountamountamountamountamountamountamountamount')
                _logger.info \
                    ('amountamountamountamountamountamountamountamountamountamountamountamountamountamountamountamountamountamountamountamount')
                rec.sudo().write({'amount' : amount})



class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    applied_global_input_ids = fields.Many2many(
        'global.input',
        'payslip_global_input_rel',
        'payslip_id', 'global_input_id',
        string="Applied Global Inputs"
    )


class GlobalInputs(models.Model):
    _name = 'global.input'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Global Input'

    name = fields.Char('Name', store=True, tracking=True)
    date_to = fields.Date(string='Date To', required=True, tracking=True)
    date_from = fields.Date(string='Date From', required=True, tracking=True)
    apply_by = fields.Selection([
        ('batch', "Batch"),
        ('dpt', "Department"),
        ('comp', "Company"),
        ('emp', "Employees"),
        ('group_department', "Group By Department"),
    ], string="Apply Inputs By", default='batch', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft')
    batch_id = fields.Many2one('hr.payslip.run', 'Batch', tracking=True)
    department_id = fields.Many2one('hr.department', 'Department', tracking=True)
    department_group = fields.Many2one('department.group', string='Department Group')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id, store=True,
                                 tracking=True)
    is_emp = fields.Boolean('By Employee', compute='set_emp', store=True, tracking=True)
    is_service = fields.Boolean('Service', tracking=True)
    amount = fields.Float('Amount', tracking=True)
    input_line_ids = fields.One2many(
        'global.input.line', 'input_id', string='Payslip Inputs', store=True,
        readonly=False)
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Type', tracking=True)

    def set_draft(self):
        self.write({'state': 'draft'})

    @api.depends('apply_by')
    def set_emp(self):
        for rec in self:
            rec.is_emp = (rec.apply_by == 'emp')

    @api.onchange('apply_by')
    def onchangeapply(self):
        self.batch_id = None
        self.department_id = None

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def get_payslips(self):

        payslip_model = self.env['hr.payslip']

        # find payslips by selection criteria
        if self.batch_id and self.apply_by == 'batch':
            payslips = payslip_model.search([
                ('payslip_run_id', '=', self.batch_id.id),
                ('date_to', '<=', self.date_to),
                ('date_from', '>=', self.date_from),
                ('company_id', '=', self.company_id.id),
                ('state', 'in', ['draft', 'verify'])
            ])
        elif self.company_id and self.apply_by == 'comp':
            payslips = payslip_model.search([
                ('date_to', '<=', self.date_to),
                ('date_from', '>=', self.date_from),
                ('company_id', '=', self.company_id.id),
                ('state', 'in', ['draft', 'verify'])])
        elif self.department_id and self.apply_by == 'dpt':
            payslips = payslip_model.search([
                ('date_to', '<=', self.date_to),
                ('date_from', '>=', self.date_from),
                ('employee_id.department_id', '=', self.department_id.id),
                ('company_id', '=', self.company_id.id),
                ('state', 'in', ['draft', 'verify'])])
        elif self.apply_by == 'emp':
            payslips = payslip_model.search([
                ('date_to', '<=', self.date_to),
                ('date_from', '>=', self.date_from),
                ('employee_id', 'in', self.input_line_ids.mapped('employee_id').ids),
                ('company_id', '=', self.company_id.id),
                ('state', 'in', ['draft', 'verify'])])
        elif self.apply_by == 'group_department':
            payslips = payslip_model.search([
                ('date_to', '<=', self.date_to),
                ('date_from', '>=', self.date_from),
                ('employee_id.department_id.department_group', '=', self.department_group.id),
                ('company_id', '=', self.company_id.id),
                ('state', 'in', ['draft', 'verify'])])
        else:
            raise ValidationError(_('Unable to find any payslip to perform action on.'))

        if not payslips:
            raise ValidationError(_('No payslips found for the selected criteria.'))

        return payslips

    def add_inputs(self):
        if not self.input_line_ids:
            raise ValidationError(_('No lines to add in payslips.'))
        payslips = self.get_payslips()

        attendance_count = sum(payslips.mapped('attendance_count'))

        for slip in payslips:
            if not self.input_line_ids:
                continue

            # 1. Check if this global.input already applied
            if self in slip.applied_global_input_ids:
                continue  # Skip, already applied

            # 2. Collect totals grouped by input_type_id
            totals_by_input = {}
            for rec in self.input_line_ids:
                if rec.input_id.is_service:
                    abc = rec.amount / attendance_count if attendance_count else 0
                    xyz = abc * slip.attendance_count
                else:
                    xyz = rec.amount

                if rec.input_type_id.id not in totals_by_input:
                    totals_by_input[rec.input_type_id.id] = 0
                totals_by_input[rec.input_type_id.id] += xyz

            # 3. Apply totals
            input_vals = []
            for input_type_id, total_amount in totals_by_input.items():
                existing_line = slip.input_line_ids.filtered(
                    lambda l: l.input_type_id.id == input_type_id
                )

                if existing_line:
                    existing_line.amount += total_amount
                else:
                    input_type = self.env['hr.payslip.input.type'].browse(input_type_id)

                    vals = {
                        "name": input_type.name or "Unknown Input Type",
                        "input_type_id": input_type_id,
                        "amount": total_amount,
                    }
                    input_vals.append((0, 0, vals))

            if input_vals:
                slip.write({"input_line_ids": input_vals})

            # 4. Mark this global.input as applied
            slip.write({"applied_global_input_ids": [(4, self.id)]})
            slip.compute_sheet()

            employee_input = self.env['employee.global.input'].create({
                'employee_id': slip.employee_id.id,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'apply_by': self.apply_by,
                'global_input_id': self.id if self.id else False,
                'batch_id': self.batch_id.id if self.batch_id else False,
                'department_id': self.department_id.id if self.department_id else False,
                'department_group': self.department_group.id if self.department_group else False,
                'company_id': self.company_id.id,
            })

            employee_input_lines = []
            totals_by_input_type = {}

            input_lines = self.input_line_ids
            if self.apply_by == 'emp':
                input_lines = self.input_line_ids.filtered(lambda l: l.employee_id == slip.employee_id)

            for rec in input_lines:
                if rec.input_id.is_service:
                    abc = rec.amount / attendance_count if attendance_count else 0
                    xyz = abc * slip.attendance_count
                    print("LLLLLLLLLLLLLLLLLLL")
                    print(attendance_count)
                    print(slip.attendance_count)
                    print(abc)
                    print(xyz)
                else:
                    xyz = rec.amount

                if rec.input_type_id.id not in totals_by_input_type:
                    totals_by_input_type[rec.input_type_id.id] = {
                        'name': rec.name,
                        'sequence': rec.sequence,
                        'amount': xyz,
                    }
                else:
                    totals_by_input_type[rec.input_type_id.id]['amount'] += xyz

            employee_input_lines = [
                (0, 0, {
                    'input_type_id': input_type_id,
                    'name': vals['name'],
                    'sequence': vals['sequence'],
                    'amount': vals['amount'],
                })
                for input_type_id, vals in totals_by_input_type.items()
            ]

            if employee_input_lines:
                employee_input.write({'input_line_ids': employee_input_lines})

        payslips.input_line_ids.recalculate_amount_input_line()
        self.state = 'done'

    def action_view_employee_input(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Employee Global Input'),
            'res_model': 'employee.global.input',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('payroll_overtime_inputs.view_employee_global_input_tree').id, 'list'),
                (self.env.ref('payroll_overtime_inputs.view_employee_global_inp_master_form').id, 'form'),
            ],
            'domain': [('global_input_id', '=', self.id)],
            'target': 'current',
        }

    @api.onchange('batch_id', 'amount', 'date_from', 'date_to')
    def _onchange_batch_summary(self):
        if self.apply_by != 'batch':
            return
        if not (self.batch_id and self.date_from and self.date_to and self.amount):
            self.input_line_ids = [(5, 0, 0)]
            return

        payslips = self.env['hr.payslip'].search([
            ('payslip_run_id', '=', self.batch_id.id),
            ('company_id', '=', self.company_id.id),
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
        ])

        if not payslips:
            raise ValidationError(_('No payslips found for selected batch and date range.'))

        attendance_obj = self.env['hr.attendance']
        total_attendance_days = 0

        for emp in payslips.mapped('employee_id'):
            records = attendance_obj.search([
                ('employee_id', '=', emp.id),
                ('check_in', '>=', self.date_from),
                ('check_in', '<=', self.date_to),
            ])
            unique_days = set(att.check_in.date() for att in records if att.check_in)
            total_attendance_days += len(unique_days)

        if total_attendance_days == 0:
            raise ValidationError(_('Total attendance days is zero.'))

        self.input_line_ids = [(5, 0, 0), (0, 0, {
            'attendance': total_attendance_days,
            'amount': self.amount,
            'name': _('Batch %s', self.batch_id.name),
            'input_type_id': self.input_type_id.id if self.input_type_id else False,
        })]

    @api.onchange('department_id', 'amount', 'date_from', 'date_to')
    def _onchange_department_id_or_amount(self):
        if self.apply_by != 'dpt' or not self.department_id or not self.amount:
            self.input_line_ids = [(5, 0, 0)]
            return
        if not self.date_from or not self.date_to:
            raise ValidationError(_('Please set the date range first.'))

        payslips = self.env['hr.payslip'].search([
            ('department_id', '=', self.department_id.id),
            ('company_id', '=', self.company_id.id),
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
        ])

        if not payslips:
            raise ValidationError(_('No payslips found for this department and date range.'))

        attendance_obj = self.env['hr.attendance']
        total_attendance_days = 0

        for emp in payslips.mapped('employee_id'):
            attendances = attendance_obj.search([
                ('employee_id', '=', emp.id),
                ('check_in', '>=', self.date_from),
                ('check_in', '<=', self.date_to)
            ])
            unique_days = set(att.check_in.date() for att in attendances if att.check_in)
            total_attendance_days += len(unique_days)

        if total_attendance_days == 0:
            raise ValidationError(_('Total attendance days is zero.'))

        # Only one line
        self.input_line_ids = [(5, 0, 0), (0, 0, {
            'attendance': total_attendance_days,
            'amount': self.amount,
            'name': _('Department %s', self.department_id.name),
            'input_type_id': self.input_type_id.id if self.input_type_id else False,
        })]

    @api.onchange('apply_by', 'company_id', 'date_from', 'date_to', 'amount')
    def _onchange_company_apply(self):
        if self.apply_by != 'comp' or not (self.company_id and self.date_from and self.date_to and self.amount):
            self.input_line_ids = [(5, 0, 0)]
            return

        payslips = self.env['hr.payslip'].search([
            ('company_id', '=', self.company_id.id),
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
        ])

        if not payslips:
            raise ValidationError("No employee payslips found for selected company and date range.")

        attendance_obj = self.env['hr.attendance']
        total_attendance_days = 0

        for emp in payslips.mapped('employee_id'):
            records = attendance_obj.search([
                ('employee_id', '=', emp.id),
                ('check_in', '>=', self.date_from),
                ('check_in', '<=', self.date_to),
            ])
            unique_days = set(att.check_in.date() for att in records if att.check_in)
            total_attendance_days += len(unique_days)

        if total_attendance_days == 0:
            raise ValidationError("Total attendance days is zero for selected employees.")

        # Only one line
        self.input_line_ids = [(5, 0, 0), (0, 0, {
            'attendance': total_attendance_days,
            'amount': self.amount,
            'name': _('Company %s', self.company_id.name),
            'input_type_id': self.input_type_id.id if self.input_type_id else False,
        })]


    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise ValidationError(_("You cannot delete a Global Input in 'Done' state."))
            rec.input_line_ids.unlink()
        return super(GlobalInputs, self).unlink()


class GlobalInputLine(models.Model):
    _name = 'global.input.line'

    name = fields.Char(string="Description")
    input_id = fields.Many2one('global.input', string='Global Input', ondelete='cascade', index=True)
    sequence = fields.Integer(required=True, index=True, default=10)
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Type', required=True, store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    attendance = fields.Integer(string='Attendance')
    code = fields.Char(related='input_type_id.code', required=True,
                       help="The code that can be used in the salary rules")
    amount = fields.Float(string="Amount")


    def get_add_input_lines_amount(self):
        payslips = self.input_id.get_payslips()
        attendance_count = sum(payslips.mapped('attendance_count'))
        if self.input_id.is_service:
            if attendance_count and self.amount:
                return self.amount / attendance_count
            else:
                return 0.0
        else:
            return self.amount

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.input_id.state == 'done':
                raise ValidationError(_("You cannot modify a Global Input Line in 'Done' state."))
            # rec._update_payslip_inputs()
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.input_id.date_from and self.input_id.date_to and self.input_id.is_service:
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', self.employee_id.id),
                ('check_in', '>=', self.input_id.date_from),
                ('check_in', '<=', self.input_id.date_to)
            ])
            unique_days = set(att.check_in.date() for att in attendances if att.check_in)
            self.attendance = len(unique_days)
            # self.input_id._onchange_distribute_amount()

    @api.onchange('input_id')
    def _onchange_input_id(self):
        if self.input_id and self.input_id.input_type_id and self.input_id.apply_by == 'emp' and self.input_id.is_service:
            if not self.input_type_id:
                self.input_type_id = self.input_id.input_type_id