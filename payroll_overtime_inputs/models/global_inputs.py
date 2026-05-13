from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, time
import calendar
import logging

_logger = logging.getLogger(__name__)


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    global_input_id = fields.Many2one('global.input', string="Global Input")

    # def unlink(self):
    #     for rec in self:
    #         if rec.payslip_id and rec.payslip_id.applied_global_input_ids:
    #             rec.payslip_id.write({
    #                 'applied_global_input_ids': [(5, 0, 0)]
    #             })
    #     return super().unlink()

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
                print(amount, rec.payslip_id.employee_id.name)
                rec.sudo().write({'amount': amount})


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
    equal_amount = fields.Boolean('Equal Amount', tracking=True)
    amount = fields.Float('Amount', tracking=True, store=True, compute='compute_lines_mount')
    input_line_ids = fields.One2many(
        'global.input.line', 'input_id', string='Payslip Inputs', store=True,
        readonly=False)
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Type', tracking=True)
    group_departments = fields.Many2many('hr.department', 'Departments', store=True, compute='department_group_compute',
                                         tracking=True)

    @api.depends('department_group')
    def department_group_compute(self):
        for rec in self:
            if rec.department_group:
                rec.group_departments = rec.department_group.department_id
            else:
                rec.group_departments = [(5, 0, 0)]

    month = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string="Month",
        required=True,
        tracking=True
    )

    def _get_month_selection(self):
        months = [
            ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
            ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        month_selection = []
        for year in range(2025, 2035):
            for code, name in months:
                month_selection.append((f'{year}-{code}', f'{name} {year}'))
        return month_selection

    @api.depends('input_line_ids.amount')
    def compute_lines_mount(self):
        for rec in self:
            amount = 0
            for line in rec.input_line_ids:
                if line.amount:
                    amount += line.amount
            rec.amount = round(amount)

    @api.onchange('month')
    def _onchange_month(self):
        if self.month:
            year, month = map(int, self.month.split('-'))
            self.date_from = f'{year}-{month:02d}-01'
            last_day = calendar.monthrange(year, month)[1]
            self.date_to = f'{year}-{month:02d}-{last_day}'

    @api.depends('apply_by')
    def set_emp(self):
        for rec in self:
            rec.is_emp = (rec.apply_by == 'emp')

    @api.onchange('apply_by')
    def onchangeapply(self):
        self.batch_id = None
        self.department_id = None

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
                ('employee_id.department_id.department_group_ids', 'in', self.department_group.id),
                ('company_id', '=', self.company_id.id),
                ('state', 'in', ['draft', 'verify'])])
        else:
            raise ValidationError(_('Unable to find any payslip to perform action on.'))

        if not payslips:
            raise ValidationError(_('No payslips found for the selected criteria.'))

        return payslips

    def _get_attendance_data(self, payslips):
        from datetime import datetime, time

        if not payslips:
            return {}, 0, 0, None, None

        date_from = min(payslips.mapped('date_from'))
        date_to = max(payslips.mapped('date_to'))

        current_month_start = datetime.combine(date_from, time.min)
        current_month_end = datetime.combine(date_to, time.max)

        #employees = payslips.mapped('employee_id')
        employees = payslips.filtered(lambda x:not x.contract_id.date_end or x.contract_id.date_end >= x.date_from).mapped('employee_id')
        emp_ids = employees.ids

        # Fetch ALL attendances for all employees in one query
        all_attendances = self.env['hr.attendance'].search([
            ('employee_id', 'in', emp_ids),
            ('attend_check_in', '>=', date_from),
            ('attend_check_in', '<=', date_to),
        ])
        _logger.info("all Attendancesssssssssssssssss")
        _logger.info(len(all_attendances))

        attendance_map = {}
        total_attendance = 0

        for emp in employees:
            resource_calendar = emp.resource_calendar_id
            contract = emp.contract_id

            # emp_att = all_attendances.filtered(lambda a: a.employee_id.id == emp.id and a.check_in and a.check_out )
            contract_start = contract.date_start if contract and contract.date_start else date_from
            emp_att = all_attendances.filtered(
                lambda a: (
                    a.employee_id.id == emp.id
                    and a.check_in
                    and a.check_out
                    and a.check_in.date() >= contract_start
                )
            )
            if not (resource_calendar and resource_calendar.x_studio_is_zero):
                # Only count check-ins where worked_hours >= 6
                emp_att = emp_att.filtered(lambda a: a.worked_hours >= 6)

            # Count unique days
            # unique_days = set(att.attend_check_in for att in emp_att if att.attend_check_in)
            #emp_attendance = len(unique_days)
            emp_attendance = len(emp_att)

            attendance_map[emp.id] = emp_attendance
            total_attendance += emp_attendance

        unique_employees = len(employees)
        total_attendance = total_attendance

        _logger.info("PPPPPPPPPPPP")
        _logger.info(total_attendance)

        return attendance_map, total_attendance, unique_employees, current_month_start, current_month_end

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            if not self.input_line_ids:
                raise ValidationError(_('No lines to add in payslips.'))
            payslips = self.get_payslips()
            attendance_map, attendance_count, unique_employees, _, _ = self._get_attendance_data(payslips)

            for slip in payslips:
                EmployeeGlobalInput = self.env['employee.global.input']
                # attendance_count_total = sum(payslips.mapped('attendance_count'))
                employee = slip.employee_id
                resource_calendar = employee.resource_calendar_id
                contract = employee.contract_id
                if not contract:
                    continue

                if contract.date_end and contract.date_end < self.date_from:
                    continue

                emp_attendance = attendance_map.get(employee.id, 0)

                if self.apply_by == 'emp':
                    employee_input = EmployeeGlobalInput.search([
                        ('employee_id', '=', slip.employee_id.id),
                        ('global_input_id', '=', self.id)
                    ], limit=1)

                    if not employee_input:
                        employee_input = EmployeeGlobalInput.create({
                            'employee_id': slip.employee_id.id,
                            'date_from': self.date_from,
                            'date_to': self.date_to,
                            'apply_by': self.apply_by,
                            'month': self.month,
                            'global_input_id': self.id,
                            'batch_id': self.batch_id.id,
                            'department_id': slip.employee_id.department_id.id,
                            'department_group': slip.employee_id.department_id.department_group.id if slip.employee_id.department_id.department_group else False,
                            'company_id': slip.company_id.id,
                            'present_days': emp_attendance,  # CHANGED: Use individual employee attendance

                        })

                    emp_lines = self.input_line_ids.filtered(lambda l: l.employee_id == slip.employee_id)
                    emp_input_lines = []

                    for line in emp_lines:
                        if line.input_id.is_service:
                            per_attendance = line.amount / attendance_count if attendance_count else 0
                            xyz = per_attendance * emp_attendance
                            # xyz = attendance_count
                        elif line.input_id.equal_amount:
                            xyz = line.amount / unique_employees if unique_employees else 0
                        else:
                            xyz = line.amount

                        existing_line = employee_input.input_line_ids.filtered(
                            lambda l: l.input_type_id.id == line.input_type_id.id)
                        if xyz:
                            if existing_line:
                                existing_line.amount += xyz
                            else:
                                emp_input_lines.append((0, 0, {
                                    'name': line.input_type_id.name,
                                    'input_type_id': line.input_type_id.id,
                                    'amount': round(xyz),
                                    'global_input_id': self.id,
                                    'employee_id': slip.employee_id.id,
                                    'apply_by': self.apply_by,
                                    'month': self.month,
                                }))

                    if emp_input_lines:
                        employee_input.write({'input_line_ids': emp_input_lines})

                else:
                    # For all other apply_by types (batch, dept, comp, group_department)
                    emp = slip.employee_id
                    emp_input = EmployeeGlobalInput.search([
                        ('employee_id', '=', emp.id),
                        ('global_input_id', '=', self.id)
                    ], limit=1)

                    if emp_input:
                        continue  # already created

                    # emp_attendance = slip.attendance_count if slip else 0

                    emp_input = EmployeeGlobalInput.create({
                        'employee_id': emp.id,
                        'date_from': self.date_from,
                        'date_to': self.date_to,
                        'apply_by': self.apply_by,
                        'month': self.month,
                        'global_input_id': self.id,
                        'batch_id': self.batch_id.id,
                        'department_id': emp.department_id.id,
                        'department_group': emp.department_id.department_group.id if emp.department_id.department_group else False,
                        'company_id': emp.company_id.id,
                        'present_days': emp_attendance,  # CHANGED: Use individual employee attendance

                    })

                    emp_input_lines = []
                    for line in self.input_line_ids:
                        if line.input_id.is_service:
                            per_attendance = line.amount / attendance_count if attendance_count else 0
                            xyz = per_attendance * emp_attendance
                            # xyz = attendance_count
                        elif line.input_id.equal_amount:
                            xyz = line.amount / unique_employees if unique_employees else 0
                        else:
                            xyz = line.amount
                        if xyz:
                            emp_input_lines.append((0, 0, {
                                'name': line.input_type_id.name,
                                'input_type_id': line.input_type_id.id,
                                'amount': round(xyz),
                                'global_input_id': self.id,
                                'employee_id': emp.id,
                                'apply_by': self.apply_by,
                                'month': self.month,
                            }))

                    if emp_input_lines:
                        emp_input.write({'input_line_ids': emp_input_lines})

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
                ('employee_id.department_id.department_group_ids', 'in', self.department_group.id),
                ('company_id', '=', self.company_id.id),
                ('state', 'in', ['draft', 'verify'])])
        else:
            raise ValidationError(_('Unable to find any payslip to perform action on.'))

        if not payslips:
            raise ValidationError(_('No payslips found for the selected criteria.'))

        return payslips

    def set_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})
            payslips = self.get_payslips()

            for slip in payslips:
                if rec in slip.applied_global_input_ids:
                    slip.applied_global_input_ids = [(3, rec.id)]

                # if rec in slip.applied_global_input_ids:
                #     a = slip.applied_global_input_ids.ids
                #     b = rec.ids
                #     result = [x for x in a if x not in b]
                #     slip.applied_global_input_ids = result

                for line in slip.input_line_ids:
                    if line.global_input_id.id == rec.id:
                        line.unlink()

            employee_global_input = self.env['employee.global.input'].search([
                ('global_input_id', '=', rec.id)
            ])
            employee_global_input.unlink()

    def add_inputs(self):
        if not self.input_line_ids:
            raise ValidationError(_('No lines to add in payslips.'))

        payslips = self.get_payslips()
        # attendance_count = sum(payslips.mapped('attendance_count'))
        attendance_map, total_attendance_count, total_employees, _, _ = self._get_attendance_data(payslips)

        for slip in payslips:

            if self in slip.applied_global_input_ids:
                continue
            emp = slip.employee_id
            emp_attendance = attendance_map.get(emp.id, 0)

            input_vals = []
            if self.apply_by == 'emp':

                hj = []
                for line in self.input_line_ids:
                    print(line.employee_id.name)
                    if slip.employee_id.id == line.employee_id.id:
                        hj.append(line.input_type_id.id)

                        if line.input_id.is_service:
                            per_attendance = line.amount / total_attendance_count if total_attendance_count else 0
                            # xyz = per_attendance * slip.attendance_count
                            xyz = per_attendance * emp_attendance
                        elif line.input_id.equal_amount:
                            # unique_employees = len(set(payslips.mapped('employee_id.id')))
                            # xyz = line.amount / unique_employees if unique_employees else 0
                            xyz = line.amount / total_employees if total_employees else 0
                        else:
                            xyz = line.amount
                        print('-------', xyz)

                        existing_line = slip.input_line_ids.filtered(lambda
                                                                         l: l.input_type_id.id == line.input_type_id.id and line.employee_id.id == slip.employee_id.id and slip.id == l.payslip_id.id)

                        if existing_line:
                            existing_line.amount += xyz
                        else:

                            existing_line = self.env['hr.payslip.input'].create({
                                "name": line.input_type_id.name,
                                "global_input_id": line.input_id.id,
                                "input_type_id": line.input_type_id.id,
                                "amount": round(xyz),
                                'payslip_id': slip.id,
                            })
                        print(existing_line)



            else:
                totals_by_input = {}
                for rec in self.input_line_ids:
                    if rec.input_id.is_service:
                        per_attendance = rec.amount / total_attendance_count if total_attendance_count else 0
                        xyz = per_attendance * emp_attendance
                    elif rec.input_id.equal_amount:
                        xyz = rec.amount / total_employees if total_employees else 0
                    else:
                        xyz = rec.amount
                    totals_by_input[rec.input_type_id.id] = totals_by_input.get(rec.input_type_id.id, 0) + xyz

                for input_type_id, total_amount in totals_by_input.items():
                    existing_line = slip.input_line_ids.filtered(
                        lambda l: l.input_type_id.id == input_type_id
                    )
                    if existing_line:
                        existing_line.amount += total_amount
                    else:
                        input_type = self.env['hr.payslip.input.type'].browse(input_type_id)
                        input_vals.append((0, 0, {
                            "global_input_id": self.id,
                            "name": input_type.name,
                            "input_type_id": input_type_id,
                            "amount": round(total_amount),
                        }))

            if input_vals:
                slip.write({"input_line_ids": input_vals})

            slip.write({"applied_global_input_ids": [(4, self.id)]})
            slip.compute_sheet()

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

    @api.onchange('batch_id')
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

    @api.onchange('department_id')
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

    @api.onchange('apply_by', 'company_id', 'date_from', 'date_to')
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
        elif self.input_id.equal_amount:
            unique_employees = len(set(payslips.mapped('employee_id.id')))
            if unique_employees:
                return rec.amount / unique_employees if unique_employees else 0
            else:
                return 0.0
        else:
            return self.amount

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.input_id.state == 'done':
                raise ValidationError(_("You cannot modify a Global Input Line in 'Done' state."))
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
