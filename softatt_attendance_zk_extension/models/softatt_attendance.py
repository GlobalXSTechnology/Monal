from odoo import models
import logging


_logger = logging.getLogger(__name__)


class saAttendanceLog(models.Model):
    _inherit           = "sa.attendance.log"
    
    def _is_same_server_logs(self):
        super()._is_same_server_logs()
        return True
    
    def action_compute_employees(self):
        employees = self.env["sa.attendance.employee.code"]
        for r in self:
            employee_id = employees.search([("code", "=", r.code),("device_id.id", "=", r.device_code),],limit=1).employee_id
            if employee_id:
                r.employee_id = employee_id.id
            else:
                r.employee_id = None
                
    def _same_server_transactions(self):
        super()._same_server_transactions()
        query = """
                SELECT
                    attl.id,
                    d.name as area,
                    attl.emp_code,
                    attl.device_id,
                    attl.punch_time,
                    attl.punch_state,
                    current_database() as db_name
				FROM sa_biometric_att AS attl
                LEFT JOIN sa_biometric_device AS d 
                    ON(d.id=attl.device_id)
				LEFT JOIN (SELECT db_name, hubid, device_code FROM sa_attendance_log smal) AS mal 
                    ON mal.hubid=attl.id AND mal.db_name=db_name
		WHERE mal.hubid is NULL 
                ORDER BY punch_time, punch_state
		LIMIT 1000"""
        
        self._process_sql_logs(query)
        
        
    def _process_sql_logs(self, query):
        self.env.cr.execute(query)
        transactions    = self.env.cr.dictfetchall()
        employees       = self.env["sa.attendance.employee.code"]
        devices         = self.env['sa.biometric.device']
        attendance_log  = self
        logs            = []
        for line in transactions:
            device_id = devices.search([("id", "=", line["device_id"])],limit=1)
            logs.append({"hubid"           : line["id"],
                        "location_alias"   : line["area"],
                        "code"             : line["emp_code"],
                        "device_code"      : line["device_id"],
                        "punch_time"       : line["punch_time"],
                        "punch_state"      : line["punch_state"],
                        "db_name"          : line["db_name"],
                        "company_id"       : device_id.company_id.id if device_id else None,
                        })
        log = attendance_log.sudo().create(logs)
        log.action_update_hr_attendance()