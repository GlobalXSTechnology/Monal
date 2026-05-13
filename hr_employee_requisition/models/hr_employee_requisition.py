from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class HREmployeeRequisition(models.Model):
    _name = 'hr.employee.requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Requisition"

    name = fields.Char(string="Name", default="NEW", tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", tracking=True, required=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    required_employees = fields.Integer(string="Employees", tracking=True, required=True)
    required_budget = fields.Monetary(string="Budget", tracking=True, required=True)
    state = fields.Selection([('draft', 'HR'), ('approval', 'Deputy CFO'), ('approved', 'CEO'), ('cancel', 'Cancel')],
                             default="draft", tracking=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    date = fields.Date(string="Date", default=fields.Date.today(), required=True, tracking=True)
    current_head_count = fields.Integer(string="Current Head Count")
    current_employee_count = fields.Integer(string="Current Employee Count")
    user_id = fields.Many2one('res.users', string="Requested By")
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id.id,
        required=True)
    total_wage = fields.Monetary(
        string="Additional Budget ",
        store=True,
        related='department_id.total_wage',
        currency_field='currency_id',
        tracking=True,
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.employee.requisition') or 'New'
        vals['user_id'] = self.env.user.id
        result = super(HREmployeeRequisition, self).create(vals)
        return result

    @api.onchange('department_id')
    def onchange_department_id(self):
        self.current_head_count = self.department_id.head_count_employee
        self.current_employee_count = self.department_id.total_employee

    def action_approve(self):
        # if self.department_id.head_count_employee < self.department_id.total_employee + self.required_employees:
        self.write({'state': 'approval'})
        self.send_approval_email()

    def action_approval(self):
        self.write({'state': 'approved'})
        self.department_id.write({'head_count_employee': self.department_id.head_count_employee + self.required_employees})
        self.department_id.write({'budget': self.department_id.budget + self.required_budget})

    def action_draft(self):
        if self.state != 'approved':
            self.write({'state': 'draft'})
        else:
            raise ValidationError(_("You cannot set this record to draft as its already approved"))

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_archive(self):
        for rec in self:
            if rec.state != 'approved':
                rec.write({'active': False})
            else:
                raise ValidationError(_("You cannot archive this record as it is approved."))

    def action_unarchive(self):
        for rec in self:
            rec.write({'active': True})

    def send_approval_email(self):

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_url = f"{base_url}/odoo/employee-requisition/{self.id}"

        company_email = self.env['res.company'].search([('id', '=', 1)]).email
        group = self.env.ref('hr_employee_requisition.group_emp_requisition_admin')
        users = group.users

        for rec in users:
            # data = {
            #     'email_from': company_email,
            #     'email_to': rec.partner_id.email,
            #     'subject': 'Employee Requisition Approval',
            #
            #     'body_html': f"""<div>
            #                                 <p>Dear {rec.partner_id.name},</p>
            #                                 <p>Hope you are doing well.</p>
            #                                 <p>This email is to notify you to approve employee requisition for the department {self.department_id.name}.</p>
            #                                 <p>Please <a href="{action_url}">click here</a> to view and approve the requisition.</p>
            #                                 </div>
            #                                         """
            # }
            data = {
                'email_from': company_email,
                'email_to': rec.partner_id.email,
                'subject': 'Employee Head Count Approval',

                'body_html': f"""<div>
                                            <p>Dear {rec.partner_id.name},</p>
                                            <p>Hope you are doing well.</p>
                                            <p>This email is to notify you to approve employee head count for the department <b>{self.department_id.name}</b>.</p>
                                            </div>
                                                    """
            }
            self.env['mail.mail'].create(data).send()
        return
