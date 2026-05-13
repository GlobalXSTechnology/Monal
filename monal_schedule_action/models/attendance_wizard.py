from odoo import models, fields, api


class MonalAttendanceWizard(models.TransientModel):
    _name = 'monal.attendance.wizard'
    _description = 'Monal Attendance Process Wizard'

    date = fields.Datetime(string="Date", required=True)
    date_to = fields.Datetime(string="Date To", required=True)
    employee_ids = fields.Many2many("hr.employee", string="Employee")

    company_ids = fields.Many2many(
        'res.company',
        string="Companies",
        default=lambda self: self.env.company,
        required=True
    )

    def action_confirm(self):

        attendance_obj = self.env['hr.attendance'].sudo()
        logs_obj = self.env['sa.attendance.log'].sudo()
        date_str = '2/03/2026 00:01:01'
        current_date = self.date
        current_date_to = self.date_to

        attend = attendance_obj.search([('check_in', '>=', current_date),('check_out', '<=', current_date_to),('employee_id','in',self.employee_ids.ids)])

        # records = attend.filtered(
        #     lambda r: r.check_in == r.check_out
        # )
        for i in attend:
            i.unlink()

        # domain = [('punch_time', '>=', current_date),('punch_time', '<=', current_date_to), ('x_studio_punch_type', 'not in', [15, 1]),('x_studio_company','in',self.company_ids.ids)]
        # if self.employee_ids:
        #     domain.append
            

        logs = self.env['sa.attendance.log'].sudo().search(
            [('punch_time', '>=', current_date),('punch_time', '<=', current_date_to), ('x_studio_punch_type', 'not in', [15, 1]),('x_studio_company','in',self.company_ids.ids),('employee_id','in',self.employee_ids.ids)], limit=2000,
            order='punch_time ASC')
        for rec in logs:
            punch = self.env['sa.biometric.att'].search(
                [('punch_time', '=', rec.punch_time), ('emp_code', '=', rec.code)])
            rec.write({'x_studio_punch_type': punch.punch_type})

            # ('punch_time','>=',current_date),
        logs = self.env['sa.attendance.log'].sudo().search(
            [('punch_time', '>=', current_date),('punch_time', '<=', current_date_to), ('x_studio_punch_type', '=', 15), ('employee_id', '!=', False),
             ('x_studio_attendance', '=', False),('x_studio_company','in',self.company_ids.ids)], limit=2000, order='punch_time ASC')
        # for log in logs:
        #     log.write({'x_studio_attendance':False})
        # logs = []
        # raise UserError(len(logs))
        for log in logs:
            log = log.sudo()
            if not log.x_studio_attendance:
                p = attendance_obj.search(
                    [('check_in', '=', log.punch_time), ("employee_id", "=", log.employee_id.id)])
                o = attendance_obj.search(
                    [('check_out', '=', log.punch_time), ("employee_id", "=", log.employee_id.id)])
                if p:
                    logs_att = logs_obj.search([('id', 'in', logs.ids), ('employee_id', '=', p.employee_id.id),
                                                ('punch_time', '>=', p.check_in),
                                                ('punch_time', '<=', p.check_out)], limit=2000,
                                               order='punch_time ASC')
                    log.sudo().write({'x_studio_attendance': p.id})
                    for i in logs_att:
                        i.sudo().write({'x_studio_attendance': p.id})
                elif o:
                    logs_att = logs_obj.search([('id', 'in', logs.ids), ('employee_id', '=', o.employee_id.id),
                                                ('punch_time', '>=', o.check_in),
                                                ('punch_time', '<=', o.check_out)], limit=2000,
                                               order='punch_time ASC')

                    log.write({'x_studio_attendance': o.id})
                    for i in logs_att:
                        i.sudo().write({'x_studio_attendance': o.id})
                else:
                    log.action_update_hr_attendance()
