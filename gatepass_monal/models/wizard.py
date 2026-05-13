import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class GatepassReturnWizard(models.TransientModel):
    _name = "gatepass.return.wizard"
    _description = "GatePass Return Wizard"

    gatepass_id = fields.Many2one("monal.gatepass", string="Gatepass")
    line_ids = fields.One2many("gatepass.return.wizard.line", "wizard_id", string="Return Lines")

    def action_create_return(self):

        self.ensure_one()
        rec = self.gatepass_id
        new_type = 'inwards' if rec.type == 'outwards' else 'outwards'

        new_lines = []
        for line in self.line_ids:
            if line.return_qty > 0:
                new_lines.append((0, 0, {
                    "product_id": line.product_id.id,
                    "product_qty": line.return_qty,
                    "return_type": "not_returnable",
                    "status": "done",
                }))
                line.original_line_id.returned_qty += line.return_qty

        if not new_lines:
            return

        new_vals = {
            "ware_house": rec.ware_house.id,
            "partner_id": rec.partner_id.id,
            "from_location": rec.from_location.id,
            "company_id": rec.company_id.id,
            "ref": rec.name,
            "return_of": f"Return Of {rec.name}",
            "remarks": rec.remarks,
            'parent_id': rec.id,
            "transfer_date": datetime.date.today(),
            "transferred_by": self.env.user.id,
            "type": new_type,
            "state": "done",
            "line_ids": new_lines,
        }
        new_rec = self.env["monal.gatepass"].create(new_vals)

        all_done = all(l.product_qty <= l.returned_qty for l in rec.line_ids if l.return_type == "returnable")
        rec.state = "done" if all_done else "returnable"

        return {
            "type": "ir.actions.act_window",
            "res_model": "monal.gatepass",
            "view_mode": "form",
            "res_id": new_rec.id,
            "target": "current",
        }


class GatepassReturnWizardLine(models.TransientModel):
    _name = "gatepass.return.wizard.line"
    _description = "GatePass Return Wizard Line"

    wizard_id = fields.Many2one("gatepass.return.wizard", store=True)
    original_line_id = fields.Many2one("monal.gatepass.line", string="Original Line", store=True)
    product_id = fields.Many2one("product.product", string="Product", readonly=True, store=True)
    product_qty = fields.Float(string="Total Qty", readonly=True, store=True)
    returned_qty = fields.Float(string="Already Returned", readonly=True, store=True)
    remaining_qty = fields.Float(string="Remaining", compute="_compute_remaining", store=False)
    return_qty = fields.Float(string="Return Now", store=True)

    @api.depends("product_qty", "returned_qty")
    def _compute_remaining(self):
        for rec in self:
            rec.remaining_qty = rec.product_qty - rec.returned_qty

    @api.constrains("return_qty")
    def _check_return_qty(self):
        for rec in self:
            remaining = rec.original_line_id.product_qty - rec.original_line_id.returned_qty
            print(remaining)
            if rec.return_qty > remaining:
                raise ValidationError(
                    f"Return quantity for product '{rec.product_id.display_name}' "
                    f"cannot exceed remaining ({remaining})."
                )
