from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import qrcode
import base64
from io import BytesIO


class CustomerFeedback(models.Model):
    _name = 'customer.feedback'
    _description = "Customer Feedback"
    _rec_name = "name"
    _order = 'create_date desc'

    name = fields.Char(string="Customer")
    email = fields.Char(string="Email Address")
    contact_number = fields.Char(string="Contact Number")
    date_birth = fields.Date(string="Date of Birth")
    anniversary = fields.Char(string="Anniversary")
    address = fields.Char(string="Address")
    remarks = fields.Text(string="Suggestions / Remarks")
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments", help="Attach images or files with your feedback")
    customer_feedback_lines_id = fields.One2many('customer.feedback.lines', 'customer_feedback_id', string='Customer Feedback Lines')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    website_id = fields.Many2one('website', string='Website', help="Website where this feedback was submitted")
    excelent_count = fields.Integer(string="Excellent Count", compute="compute_feedback")
    good_count = fields.Integer(string="Good Count", compute="compute_feedback")
    average_count = fields.Integer(string="Average Count", compute="compute_feedback")

    @api.depends('customer_feedback_lines_id')
    def compute_feedback(self):
        for rec in self:
            rec.excelent_count = len(rec.customer_feedback_lines_id.filtered(lambda x: x.value == '1'))
            rec.good_count = len(rec.customer_feedback_lines_id.filtered(lambda x: x.value == '2'))
            rec.average_count = len(rec.customer_feedback_lines_id.filtered(lambda x: x.value == '3'))
            


class CustomerFeedbackLines(models.Model):
    _name = 'customer.feedback.lines'

    customer_feedback_id = fields.Many2one('customer.feedback', string='Customer Feedback Id')
    question = fields.Many2one('monal.customer.feedback.line', string='Question')
    value = fields.Selection([
        ('1', 'Excellent'),
        ('2', 'Good'),
        ('3', 'Average'),
    ], string='Value')
    company_id = fields.Many2one('res.company', string='Company', related='customer_feedback_id.company_id', store=True, readonly=True)
    website_id = fields.Many2one('website', string='Website', related='customer_feedback_id.website_id', store=True, readonly=True)


class MonalCustomerFeedback(models.Model):
    _name = 'monal.customer.feedback'
    _description = "Monal Customer Feedback Record"

    name = fields.Char(string="Name", store=True)
    lines_ids = fields.One2many("monal.customer.feedback.line", "feedback_id", string="Feedback lines")
    remarks = fields.Html(string="Remarks")
    company_id = fields.Many2one('res.company', string='Company', store=True, default=lambda self: self.env.company, readonly=True)
    website_id = fields.Many2one('website', string='Website', store=True)
    page_url = fields.Char(string="Page URL", help="URL of the webpage where this feedback was submitted")
    thank_you_url = fields.Char(string="Thank You URL", help="URL of the webpage where this feedback was submitted")
    qr_code = fields.Binary(string="QR Code", compute='generate_qr_code', help="QR Code generated from Page URL")
    qr_code_url = fields.Char(string="QR Code URL", compute='generate_qr_code', help="URL of the QR code image")
    
    @api.depends('page_url')
    def generate_qr_code(self):
        """Generate QR code from page_url with base URL and store as base64 encoded image."""
        for record in self:
            if record.page_url:
                # Get base URL from system parameters
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
                # Combine base URL with page URL path
                full_url = f"{base_url}/website/forced/{record.website_id.id}?path=/{record.page_url}"
                
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(full_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                record.qr_code = base64.b64encode(buffer.getvalue())
                record.qr_code_url = full_url
            else:
                record.qr_code = False
                record.qr_code_url = False
    
    def action_download_qr_code(self):
        """Download the QR code as a PNG file."""
        self.ensure_one()
        if not self.qr_code:
            return
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=monal.customer.feedback&id={self.id}&field=qr_code&filename={self.name or "qr_code"}.png&download=1',
            'target': 'self',
        }
    
    @api.onchange('page_url')
    def _onchange_page_url(self):
        """Auto-generate QR code when page_url changes."""
        self.generate_qr_code()
    
    
    @api.model
    def _load_pos_data_domain(self, data):
        """
        Extend the domain logic to include custom filtering for riders while preserving
        the original logic for cashiers.
        """
        # Call the original method (used for cashiers)
        # Get the POS config
        config_id = self.env['pos.config'].browse(data['pos.config']['data'][0]['id'])
        print(config_id)
        # If rider-specific logic is required
        if config_id.iface_available_ft_id:
            ft_domain = [
                '&', ('company_id', '=', config_id.company_id.id),
                ('id', '=', config_id.iface_available_ft_id.id)
            ]
            print(ft_domain)
            return ft_domain

        # Default to the cashier domain if no rider-specific logic applies
        return [('id', '=', False)]

    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Extend the fields logic to specify rider fields if necessary.
        """
        # Call the original method (used for cashiers)

        # Define custom fields for riders
        ft_fields = ['name', 'lines_ids']

        # Return rider-specific fields instead of default cashier fields
        return ft_fields

    def _load_pos_data(self, data):
        """
        Extend the data loading logic to include rider data separately
        while ensuring the cashier data remains intact.
        """
        # Call the original method (used for cashiers)
        # Get the domain and fields for riders
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])

        # Search for employees (riders) matching the domain
        ft = self.search(domain)
        # Read the data for the riders based on the defined fields
        ft_data = ft.read(fields, load=False)

        # Debugging logs (optional)
        print("Ft:", ft)
        print("Ft Data:", ft_data)

        # Return the rider-specific data while keeping the original response intact
        return {
            'data': ft_data,
            'fields': fields,
        }


class MonalCustomerFeedbackLines(models.Model):
    _name = 'monal.customer.feedback.line'
    _description = "Monal Customer Feedback Record"

    feedback_id = fields.Many2one("monal.customer.feedback", string="Feedback Template Name")
    name = fields.Char(string="Name")
    value = fields.Selection([
        ('1', 'Excellent'),
        ('2', 'Good'),
        ('3', 'Average'),
    ], string='Value')
    company_id = fields.Many2one(related='feedback_id.company_id', string='Company')
    website_id = fields.Many2one(related='feedback_id.website_id', string='Website')

    @api.model
    def _load_pos_data_domain(self, data):
        config_id = self.env['pos.config'].browse(data['pos.config']['data'][0]['id'])
        card_domain = [('id', '!=', False)]
        return card_domain

    @api.model
    def _load_pos_data_fields(self, config_id):
        card_fields = ['id', 'feedback_id', 'name', 'value']
        return card_fields

    def _load_pos_data(self, data):
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
        card = self.search(domain)
        card_data = card.read(fields, load=False)
        return {
            'data': card_data,
            'fields': fields,
        }


class OrderFeedbackLines(models.Model):
    _name = 'order.feedback.line'

    order_id = fields.Many2one('pos.order', string='Order')
    question = fields.Many2one('monal.customer.feedback.line', string='Question')

    value = fields.Selection([
        ('1', 'Excellent'),
        ('2', 'Good'),
        ('3', 'Average'),
    ], string='Value')

    @api.model
    def _load_pos_data_domain(self, data):
        config_id = self.env['pos.config'].browse(data['pos.config']['data'][0]['id'])
        card_domain = [('id', '!=', False)]
        return card_domain

    @api.model
    def _load_pos_data_fields(self, config_id):
        card_fields = ['id', 'question', 'value', 'order_id']
        return card_fields

    def _load_pos_data(self, data):
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
        card = self.search(domain)
        card_data = card.read(fields, load=False)
        return {
            'data': card_data,
            'fields': fields,
        }
