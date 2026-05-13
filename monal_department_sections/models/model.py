from odoo import models, fields, api


class DepartmentSection(models.Model):
	_name = 'department.section'
	_description = 'Department Section'
	
	
	name = fields.Char(string="Name")
	
	
	
	
	
	
class HrDepartment(models.Model):
	_inherit= 'hr.department'
	
	
	
	section_id = fields.Many2one("department.section", string="Section")