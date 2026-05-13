from odoo import models, fields, api
from odoo.exceptions import UserError


class HrContract(models.Model):
    _inherit = "hr.contract"

    is_locked = fields.Boolean(string="Locked", default=False)
    locked_by = fields.Many2one('res.users', string="Locked By")
    locked_date = fields.Datetime(string="Locked Date")
    unlocked_by = fields.Many2one('res.users', string="Unlocked By")
    unlocked_date = fields.Datetime(string="Unlocked Date")

    def write(self, vals):
        if self.env.context.get('bypass_lock_restriction'):
            return super().write(vals)

        # Allow lock/unlock related fields to be updated anytime
        lock_fields = {'is_locked', 'locked_by', 'locked_date', 'unlocked_by', 'unlocked_date'}
        if set(vals.keys()).issubset(lock_fields):
            return super().write(vals)

        # Handle auto-locking when state changes to 'open'
        if 'state' in vals:
            if vals['state'] == 'open':
                for rec in self:
                    if not rec.is_locked:
                        super(HrContract, rec).write({
                            'is_locked': True,
                            'locked_by': self.env.user.id,
                            'locked_date': fields.Datetime.now()
                        })
            elif vals['state'] != 'open':
                for rec in self:
                    if rec.is_locked:
                        super(HrContract, rec).write({
                            'is_locked': False,
                            'unlocked_by': self.env.user.id,
                            'unlocked_date': fields.Datetime.now()
                        })

        return super().write(vals)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.state == 'open' and not record.is_locked:
            record.with_context(bypass_lock_restriction=True).write({
                'is_locked': True,
                'locked_by': self.env.user.id,
                'locked_date': fields.Datetime.now()
            })
        return record

    def action_lock(self):
        for rec in self:
            if not rec.is_locked:
                rec.with_context(bypass_lock_restriction=True).write({
                    'is_locked': True,
                    'locked_by': self.env.user.id,
                    'locked_date': fields.Datetime.now(),
                    'unlocked_by': False,
                    'unlocked_date': False
                })
        return True

    def action_unlock(self):
        for rec in self:
            if rec.is_locked:
                rec.with_context(bypass_lock_restriction=True).write({
                    'is_locked': False,
                    'unlocked_by': self.env.user.id,
                    'unlocked_date': fields.Datetime.now()
                })
        return True

    def unlink(self):
        locked_records = self.filtered(lambda r: r.is_locked)
        if locked_records:
            contract_names = ", ".join(locked_records.mapped('name') or ['Unknown'])
            raise UserError(
                f"You cannot delete locked contracts: {contract_names}. "
                "Please unlock them first."
            )
        return super().unlink()