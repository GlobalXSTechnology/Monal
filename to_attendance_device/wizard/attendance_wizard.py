import logging
from datetime import datetime
import pytz
# from datetime import timedelta
from datetime import date, timedelta
from odoo import models, fields, api,registry, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class AttendanceWizard(models.TransientModel):
    _name = 'attendance.wizard'
    _description = 'Attendance Wizard'

    @api.model
    def _get_all_device_ids(self):
        all_devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
        if all_devices:
            return all_devices.ids
        else:
            return []

    set_date = fields.Date(string='Sync Date From',
                           default=lambda self: fields.Date.to_string(date.today() - timedelta(days=1)))
    set_date_to = fields.Date(string='Sync Date To', default=date.today())
    time_date = fields.Datetime(string='Download from',
                                default=lambda self: fields.Date.to_string(datetime.today() - timedelta(days=1)))
    device_ids = fields.Many2many('attendance.device', string='Devices', default=_get_all_device_ids,
                                  domain=[('state', '=', 'confirmed')])
    fix_attendance_valid_before_synch = fields.Boolean(string='Fix Attendance Valid',
                                                       help="If checked, Odoo will recompute all attendance data for their valid"
                                                            " before synchronizing with HR Attendance (upon you hit the 'Synchronize Attendance' button)")

    def download_attendance_manually(self):
        # TODO: remove me after 12.0
        self.action_download_attendance()

    def action_download_attendance(self):
        if not self.device_ids:
            raise UserError(_('You must select at least one device to continue!'))
        self.device_ids.action_attendance_download()

    def download_device_attendance(self):
        # TODO: remove me after 12.0
        self.cron_download_device_attendance()

    def cron_download_device_attendance_custom(self, device):
        devices = self.env['attendance.device'].search([('state', '=', 'confirmed'), ('id', '=', device)])
        for i in devices:
            print(devices, 'tryyyyyyyyyyy')

            try:
                zk = i.connect()
                if zk:
                    zk.connect()

                    i.enableDevice()
                    i.disableDevice()
                    i.action_attendance_download_auto()
                    #self.download_attendance_custom_auto()
                    
                else:
                    print('doubl fail')

            except:
                print("Fail")
                pass

    def cron_sync_attendance(self):
        print('self.with_context(synch_ignore_constraints=True).sync_attendance()')
        # self.with_context(synch_ignore_constraints=True).sync_attendance()
        self.download_attendance_custom_auto()
    #
    # def download_attendance_custom_auto(self):
    #
    #     synch_ignore_constraints = self.env.context.get('synch_ignore_constraints', False)
    #
    #     att_obj = self.env['hr.attendance']
    #     user = self.env['attendance.device.user'].search([('employee_id', '!=', False)])
    #
    #     N_DeviceUserAttendance = self.env['user.attendance']
    #
    #     devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
    #     for device in devices:
    #         for n in range(1):
    #
    #             n_unsync_data = N_DeviceUserAttendance.search(
    #                 [('device_id','=',device.id),('hr_attendance_id', '=', False),
    #                  ('employee_id', '!=', False), ('valid', '=', True),
    #                  ('date', '>=', self.set_date),('date','<=',self.set_date_to)
    #
    #                  ], order='timestamp ASC')
    #             _logger.debug(n_unsync_data, '///////////////////')
    #             _logger.error(n_unsync_data)
    #             print("work")
    #             for each in n_unsync_data.with_progress(msg="Message"):
    #
    #                 atten_time = each.timestamp
    #                 for uid in user:
    #                     if uid.user_id == each.employee_id.barcode and each.date >= self.set_date:
    #                         get_user_id = uid.employee_id.id
    #                         if get_user_id:
    #                             duplicate_atten_ids = att_obj.search(
    #                                 [('employee_id', '=', get_user_id), ('check_in', '=', atten_time)])
    #                             if duplicate_atten_ids:
    #                                 continue
    #                             else:
    #                                 check_some = 1
    #                                 att_var = att_obj.search([("employee_id", "=", get_user_id),
    #                                                           ("check_out", "=", False), ])
    #                                 if att_var:
    #                                     att_var = att_obj.search([("employee_id", "=", get_user_id)])
    #                                     timestamp = atten_time - att_var[0].check_in
    #                                     count_18 = timestamp.total_seconds() / 3600
    #                                     if count_18 <= 13.0 and att_var:
    #                                         id = att_var[0].id
    #                                         att_var = att_obj.search([('id', '=', id),
    #                                                                   ])
    #                                     else:
    #                                         att_var = att_obj.search([("employee_id", "=", get_user_id),
    #                                                                   ("check_in", "=", False), ])
    #                                         check_some = 2
    #                                 if not att_var and check_some == 1:
    #                                     att_var = att_obj.search([("employee_id", "=", get_user_id)
    #                                                               ])
    #                                     count_18 = 1
    #                                     if att_var:
    #                                         timestamp = atten_time - att_var[0].check_in
    #                                         id = att_var[0].id
    #                                         count_18 = timestamp.total_seconds() / 3600
    #                                     if count_18 <= 13.0 and att_var:
    #                                         att_var = att_obj.search([("id", "=", id)
    #                                                                   ])
    #                                     else:
    #                                         att_var = att_obj.search([("employee_id", "=", get_user_id),
    #                                                                   ("check_out", "=", False), ])
    #                                 if not att_var:
    #                                     id_checkin = att_obj.create({'employee_id': get_user_id,
    #                                                                  'check_in': atten_time,
    #                                                                  'checkin_device_id': each.device_id.id,
    #                                                                  })
    #                                     each.write({'valid': True,
    #                                                 'hr_attendance_id': id_checkin.id})
    #                                     self.env.cr.commit()
    #                                     # dbname = self._cr.dbname
    #                                     # print(dbname)
    #                                     # cr = registry(dbname).cursor()
    #                                     # cr.commit()
    #
    #                                 if len(att_var) == 1:
    #                                     if att_var.check_in < atten_time:
    #                                         att_var.write(
    #                                             {'check_out': atten_time, 'checkout_device_id': each.device_id.id,
    #                                              })
    #                                         each.write({'valid': True,
    #                                                     'hr_attendance_id': att_var.id})
    #                                         self.env.cr.commit()
    #                                         # dbname = self._cr.dbname
    #                                         # cr = registry(dbname).cursor()
    #                                         # cr.commit()
    #                                         # cr.close()
    #
    #
    #
    #                     else:
    #                         pass

    def download_attendance_custom(self):

        synch_ignore_constraints = self.env.context.get('synch_ignore_constraints', False)

        att_obj = self.env['hr.attendance']
        user = self.env['attendance.device.user'].search([('employee_id', '!=', False)])

        N_DeviceUserAttendance = self.env['user.attendance']



        for n in range(1):

            n_unsync_data = N_DeviceUserAttendance.search([('hr_attendance_id', '=', False),
                                                           ('employee_id', '!=', False), ('valid', '=', True),
                                                           ('date', '>=', self.set_date),('date','<=',self.set_date_to)

                                                           ], order='timestamp ASC')
            print(len(n_unsync_data),'/////////')

            # for each in n_unsync_data:

            for each in n_unsync_data:
                atten_time = each.timestamp
                for uid in user:
                    if uid.user_id == each.employee_id.barcode:
                        get_user_id = uid.employee_id.id
                        if get_user_id:
                            duplicate_atten_ids = att_obj.search(
                                [('employee_id', '=', get_user_id), ('check_in', '=', atten_time)])



                            if duplicate_atten_ids:
                                continue
                            else:
                                check_some = 1

                                # print('saad', sql)
                                att_var = att_obj.search([("employee_id", "=", get_user_id),
                                                          ("check_out", "=", False), ])
                                if att_var:
                                    att_var = att_obj.search([("employee_id", "=", get_user_id)])
                                    timestamp = atten_time - att_var[0].check_in
                                    check_in_xz = att_var[0].check_in
                                    timestamp = datetime.combine(check_in_xz.date(), time(4, 0))
                                    count_18 = timestamp.total_seconds() / 3600
                                    if count_18 <= 24.0 and att_var:
                                        id = att_var[0].id
                                        att_var = att_obj.search([('id', '=', id),
                                                                  ])
                                    else:
                                        att_var = att_obj.search([("employee_id", "=", get_user_id),
                                                                  ("check_in", "=", False), ])
                                        check_some = 2
                                if not att_var and check_some == 1:
                                    att_var = att_obj.search([("employee_id", "=", get_user_id)
                                                              ])
                                    count_18 = 1
                                    if att_var:
                                        timestamp = atten_time - att_var[0].check_in
                                        id = att_var[0].id
                                        check_in_xz = att_var[0].check_in
                                        timestamp = datetime.combine(check_in_xz.date(), time(4, 0))
                                        count_18 = timestamp.total_seconds() / 3600
                                    if count_18 <= 24.0 and att_var:
                                        att_var = att_obj.search([("id", "=", id)
                                                                  ])
                                    else:
                                        att_var = att_obj.search([("employee_id", "=", get_user_id),
                                                                  ("check_out", "=", False), ])
                                if not att_var:

                                    # rec.checkin_date = new_checkin

                                    sql = "INSERT INTO hr_attendance(employee_id,check_in,checkin_device_id)VALUES(%s,%s,%s)"

                                    self.env.cr.execute(sql, (get_user_id,atten_time,each.device_id.id))
                                    att_var._plan_attendance()
                                    att_var._get_new_current_checkin()
                                    att_var._late_emp_hours()

                                    id_checkin = att_obj.search(
                                        [('employee_id', '=', get_user_id)
                                         ], limit=1, order='id desc')
                                    #id_checkin._get_new_current_checkin()
                                    #id_checkin._plan_attendance()
                                    #id_checkin._late_emp_hours()
                                    #id_checkin._compute_worked_hours()

                                    print(id_checkin)
                                    sql = ("UPDATE user_attendance SET hr_attendance_id=%s WHERE id=%s")
                                    self.env.cr.execute(sql,(id_checkin.id,each.id))

                                    self.env.cr.commit()


                                if len(att_var) == 1:
                                    if att_var.check_in < atten_time:
                                        # att_var.write({'check_out': atten_time, 'checkout_device_id': each.device_id.id,
                                        #                })
                                        sql = ("UPDATE hr_attendance SET check_out=%s , checkout_device_id=%s WHERE id=%s")
                                        self.env.cr.execute(sql, (atten_time, each.device_id.id,att_var.id))
                                        att_var._plan_attendance()
                                        att_var._get_new_current_checkin()
                                        att_var._late_emp_hours()
                                        # att_var._get_new_current_checkout()
                                        #att_var._overtime_emp_hour()
                                        #att_var._compute_worked_hours()
                                        # each.write({'valid': True,
                                        #             'hr_attendance_id': att_var.id})

                                        sql = ("UPDATE user_attendance SET hr_attendance_id=%s WHERE id=%s")
                                        self.env.cr.execute(sql, (att_var.id, each.id))

                                        # dbname = self._cr.dbname
                                        # cr = registry(dbname).cursor()
                                        self.env.cr.commit()
                                        print('cr work/////////////')
                                        # cr.close()
                            x = att_obj.search([('employee_id', '=', get_user_id)])
                            for b in x:
                                x._plan_attendance()
                                x._get_new_current_checkin()
                                x._late_emp_hours()
                    else:
                        pass


    def download_attendance_custom_auto(self):

        synch_ignore_constraints = self.env.context.get('synch_ignore_constraints', False)

        att_obj = self.env['hr.attendance']
        user = self.env['attendance.device.user'].search([('employee_id', '!=', False)])

        N_DeviceUserAttendance = self.env['user.attendance']



        for n in range(1):
            set_date =  (date.today() - timedelta(days=1))
            set_date_to =  date.today()
            print(set_date,set_date_to)
            n_unsync_data = N_DeviceUserAttendance.search([('hr_attendance_id', '=', False),
                                                           ('employee_id', '!=', False), ('valid', '=', True),
                                                           ('date', '>=', set_date),('date','<=',set_date_to)

                                                           ], order='timestamp ASC')
            print(len(n_unsync_data),'/////////')

            # for each in n_unsync_data:

            for each in n_unsync_data:
                atten_time = each.timestamp
                for uid in user:
                    if uid.user_id == each.employee_id.barcode:
                        get_user_id = uid.employee_id.id
                        if get_user_id:
                            duplicate_atten_ids = att_obj.search(
                                [('employee_id', '=', get_user_id), ('check_in', '=', atten_time)])



                            if duplicate_atten_ids:
                                continue
                            else:
                                check_some = 1

                                # print('saad', sql)
                                att_var = att_obj.search([("employee_id", "=", get_user_id),
                                                          ("check_out", "=", False), ])
                                if att_var:
                                    att_var = att_obj.search([("employee_id", "=", get_user_id)])
                                    timestamp = atten_time - att_var[0].check_in
                                    check_in_xz = att_var[0].check_in
                                    timestamp = datetime.combine(check_in_xz.date(), time(4, 0))

                                    count_18 = timestamp.total_seconds() / 3600
                                    if count_18 <= 24.0 and att_var:
                                        id = att_var[0].id
                                        att_var = att_obj.search([('id', '=', id),
                                                                  ])
                                    else:
                                        att_var = att_obj.search([("employee_id", "=", get_user_id),
                                                                  ("check_in", "=", False), ])
                                        check_some = 2
                                if not att_var and check_some == 1:
                                    att_var = att_obj.search([("employee_id", "=", get_user_id)
                                                              ])
                                    count_18 = 1
                                    if att_var:
                                        timestamp = atten_time - att_var[0].check_in
                                        id = att_var[0].id
                                        check_in_xz = att_var[0].check_in
                                        timestamp = datetime.combine(check_in_xz.date(), time(4, 0))

                                        count_18 = timestamp.total_seconds() / 3600
                                    if count_18 <= 24.0 and att_var:
                                        att_var = att_obj.search([("id", "=", id)
                                                                  ])
                                    else:
                                        att_var = att_obj.search([("employee_id", "=", get_user_id),
                                                                  ("check_out", "=", False), ])
                                if not att_var:
                                    sql = "INSERT INTO hr_attendance(employee_id,check_in,checkin_device_id)VALUES(%s,%s,%s)"

                                    self.env.cr.execute(sql, (get_user_id,atten_time,each.device_id.id))

                                    id_checkin = att_obj.search(
                                        [('employee_id', '=', get_user_id)
                                         ], limit=1, order='id desc')
                                    #id_checkin._get_new_current_checkin()
                                    id_checkin._plan_attendance()
                                    #id_checkin._late_emp_hours()
                                    #id_checkin._compute_worked_hours()

                                    print(id_checkin)
                                    sql = ("UPDATE user_attendance SET hr_attendance_id=%s WHERE id=%s")
                                    self.env.cr.execute(sql,(id_checkin.id,each.id))

                                    self.env.cr.commit()


                                if len(att_var) == 1:
                                    if att_var.check_in < atten_time:
                                        # att_var.write({'check_out': atten_time, 'checkout_device_id': each.device_id.id,
                                        #                })
                                        sql = ("UPDATE hr_attendance SET check_out=%s , checkout_device_id=%s WHERE id=%s")
                                        self.env.cr.execute(sql, (atten_time, each.device_id.id,att_var.id))
                                        # each.write({'valid': True,
                                        #             'hr_attendance_id': att_var.id})
                                        #att_var._overtime_emp_hour()
                                        att_var._compute_worked_hours()
                                        sql = ("UPDATE user_attendance SET hr_attendance_id=%s WHERE id=%s")
                                        self.env.cr.execute(sql, (att_var.id, each.id))

                                        # dbname = self._cr.dbname
                                        # cr = registry(dbname).cursor()
                                        self.env.cr.commit()
                                        print('cr work/////////////')
                                        # cr.close()




                    else:
                        pass

    # def sync_attendance(self):
    #     """
    #     This method will synchronize all downloaded attendance data with Odoo attendance data.
    #     It do not download attendance data from the devices.
    #     """
    #     if self.fix_attendance_valid_before_synch:
    #         self.action_fix_user_attendance_valid()
    #
    #     synch_ignore_constraints = self.env.context.get('synch_ignore_constraints', False)
    #
    #     error_msg = {}
    #     HrAttendance = self.env['hr.attendance'].with_context(synch_ignore_constraints=synch_ignore_constraints)
    #     attendance = self.env['hr.attendance']
    #     activity_ids = self.env['attendance.activity'].search([])
    #
    #     DeviceUserAttendance = self.env['user.attendance']
    #
    #     last_employee_attendance = {}
    #     for activity_id in activity_ids:
    #         if activity_id.id not in last_employee_attendance.keys():
    #             last_employee_attendance[activity_id.id] = {}
    #
    #         unsync_data = DeviceUserAttendance.search([('hr_attendance_id', '=', False),
    #                                                    ('valid', '=', True),
    #                                                    ('employee_id', '!=', False),
    #                                                    ('activity_id', '=', activity_id.id)], order='timestamp ASC')
    #
    #         for att in unsync_data:
    #             employee_id = att.user_id.employee_id
    #             if employee_id.id not in last_employee_attendance[activity_id.id].keys():
    #                 last_employee_attendance[activity_id.id][employee_id.id] = False
    #
    #             if att.type == 'checkout':
    #                 # find last attendance
    #                 last_employee_attendance[activity_id.id][employee_id.id] = HrAttendance.search(
    #                     [('employee_id', '=', employee_id.id),
    #                      ('activity_id', 'in', (activity_id.id, False)),
    #                      ('check_in', '<=', att.timestamp)], limit=1, order='check_in DESC')
    #
    #                 hr_attendance_id = last_employee_attendance[activity_id.id][employee_id.id]
    #
    #                 if hr_attendance_id:
    #                     try:
    #                         hr_attendance_id.with_context(synch_ignore_constraints=synch_ignore_constraints).write({
    #                             'check_out': att.timestamp,
    #                             'checkout_device_id': att.device_id.id
    #                         })
    #                         hr_attendance_id.with_context(
    #                             synch_ignore_constraints=synch_ignore_constraints)._get_new_current_checkin()
    #                         hr_attendance_id.with_context(
    #                             synch_ignore_constraints=synch_ignore_constraints)._plan_attendance()
    #                         hr_attendance_id.with_context(
    #                             synch_ignore_constraints=synch_ignore_constraints)._late_emp_hours()
    #                         hr_attendance_id.with_context(
    #                             synch_ignore_constraints=synch_ignore_constraints)._overtime_emp_hour()
    #                         hr_attendance_id.with_context(
    #                             synch_ignore_constraints=synch_ignore_constraints)._get_new_current_checkout()
    #                     except ValidationError as e:
    #                         if att.device_id not in error_msg:
    #                             error_msg[att.device_id] = ""
    #
    #                         msg = ""
    #                         att_check_time = fields.Datetime.context_timestamp(att, att.timestamp)
    #                         msg += str(e) + "<br />"
    #                         msg += _("'Check Out' time cannot be earlier than 'Check In' time. Debug information:<br />"
    #                                  "* Employee: <strong>%s</strong><br />"
    #                                  "* Type: %s<br />"
    #                                  "* Attendance Check Time: %s<br />") % (
    #                                    employee_id.name, att.type, fields.Datetime.to_string(att_check_time))
    #                         _logger.error(msg)
    #                         error_msg[att.device_id] += msg
    #             else:
    #                 # create hr attendance data
    #                 vals = {
    #                     'employee_id': employee_id.id,
    #                     'check_in': att.timestamp,
    #                     'checkin_device_id': att.device_id.id,
    #                     'activity_id': activity_id.id,
    #                 }
    #                 hr_attendance_id = HrAttendance.search([
    #                     ('employee_id', '=', employee_id.id),
    #                     ('check_in', '=', att.timestamp),
    #                     ('checkin_device_id', '=', att.device_id.id),
    #                     ('activity_id', '=', activity_id.id)], limit=1)
    #                 if not hr_attendance_id:
    #                     try:
    #                         hr_attendance_id = HrAttendance.create(vals)
    #                     except Exception as e:
    #                         _logger.error(e)
    #
    #             if hr_attendance_id:
    #                 att.write({
    #                     'hr_attendance_id': hr_attendance_id.id
    #                 })
    #
    #     if bool(error_msg):
    #         for device in error_msg.keys():
    #
    #             if not device.debug_message:
    #                 continue
    #             device.message_post(body=error_msg[device])

    def clear_attendance(self):
        if not self.device_ids:
            raise (_('You must select at least one device to continue!'))
        if not self.env.user.has_group('hr_attendance.group_hr_attendance_manager'):
            raise UserError(_('Only HR Attendance Managers can manually clear device attendance data'))

        for device in self.device_ids:
            device.clearAttendance()

    def action_fix_user_attendance_valid(self):
        all_attendances = self.env['user.attendance'].search([])
        for attendance in all_attendances:
            if attendance.is_valid():
                attendance.write({'valid': True})
            else:
                attendance.write({'valid': False})
