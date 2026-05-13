from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MultiReturnWizard(models.TransientModel):
    _name = "multi.return.wizard"
    _description = "GatePass Multi Return Wizard"

    gatepass_id = fields.Many2one("monal.gatepass", string="Gatepass")
    line_ids = fields.One2many("multi.return.wizard.line", "wizard_id", string="Return Lines")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids")
        if active_ids:
            lines = self.env["monal.gatepass.line"].browse(active_ids)
            res["gatepass_id"] = lines[0].gatepass_id.id if lines else False

            line_vals = []
            for l in lines:
                line_vals.append((0, 0, {
                    "original_line_id": l.id,
                    "product_id": l.product_id.id,
                    "product_qty": l.product_qty,
                    "returned_qty": l.returned_qty,
                }))
            res["line_ids"] = line_vals
        return res

    def action_create_return(self):
        for wizard in self:
            if not wizard.line_ids:
                continue

            # Group lines by their parent gatepass
            grouped_lines = {}
            for line in wizard.line_ids:
                grouped_lines.setdefault(line.original_line_id.gatepass_id, self.env['multi.return.wizard.line'])
                grouped_lines[line.original_line_id.gatepass_id] |= line

            for parent_gp, lines in grouped_lines.items():
                return_type = "outwards" if parent_gp.type == "inwards" else "inwards"

                new_gatepass = self.env["monal.gatepass"].create({
                    "type": return_type,
                    "partner_id": parent_gp.partner_id.id,
                    "ware_house": parent_gp.ware_house.id,
                    "from_location": parent_gp.from_location.id,
                    "company_id": parent_gp.company_id.id,
                    "parent_id": parent_gp.id,
                    "transfer_date": fields.Datetime.now(),
                    "return_of": f"Return Of {parent_gp.name}",
                    "remarks": "Auto return created from wizard",
                })

                for l in lines:
                    if l.return_qty > 0:
                        l.original_line_id.returned_qty += l.return_qty
                        if l.original_line_id.returned_qty >= l.original_line_id.product_qty:
                            l.original_line_id.return_type = "not_returnable"

                        self.env["monal.gatepass.line"].create({
                            "gatepass_id": new_gatepass.id,
                            "product_id": l.original_line_id.product_id.id,
                            "product_qty": l.return_qty,
                            "return_type": "not_returnable",
                            "status": "done",
                            "remarks": l.original_line_id.remarks,
                        })

                returnable_lines = parent_gp.line_ids.filtered(lambda l: l.return_type == "returnable")
                if returnable_lines and all(l.product_qty <= l.returned_qty for l in returnable_lines):
                    parent_gp.state = "done"
                elif returnable_lines:
                    parent_gp.state = "returnable"
                else:
                    parent_gp.state = "done"


class MultiReturnWizardLine(models.TransientModel):
    _name = "multi.return.wizard.line"
    _description = "GatePass Multi Return Wizard Line"

    wizard_id = fields.Many2one("multi.return.wizard", store=True)
    original_line_id = fields.Many2one("monal.gatepass.line", string="Original Line", store=True)
    product_id = fields.Many2one("product.product", string="Product", store=True)
    product_qty = fields.Float(string="Total Qty", readonly=True, store=True)
    returned_qty = fields.Float(string="Already Returned", readonly=True, store=True)
    remaining_qty = fields.Float(string="Remaining", compute="_compute_remaining", store=True)
    return_qty = fields.Float(string="Return Now")

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