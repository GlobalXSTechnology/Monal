from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import Markup


class EmployeeAllowanceUpdate(models.Model):
    _name = 'employee.allowance.update'
    _description = 'Employee Allowance Update'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Reference',
        required=True,
        default=lambda self: _('New'),
        copy=False, tracking=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('created', 'Created'),
        ('approved', 'Approved')
    ], string='Status', default='draft', tracking=True)

    select_type = fields.Selection([
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('employee', 'By Employee')
    ], string='Select Type', required=True, default='company', tracking=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True, tracking=True,
        default=lambda self: self.env.company
    )
    department_ids = fields.Many2many('hr.department', string='Departments', tracking=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees', tracking=True)

    # Computed fields to show counts
    total_employees = fields.Integer(
        string='Total Selected Employees',
        compute='_compute_employee_counts', tracking=True
    )
    employees_with_active_contracts = fields.Integer(
        string='Employees with Active Contracts',
        compute='_compute_employee_counts', tracking=True
    )

    # Single-line Allowance Fields
    resident_allowance = fields.Float(string='Resident Allowance', tracking=True)
    realocation = fields.Float(string='Relocation', tracking=True)
    bike = fields.Float(string='Bike', tracking=True)
    car_maintence = fields.Float(string='Car Maintenance', tracking=True)
    house = fields.Float(string='House', tracking=True)
    car_allowance = fields.Float(string='Car Allowance', tracking=True)
    mobile_allowance = fields.Float(string='Mobile Allowance', tracking=True)
    miscellaneous_allowance = fields.Float(string='Miscellaneous Allowance', tracking=True)
    fuel_allowance_cash_1 = fields.Float(string='Fuel Allowance', tracking=True)
    allow_food_allowance = fields.Float(string='Allow Food Allowance', tracking=True)
    food_allowance = fields.Float(string='Food Allowance', tracking=True)
    gun_allowance = fields.Float(string='Gun Allowance', tracking=True)
    hill = fields.Float(string='Hill', tracking=True)

    # FIELD_MAP for hr.contract model
    FIELD_MAP = {
        'resident_allowance': 'x_studio_resident_allowance',
        'realocation': 'x_studio_realocation',
        'bike': 'x_studio_bike',
        'car_maintence': 'x_studio_car_maintence',
        'house': 'x_studio_house',
        'car_allowance': 'x_studio_car_allowance',
        'mobile_allowance': 'x_studio_mobile_allowance',
        'miscellaneous_allowance': 'x_studio_miscellaneous_allowance',
        'fuel_allowance_cash_1': 'x_studio_fuel_allowance_cash_1',
        # 'allow_food_allowance': 'x_studio_allow_food_allowance',
        # 'food_allowance': 'x_studio_food_allowance',
        'gun_allowance': 'x_studio_gun_allowance',
        'hill': 'x_studio_hill',
    }

    # Human readable field names for messages
    FIELD_LABELS = {
        'resident_allowance': 'Resident Allowance',
        'realocation': 'Relocation',
        'bike': 'Bike',
        'car_maintence': 'Car Maintenance',
        'house': 'House',
        'car_allowance': 'Car Allowance',
        'mobile_allowance': 'Mobile Allowance',
        'miscellaneous_allowance': 'Miscellaneous Allowance',
        'fuel_allowance_cash_1': 'Fuel Allowance',
        # 'allow_food_allowance': 'Allow Food Allowance',
        # 'food_allowance': 'Food Allowance',
        'gun_allowance': 'Gun Allowance',
        'hill': 'Hill',
    }

    # Fields to store original values for cancellation
    original_contract_data = fields.Text(string='Original Contract Data', copy=False, tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('employee.allowance.update') or _('New')
        return super().create(vals)

    @api.depends('select_type', 'company_id', 'department_ids', 'employee_ids')
    def _compute_employee_counts(self):
        """Compute total employees and those with active contracts."""
        for record in self:
            employees = record._get_target_employees()
            record.total_employees = len(employees)

            # Get employees with active contracts
            active_contract_employees = self.env['hr.employee'].search([
                ('id', 'in', employees.ids),
                ('contract_id.state', '=', 'open')
            ])
            record.employees_with_active_contracts = len(active_contract_employees)

    def _get_target_employees(self):
        """Return employee records based on selection type."""
        if self.select_type == 'employee' and self.employee_ids:
            return self.employee_ids
        elif self.select_type == 'department' and self.department_ids:
            return self.env['hr.employee'].search([
                ('department_id', 'in', self.department_ids.ids)
            ])
        elif self.select_type == 'company' and self.company_id:
            return self.env['hr.employee'].search([
                ('company_id', '=', self.company_id.id)
            ])
        return self.env['hr.employee']

    def _get_employees_with_active_contracts(self, employees):
        """Filter only employees who have active contracts."""
        return employees.filtered(lambda emp: emp.contract_id and emp.contract_id.state == 'open')

    def _get_active_contracts(self, employees):
        """Get active contracts for selected employees."""
        employees_with_contracts = self._get_employees_with_active_contracts(employees)
        return self.env['hr.contract'].search([
            ('employee_id', 'in', employees_with_contracts.ids),
            ('state', '=', 'open')
        ])

    def _save_original_contract_data(self, contracts):
        """Save original contract data for cancellation support."""
        original_data = []
        for contract in contracts:
            contract_data = {'contract_id': contract.id, 'employee_name': contract.employee_id.name}
            for field, contract_field in self.FIELD_MAP.items():
                contract_data[field] = getattr(contract, contract_field, 0.0)
            original_data.append(contract_data)

        self.original_contract_data = str(original_data)

    def _restore_original_contract_data(self):
        """Restore original contract data when cancelling."""
        if not self.original_contract_data:
            return

        try:
            import ast
            original_data = ast.literal_eval(self.original_contract_data)

            for data in original_data:
                contract = self.env['hr.contract'].browse(data['contract_id'])
                if contract.exists():
                    update_vals = {}
                    changes = []

                    for field, contract_field in self.FIELD_MAP.items():
                        if field in data:
                            old_value = getattr(contract, contract_field, 0.0)
                            new_value = data[field]

                            if old_value != new_value:
                                update_vals[contract_field] = new_value
                                changes.append(
                                    _("%s: %s → %s") % (
                                        self.FIELD_LABELS.get(field, field),
                                        old_value,
                                        new_value
                                    )
                                )

                    if update_vals:
                        contract.with_context(bypass_lock_restriction=True).write(update_vals)

                        # Add message to contract's chatter
                        if changes:
                            message = Markup(
                                "<b>Allowances restored from:</b> %s<br/><b>Changes:</b><br/>%s"
                            ) % (self.name, "<br/>".join(changes))
                            contract.message_post(body=message)



        except Exception as e:
            raise UserError(_("Error restoring original contract data: %s") % str(e))

    def _get_contract_changes_message(self, contract, update_vals):
        """Generate a human-readable message about what changed in the contract."""
        changes = []
        for field, contract_field in self.FIELD_MAP.items():
            if contract_field in update_vals:
                old_value = getattr(contract, contract_field, 0.0)
                new_value = update_vals[contract_field]

                if old_value != new_value:
                    changes.append(
                        _("%s: %s → %s") % (
                            self.FIELD_LABELS.get(field, field),
                            old_value,
                            new_value
                        )
                    )

        return changes

    def action_create(self):
        self.ensure_one()

        if self.state != 'draft':
            raise UserError(_("You can only create from draft state."))

        self.write({'state': 'created'})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'employee.allowance.update',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def action_approve(self):
        """Move to Created state - Apply allowances to contracts."""
        self.ensure_one()

        if self.state != 'created':
            raise UserError(_("You can only approve from created state."))

        employees = self._get_target_employees()
        if not employees:
            raise UserError(_("No employees found for the selected criteria."))

        # Filter only employees with active contracts
        employees_with_contracts = self._get_employees_with_active_contracts(employees)
        if not employees_with_contracts:
            raise UserError(_("No employees with active contracts found for the selected criteria."))

        # Get active contracts
        contracts = self._get_active_contracts(employees)
        if not contracts:
            raise UserError(_("No active contracts found."))

        # Save original contract data before making changes
        self._save_original_contract_data(contracts)

        # Prepare update values - only non-zero values
        update_vals = {}
        for field, contract_field in self.FIELD_MAP.items():
            # Include zero values also (update all non-empty fields)
            if self[field] is not None:
                update_vals[contract_field] = self[field]


        try:
            updated_contracts = []
            # Update contracts one by one to track changes in chatter
            for contract in contracts:
                contract_changes = self._get_contract_changes_message(contract, update_vals)

                if contract_changes:
                    contract.with_context(bypass_lock_restriction=True).write(update_vals)
                    updated_contracts.append(contract)

                    # Add message to contract's chatter

                    message = Markup(
                        "Allowances updated via <b>%s</b><br/>Changes:<br/>%s"
                    ) % (self.name, "<br/>".join(contract_changes))
                    contract.message_post(body=message)

            # Move to Approved state
            self.write({'state': 'approved'})

            # Show warning if some employees were skipped
            skipped_count = len(employees) - len(employees_with_contracts)
            message = _("Allowances successfully updated for %d employees with active contracts.") % len(
                updated_contracts)

            if skipped_count > 0:
                message += _("\n\n%d employees were skipped because they don't have active contracts.") % skipped_count

            # Show success message
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'employee.allowance.update',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'current',
            }

        except Exception as e:
            raise UserError(_("Error updating contracts: %s") % str(e))

    def action_set_to_draft(self):
        self.ensure_one()

        if self.original_contract_data:
            self._restore_original_contract_data()

        self.write({'state': 'draft'})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'employee.allowance.update',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def unlink(self):
        for record in self:
            if record.original_contract_data and record.state != 'draft':
                record._restore_original_contract_data()
        return super().unlink()

    # Make form fields readonly based on state
    def _get_readonly_fields(self):
        """Helper method to determine which fields should be readonly."""
        if self.state == 'draft':
            return []
        else:
            # In 'created' and 'approved' states, make allowance fields readonly
            return list(self.FIELD_MAP.keys()) + ['select_type', 'company_id', 'department_ids', 'employee_ids']
