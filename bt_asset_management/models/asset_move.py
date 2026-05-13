# -*- coding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2018 BroadTech IT Solutions Pvt Ltd 
#    (<http://broadtech-innovations.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
    
from odoo import api, fields, models, _
import string
from odoo.exceptions import ValidationError
import copy


class BtAssetMove(models.Model):
    _name = "bt.asset.move"
    _description = "Asset Move"

    name = fields.Char(string='Name', default="New", copy=False)
    available_assets_ids = fields.Many2many('account.asset', string="Available Assets", compute="_compute_available_assets", store=True)
    @api.depends('from_loc_id')
    def _compute_available_assets(self):
        for record in self:
            if record.from_loc_id:
                record.available_assets_ids = self.env['account.asset'].search([('current_location', '=', record.from_loc_id.id)]).ids
            else:
                record.available_assets_ids = False

    from_loc_id = fields.Many2one(
        'stock.location', "From Location",
        widget="selection", store=True, domain="[('usage', '=', 'asset')]",required=True)
    domain = [('usage', 'like', 'asset')]
    asset_id = fields.Many2one('account.asset', string='Asset', required=False, copy=False, widget="selection")
    to_loc_id = fields.Many2one(
        'stock.location', "To Location",
        required=True, widget="selection", store=True, domain="[('usage', '=', 'asset')]")
    # domain = [('usage', 'like', 'asset')]
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),], string='State', track_visibility='onchange', default='draft', copy=False)
    asset_loc_id = fields.Many2one('hr.employee', string="Assigned to")
    date_move = fields.Date("Date", required=True)

    # serviceable = fields.Boolean("SA")
    # unserviceable = fields.Boolean("US")
    # repairable = fields.Boolean("Ra")
    #
    # @api.onchange('from_loc_id')
    # def _onchange_from_loc_id(self):
    #     self.asset_id = False  # Reset asset selection when changing location
    #     if self.from_loc_id:
    #         return {
    #             'domain': {
    #                 'asset_id': [('current_location', '=', self.from_loc_id.id)]
    #             }
    #         }
    #     return {'domain': {'asset_id': []}}
    
    # @api.onchange('from_loc_id')
    # def _onchange_from_loc_id(self):
    #     if self.from_loc_id:
    #         assets = self.env['account.asset'].search([('current_location', '=', self.from_loc_id.id)])
    #         return {'domain': {'asset_id': [('id', 'in', assets.ids)]}}
    #     else:
    #         return {'domain': {'asset_id': []}}
    
    # @api.onchange('asset_id')
    # def set_fild_name(self):
    #     self.from_loc_id = self.asset_id.current_location.id
    #     self.asset_loc_id = self.asset_id.asset_loc_id.id

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('bt.asset.move') or 'New'
        result = super(BtAssetMove, self).create(vals)
        # if vals.get('from_loc_id', False) or vals.get('to_loc_id', False):
        #     if result.from_loc_id == result.to_loc_id:
        #         raise ValidationError(_("From location and to location must be different."))
        # if vals.get('asset_id',False):
        #     if result.asset_id.current_loc_id != result.from_loc_id:
        #         raise ValidationError(_("Current location and from location must be same while creating asset."))
        return result

    def write(self, vals):
        result = super(BtAssetMove, self).write(vals)
        # if vals.get('from_loc_id', False) or vals.get('to_loc_id', False):
        #     for move in self:
        #         if move.from_loc_id == move.to_loc_id:
        #             raise ValidationError(_("From location and to location must be different."))
        if vals.get('asset_id', False):
            for asset_obj in self:
                # if asset_obj.asset_id.current_loc_id != asset_obj.from_loc_id:
                raise ValidationError(_("Current location and from location must be same while creating asset."))
        return result

    def action_cancel(self):
        for move in self:
            move.state = 'cancel'
        return True
        
    
    def action_move(self):

        for move in self:
            move.asset_id.current_location = move.to_loc_id and move.to_loc_id.id or False
            move.asset_id.asset_loc_id = move.asset_loc_id and move.asset_loc_id.id or False
            move.state = 'done'
            move.asset_id.check = 'True'
            # move.asset_id.status = 'issue'

        return True


# vim:expandtab:smartindent:tabstop=2:softtabstop=2:shiftwidth=2:


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    check = fields.Boolean(string='Check Field')
