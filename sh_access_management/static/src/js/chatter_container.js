/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";
import { user } from "@web/core/user";

patch(Chatter.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.modelRestrictions = {};
        this.currentRestrictions = {};
        this.globalRestrictions = {};

        onWillStart(async () => {
            try {
                const { model_restrictions } = await this.orm.call(
                    "sh.hide.chatter",
                    "sh_checkhide_chatter",
                    [{ user_id: user.userId }]
                );
                this.modelRestrictions = model_restrictions || {};
                this.globalRestrictions = this.modelRestrictions["global"] || {};
                this.currentRestrictions = this.modelRestrictions[this.props.threadModel] || {};

            } catch (error) {
                console.error("\n\n Error fetching chatter restrictions:", error);
            }
        });
    },
    isSHChatterHidden() {
        // Check if global hide or model-specific hide applies
        return this.globalRestrictions.sh_global_hide_full_chatter || this.currentRestrictions.hide_full_chatter || false;
    },
});
