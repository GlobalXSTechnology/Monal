from odoo import models, fields


class CustomerFeedbackWizard(models.TransientModel):
    _name = 'customer.feedback.wizard'
    _description = 'Customer Feedback Report Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    website_id = fields.Many2one(
        'website',
        string="Website",
        required=True
    )

    def action_print_report(self):
        self.ensure_one()

        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'website_id': self.website_id.id if self.website_id else False,
        }

        return self.env.ref(
            'customer_feedback_report.action_feedback_report'
        ).report_action(self, data=data)


class FeedbackReport(models.AbstractModel):
    _name = 'report.customer_feedback_report.feedback_template'

    def _get_report_values(self, docids, data=None):

        date_from = data.get('date_from')
        date_to = data.get('date_to')
        website_id = data.get('website_id')

        domain = [
            ('create_date', '>=', date_from),
            ('create_date', '<=', date_to)
        ]

        if website_id:
            domain.append(('website_id', '=', website_id))

        records = self.env['customer.feedback'].search(domain)

        # SUMMARY
        summary = {
            'total': {
                'FQ': 0, 'SR': 0, 'PR': 0,
                'CL': 0, 'EN': 0, 'SA': 0, 'MU': 0,
            },
            'excellent': {
                'FQ': 0, 'SR': 0, 'PR': 0,
                'CL': 0, 'EN': 0, 'SA': 0, 'MU': 0,
            },
            'good': {
                'FQ': 0, 'SR': 0, 'PR': 0,
                'CL': 0, 'EN': 0, 'SA': 0, 'MU': 0,
            },
            'average': {
                'FQ': 0, 'SR': 0, 'PR': 0,
                'CL': 0, 'EN': 0, 'SA': 0, 'MU': 0,
            },
        }

        question_map = {
            'Food Quality': 'FQ',
            'Service': 'SR',
            'Presentation': 'PR',
            'Cleanliness': 'CL',
            'Environment': 'EN',
            'Staff Attitude': 'SA',
            'Music': 'MU',
        }

        docs = []

        for rec in records:

            answers = {
                'FQ': '',
                'SR': '',
                'PR': '',
                'CL': '',
                'EN': '',
                'SA': '',
                'MU': '',
            }

            value_map = {
                '1': 'E',
                '2': 'G',
                '3': 'A',
            }

            for line in rec.customer_feedback_lines_id:

                abbreviated_value = value_map.get(line.value, '')

                key = question_map.get(line.question.name)

                if key:
                    answers[key] = abbreviated_value

                    # SUMMARY COUNTS
                    summary['total'][key] += 1

                    if line.value == '1':
                        summary['excellent'][key] += 1

                    elif line.value == '2':
                        summary['good'][key] += 1

                    elif line.value == '3':
                        summary['average'][key] += 1

            user_tz_date = fields.Datetime.context_timestamp(
                self,
                rec.create_date
            ) if rec.create_date else False

            docs.append({
                'bill_no': rec.id,
                'date': user_tz_date.strftime('%Y-%m-%d %H:%M:%S') if user_tz_date else '',
                'time': user_tz_date.strftime('%H:%M') if user_tz_date else '',
                'name': rec.name,
                'address': rec.address,
                'email': rec.email,
                'date_birth': rec.date_birth,
                'anniversary': rec.anniversary,
                'contact': rec.contact_number,
                'answers': answers,
                'remarks': rec.remarks,
                'website_name': rec.website_id.name if rec.website_id else '',
            })

        website_name = ''

        if website_id:
            website = self.env['website'].browse(website_id)
            website_name = website.name if website else ''

        return {
            'docs': docs,
            'website_name': website_name,
            'summary': summary,
            'date_from': date_from,
            'date_to': date_to,
        }