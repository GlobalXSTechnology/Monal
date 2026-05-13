/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";
import options from "@web_editor/js/editor/snippets.options";

options.registry.FeedbackSnippet = options.Class.extend({
    /**
     * @constructor
     */
    init() {
        this._super(...arguments);
        this.containerSelector = '.s_feedback_snippets_options';
        console.log('FeedbackSnippet initialized');
    },
    
    async start() {
        console.log('FeedbackSnippet start method called');
        await this.loadFeedbackData();
        return this._super(...arguments);
    },
    
    async loadFeedbackData() {
        console.log('Loading feedback data...');
        try {
            const response = await rpc("/website/snippet/feedback/render", {
                'template': 'customer_feedback_form_snippet',
            });
            
            console.log('RPC response:', response);
            
            if (response.error) {
                console.error('Error rendering feedback template:', response.error);
                return;
            }
            
            if (this.$target && response.content) {
                console.log('Updating snippet content');
                this.$target.html(response.content);
            } else {
                console.error('No target element or content found');
            }
            
        } catch (error) {
            console.error('Error loading feedback data:', error);
        }
    },
    
    // Container Background Color
    setContainerBackgroundColor(previewMode, widgetValue, params) {
        this.$target.find('.antique-book-container').css('background-color', widgetValue);
    },
    
    // Table Header Background Color  
    setTableHeaderColor(previewMode, widgetValue, params) {
        this.$target.find('.antique-table th').css('background-color', widgetValue);
    },
    
    // Table Header Text Color
    setTableHeaderTextColor(previewMode, widgetValue, params) {
        this.$target.find('.antique-table th').css('color', widgetValue);
    },
    
    // Button Background Color
    setButtonBackgroundColor(previewMode, widgetValue, params) {
        this.$target.find('.antique-button').css('background-color', widgetValue);
    },
    
    // Button Text Color
    setButtonTextColor(previewMode, widgetValue, params) {
        this.$target.find('.antique-button').css('color', widgetValue);
    },
    
    // Title Text Color
    setTitleColor(previewMode, widgetValue, params) {
        this.$target.find('.antique-title').css('color', widgetValue);
    },
    
    // Subtitle Text Color
    setSubtitleColor(previewMode, widgetValue, params) {
        this.$target.find('.antique-subtitle').css('color', widgetValue);
    },
    
    // Override the onClone method
    async onClone() {
        console.log('FeedbackSnippet cloned');
        await this.loadFeedbackData();
    },
    
    // Override the onMove method
    async onMove() {
        console.log('FeedbackSnippet moved');
        await this.loadFeedbackData();
    },
});

// Thank You Snippet Options - Extends functionality for thank you page
options.registry.ThankYouSnippet = options.Class.extend({
    /**
     * @constructor
     */
    init() {
        this._super(...arguments);
        this.containerSelector = '.s_thank_you_snippet_options';
        console.log('ThankYouSnippet initialized');
    },
    
    async start() {
        console.log('ThankYouSnippet start method called');
        return this._super(...arguments);
    },
    
    // Card Background Color
    setCardBackgroundColor(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_card').css('background', widgetValue);
    },
    
    // Card Background Image
    setCardBackgroundImage(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_card').css('background-image', `url(${widgetValue})`);
    },
    
    // Success Icon Background
    setSuccessIconBackground(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_success_icon').css('background', widgetValue);
    },
    
    // Success Icon Color
    setSuccessIconColor(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_success_icon svg').css('color', widgetValue);
    },
    
    // Main Title Color
    setMainTitleColor(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_main_title').css('color', widgetValue);
    },
    
    // Subtitle Color
    setThankYouSubtitleColor(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_subtitle').css('color', widgetValue);
    },
    
    // Message Box Background
    setMessageBoxBackground(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_message').css('background', widgetValue);
    },
    
    // Message Box Text Color
    setMessageBoxTextColor(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_message').css('color', widgetValue);
    },
    
    // Message Box Border Color
    setMessageBoxBorderColor(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_message').css('border-color', widgetValue);
    },
    
    // Customer Name Color
    setCustomerNameColor(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_customer_name').css('color', widgetValue);
    },
    
    // Divider Color
    setDividerColor(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_divider').css('background', widgetValue);
    },
    
    // Button Background
    setThankYouButtonBackground(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_button').css('background', widgetValue);
    },
    
    // Button Text Color
    setThankYouButtonTextColor(previewMode, widgetValue, params) {
        this.$target.find('.s_thank_you_button').css('color', widgetValue);
    },
    
    // Override the onClone method
    async onClone() {
        console.log('ThankYouSnippet cloned');
    },
    
    // Override the onMove method
    async onMove() {
        console.log('ThankYouSnippet moved');
    },
});

return {
    FeedbackSnippet: options.registry.FeedbackSnippet,
    ThankYouSnippet: options.registry.ThankYouSnippet,
};
