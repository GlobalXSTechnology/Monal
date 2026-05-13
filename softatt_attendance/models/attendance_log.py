from odoo import _, api, fields, models
import requests
import pytz
from datetime import datetime, timedelta, time
import json
import logging
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)


class ConfPunchState(models.Model):
    _name = 'sa.punch.state'
    _description = 'Punch State'

    code = fields.Integer()
    punch_type = fields.Selection([('in', 'Check In'), ('out', 'Check Out')])
    company_id = fields.Many2one(comodel_name='res.company', required=True, index=True,
                                 default=lambda self: self.env.company)
    # !!


class saAttendanceLog(models.Model):
    _name = "sa.attendance.log"
    _description = "sa Attendance Log"
    _order = "punch_time desc"

    hubid = fields.Integer(string="ATT ID")
    punch_time = fields.Datetime(string="Punch Time", required=True, tracking=True)
    punch_state = fields.Char(required=True)
    check_in_check_out = fields.Char(store=True, string="Check In/Check Out")
    employee_id = fields.Many2one("hr.employee", string="Employee", tracking=True)
    department_id = fields.Many2one(related="employee_id.department_id", readonly=True, store=True)
    device_code = fields.Integer(string="Device ID", tracking=True)
    code = fields.Char(string="Code")
    location_alias = fields.Char(string="Location Alias", )
    location_id = fields.Many2one(related="employee_id.work_location_id", string="Location", tracking=True, store=True)
    db_name = fields.Char()
    company_id = fields.Many2one(comodel_name='res.company', required=False, index=True,
                                 default=lambda self: self.env.company)
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', compute="_compute_dayofweek")

    @api.depends('punch_time')
    def _compute_dayofweek(self):
        for record in self:
            if record.punch_time:
                # Directly use the day of the week index (0=Monday, 1=Tuesday, ..., 6=Sunday)
                punch_time = date_utils._softatt_localize(record.punch_time, self.env.user.tz)
                day_of_week = punch_time.weekday()
                record.dayofweek = str(day_of_week)
                punch = self.env['sa.biometric.att'].search(
                    [('punch_time', '=', record.punch_time), ('emp_code', '=', record.code)], limit=1)
                record.write({'x_studio_punch_type': punch.punch_type})

    def action_compute_employees(self):
        employees = self.env["sa.attendance.employee.code"]
        for r in self:
            employee_id = employees.search([("code", "=", r.code), ("device_id.externalid", "=", r.device_code), ],
                                           limit=1, ).employee_id
            if employee_id:
                r.employee_id = employee_id.id
            else:
                r.employee_id = None

    def _process_hr_attendance_punch(self, attendance_obj, punch_states):

        employee = self.employee_id
        punch_time = self.punch_time + timedelta(hours=5)
        attendance_obj = self.env['hr.attendance']

        if not punch_time:
            self.check_in_check_out = "Error (no punch)"
            return

        slab_start_time = employee.resource_calendar_id.start_check
        slab_end_time = employee.resource_calendar_id.end_check

        slab_start_hour = int(slab_start_time)
        slab_end_hour = int(slab_end_time)

        # Determine shift date (NIGHT SHIFT SAFE)
        if slab_end_time <= slab_start_time:
            # Night shift
            if punch_time.hour < slab_end_hour:
                shift_date = punch_time.date() - timedelta(days=1)
            else:
                shift_date = punch_time.date()
        else:
            # Day shift
            shift_date = punch_time.date()

        shift_start = datetime.combine(shift_date, time(slab_start_hour, 0))
        shift_end = datetime.combine(
            shift_date + timedelta(days=1) if slab_end_time <= slab_start_time else shift_date,
            time(slab_end_hour, 0)
        )

        # Ignore punches outside shift window
        if not (shift_start <= punch_time <= shift_end):
            self.check_in_check_out = "Ignored (outside shift)"
            return

        # Find attendance inside shift window
        att_var = attendance_obj.search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', shift_start - timedelta(hours=5)),
            ('check_in', '<=', shift_end - timedelta(hours=5)),
        ], order="check_in desc", limit=1)

        # Prevent duplicate exact punch
        duplicate_in = attendance_obj.search([
            ('employee_id', '=', employee.id),
            ('check_in', '=', punch_time)
        ], limit=1)

        duplicate_out = attendance_obj.search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', punch_time)
        ], limit=1)

        if duplicate_in or duplicate_out:
            return True

        if att_var:
            attendance = att_var[0]

            # Smallest punch → check_in
            if punch_time - timedelta(hours=5) < attendance.check_in:
                attendance.check_in = punch_time - timedelta(hours=5)

            # Largest punch → check_out
            if not attendance.check_out or punch_time - timedelta(hours=5) > attendance.check_out:
                attendance.check_out = punch_time - timedelta(hours=5)

            self.check_in_check_out = f'Updated {employee.name} ---- {punch_time}'

            self.x_studio_attendance = attendance.id


        else:
            uid0 = attendance_obj.create({
                'employee_id': employee.id,
                'check_in': punch_time - timedelta(hours=5),
                'device_code': self.device_code,
                'attend_check_in': (shift_start - timedelta(hours=5)).date()
            })

            self.check_in_check_out = f'New Checkin {employee.name} ---- {punch_time}'
            self.x_studio_attendance = uid0.id

    def _process_hr_attendance_punch_old(self, attendance_obj, punch_states):
        employee = self.employee_id
        punch_time = self.punch_time + timedelta(hours=5)
        attendance_obj = self.env['hr.attendance']
        if not punch_time:
            self.check_in_check_out = "Error (no punch)"
            return

        att_var = attendance_obj.search([('check_in', '<', punch_time), ("employee_id", "=", employee.id)],
                                        order="check_in desc")
        _logger.info(att_var.mapped('check_in'))
        _logger.info(att_var.mapped('id'))
        timestamp = False
        slab_start_time = employee.resource_calendar_id.start_check  # e.g. 4.0, 9.5, 22.0
        # slab_end_time = employee.resource_calendar_id.end_check
        slab_start_hour = int(slab_start_time)
        if att_var:
            check_in_xz = att_var[0].check_in
            timestamp = datetime.combine(check_in_xz.date(), time(slab_start_hour, 0))
            att_var21 = attendance_obj.search([('check_in', '=', punch_time), ("employee_id", "=", employee.id)],
                                              order="check_in desc")
            att_var22 = attendance_obj.search([('check_out', '=', punch_time), ("employee_id", "=", employee.id)],
                                              order="check_in desc")
            if att_var21 or att_var22:
                return True

            _logger.info(f'{employee.name}----{punch_time} --- {punch_time.hour}---{timestamp}')

            if punch_time.hour < 24 and punch_time.date() == timestamp.date():
                if att_var[0].check_in + timedelta(hours=5) < punch_time:
                    _logger.info(f"attendance id=>{att_var[0]},,,,,{punch_time}.....{att_var[0].check_in}11111111")
                    att_var[0].check_out = punch_time - timedelta(hours=5)
                    self.check_in_check_out = f'1st{employee.name}----{punch_time} --- {punch_time.hour}---{timestamp}'
                    self.x_studio_attendance = att_var[0].id
                    att_var[0].sudo()._compute_worked_hours()
            elif punch_time.hour < slab_start_hour and (punch_time.date() - timedelta(days=1)) == timestamp.date():
                if att_var[0].check_in + timedelta(hours=5) < punch_time:
                    _logger.info(f"attendance id=>{att_var[0]},,,,,{punch_time}.....{att_var[0].check_in}22222222")
                    att_var[0].check_out = punch_time - timedelta(hours=5)
                    self.check_in_check_out = f'2nd{employee.name}----{punch_time} --- {punch_time.hour}---{timestamp}'
                    self.x_studio_attendance = att_var[0].id
                    att_var[0].sudo()._compute_worked_hours()
            else:
                uid0 = attendance_obj.create({
                    'employee_id': employee.id,
                    'check_in': punch_time - timedelta(hours=5),
                    'device_code': self.device_code,
                    'attend_check_in': (punch_time - timedelta(hours=5)).date()
                })
                self.check_in_check_out = f'New Checkin{employee.name}----{punch_time} --- {punch_time.hour}---{timestamp}'
                self.x_studio_attendance = uid0.id
        else:
            uid0 = attendance_obj.create({
                'employee_id': employee.id,
                'check_in': punch_time - timedelta(hours=5),
                'device_code': self.device_code,
                'attend_check_in': (punch_time - timedelta(hours=5)).date()
            })
            self.check_in_check_out = f'New Checkin{employee.name}----{punch_time} --- {punch_time.hour}---{timestamp}'
            self.x_studio_attendance = uid0.id

    def _process_hr_attendance_punch2(self, attendance_obj, punch_states):
        """
        Strict 4 AM → 4 AM slab rule:
          • Slab = [04:00 of day → 04:00 of next day] in local tz
          • First punch in slab → check_in
          • Last punch in slab  → check_out
          • Punch outside current slab → new record
        """
        employee = self.employee_id
        punch_time = self.punch_time
        if not punch_time:
            self.check_in_check_out = "Error (no punch)"
            return

        # ---- Define current 4 AM → 4 AM slab boundaries ----
        # slab_start_time = employee.resource_calendar_id.start_check
        # slab_end_time = employee.resource_calendar_id.end_check
        # slab_start = punch_time.replace(hour=4, minute=0, second=0, microsecond=0)
        # if punch_time < slab_start:
        #     slab_start -= timedelta(days=1)
        # slab_end = slab_start + timedelta(days=1)
        slab_start_time = employee.resource_calendar_id.start_check  # e.g. 4.0, 9.5, 22.0
        slab_end_time = employee.resource_calendar_id.end_check  # e.g. 4.0, 18.0, 6.0

        # --- Convert float → hours and minutes ---
        slab_start_hour = int(slab_start_time)
        slab_start_minute = int(round((slab_start_time % 1) * 60))
        slab_end_hour = int(slab_end_time)
        slab_end_minute = int(round((slab_end_time % 1) * 60))

        # --- Define base slab start based on punch day ---
        slab_start = punch_time.replace(
            hour=slab_start_hour,
            minute=slab_start_minute,
            second=0,
            microsecond=0
        )

        # If punch is before slab start → slab started previous day
        if punch_time < slab_start:
            slab_start -= timedelta(days=1)

        # --- Define slab end (based on start & end_check float) ---
        slab_end = slab_start.replace(
            hour=slab_end_hour,
            minute=slab_end_minute,
            second=0,
            microsecond=0
        )

        # If end time is less than start time (overnight shift)
        # → it ends next day
        if slab_end <= slab_start:
            slab_end += timedelta(days=1)

        _logger.info(
            "Processing punch for %s | punch=%s | slab=%s → %s",
            employee.name, punch_time, slab_start, slab_end
        )

        _logger.info(
            "Processing punch for %s | punch=%s | slab=%s → %s",
            employee.name, punch_time, slab_start, slab_end
        )

        # ---- Find all attendances for employee in this slab ----
        att_in_slab = attendance_obj.search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', slab_start),
            ('check_in', '<', slab_end),
        ], order='check_in asc')

        # === CASE 1: No record in slab → create new check_in ===
        if not att_in_slab:
            attendance_obj.create({
                'employee_id': employee.id,
                'check_in': punch_time,
            })
            self.check_in_check_out = "Check In (first punch in slab)"
            _logger.info("Created new Check In for %s at %s", employee.name, punch_time)
            return

        # === CASE 2: Record(s) exist in this slab ===
        att = att_in_slab[0]  # should only be one record per slab ideally
        check_in = att.check_in
        check_out = att.check_out
        _logger.info(punch_time)
        _logger.info(slab_start)
        _logger.info(slab_end)
        _logger.info('gtttttttftftftf')

        # 🔹 If punch < slab_start or >= slab_end → belongs to another slab
        if punch_time < slab_start or punch_time >= slab_end:
            # start new record for that slab (do not close old one)
            attendance_obj.create({
                'employee_id': employee.id,
                'check_in': punch_time,
            })
            self.check_in_check_out = "Check In (new slab boundary)"
            _logger.info(
                "Punch %s for %s belongs to next slab — started new record",
                punch_time, employee.name
            )
            return

        # 🔹 Within current slab
        # case: punch earlier than check_in (out-of-order / duplicate)
        if punch_time <= check_in:
            self.check_in_check_out = "Ignored (Earlier than check_in)"
            _logger.info("Ignored early punch %s <= check_in %s", punch_time, check_in)
            return

        # case: first checkout in this slab
        if not check_out:
            att.check_out = punch_time
            self.check_in_check_out = "Check Out (first in slab)"
            _logger.info(
                "Set Check Out for %s at %s (attendance %s)",
                employee.name, punch_time, att.id
            )
            return

        # case: punch inside slab and later than existing checkout → extend it
        if punch_time > check_out:
            att.check_out = punch_time
            self.check_in_check_out = "Check Out (updated to last punch)"
            _logger.info(
                "Extended Check Out for %s to %s (attendance %s)",
                employee.name, punch_time, att.id
            )
            return

        # case: punch between check_in and check_out → ignore
        self.check_in_check_out = "Ignored (Between IN/OUT)"
        _logger.info(
            "Ignored intermediate punch %s between %s and %s for %s",
            punch_time, check_in, check_out, employee.name
        )

    # for punch_type Based attendance calculation workinn
    # def _process_hr_attendance_punch(self, attendance_obj,punch_states):
    #     """
    #     Policy:
    #       - slab: 04:00 (local Asia/Karachi) .. next day 04:00
    #       - first punch in slab = check_in (create attendance)
    #       - later punches in same slab = update same record's check_out to the latest punch
    #       - punches from a new slab MUST NOT be used to close the previous slab
    #       - datetime values written to DB are naive UTC (Odoo expectation)
    #     """
    #     try:
    #         tz = pytz.timezone('Asia/Karachi')
    #
    #         # --- Normalize punch_time to an aware datetime in UTC ---
    #         punch = self.punch_time
    #         if isinstance(punch, str):
    #             punch = fields.Datetime.from_string(punch)
    #         # If naive, treat as UTC (Odoo stores datetimes as naive UTC in DB)
    #         if punch.tzinfo is None:
    #             punch = pytz.UTC.localize(punch)
    #         # Convert to local tz for slab calculation
    #         punch_local = punch.astimezone(tz)
    #
    #         # --- Compute slab start and end in local time ---
    #         slab_start_local = punch_local.replace(hour=4, minute=0, second=0, microsecond=0)
    #         if punch_local < slab_start_local:
    #             # If punch is before today's 04:00, then slab started yesterday 04:00
    #             slab_start_local -= timedelta(days=1)
    #         slab_end_local = slab_start_local + timedelta(days=1)
    #
    #         # --- Convert slab bounds and punch to naive UTC datetimes for DB operations ---
    #         slab_start_utc = slab_start_local.astimezone(pytz.UTC).replace(tzinfo=None)
    #         slab_end_utc = slab_end_local.astimezone(pytz.UTC).replace(tzinfo=None)
    #         punch_utc_naive = punch_local.astimezone(pytz.UTC).replace(tzinfo=None)
    #
    #         employee_id = self.employee_id.id
    #
    #         # --- Search ONLY for attendance whose check_in is inside this slab ---
    #         att = attendance_obj.search([
    #             ('employee_id', '=', employee_id),
    #             ('check_in', '>=', slab_start_utc),
    #             ('check_in', '<', slab_end_utc)
    #         ], limit=1, order='check_in asc')
    #
    #         if not att:
    #             # First punch in this slab -> create check_in (leave check_out empty)
    #             attendance_obj.create({
    #                 'employee_id': employee_id,
    #                 'check_in': punch_utc_naive,
    #             })
    #             self.check_in_check_out = "Check In"
    #             return
    #
    #         # There is already a record for this slab -> update its checkout to the LATEST punch
    #         # Ignore punches that are older than or equal to the check_in (e.g., delayed/duplicate old punches)
    #         if punch_utc_naive <= att.check_in:
    #             self.check_in_check_out = "Ignored (Older Punch)"
    #             return
    #
    #         # Update check_out if empty or if this punch is later than the existing checkout
    #         if not att.check_out or punch_utc_naive > att.check_out:
    #             att.write({'check_out': punch_utc_naive})
    #             self.check_in_check_out = "Check Out"
    #         else:
    #             self.check_in_check_out = "Ignored (Older Punch)"
    #
    #     except Exception:
    #         _logger.exception("Error processing attendance punch for employee %s",
    #                           getattr(self.employee_id, 'id', False))
    #         self.check_in_check_out = "Error"

    # for smart attendance calculation
    # def _process_hr_attendance(self, obj, target_timezone):
    #     no_checkout_tolerance    = self.env['ir.config_parameter'].sudo().get_param('softatt_attendance.no_checkout_tolerance')
    #
    #     punch_time      = self.punch_time.astimezone(target_timezone).replace(tzinfo=None)
    #     employee        = self.employee_id
    #     employee_id     = employee.id
    #     working_hours   = employee.resource_calendar_id
    #     punch_state     = working_hours._softatt_get_period_punch(str(punch_time.weekday()), punch_time.time())
    #     if not punch_state:
    #         self.check_in_check_out = "Undefined Punch"
    #         return
    #     punch_state     = punch_state.punch_type
    #     punch_time      = self.punch_time
    #     try:
    #         oatt_domain=[('employee_id.id','=',employee_id),('check_in','!=',False),('check_out', '=', False)]
    #         open_att=obj.search(oatt_domain, limit=1)
    #         if punch_state == "in":
    #             self.check_in_check_out = "Check In"
    #             if not open_att:
    #                 obj.create({'employee_id':employee_id,'check_in':punch_time})
    #             if open_att and punch_time >= open_att.check_in +timedelta(hours=float(no_checkout_tolerance)):
    #                 open_att.check_out = open_att.check_in
    #                 obj.create({'employee_id':employee_id,'check_in':punch_time})
    #             else:
    #                 return
    #         if punch_state == "out":
    #             self.check_in_check_out = "Check Out"
    #             if not open_att:
    #                 pass
    #
    #             if open_att and punch_time >= open_att.check_in +timedelta(hours=float(no_checkout_tolerance)):
    #                 open_att.check_out = open_att.check_in
    #             else:
    #                 open_att.write({'check_out': punch_time})
    #     except Exception as e:
    #         return

    # def action_update_hr_attendance(self):
    #     self.action_compute_employees()
    #     obj = self.env["hr.attendance"]
    #     punch_states = self.env["sa.punch.state"]
    #     recs = self.filtered(lambda x: x.employee_id).sorted(key=lambda x: x.punch_time)
    #     for r in recs:
    #         target_timezone = pytz.timezone(self.env.user.tz)
    #         try:
    #             if r.employee_id.attendance_type == 'smart':
    #                 r._process_hr_attendance(obj, target_timezone)
    #             else:
    #                 r._process_hr_attendance_punch(obj, punch_states)
    #         except:
    #             continue

    def action_update_hr_attendance(self):
        self.action_compute_employees()
        attendance_obj = self.env["hr.attendance"]
        punch_states = self.env["sa.punch.state"]

        # ✅ Ensure punch times are sorted oldest → newest
        recs = self.filtered(lambda x: x.employee_id and x.punch_time and x.x_studio_punch_type == 15).sorted(
            key=lambda x: x.punch_time
        )

        for rec in recs:
            target_timezone = pytz.timezone(self.env.user.tz or 'UTC')
            # try:
            if 1 == 1:
                if rec.employee_id.attendance_type == 'smart' and 1==2:
                    # If your smart attendance uses timezone-based method
                    rec._process_hr_attendance(attendance_obj, target_timezone)
                else:
                    # Default “punch machine” handling
                    rec._process_hr_attendance_punch(attendance_obj, punch_states)
            # except Exception as e:
            else:
                _logger.warning(
                    f"⚠️ Attendance sync skipped for {rec.employee_id.name or 'Unknown'} at {rec.punch_time}: {e}"
                )
                continue

    def _is_same_server_logs(self):
        return False

    def get_transactions(self):
        if self._is_same_server_logs():
            self._same_server_transactions()
            return
        mode = self.env['ir.config_parameter'].sudo().get_param('softatt_attendance.softatt_comm_mode')
        if mode == 'api':
            self._api_transactions()
        if mode == 'dblink':
            device_codes = self.env["sa.biometric.device"].search([]).mapped("externalid")
            self._dblink_transactions(device_codes)

    def _dblink_transactions(self, device_codes=()):
        linked_servers = self.env['sa.db_link.server'].sudo().search([('registered', '=', True)])
        query = ""
        count_server_ids = len(linked_servers.sudo().read(['name']))
        count = 0
        codes = f"({str(device_codes)[1:-1]})"
        for server in linked_servers:
            count += 1

            query += f"""
				SELECT
                    DATA.id,
                    DATA.area,
                    DATA.emp_code,
                    DATA.device_id,
                    DATA.punch_time,
                    DATA.punch_state,
                    DATA.db_name
				FROM public.dblink
				    ('{server.name}',
                            'SELECT 
                                t.id,
                                d.name as area,
                                device_id,
                                emp_code,
                                punch_time,
                                punch_state,
                                current_database()
                            FROM public.sa_biometric_att t
                            LEFT JOIN sa_biometric_device d ON(d.id=t.device_id) 
                            WHERE device_id in {codes}') AS DATA

                                (id integer,
                                area CHARACTER VARYING,
                                device_id integer,
                                emp_code CHARACTER VARYING,
                                punch_time timestamp,
                                punch_state CHARACTER VARYING,
                                db_name CHARACTER VARYING)
				LEFT JOIN (
                            SELECT db_name, hubid, device_code 
                            FROM sa_attendance_log smal 
                            WHERE smal.device_code in {codes}) AS mal 
                    ON mal.hubid=Data.id AND mal.db_name=Data.db_name
				WHERE mal.hubid is NULL
			"""

            if count_server_ids > count:
                query += """ UNION """
            else:
                query += """ ORDER BY punch_time,punch_state LIMIT 500;"""
        self._process_sql_logs(query)

    def _process_sql_logs(self, query):
        self.env.cr.execute(query)
        transactions = self.env.cr.dictfetchall()
        devices = self.env['sa.biometric.device']
        attendance_log = self
        logs = []
        for line in transactions:
            device_id = devices.search([("externalid", "=", line["device_id"])], limit=1)
            logs.append({"hubid": line["id"],
                         "location_alias": line["area"],
                         "code": line["emp_code"],
                         "device_code": line["device_id"],
                         "punch_time": line["punch_time"],
                         "punch_state": line["punch_state"],
                         "db_name": line["db_name"],
                         "company_id": device_id.company_id.id if device_id else None,
                         })
        log = attendance_log.sudo().create(logs)
        log.action_update_hr_attendance()

    def _api_transactions(self):
        conf_param = self.env['ir.config_parameter']
        session_id = conf_param._softatt_authenticate()
        url = conf_param.sudo().get_param('softatt_attendance.att_server_url')
        limit = conf_param.sudo().get_param('softatt_attendance.att_limit')
        self.env.cr.execute("SELECT max(hubid) as max_id FROM sa_attendance_log")
        max_id = self.env.cr.dictfetchone()['max_id'] or 0
        full_url = "%s/attendence/transactions/%s/%s" % (url, max_id, limit)
        headers = {"Cookie": 'session_id=%s' % session_id}
        request = requests.request("GET", full_url, headers=headers, data={})
        response = json.loads(request.text)
        _logger.info(full_url)
        res = response.get('transactions')
        attendance_log = self
        employees = self.env["sa.attendance.employee.code"]
        logs = []
        for line in res:
            emp_code_id = employees.search([
                ("code", "=", line["emp_code"]),
                ("device_id.externalid", "=", line["device_id"])], limit=1)
            logs.append({
                'hubid': line['id'],
                'location_alias': line['area'],
                'code': line['emp_code'],
                'device_code': line['device_id'],
                'punch_time': line['punch_time'],
                'punch_state': line['punch_state'],
                'employee_id': emp_code_id.employee_id.id if emp_code_id else None,
            })
        log = attendance_log.sudo().create(logs)
        log.action_update_hr_attendance()

    def _same_server_transactions(self):
        return

    def download_latest_logs(self):
        self.get_transactions()
