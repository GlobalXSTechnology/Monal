/** @odoo-module **/

import { registry } from "@web/core/registry";

import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { useAddInlineRecord } from "@web/views/fields/relational_utils";

export class PaymentTermLineIdsOne2Many extends X2ManyField {
    get pagerProps() {
        const list = this.list;
        console.log('---------------444----------',list.limit)
        let list_limit = list.limit == 40 ? 70 : list.limit;
        console.log(list_limit,'---------------444----------',list.limit)


        return {
            offset: list.offset,
            limit: list_limit,
//            limit: list.limit,
            total: list.count,
            onUpdate: async ({ offset, limit }) => {
                const initialLimit = list_limit;
                const leaved = await list.leaveEditMode();
                if (leaved) {
                    if (initialLimit === limit && initialLimit === list_limit + 1) {
                        // Unselecting the edited record might have abandonned it. If the page
                        // size was reached before that record was created, the limit was temporarily
                        // increased to keep that new record in the current page, and abandonning it
                        // decreased this limit back to it's initial value, so we keep this into
                        // account in the offset/limit update we're about to do.
                        offset -= 1;
                        limit -= 1;
                    }
                    await list.load({ limit, offset });
                    this.render();
                }
            },
            withAccessKey: false,
        };
    }
}

export const limit_70 = {
    ...x2ManyField,
    component: PaymentTermLineIdsOne2Many,
}

registry.category("fields").add("limit_70", limit_70);
