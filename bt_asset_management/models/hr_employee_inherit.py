from dateutil.relativedelta import relativedelta
from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # asset_move_count = fields.Integer(
    #     string='Asset Move Count',
    #     compute='_compute_asset_move_count',
    #     readonly=True,
    # )
    #
    # # @api.depends("id")  # ↓ nothing to track, force recompute through context or onchange
    # def _compute_asset_move_count(self):
    #     move = self.env["bt.asset.move"]
    #     for employee in self:
    #         employee.asset_move_count = move.search_count(
    #             [("asset_loc_id", "=", employee.id)]
    #         )
    #
    # def action_open_asset_move(self):
    #     self.ensure_one()
    #
    #     # Any title you like
    #     name = f"Asset Moves – {self.name}"
    #
    #     return {
    #         "type": "ir.actions.act_window",
    #         "name": name,
    #         "res_model": "bt.asset.move",
    #         # only our read‑only tree
    #         "views": [
    #             (self.env.ref("bt_asset_management.bt_asset_management_asset_move_tree").id, "list"),
    #         ],
    #         "view_mode": "list",
    #         "target": "current",
    #         "domain": [("asset_loc_id", "=", self.id)],
    #         # context flags also remove the “Create” button in v14+
    #         "context": {
    #             "default_asset_loc_id": self.id,
    #             "create": 0,  # hide Create
    #         },
    #     }
    #     # self.ensure_one()
    #     # # load the generic asset‑move action
    #     # action = self.env.ref('bt_asset_management.action_bt_asset_move').read()[0]
    #     # # narrow to this employee
    #     # action['domain'] = [('asset_loc_id', '=', self.id)]
    #     # # optional: put employee’s name in the action title
    #     # action['name'] = f"Asset Moves – {self.name}"
    #     # action["context"] = {
    #     #     "default_asset_loc_id": self.id,
    #     #     "create": 0,
    #     # }
    #     # return action

    asset_count = fields.Integer(
        string="Asset Count",
        compute="_compute_asset_count",
        readonly=True,
    )

    def _compute_asset_count(self):
        asset = self.env["account.asset"]
        for employee in self:
            employee.asset_count = asset.search_count(
                [("asset_loc_id", "=", employee.id)]
            )

    # -----------------------------------------------------------------
    # SMART‑BUTTON ACTION
    # -----------------------------------------------------------------
    def action_open_assets(self):
        """Read‑only asset list, filtered to this employee."""
        self.ensure_one()

        # Use any existing tree view for account.asset.
        # The stock view id in most versions ≤ v17 is
        #   account_asset.view_account_asset_asset_tree
        # Inspect in ⚙ > Debug > Edit View if yours differs.
        tree_view = self.env.ref(
            "bt_asset_management.view_account_asset_tree_readonly"
        ).id  # ← change if your ID is different

        return {
            "type": "ir.actions.act_window",
            "name": f"Assets – {self.name}",
            "res_model": "account.asset",
            "views": [(tree_view, "list")],
            "view_mode": "list",
            "target": "current",
            "domain": [("asset_loc_id", "=", self.id)],
            # context flags hide the “Create” button in ≥ v14
            "context": {
                "create": 0,
                "default_asset_loc_id": self.id,
            },
        }