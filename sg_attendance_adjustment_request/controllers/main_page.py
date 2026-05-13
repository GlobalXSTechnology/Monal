from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request
# This is for inherit controller of another module
# from odoo.odoo import SUPERUSER_ID
# from odoo.exceptions import AccessError, MissingError
# from odoo import fields, _
# from odoo.tools import consteq
# from odoo.odoo.osv import expression
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
import logging

_logger = logging.getLogger(__name__)


class AttendancePortal(CustomerPortal):

    def get_domain_my_attendances(self, user):
        user = request.env.user
        payslip = request.env['hr.attendance']
        payslip_count = payslip.search_count([
            ('employee_id.user_id', '=', [user.id])
        ])

        emp = request.env['hr.employee'].search([('user_id', '=', user.id)],
                                                limit=1)
        return [
            ('employee_id', '=', emp and emp.id or False),
        ]

    def _prepare_portal_layout_values(self):
        values = super(AttendancePortal, self)._prepare_portal_layout_values()
        user = request.env.user
        attendance = request.env['hr.attendance']
        attendance_count = attendance.search_count([
            ('employee_id.user_id', '=', [user.id]),

        ])
        print(attendance)
        print('First', attendance_count)

        values.update({
            'payslip_count': attendance_count,
        })
        return values

    @http.route(['/employee/attendance/record'], type='http', website=True, auth='user')
    def employee_attendances(self, **kw):
        user = request.env.user
        Hrattendance = request.env['hr.attendance']
        payslip_sudo = request.env['hr.attendance'].sudo()
        domain = [('employee_id.user_id', '=', [user.id])]

        emp = request.env['hr.employee'].search([('user_id', '=', user.id)],
                                                limit=1)
        payslips_count = Hrattendance.search_count(domain)
        attendances = Hrattendance.sudo().search([('employee_id.user_id', '=', user.id)])
        print(attendances)
        return request.render("sg_attendance_adjustment_request.attendances_record", {
            'attendances': attendances,
        })

    # @http.route('/attendance/form/', type="http", auth="public", website=True)
    # def attendance_form(self, **kw):
    #     # values = self._prepare_portal_layout_values()
    #     user_rec = request.env['hr.employee'].sudo().search([])
    #     # print(user_rec)
    #     # responsible = request.env['res.users'].sudo().search([])
    #
    #     return http.request.render('sg_attendance_adjustment_request.create_request', {'user_rec': user_rec})
    #
    # # My Task
    # @http.route('/create/attendance/request/', type="http", auth="user", website=True)
    # def create_attendance(self, **kw):
    #     request.env['attendance.adjustment'].sudo().create(kw)
    #     return request.render("sg_attendance_adjustment_request.employee_thanks", {})

    #
    @http.route(['/employee/attendance/'], type='http', website=True, auth='user')
    def view_adjustments(self, **kw):
        user = request.env.user
        attendances = request.env['attendance.adjustment'].sudo().search([('name.user_id', '=', user.id)])
        return request.render("sg_attendance_adjustment_request.attendances", {
            'attendances': attendances,
        })

    # adjustment view
    @http.route(['/employee/attendance/<int:attend_id>'], type='http', auth="user", website=True)
    def portal_my_attend_detail(self, attend_id, access_token=None, **kw):
        user = request.env.user
        attendance_sudo = self._document_check_access('attendance.adjustment', attend_id, access_token=access_token)
        values = {
            'attendance_rec': attendance_sudo,
            'token': access_token,
        }
        print(attendance_sudo.id)

        values['pms'] = http.request.env['hr.employee'].search([('id', '=', attendance_sudo.id)])
        print(values)
        return request.render("sg_attendance_adjustment_request.portal_page_adjustment", values)
