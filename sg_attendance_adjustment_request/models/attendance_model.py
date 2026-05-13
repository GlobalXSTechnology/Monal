from odoo import models,fields,api
from datetime import datetime
from datetime import datetime, timedelta, time



class AttendnceFields(models.Model):
    _inherit = 'hr.attendance'

    # date = fields.Date(string="Date", default=fields.Date.today)
    @api.depends('check_in')
    def new_date(self):
        for rec in self:
            # rec.attend_check_in = (rec.check_in + timedelta(hours=5)).date()
            rec.shift_check_in_date = (rec.check_in + timedelta(hours=5)).date()
            if 2==2:
                employee = rec.employee_id
                # timedelta = datetime.timedelta
                
                slab_start_time = employee.resource_calendar_id.start_check
                slab_end_time = employee.resource_calendar_id.end_check
            
                slab_start_hour = int(slab_start_time)
                slab_end_hour = int(slab_end_time)
                # raise UserError(rec.check_in + timedelta(hours=5))
                check_in = rec.check_in + timedelta(hours=5)
                # Determine shift date (NIGHT SHIFT SAFE)
                if slab_end_time <= slab_start_time:
                    # Night shift
                    if check_in.hour < slab_end_hour:
                        shift_date = check_in.date() - timedelta(days=1)
                    else:
                        shift_date = check_in.date()
                else:
                    # Day shift
                    shift_date = check_in.date()
            
                shift_start = datetime.combine(shift_date,time(slab_start_hour, 0))
                
                # rec.write({'attend_check_in':(shift_start - timedelta(hours=5)).date()})
                adjustment_record = self.env['attendance.adjustment'].search([('emp_check_in','=',rec.check_in),('name','=',employee.id)],limit=1)
                if not adjustment_record:
                    rec.write({'attend_check_in':(shift_start - timedelta(hours=5)).date()})
                else:
                    rec.write({'attend_check_in':adjustment_record[0].att_date})

      

    attend_check_in = fields.Date('Hide this check in',compute='new_date',store=True)
    shift_check_in_date = fields.Date('Shift date',store=True)
