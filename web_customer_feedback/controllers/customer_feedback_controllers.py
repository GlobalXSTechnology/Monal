from odoo import http
from odoo.http import request
import logging
import werkzeug.urls
from odoo.addons.website.controllers.main import Website

import base64

_logger = logging.getLogger(__name__)

class CustomerFeedbackController(http.Controller):

    @http.route('/customer/feedback/submit', type='http', auth='public', website=True, csrf=False)
    def customer_feedback_submit(self, **post):
        # Get website_id from form data first, then fallback to current website
        website_id = post.get('website_id')
        feeback_id = post.get('feedback_id')
        if feeback_id:
            feeback_id = request.env['monal.customer.feedback'].sudo().browse(int(feeback_id))
        else:
            feeback_id = False
            
        if website_id:
            current_website = request.env['website'].sudo().browse(int(website_id))
            if not current_website.exists():
                current_website = request.website
        else:
            current_website = request.website
        
        # Get company from website or fallback to current company
        current_company = current_website.company_id if current_website else request.env.company
        
        # Create feedback with company and website
        feedback = request.env['customer.feedback'].sudo().create({
            'name': post.get('name'),
            'email': post.get('email'),
            'contact_number': post.get('contact_number'),
            'date_birth': post.get('date_birth') or False,
            'anniversary': post.get('anniversary'),
            'address': post.get('address'),
            'remarks': post.get('remarks'),
            'company_id': current_company.id,
            'website_id': current_website.id if current_website else False,
        })

        # Handle file attachments
        files = request.httprequest.files.getlist('attachments')
        if files:
            attachment_ids = []
            for attachment in files:
                if attachment.filename:
                    file_content = attachment.read()
                    attachment_data = {
                        'name': attachment.filename,
                        'datas': base64.b64encode(file_content),
                        'res_model': 'customer.feedback',
                        'res_id': feedback.id,
                    }
                    attachment_id = request.env['ir.attachment'].sudo().create(attachment_data)
                    attachment_ids.append(attachment_id.id)
            if attachment_ids:
                feedback.write({'attachment_ids': [(6, 0, attachment_ids)]})

        # Get question IDs directly from POST data (keys that are numeric)
        for key, value in post.items():
            if key.isdigit():
                question_id = int(key)
                if value:
                    request.env['customer.feedback.lines'].sudo().create({
                        'customer_feedback_id': feedback.id,
                        'question': question_id,
                        'value': value,
                    })
        
        # Redirect to thank you page with customer name
        customer_name = post.get('name', '')
        # Get custom redirect URL from form or use default
        custom_redirect = post.get('redirect_url') or '/feedback/thank-you'
        if custom_redirect:
            # Append name parameter to custom URL
            separator = '&' if '?' in custom_redirect else '?'
            redirect_url = custom_redirect + separator + 'name=' + werkzeug.urls.url_quote(customer_name)
        else:
            redirect_url = '/feedback/thank-you?name=' + werkzeug.urls.url_quote(customer_name)
        
        response = request.redirect(redirect_url)
        # Prevent browser caching to ensure form is fresh on back button
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @http.route('/feedback/thank-you', type='http', auth='public', website=True)
    def feedback_thank_you(self, **kw):
        """Custom URL for thank you page"""
        response = request.render('web_customer_feedback.customer_feedback_thank_you', {
            'customer_name': kw.get('name', 'valued customer'),
        })
        # Prevent browser caching to ensure fresh page on back button
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @http.route('/customer/feedback/data', type='json', auth='public', website=True, csrf=False)
    def get_feedback_data(self, **kw):
        """Get feedback data for snippet rendering via JSON-RPC"""
        try:
            # Get current website and company
            current_website = request.website
            current_company = current_website.company_id if current_website else request.env.company
            # Get questions for the feedback form
            feedback_template_id = request.env['monal.customer.feedback']
            if current_company:
                domain = [('company_id', '=', current_company.id), ('website_id', '=', current_website.id)]
                feedback_template_id = request.env['monal.customer.feedback'].sudo().search(domain, limit=1, order='id DESC')
                
                questions = request.env['monal.customer.feedback.line'].sudo().search([('feedback_id', '=', feedback_template_id.id)], order='id ASC')
                questions_data = questions.read(['name', 'id'])
            else:
                questions_data = []
            _logger.info(f'Questions data: {questions_data}')
            return {
                'questions': questions_data,
                'redirect_url': feedback_template_id.thank_you_url,
                'current_company': {'id': current_company.id, 'name': current_company.name} if current_company else None,
                'current_website': {'id': current_website.id, 'name': current_website.name} if current_website else None,
                'feedback_id': {'id': feedback_template_id.id, 'name': feedback_template_id.name} if feedback_template_id else None,
            }
        except Exception as e:
            return {'error': str(e)}
        
        
class CustomerFeedbackWebsite(Website):

    @http.route('/website/forced/<int:website_id>', type='http', auth="public", website=True, sitemap=False, multilang=False, readonly=True)
    def website_forced(self, website_id, path='/', isredir=False, **kw):
        website = request.env['website'].browse(website_id)
        # url_to = werkzeug.urls.url_join(website.domain, '/website/force/%s?isredir=1&path=%s' % (website.id, path))
        # return request.redirect(url_to)
        website._force()
        return request.redirect(path)
        # return super(CustomerFeedbackWebsite, self).website_force(website_id, path=path, isredir=isredir, **kw)
