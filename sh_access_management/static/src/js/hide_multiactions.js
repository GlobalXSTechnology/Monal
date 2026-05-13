/* @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { FormController } from "@web/views/form/form_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { ExportAll } from "@web/views/list/export_all/export_all";
import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { onWillStart, onMounted, useState } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { session } from '@web/session';
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";

import {
    deleteConfirmationMessage,
    ConfirmationDialog,
    
} from "@web/core/confirmation_dialog/confirmation_dialog";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.state = useState({
            rpc_result: null,
            group_show_create: true,
            group_show_export: true,
            group_show_delete: true,
            group_show_duplicate: true,
            group_show_archive: true,
        });
        this.orm = useService('orm')
        // this.user = useService("user");
        var self = this;
        onWillStart(async () => {
            let uid = Array.isArray(session.user_id) ? session.user_id[0] : user.userId
            let model_dic = await this.orm.call("sh.access.model", 'check_crud_operation', [{ user_id: uid }], {});
            this.state.rpc_result = model_dic
        })
        onMounted(() => this.onMounted());

    },

    async onMounted() {
        var self = this;
        let count = 0;
        if (Object.keys(this.state.rpc_result).length) {
            for (const [index, value] of Object.entries(this.state.rpc_result)) {
                if (count == 0) {
                    if (index == self.props.resModel) {
                        count = count + 1;
                        self.state.group_show_create = value["hide_create"];
                        self.state.group_show_export = value["hide_export"];
                        self.state.group_show_delete = value["hide_delete"];
                        self.state.group_show_duplicate = value["hide_duplicate"];
                        self.state.group_show_archive = value["hide_archieve"];
                    } else {
                        self.state.group_show_create = true;
                        self.state.group_show_edit = true;
                    }
                }
            };
        }
    },


    getStaticActionMenuItems() {
        const list = this.model.root;
        const isM2MGrouped = list.groupBy.some((groupBy) => {
            const fieldName = groupBy.split(":")[0];
            return list.fields[fieldName].type === "many2many";
        });
        return {
            export: {
                isAvailable: () => this.isExportEnable && this.state.group_show_export,
                sequence: 10,
                icon: "fa fa-upload",
                description: _t("Export"),
                callback: () => this.onExportData(),
            },
            archive: {
                isAvailable: () => this.archiveEnabled && !isM2MGrouped && this.state.group_show_archive,
                sequence: 20,
                icon: "oi oi-archive",
                description: _t("Archive"),
                callback: () => {
                    this.dialogService.add(ConfirmationDialog, this.archiveDialogProps);
                },
            },
            unarchive: {
                isAvailable: () => this.archiveEnabled && !isM2MGrouped,
                sequence: 30,
                icon: "oi oi-unarchive",
                description: _t("Unarchive"),
                callback: () => this.toggleArchiveState(false),
            },
            duplicate: {
                isAvailable: () => this.activeActions.duplicate && !isM2MGrouped && this.state.group_show_duplicate,
                sequence: 35,
                icon: "fa fa-clone",
                description: _t("Duplicate"),
                callback: () => this.duplicateRecords(),
            },
            delete: {
                isAvailable: () => this.activeActions.delete && !isM2MGrouped && this.state.group_show_delete,
                sequence: 40,
                icon: "fa fa-trash-o",
                description: _t("Delete"),
                callback: () => this.onDeleteSelectedRecords(),
            },
        };
    }
});


patch(FormController.prototype, {
    setup() {
        super.setup();
        this.state = useState({
            rpc_result: null,
            group_show_create: true,
            group_show_delete: true,
            group_show_duplicate: true,
            group_show_archive: true,
        });
        this.orm = useService('orm')
        // this.user = useService("user");
        var self = this;
        onWillStart(async () => {
            let uid = Array.isArray(session.user_id) ? session.user_id[0] : user.userId
            let model_dic = await this.orm.call("sh.access.model", 'check_crud_operation', [{ user_id: uid }], {});
            this.state.rpc_result = model_dic
        })
        onMounted(() => this.onMounted());

    },

    async onMounted() {
        var self = this;
        let count = 0;
        if (Object.keys(this.state.rpc_result).length) {
            for (const [index, value] of Object.entries(this.state.rpc_result)) {
                if (count == 0) {
                    if (index == self.props.resModel) {
                        count = count + 1;
                        self.state.group_show_create = value["hide_create"];
                        self.state.group_show_delete = value["hide_delete"];
                        self.state.group_show_duplicate = value["hide_duplicate"];
                        self.state.group_show_archive = value["hide_archieve"];
                    } else {
                        self.state.group_show_create = true;
                        self.state.group_show_edit = true;
                    }
                }
            };
        }
    },


    getStaticActionMenuItems() {
        const { activeActions } = this.archInfo;
        return {
            archive: {
                isAvailable: () => this.archiveEnabled && this.model.root.isActive && this.state.group_show_archive,
                sequence: 10,
                description: _t("Archive"),
                icon: "oi oi-archive",
                callback: () => {
                    this.dialogService.add(ConfirmationDialog, this.archiveDialogProps);
                },
            },
            unarchive: {
                isAvailable: () => this.archiveEnabled && !this.model.root.isActive,
                sequence: 20,
                icon: "oi oi-unarchive",
                description: _t("Unarchive"),
                callback: () => this.model.root.unarchive(),
            },
            duplicate: {
                isAvailable: () => activeActions.create && activeActions.duplicate && this.state.group_show_duplicate,
                sequence: 30,
                icon: "fa fa-clone",
                description: _t("Duplicate"),
                callback: () => this.duplicateRecord(),
            },
            delete: {
                isAvailable: () => activeActions.delete && !this.model.root.isNew && this.state.group_show_delete,
                sequence: 40,
                icon: "fa fa-trash-o",
                description: _t("Delete"),
                callback: () => this.deleteRecord(),
                skipSave: true,
            },
        };
    }
});


patch(KanbanController.prototype, {
    setup() {
        super.setup();
        this.state = useState({
            rpc_result: null,
            group_show_create: true,
        });
        this.orm = useService('orm')
        // this.user = useService("user");
        var self = this;
        onWillStart(async () => {
            let model_dic = await this.orm.call("sh.access.model", 'check_crud_operation', [{ user_id: session.uid }], {});
            this.state.rpc_result = model_dic
        })
        onMounted(() => this.onMounted());

    },

    async onMounted() {
        var self = this;
        let count = 0;
        if (Object.keys(this.state.rpc_result).length) {
            for (const [index, value] of Object.entries(this.state.rpc_result)) {
                if (count == 0) {
                    if (index == self.props.resModel) {
                        count = count + 1;
                        self.state.group_show_create = value["hide_create"];
                    } else {
                        self.state.group_show_create = true;
                    }
                }
            };
        }
    },


    async createRecord() {
        const { onCreate } = this.props.archInfo;
        const { root } = this.model;
        if (this.state.group_show_create) {
            if (this.canQuickCreate && onCreate === "quick_create") {
                const firstGroup = root.groups[0];
                if (firstGroup.isFolded) {
                    await firstGroup.toggle();
                }
                this.quickCreateState.groupId = firstGroup.id;
            } else if (onCreate && onCreate !== "quick_create") {
                const options = {
                    additionalContext: root.context,
                    onClose: async () => {
                        await root.load();
                        this.model.useSampleModel = false;
                        this.render(true); // FIXME WOWL reactivity
                    },
                };
                await this.actionService.doAction(onCreate, options);
            } else {
                await this.props.createRecord();
            }
        }
    }
});


patch(ExportAll.prototype, {
    setup() {
        super.setup();
        this.state = useState({
            rpc_result: null,
            group_show_export: true,
        });
        this.orm = useService('orm')
        // this.user = useService("user");
        var self = this;
        onWillStart(async () => {
            let model_dic = await this.orm.call("sh.access.model", 'check_crud_operation', [{ user_id: session.uid }], {});
            this.state.rpc_result = model_dic
        })
        onMounted(() => this.onMounted());

    },

    async onMounted() {
        var self = this;
        let count = 0;
        // ============================================================
        //      ---- GET THE CURRENT MODEL NAME FROM URL ------
        // ============================================================
        const fragment = window.location.hash.substring(1); // remove the #
        const params = new URLSearchParams(fragment);
        const modelParam = params.get('model');
        // ============================================================

        if (Object.keys(this.state.rpc_result).length) {
            for (const [index, value] of Object.entries(this.state.rpc_result)) {
                if (count == 0) {
                    if (index == modelParam) {
                        count = count + 1;
                        self.state.group_show_export = value["hide_export"];
                    } else {
                        self.state.group_show_export = true;
                    }
                }
            };
        }
    },
});
