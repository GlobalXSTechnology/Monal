odoo.define('sg_attendance_adjustment_request.attendance_adjustment', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var time = require('web.time');

publicWidget.registry.EmpPortalTimeOff = publicWidget.Widget.extend({
    selector: '#wrapwrap:has(.new_adjustment_form, .edit_adjustment_form)',
    events: {
        'click .new_attendance_confirm': '_onNewConfirm',
        'click .edit_adjustment_confirm': '_onEditAdjustmentConfirm',
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {jQuery} $btn
     * @param {function} callback
     * @returns {Promise}
     */
    _buttonExec: function ($btn, callback) {
        // TODO remove once the automatic system which does this lands in master
        $btn.prop('disabled', true);
        return callback.call(this).guardedCatch(function () {
            $btn.prop('disabled', false);
        });
    },
    /**
     * @private
     * @returns {Promise}
     */
    _create_adjustment: function () {
    	return this._rpc({
            model: 'attendance.adjustment',
            method: 'create_adjustment_portal',
            args: [{
                description: $('.new_adjustment_form .name').val(),
                check_in: $('.new_adjustment_form .emp_check_in').val(),
                check_out: $('.new_adjustment_form .emp_check_out').val(),
            }],
        }).then(function (response) {
            if (response.errors) {
                $('#new-opp-dialog .alert').remove();
                $('#new-opp-dialog div:first').prepend('<div class="alert alert-danger">' + response.errors + '</div>');
                return Promise.reject(response);
            } else {
                window.location = '/employee/attendance/' + response.id;
            }
        });
    },
    /**
     * @private
     * @returns {Promise}
     */
    _editAdjustmentRequest: function () {
        return this._rpc({
            model: 'attendance.adjustment',
            method: 'update_attendance_portal',
            args: [[parseInt($('.edit_adjustment_form .adjust_id').val())], {
            	adjustID: parseInt($('.edit_adjustment_form .adjust_id').val()),
            	description: $('.edit_adjustment_form .name').val(),
                check_in: $('.edit_adjustment_form .emp_check_in').val(),
                check_out: $('.edit_adjustment_form .emp_check_out').val(),
            }],
        }).then(function () {
            window.location.reload();
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} ev
     */
    _onNewConfirm: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this._buttonExec($(ev.currentTarget), this._create_adjustment);
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onEditAdjustmentConfirm: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this._buttonExec($(ev.currentTarget), this._editAdjustmentRequest);
    },

//    _parse_date: function (value) {
//        console.log(value);
//        var date = moment(value, "YYYY-MM-DD", true);
//        if (date.isValid()) {
//            return time.date_to_str(date.toDate());
//        }
//        else {
//            return false;
//        }
//    },
});
});
