from odoo import fields, models,api,_
import logging
_logger = logging.getLogger(__name__)

class MultipleOne2manyInherit(models.AbstractModel):
    """ The base model, which is implicitly inherited by all models. """
    _inherit = ['base']
    # _inherit = ['sale.order.line','purchase.order.line','account.move.line']

    serial_number = fields.Integer(string='Sr.',compute='_compute_serial_number',store=False)

    @api.depends()
    @api.model
    def _compute_serial_number(self):
        if not self:
            return

        Model = self.env[self._name]              # child model (e.g. purchase.order.line)
        imf = self.env['ir.model.fields'].sudo()  # metadata

        # 1) Find all one2many fields on other models that relate to this model
        #    (these are the parent model fields like 'order_line' on 'purchase.order')
        one2many_meta = imf.search([('relation', '=', self._name), ('ttype', '=', 'one2many')])

        # Map of inverse_field_name -> parent_model_name
        # inverse_field_name is the many2one name on the child (e.g. 'order_id')
        inv_map = {}  # inv_field -> parent_model_name
        for meta in one2many_meta:
            try:
                parent_model_name = meta.model         # e.g. 'purchase.order'
                parent_field_name = meta.name          # e.g. 'order_line'
                parent_model = self.env[parent_model_name]
                parent_field_obj = parent_model._fields.get(parent_field_name)
                # one2many field on parent exposes inverse_name which is the child many2one
                inv_name = getattr(parent_field_obj, 'inverse_name', None)
                if inv_name:
                    inv_map[inv_name] = parent_model_name
            except Exception:
                # defensive: skip any problematic meta entry
                continue

        # Determine sibling ordering (prefer 'sequence' if present)
        order_cols = []
        if 'sequence' in Model._fields:
            order_cols.append('sequence')
        order_cols.append('id')
        order_clause = ','.join(f'{c} asc' for c in order_cols)

        # 2) Group current records by (inverse_field, parent_id)
        groups = {}   # (inv_field, parent_id) -> [records]
        ungrouped = []  # records for which we found no parent via inv_map

        for rec in self:
            found = False
            for inv_field in inv_map.keys():
                try:
                    parent = getattr(rec, inv_field) or False
                except Exception:
                    parent = False
                if parent and not isinstance(parent, int):
                    key = (inv_field, parent.id)
                    groups.setdefault(key, []).append(rec)
                    found = True
                    break
            if not found:
                ungrouped.append(rec)

        # 3) For each group, fetch siblings (children of the same parent) once and map id->position
        for (inv_field, parent_id), recs in groups.items():
            domain = [(inv_field, '=', parent_id)]
            siblings = Model.search(domain, order=order_clause)
            pos_map = {rid: idx + 1 for idx, rid in enumerate(siblings.ids)}
            for r in recs:
                r.serial_number = pos_map.get(r.id, 0)

        # 4) For any remaining ungrouped records: fallback to indexing among the current recordset if possible;
        #    if you prefer global indexing, replace the below with a full-model search.
        if ungrouped:
            # create map of current recordset sorted by id -> position
            # (limits scope and avoids scanning entire table)
            local_sorted = sorted(self, key=lambda r: r.id)
            local_map = {r.id: idx + 1 for idx, r in enumerate(local_sorted)}
            for r in ungrouped:
                r.serial_number = local_map.get(r.id, 0)
