from odoo import _, api, fields, models


class AttendanceEmployeeCodes(models.Model):
    _name = "sa.attendance.employee.code"
    _description = "Employee Code"
    
    employee_id         = fields.Many2one("hr.employee", string="Employee", readonly=True, 
    ondelete='cascade'
    )
    public_employee_id         = fields.Many2one("hr.employee.public", string="Employee", readonly=True, ondelete='cascade')

    code                = fields.Char(string="Code", required=True, nocopy=True)
    device_id           = fields.Many2one("sa.biometric.device", string="Device", tracking=True, 
    ondelete='cascade')
    
    _sql_constraints = [
        ('unique_device_id_code', 'unique(device_id, code)', 'Device and Code must be unique together!')
    ]
        
class AttendanceEmployee(models.Model):
    _inherit = "hr.employee"
    
    attendance_type = fields.Selection([('smart', 'Smart'),('punch', 'Punch Type')], default='punch',required=True)
    code_ids        = fields.One2many('sa.attendance.employee.code', 'employee_id', string='Codes', copy=False)    


class AttendanceEmployeePublic(models.Model):
    _inherit = "hr.employee.public"
    
    attendance_type = fields.Selection([('smart', 'Smart'),('punch', 'Punch Type')], default='punch',required=True)
    code_ids        = fields.One2many('sa.attendance.employee.code', 'public_employee_id', string='Codes', copy=False)
 