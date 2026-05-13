from odoo import models, api, fields, _
from datetime import date, timedelta, datetime, date
from calendar import monthrange
import calendar
from odoo.exceptions import ValidationError
import math
import logging

_logger = logging.getLogger(__name__)


class BulkLeaveEncashment(models.TransientModel):
    _name = 'bulk.leave.encashment'

    department_ids = fields.Many2many('hr.department', string='Departments')
    # period_id = fields.Many2one('monal.evaluation.period', string='Period', required=True)
    employee_ids = fields.One2many('bulk.leave.encashment.line', 'wizard_id', string='Employees')
    attendance_line_ids = fields.One2many('bulk.attendance.encashment.line', 'wizard_id', string='Attendance Encashment')
    duration_display = fields.Float(string='Available Leaves')
    month = fields.Selection(
        selection=lambda self: self._get_month_selection(),
        string="Month",
        required=True,
        tracking=True
    )
    month_start_date = fields.Date(string='Month start Date ', tracking=True)
    month_end_date = fields.Date(string='Month End Date', tracking=True)



    def _get_month_selection(self):
        months = [
            ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
            ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        month_selection = []
        for year in range(2025, 2041):
            for code, name in months:
                month_selection.append((f'{year}-{code}', f'{name} {year}'))
        return month_selection

    @api.onchange('month')
    def _onchange_month(self):
        if self.month:
            year, month = map(int, self.month.split('-'))
            self.month_start_date = f'{year}-{month:02d}-01'
            last_day = calendar.monthrange(year, month)[1]
            self.month_end_date = f'{year}-{month:02d}-{last_day}'
            self._onchange_department_ids()


    def _get_working_days(self, start_date, end_date):
        _logger.info('getttttttt pof dayssssssssssssssss')
        _logger.info('getttttttt pof dayssssssssssssssss')
        working_days = 0
        current = start_date
        _logger.info(start_date)

        while current <= end_date:
            if current.weekday() != 6:  # 6 = Sunday
                working_days += 1
            current += timedelta(days=1)
        _logger.info(working_days)
        return working_days

    def action_load_employees(self):
        for rec in self:
            if not rec.month:
                raise ValidationError("Please select a month first.")

            start_date = rec.month_start_date
            end_date = rec.month_end_date

            domain = [('company_id', '=', self.env.company.id)]
            if rec.department_ids:
                domain.append(('department_id', 'in', rec.department_ids.ids))
            employees = self.env['hr.employee'].search(domain)

            leave_lines = []
            attendance_lines = []

            for emp in employees:
                if emp.resource_calendar_id.x_studio_is_zero:
                    present_days = self.env['hr.attendance'].search_count([
                        ('employee_id', '=', emp.id),
                        ('check_in', '>=', start_date),
                        ('check_in', '<=', end_date),
                    ])
                else:
                    present_days = self.env['hr.attendance'].search_count([
                        ('employee_id', '=', emp.id),
                        ('check_in', '>=', start_date),
                        ('check_in', '<=', end_date),
                        ('worked_hours', '>=', 6),
                    ])

                if present_days <= 0:
                    continue

                prev_enc = self.env['leave.encashment'].search([
                    ('em_p', '=', emp.id),
                    ('month', '=', rec.month),
                    ('state', 'in', ['draft', 'submit_to_approve', 'approve']),
                ])

                previous_leave_used = sum(prev_enc.mapped('tree_line.encash_leaves'))
                previous_att_used = sum(prev_enc.mapped('attendance_lines.encash_2'))

                leave_types = self.env['hr.leave.type'].search([('leave_encash', '=', True)])
                total_available_leaves = 0

                for leave_type in leave_types:
                    allocations = self.env['hr.leave.allocation'].search([
                        ('employee_id', '=', emp.id),
                        ('holiday_status_id', '=', leave_type.id),
                        ('state', '=', 'validate'),
                        ('month', '=', rec.month),
                    ]).mapped('number_of_days')

                    duration_display = sum(allocations)
                    available = duration_display - previous_leave_used

                    if available > 0:
                        if available < 0:
                            available = 0
                        total_available_leaves += available
                        leave_lines.append((0, 0, {
                            'employee_id': emp.id,
                            'attendance_count': present_days,
                            'remaining_weekly_off': available,
                        }))

                if total_available_leaves > 0:
                    working_days = self._get_working_days(start_date, end_date)
                    extra_days = present_days - working_days
                    extra_after_leave = extra_days - total_available_leaves - previous_leave_used - previous_att_used
                    extra_after_leave = max(extra_after_leave, 0)

                    if extra_after_leave > 0:
                        attendance_lines.append((0, 0, {
                            'employee_id': emp.id,
                            'present_days': present_days,
                            'extra_days': extra_after_leave,
                            'days_to_encash': 0.0,
                        }))
                    continue

                total_month_days = (end_date - start_date).days + 1
                sundays = len(
                    [d for d in (start_date + timedelta(days=i) for i in range(total_month_days)) if d.weekday() == 6])
                working_days = total_month_days - sundays

                extra_days = present_days - working_days
                remaining_days = extra_days - previous_att_used - total_available_leaves - previous_leave_used

                if remaining_days > 0:
                    attendance_lines.append((0, 0, {
                        'employee_id': emp.id,
                        'present_days': present_days,
                        'extra_days': remaining_days,
                        'days_to_encash': 0.0,
                    }))

            rec.write({
                'employee_ids': [(5, 0, 0)] + leave_lines,
                'attendance_line_ids': [(5, 0, 0)] + attendance_lines,
            })

        # Return same wizard to keep popup open
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.leave.encashment',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # @api.onchange('department_ids', 'month')
    def _onchange_department_ids(self):
        _logger.info('Bulk Encashment Onchange Triggered')

        if not self.month:
            self.employee_ids = [(5, 0, 0)]
            self.attendance_line_ids = [(5, 0, 0)]
            return

        start_date = self.month_start_date
        end_date = self.month_end_date
        _logger.info(f"startttttttttttttttttttttt dateeeeeeeeeeeeeeeeeeeeee{start_date}")
        _logger.info(f"endddddddddddddddddddd dateeeeeeeeeeeeeeeeeeeeeeeeeee{end_date}")

        # Employees by department
        domain = [('company_id', '=', self.env.company.id)]
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        employees = self.env['hr.employee'].search(domain)

        leave_lines = []
        attendance_lines = []

        for emp in employees:

            # -----------------------------------------------------------
            #   1. Calculate Present Days (same as main model)
            # -----------------------------------------------------------
            if emp.resource_calendar_id.x_studio_is_zero:
                present_days = self.env['hr.attendance'].search_count([
                    ('employee_id', '=', emp.id),
                    ('check_in', '>=', start_date),
                    ('check_in', '<=', end_date),
                ])
                _logger.info(f"if check is zeroooooooo prwsent days{present_days}")
            else:
                present_days = self.env['hr.attendance'].search_count([
                    ('employee_id', '=', emp.id),
                    ('check_in', '>=', start_date),
                    ('check_in', '<=', end_date),
                    ('worked_hours', '>=', 6),
                ])
                _logger.info(f"is zero check off prsent days{present_days}")

            if present_days <= 0:
                continue

            # -----------------------------------------------------------
            #   2. Get previous approved encashments (same logic)
            # -----------------------------------------------------------
            prev_enc = self.env['leave.encashment'].search([
                ('em_p', '=', emp.id),
                ('month', '=', self.month),
                # ('state', '=', 'approve'),
            ])
            _logger.info(f"previous encashhhhhhhhhhh{prev_enc}")

            previous_leave_used = sum(prev_enc.mapped('tree_line.encash_leaves'))
            self.duration_display = previous_leave_used
            previous_att_used = sum(prev_enc.mapped('attendance_lines.encash_2'))
            _logger.info(f"previous leaves usedddddddddddddd{previous_leave_used}")
            _logger.info(f"previous att usedddddddddddddd{previous_att_used}")

            # -----------------------------------------------------------
            #   3. GET LEAVE ENCASHMENT (same logic as action_post)
            # -----------------------------------------------------------
            leave_types = self.env['hr.leave.type'].search([('leave_encash', '=', True)])
            total_available_leaves = 0

            for leave_type in leave_types:

                allocations = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', emp.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', '=', 'validate'),
                    ('month', '=', self.month),
                ]).mapped('number_of_days')

                used = self.env['hr.leave'].search([
                    ('employee_id', '=', emp.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', '=', 'validate'),
                    ('month', '=', self.month),
                ]).mapped('number_of_days')

                # AVAILABLE LEAVES
                # duration_display = sum(allocations) - sum(used)
                duration_display = sum(allocations)
                _logger.info(f"duration displayyyyyyyyyyyyyyyyyyyyy{duration_display}")
                available = duration_display - previous_leave_used

                if available > 0:

                   
                    
                    _logger.info(f"availableeeeeeeeeeeeeeeeeeeeeeeEE{available}")
                    if available < 0:
                        available = 0
                    # if available == 0:    
                    #     raise ValidationError(f"{duration_display}---{previous_leave_used}----{sum(allocations)}----{sum(used)}")
                    total_available_leaves += available
                    _logger.info(f"total availableeeeeeeeeeeeeeeeeeeeeee{total_available_leaves}")

                    leave_lines.append((0, 0, {
                        'employee_id': emp.id,
                        'attendance_count': present_days,
                        'remaining_weekly_off': available,
                    }))

            # If leaves available → show leaves & attendance (same logic)
            if total_available_leaves > 0:

                # Extra Days regular logic
                working_days = self._get_working_days(start_date, end_date)
                extra_days = present_days - working_days
                extra_after_leave = extra_days - total_available_leaves - previous_leave_used - previous_att_used
                extra_after_leave = max(extra_after_leave, 0)
                _logger.info(f"woirking dayssssssssssssssssssssssS{working_days}")
                _logger.info(f"woirking dayssssssssssssssssssssssS{working_days}")
                _logger.info(f"extra after lkeaveeeeeeeeeeeeeeeeeeeeeeee{extra_after_leave}")
                _logger.info(f"extra after lkeaveeeeeeeeeeeeeeeeeeeeeeee{extra_after_leave}")


                if extra_after_leave > 0:
                    attendance_lines.append((0, 0, {
                        'employee_id': emp.id,
                        'present_days': present_days,
                        'extra_days': extra_after_leave,
                        'days_to_encash': 0.0,
                    }))

                continue  # do NOT go into "no leaves found" section

            # -----------------------------------------------------------
            #   4. If NO LEAVES AVAILABLE → Attendance Encashment
            # -----------------------------------------------------------
            total_month_days = (end_date - start_date).days + 1
            sundays = len(
                [d for d in (start_date + timedelta(days=i) for i in range(total_month_days)) if d.weekday() == 6])
            working_days = total_month_days - sundays

            extra_days = present_days - working_days
            remaining_days = extra_days - previous_att_used - total_available_leaves - previous_leave_used
            _logger.info('if no leave availabeeeeeeeeeeeeeeeeeeeeee')
            _logger.info('if no leave availabeeeeeeeeeeeeeeeeeeeeee')
            _logger.info('if no leave availabeeeeeeeeeeeeeeeeeeeeee')
            _logger.info(f"total month  daysssssssssss{total_month_days}")
            _logger.info(f"sundayssssssssssssssssssss{sundays}")
            _logger.info(f"extra daysssssssssssssssssssssss{extra_days}")
            _logger.info(f"remaining daysssssssssssssssssssss{remaining_days}")

            if remaining_days > 0:
                attendance_lines.append((0, 0, {
                    'employee_id': emp.id,
                    'present_days': present_days,
                    'extra_days': remaining_days,
                    'days_to_encash': 0.0,
                }))

        # RESET BOTH TABS
        self.employee_ids = [(5, 0, 0)] + leave_lines
        self.attendance_line_ids = [(5, 0, 0)] + attendance_lines


    def action_cancel_wizard(self):
        pass

    def action_confirm_bulk_encashment(self):
        for wizard in self:

            encash_data = {}  # {emp_id: {...}}

            # =====================================================
            # 1. WEEKLY-OFF (Leave) ENCASHMENT
            # =====================================================
            for line in wizard.employee_ids:

                if line.leave_to_encash > line.remaining_weekly_off:
                    raise ValidationError(_(
                        "You cannot encash more than available leaves. "
                        "Demand: %s, Available: %s"
                    ) % (line.leave_to_encash, line.remaining_weekly_off))

                emp_id = line.employee_id.id

                # Initialize employee bucket
                if emp_id not in encash_data:
                    encash_data[emp_id] = {
                        'tree_line': [],
                        'attendance_lines': [],
                        'tree_line_vals': [],
                        'attendance_line_vals': [],
                        'total_amount': 0,
                        'month': wizard.month,
                    }

                # Add tree-line record to be inserted
                encash_data[emp_id]['tree_line'].append((0, 0, {
                    'employee_id': emp_id,
                    'encash_leaves': line.leave_to_encash,
                }))

                # Save value for reassigning after action_post()
                encash_data[emp_id]['tree_line_vals'].append({
                    'encash_leaves': line.leave_to_encash
                })

                encash_data[emp_id]['total_amount'] += line.encashment_amount

            # =====================================================
            # 2. ATTENDANCE-BASED ENCASHMENT
            # =====================================================
            for att_line in wizard.attendance_line_ids:

                if att_line.days_to_encash > att_line.extra_days:
                    raise ValidationError(_(
                        "You cannot encash more than available attendance days. "
                        "Demand: %s, Available: %s"
                    ) % (att_line.days_to_encash, att_line.extra_days))

                emp_id = att_line.employee_id.id

                if emp_id not in encash_data:
                    encash_data[emp_id] = {
                        'tree_line': [],
                        'attendance_lines': [],
                        'tree_line_vals': [],
                        'attendance_line_vals': [],
                        'total_amount': 0,
                        'month': wizard.month,
                    }

                enc_amount = att_line.days_to_encash * att_line.per_day_wage

                encash_data[emp_id]['attendance_lines'].append((0, 0, {
                    'employee_id_2': emp_id,
                    'name_2': str(att_line.present_days),
                    'duration_display_2': att_line.extra_days,
                    'encash_2': att_line.days_to_encash,
                }))

                # Save values for fixing after action_post()
                encash_data[emp_id]['attendance_line_vals'].append({
                    'encash_2': att_line.days_to_encash
                })

                encash_data[emp_id]['total_amount'] += enc_amount

            # =====================================================
            # 3. CREATE ONE ENCASHMENT PER EMPLOYEE
            # =====================================================
            for emp_id, data in encash_data.items():

                vals = {
                    'em_p': emp_id,
                    'month_start_date': self.month_start_date,
                    'month_end_date': self.month_end_date,
                    'month': data['month'],
                    'amount': data['total_amount'],
                    'encashed_amount': data['total_amount'],
                    'tree_line': data['tree_line'],
                    'attendance_lines': data['attendance_lines'],
                }

                enc = self.env['leave.encashment'].create(vals)

                # Post (this may reset line fields)
                enc.action_post()

                # =====================================================
                # 4. RE-APPLY USER VALUES (AFTER action_post())
                # =====================================================

                # Fix weekly-off encashment lines
                for rec, val in zip(enc.tree_line, data['tree_line_vals']):
                    rec.encash_leaves = val['encash_leaves']

                # Fix attendance-based encashment lines
                for rec, val in zip(enc.attendance_lines, data['attendance_line_vals']):
                    rec.encash_2 = val['encash_2']
        # for wizard in self:
        #
        #     # Grouping bucket {employee_id: {tree_vals: [], att_vals: [], total_amount: x}}
        #     encash_data = {}
        #
        #     # -----------------------------------------
        #     # 1. Weekly-Off Encashment (Leaves)
        #     # -----------------------------------------
        #     for line in wizard.employee_ids:
        #
        #         if line.leave_to_encash > line.remaining_weekly_off:
        #             raise ValidationError(_(
        #                 "You cannot encash more than available leaves. "
        #                 "Demand: %s, Available: %s"
        #             ) % (line.leave_to_encash, line.remaining_weekly_off))
        #
        #         emp_id = line.employee_id.id
        #
        #         if emp_id not in encash_data:
        #             encash_data[emp_id] = {
        #                 'tree_line': [],
        #                 'attendance_lines': [],
        #                 'tree_line_vals': [],
        #                 'attendance_line_vals': [],
        #                 'total_amount': 0,
        #                 'period_id': wizard.period_id.id,
        #             }
        #
        #         # Add tree-line values
        #         encash_data[emp_id]['tree_line'].append((0, 0, {
        #             'employee_id': emp_id,
        #             'encash_leaves': line.leave_to_encash,
        #         }))
        #
        #         # Add leave amount
        #         encash_data[emp_id]['total_amount'] += line.encashment_amount
        #
        #     # -----------------------------------------
        #     # 2. Attendance Encashment
        #     # -----------------------------------------
        #     for att_line in wizard.attendance_line_ids:
        #
        #         if att_line.days_to_encash > att_line.extra_days:
        #             raise ValidationError(_(
        #                 "You cannot encash more than available days. "
        #                 "Demand: %s, Available: %s"
        #             ) % (att_line.days_to_encash, att_line.extra_days))
        #
        #         emp_id = att_line.employee_id.id
        #
        #         if emp_id not in encash_data:
        #             encash_data[emp_id] = {
        #                 'tree_line': [],
        #                 'attendance_lines': [],
        #                 'tree_line_vals': [],
        #                 'attendance_line_vals': [],
        #                 'total_amount': 0,
        #                 'period_id': wizard.period_id.id,
        #             }
        #
        #         # Correct amount
        #         enc_amount = att_line.days_to_encash * att_line.per_day_wage
        #
        #         # Add attendance-line values
        #         encash_data[emp_id]['attendance_lines'].append((0, 0, {
        #             'employee_id_2': emp_id,
        #             'name_2': str(att_line.present_days),
        #             'duration_display_2': att_line.extra_days,
        #             'encash_2': att_line.days_to_encash,
        #         }))
        #
        #         # Add attendance amount
        #         encash_data[emp_id]['total_amount'] += enc_amount
        #
        #     # -----------------------------------------
        #     # 3. Create SINGLE Encashment Per Employee
        #     # -----------------------------------------
        #     for emp_id, data in encash_data.items():
        #         vals = {
        #             'em_p': emp_id,
        #             'period': data['period_id'],
        #             'amount': data['total_amount'],
        #             'encashed_amount': data['total_amount'],
        #             'tree_line': data['tree_line'],
        #             'attendance_lines': data['attendance_lines'],
        #             # 'populate': True,
        #             # 'state': 'submit_to_approve',
        #         }
        #
        #         enc = self.env['leave.encashment'].create(vals)
        #         enc.action_post()
        #         for line_rec, val in zip(enc.tree_line, data['tree_line_vals']):
        #             line_rec.encash_leaves = val['encash_leaves']
        #
        #             # Fix attendance lines
        #         for att_rec, val in zip(enc.attendance_lines, data['attendance_line_vals']):
        #             att_rec.encash_2 = val['encash_2']

        # for wizard in self:
        #     for line in wizard.employee_ids:
        #         if line.leave_to_encash > line.remaining_weekly_off:
        #             raise ValidationError(_(
        #                 "You cannot encash more than available leaves Demand %s. Available: %s"
        #             ) % (line.leave_to_encash, line.remaining_weekly_off))
        #
        #         vals = {
        #             'em_p': line.employee_id.id,
        #             'period': wizard.period_id.id,
        #             'amount': line.encashment_amount,
        #             'encashed_amount': line.encashed_amount,
        #             'tree_line': [(0, 0, {
        #                 'employee_id': line.employee_id.id,
        #                 'encash_leaves': line.leave_to_encash,
        #             })],
        #         }
        #         enc = self.env['leave.encashment'].create(vals)
        #         enc.action_post()
        #         for l in enc.tree_line:
        #             l.encash_leaves = line.leave_to_encash
        #
        #     # Process attendance-based encashments
        #     for att_line in wizard.attendance_line_ids:
        #         _logger.info(f"atttttttttttttttttttttttttttt")
        #         _logger.info(f"atttttttttttttttttttttttttttt")
        #         _logger.info(f"atttttttttttttttttttttttttttt")
        #         _logger.info(f"atttttttttttttttttttttttttttt")
        #         _logger.info(f"atttttttttttttttttttttttttttt  {att_line.days_to_encash}")
        #         if att_line.days_to_encash > att_line.extra_days:
        #             raise ValidationError(_(
        #                 "You cannot encash more than available Days Demand %s. Available: %s"
        #             ) % (att_line.days_to_encash, att_line.extra_days))
        #         # if att_line.days_to_encash <= 0:
        #         #     continue
        #
        #         vals = {
        #             'em_p': att_line.employee_id.id,
        #             'period': wizard.period_id.id,
        #             'amount': att_line.extra_days * att_line.per_day_wage,
        #             'encashed_amount': att_line.total_amount,
        #             'attendance_lines': [(0, 0, {
        #                 'employee_id_2': att_line.employee_id.id,
        #                 'name_2': str(att_line.present_days),
        #                 'duration_display_2': att_line.extra_days,
        #                 'encash_2': att_line.days_to_encash,
        #             })],
        #         }
        #         _logger.info(vals)
        #         enc = self.env['leave.encashment'].create(vals)
        #         enc.action_post()
        #         for a in enc.attendance_lines:
        #             a.encash_2 = att_line.days_to_encash
        #         # enc.state = 'approve'


class BulkLeaveEncashmentLine(models.TransientModel):
    _name = 'bulk.leave.encashment.line'

    wizard_id = fields.Many2one('bulk.leave.encashment', string='Wizard')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    attendance_count = fields.Integer("Present Days")
    remaining_weekly_off = fields.Float("Remaining LEaves", store=True)
    leave_to_encash = fields.Float("Leaves To Encash")
    encashment_amount = fields.Float("Total Amount", compute="_compute_encashment_amount", store=False)
    encashed_amount = fields.Float(string="Encashed Amount", compute="_compute_encashment_amount_for_leaves")

    @api.depends('employee_id', 'leave_to_encash')
    def _compute_encashment_amount_for_leaves(self):
        for rec in self:
            if rec.employee_id:
                wage = rec.employee_id.contract_id.wage  # from latest running contract
                rec.encashed_amount = (wage / 30.0) * rec.leave_to_encash
            else:
                rec.encashed_amount = 0.0

    @api.depends('employee_id', 'remaining_weekly_off')
    def _compute_encashment_amount(self):
        for rec in self:
            if rec.employee_id.contract_id and rec.remaining_weekly_off > 0:
                wage = rec.employee_id.contract_id.wage  # from latest running contract
                rec.encashment_amount = (wage / 30.0) * rec.remaining_weekly_off
            else:
                rec.encashment_amount = 0.0


class BulkAttendanceEncashmentLine(models.TransientModel):
    _name = 'bulk.attendance.encashment.line'

    wizard_id = fields.Many2one('bulk.leave.encashment', string='Wizard')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    present_days = fields.Integer(string='Present Days')
    extra_days = fields.Float(string='Extra Days (Present - 26)')
    days_to_encash = fields.Float(string='Days to Encash')
    per_day_wage = fields.Float(string='Per Day Wage', compute='_compute_per_day_wage')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount')

    @api.depends('employee_id')
    def _compute_per_day_wage(self):
        for rec in self:
            contract = rec.employee_id.contract_id
            rec.per_day_wage = (contract.wage / 30.0) if contract else 0.0

    @api.depends('days_to_encash', 'per_day_wage')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.days_to_encash * rec.per_day_wage
