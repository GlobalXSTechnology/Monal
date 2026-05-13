/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { AttachmentUploadService } from "@mail/core/common/attachment_upload_service";

patch(Chatter.prototype, {
    async onUploaded(data) {
        await this.attachmentUploader.uploadData(data);
        if (this.props.hasParentReloadOnAttachmentsChanged) {
            this.reloadParentView();
        }
        this.state.isAttachmentBoxOpened = true;
        if (this.rootRef?.el) {
            this.rootRef.el.scrollTop = 0;
        }
        if (this.state.thread) {
            this.state.thread.scrollTop = "bottom";
        }
    },
});

patch(AttachmentUploadService.prototype, {
    _cleanupUploading(tmpId) {
        this.abortByAttachmentId.delete(tmpId);
        this.deferredByAttachmentId.delete(tmpId);
        this.uploadingAttachmentIds.delete(tmpId);
        this.targetsByTmpId.delete(tmpId);
        this.store.Attachment.get(tmpId)?.remove();
        this.uploadingCloudFiles?.delete(tmpId);
    },
});
