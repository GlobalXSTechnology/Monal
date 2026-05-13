# -*- coding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2018-BroadTech IT Solutions (<http://www.broadtech-innovations.com/>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo import tools
import string


class BtAsset(models.Model):
    _name = "bt.asset"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Asset"

    name = fields.Char(string='Name', required=True)
    purchase_date = fields.Date(string='Purchase Date', track_visibility='always')
    purchase_value = fields.Float(string='Purchase Value', track_visibility='always')
    asset_code = fields.Char(string='Asset Code')
    is_created = fields.Boolean('Created', copy=False)
    # asset = fields.Char('bt.con')
    current_loc_id = fields.Many2one(
        'stock.location', "Asset Location",
        company_dependent=True, domain=[('usage', 'like', 'asset')],
        help="This location will be used as the destination location for installed parts during asset life.")
    model_name = fields.Char(string='Model Name')
    serial_no = fields.Char(string='Serial No', track_visibility='always')
    manufacturer = fields.Char(string='Manufacturer')
    warranty_start = fields.Date(string='Warranty Start')
    warranty_end = fields.Date(string='Warranty End')

    note = fields.Text(string='Internal Notes')
    state = fields.Selection([
        ('active', 'Active'),
        ('scrapped', 'Scrapped')], string='State', track_visibility='onchange', default='active', copy=False)
    image = fields.Binary("Image", attachment=True,
                          help="This field holds the image used as image for the asset, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized image", attachment=True,
                                 help="Medium-sized image of the asset. It is automatically "
                                      "resized as a 128x128px image, with aspect ratio preserved, "
                                      "only when the image exceeds one of those sizes. Use this"
                                      "field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized image", attachment=True,
                                help="Small-sized image of the asset. It is automatically "
                                     "resized as a 64x64px image, with aspect ratio preserved. "
                                     "Use this field anywhere a small image is required.")

    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        vals.update({'is_created': True})
        lot = super(BtAsset, self).create(vals)
        lot.message_post(body=_("Asset %s created with asset code %s") % (lot.name, lot.asset_code))
        return lot

    def write(self, vals):
        tools.image_resize_images(vals)
        lot = super(BtAsset, self).write(vals)
        return lot
    # vim:expandtab:smartindent:tabstop=2:softtabstop=2:shiftwidth=2:


class fetch_inheritence(models.Model):
    _inherit = "account.asset"

    current_location = fields.Many2one(
        'stock.location', "Asset Location",
        company_dependent=True, required=False, widget="selection",domain="[('usage', '=', 'asset')]")

    asset_code = fields.Char(string='Order Reference', required=True,
                             copy=False, readonly=True, index=True, default=lambda self: _('New'))
    model_name = fields.Many2one('bt.con', string='Asset Model')
    manufacturer = fields.Char(string='Manufacturer')
    warranty_start = fields.Date(string='Warranty Start')
    warranty_end = fields.Date(string='Warranty End')
    note = fields.Text(string='Internal Notes')
    serial_no = fields.Char(string='Serial No', track_visibility='always')
    current_loc_id = fields.Many2one(
        'stock.location', "Asset Location",
        company_dependent=True, domain="[('usage', '=', 'asset')]",
        help="This location will be used as the destination location for installed parts during asset life.",required=False)
    asset_loc_id = fields.Many2one('hr.employee', string="User Name")
    asset_code = fields.Char(string="Asset Tag No")


    # fields add and rename
    original_value = fields.Monetary(string="Original cost", compute='_compute_value', store=True, readonly=False)
    current_cost = fields.Monetary(string="Current cost",  store=True, readonly=False)
    asset_group_id = fields.Many2one('account.asset.group', string='Asset Major Category', tracking=True, index=True)
    asset_minor_cat = fields.Many2one('asset.minor.category',string='Asset Minor Category')
    accumulated_depreciation = fields.Monetary(string='Accumulated Depreciation')
    salvage_value = fields.Monetary(string='Residual / Scrap Value',
                                    help="It is the amount you plan to have that you cannot depreciate.",
                                    compute="_compute_salvage_value",
                                    store=True, readonly=False)
    condition = fields.Selection([
        ('new', 'New'),
        ('used', 'Used')
    ], string="Condition")
    is_serviceable = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Serviceable", default='yes')
    hr_no = fields.Char(related='asset_loc_id.barcode',string="Employee_id")
    designation = fields.Many2one('hr.job',string="Designation")
    user_department = fields.Many2one('hr.department', string="User Department")
    asset_make = fields.Char(string="Assets Make")

    # asset model fields

    it_check = fields.Boolean(compute="_compute_asset_checks", store=True)
    storage = fields.Char(string="Storage")
    ram = fields.Char(string="RAM")
    display_size = fields.Char(string="Display")

    # Vehicle Fields
    registration_no = fields.Char(string="Registration No")
    engine_no = fields.Char(string="Engine No")
    chassis_no = fields.Char(string="Chassis No")
    vehicle_check = fields.Boolean(compute="_compute_asset_checks", store=True)

    # Weapon Fields
    body_no = fields.Char(string="Body No")
    weapon_check = fields.Boolean(compute="_compute_asset_checks", store=True)


    asset_type_id = fields.Many2one(
        'asset.type.category',
        string="Type",
    )

    @api.depends('model_id.asset_type_id.name')
    def _compute_asset_checks(self):
        for record in self:
            record.it_check = False
            record.vehicle_check = False
            record.weapon_check = False

            val = record.model_id.asset_type_id.name or ''

            if 'IT Equipment' in val:
                print('it before')
                record.it_check = True
                print('it after')
            elif 'Vehicle' in val:
                record.vehicle_check = True
            elif 'Weapon' in val:
                record.weapon_check = True



    @api.onchange('asset_loc_id')
    def _onchange_asset_loc_id(self):
        """ Use the exact field names defined above """
        if self.asset_loc_id:
            # Map the employee's data to your custom fields
            self.user_department = self.asset_loc_id.department_id
            self.designation = self.asset_loc_id.job_id
        else:
            self.user_department = False
            self.designation = False




class AssetMinorCategory(models.Model):
    _name = 'asset.minor.category'
    _description = 'Asset Minor Category'
    _order = 'name'

    name = fields.Char(string="Minor Category Name", required=True)


class AsseTypeCategory(models.Model):
    _name = 'asset.type.category'
    _description = 'Asset type Category'
    _order = 'name'

    name = fields.Char(string="Type Category Name", required=True)
