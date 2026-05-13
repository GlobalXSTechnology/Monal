/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

const FeedbackSnippet = publicWidget.Widget.extend({
    selector: '.s_feedback_snippets_options',
    disabledInEditableMode: false,
    events: {
        'submit form': '_onFormSubmit',
    },

    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.data = {};
        console.log('[FeedbackSnippet] Widget initialized');
    },

    /**
     * @override
     */
    willStart: function () {
        console.log('[FeedbackSnippet] willStart called');
        return this._super.apply(this, arguments).then(
            () => this._fetchData()
        );
    },

    /**
     * @override
     */
    start: function () {
        console.log('[FeedbackSnippet] start called, element:', this.$el);
        const self = this;

        // Listen for page visibility changes to clear form on back button
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden) {
                // Page became visible (e.g., via back button)
                console.log('[FeedbackSnippet] Page visible, clearing form');
                self._clearFormFields();
            }
        });

        return this._super.apply(this, arguments).then(function() {
            // Small delay to ensure DOM is fully rendered
            setTimeout(function() {
                self._render();
                // Clear any cached form data from browser
                self._clearFormFields();
            }, 100);
        });
    },

    // ---------------------------------------------------------------------
    // Private
    // ---------------------------------------------------------------------

    /**
     * Clear all form fields to prevent back-button caching issues
     * @private
     */
    _clearFormFields: function () {
        console.log('[FeedbackSnippet] Clearing form fields');

        // Clear text inputs
        this.$el.find('input[type="text"], input[type="email"], input[type="number"], input[type="date"], input[type="tel"], textarea').each(function() {
            $(this).val('');
        });

        // Clear radio selections
        this.$el.find('input[type="radio"]').prop('checked', false);

        // Clear file inputs
        this.$el.find('input[type="file"]').val('');

        // Clear session storage
        sessionStorage.removeItem('feedback_form_data');

        console.log('[FeedbackSnippet] Form fields cleared');
    },

    /**
     * Fetch data from the controller
     * @private
     */
    _fetchData: function () {
        const self = this;
        console.log('[FeedbackSnippet] Fetching data via fetch API');

        return fetch("/customer/feedback/data", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin',
            body: JSON.stringify({})
        })
        .then(function(response) {

            console.log('[FeedbackSnippet] Response status:', response);
            console.log('[FeedbackSnippet] Response status:', response.status);
            if (!response.ok) {
                throw new Error('HTTP error! status: ' + response.status);
            }
            return response.json();
        })
        .then(function(data) {
            console.log('[FeedbackSnippet] Data received:', data);
            self.data = data;
        })
        .catch(function (error) {
            console.error("[FeedbackSnippet] Error fetching feedback data:", error);
            self.data = { error: error.message || "Failed to load data" };
        });
    },

    /**
     * Render only the questions section with fetched data
     * @private
     */
    _render: function () {
        console.log('[FeedbackSnippet] Rendering questions with data:', this.data);

        if (this.data.error) {
            console.error('[FeedbackSnippet] Error:', this.data.error);
            return;
        }
        console.log('[FeedbackSnippet] Dataaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:', this.data);
        const questions = this.data?.result?.questions || [];
        console.log('[FeedbackSnippet] Questionssssssssssssssssssss:', questions);
        const currentCompany = this.data?.result?.current_company;
        const currentWebsite = this.data.result?.current_website;
        const redirect_url = this.data.result?.redirect_url;
        const feedback_id = this.data.result?.feedback_id;

        // Build questions HTML only
        let questionsHtml = '';
        if (questions.length > 0) {
            questions.forEach(function(q, index) {
                questionsHtml += `
                    <tr class="s_feedback_question_row">
                        <td class="text-center antique-subtitle">
                            ${q.name}
                        </td>
                        <td class="s_feedback_rating_cell">
                            <label class="s_feedback_radio_label">
                                <input type="radio" name="${q.id}" value="1"/>
                                <span class="s_feedback_radio_custom"></span>
                                <span class="s_feedback_radio_text">★★★</span>
                            </label>
                        </td>
                        <td class="s_feedback_rating_cell">
                            <label class="s_feedback_radio_label">
                                <input type="radio" name="${q.id}" value="2"/>
                                <span class="s_feedback_radio_custom"></span>
                                <span class="s_feedback_radio_text">★★</span>
                            </label>
                        </td>
                        <td class="s_feedback_rating_cell">
                            <label class="s_feedback_radio_label">
                                <input type="radio" name="${q.id}" value="3"/>
                                <span class="s_feedback_radio_custom"></span>
                                <span class="s_feedback_radio_text">★</span>
                            </label>
                        </td>
                    </tr>
                `;
            });
        } else {
            questionsHtml = `
                <tr>
                    <td colspan="4" class="text-center p-4 text-muted antique-subtitle">
                        <em>No feedback questions configured for this website.</em>
                    </td>
                </tr>
            `;
        }

        // Update only the questions tbody - rest of template stays static
        const $tbody = this.$el.find('#s_feedback_questions_body');
        if ($tbody.length) {
            $tbody.html(questionsHtml);
            console.log('[FeedbackSnippet] Questions updated successfully');
        } else {
            console.error('[FeedbackSnippet] Could not find #s_feedback_questions_body element');
        }

        // Update hidden company/website fields if they exist
        if (currentCompany) {
            this.$el.find('input[name="company_id"]').val(currentCompany.id);
        }
        if (currentWebsite) {
            this.$el.find('input[name="website_id"]').val(currentWebsite.id);
        }
        if (feedback_id) {
            this.$el.find('input[name="feedback_id"]').val(feedback_id.id);
        }
        if (redirect_url) {
            this.$el.find('input[name="redirect_url"]').val(redirect_url);
        }
    },

    /**
     * Handle form submission - validate that all questions are answered
     * @private
     * @param {Event} ev - The submit event
     */
    _onFormSubmit: function (ev) {
        const questions = this.data?.result?.questions || [];
        let hasUnanswered = false;
        let firstUnansweredRow = null;

        console.log('[FeedbackSnippet] Form submit - validating', questions.length, 'questions');

        // Clear previous error highlights
        this.$el.find('.s_feedback_question_row').removeClass('s_feedback_unanswered');
        this.$el.find('.s_feedback_validation_error').remove();

        // Check each question
        questions.forEach(function (q) {
            const radioName = String(q.id);
            const $radio = this.$el.find('input[name="' + radioName + '"]');
            const isAnswered = $radio.filter(':checked').length > 0;
            const $row = $radio.closest('.s_feedback_question_row');

            console.log('[FeedbackSnippet] Question', q.id, '- answered:', isAnswered, '- row found:', $row.length);

            if (!isAnswered) {
                hasUnanswered = true;
                $row.addClass('s_feedback_unanswered');
                console.log('[FeedbackSnippet] Added s_feedback_unanswered class to row for question', q.id);
                if (!firstUnansweredRow) {
                    firstUnansweredRow = $row;
                }
            }
        }.bind(this));

        if (hasUnanswered) {
            // Prevent form submission
            ev.preventDefault();
            ev.stopPropagation();

            // Scroll to first unanswered question
            if (firstUnansweredRow && firstUnansweredRow.length) {
                firstUnansweredRow[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
            }

            // Show error message with icon
            const $errorMsg = $('<div class="s_feedback_validation_error"><span>⚠️</span> Please answer all questions before submitting.</div>');
            this.$el.find('form').prepend($errorMsg);

            // Auto-remove highlight when question is answered
            this.$el.find('input[type="radio"]').on('change.feedback_validation', function () {
                const $row = $(this).closest('.s_feedback_question_row');
                const radioName = $(this).attr('name');
                const isAnswered = $('input[name="' + radioName + '"]:checked').length > 0;
                if (isAnswered) {
                    $row.removeClass('s_feedback_unanswered');
                }
            });

            console.log('[FeedbackSnippet] Validation failed - some questions unanswered');
            return false;
        }

        // Remove the change handlers if validation passes
        this.$el.find('input[type="radio"]').off('change.feedback_validation');

        console.log('[FeedbackSnippet] Form validation passed');
    },
});

publicWidget.registry.FeedbackSnippet = FeedbackSnippet;

export default FeedbackSnippet;
