from odoo import _, api, fields, models
from odoo.exceptions import UserError

class AccountPaymentInherited(models.Model):
    _inherit = 'account.payment'
    
    _is_write_in_progress = fields.Boolean(default=False, store=False)
    amount_total_words_payment = fields.Char(string='Amount in Words', compute="_compute_amount_in_words")

    @api.depends('amount', 'currency_id')
    def _compute_amount_in_words(self):
        for rec in self:
            try:
                if rec.amount and rec.currency_id:
                    # Using updated amount_to_text() from res.currency
                    amount_text = rec.currency_id.amount_to_text(rec.amount).replace(',', '')
                    rec.amount_total_words_payment = amount_text + " Only"
                else:
                    rec.amount_total_words_payment = False
            except:
                rec.amount_total_words_payment = False


    deduction_ids = fields.One2many(
        comodel_name="account.direct.payment.deduction",
        inverse_name="payment_id",
        string="Deductions",
        copy=False,
    )

    actual_amount = fields.Monetary(currency_field='currency_id')
    is_locked = fields.Boolean(string="Locked Taxes",copy=False)
    is_multiple_deduction = fields.Boolean(string="With Holding Tax",copy=False)

    @api.onchange('is_multiple_deduction')
    def _onchange_is_multiple_deduction(self):
        for rec in self:
            if rec.is_multiple_deduction:
                if not rec.actual_amount:
                    raise UserError("First Save the Payment!")


    @api.model
    def create(self,vals):
        if vals['amount'] and not vals.get('actual_amount'):
            vals['actual_amount'] = vals['amount']
        
        return super(AccountPaymentInherited, self).create(vals)


    @api.onchange("deduction_ids", "deduction_ids.tax_id", "deduction_ids.amount","deduction_ids.use_deducted_amount_for_tax","deduction_ids.account_id")
    def _onchange_deduction_ids(self):
        '''onchnage method to get tax account label and amount from selected tax'''
        for rec in self:
            if rec.deduction_ids:
                rec.amount = rec.actual_amount
                # raise UserError(str([rec.deduction_ids]))
                for line in rec.deduction_ids:
                    if line.tax_id:
                        for account_line in line.tax_id.invoice_repartition_line_ids:
                            if account_line.account_id:
                                line.account_id = account_line.account_id.id
                                break
                        base_amount = rec.amount if line.use_deducted_amount_for_tax else rec.actual_amount
                        line.amount = base_amount * (line.tax_id.amount / 100)
                        line.name = line.tax_id.invoice_label
                        rec.amount -= line.amount

                    elif line.account_id and line.is_direct_deduct:
                        rec.amount -= line.amount
                    else:
                        pass
           

    def button_refresh_tax(self):
        for rec in self:
            if rec.move_id:
            ##Vendor Payment
                if rec.payment_type == 'outbound':
                    move = rec.move_id
                    label = move.line_ids[0].name
                    move.line_ids.unlink()
                    
                    #reset line_ids
                    line_updates = []

                    # Credit line for the actual amount
                    line_updates.append((0, 0, {
                        'move_id': move.id,
                        'name': label or '',
                        'account_id': rec.journal_id.default_account_id.id,
                        'credit': rec.actual_amount,
                        'debit': 0.0,
                        'sequence':10,
                    }))

                    # Debit line for the actual amount
                    line_updates.append((0, 0, {
                        'move_id': move.id,
                        'name': label or '',
                        'account_id': rec.destination_account_id.id,
                        'debit': rec.actual_amount,
                        'credit': 0.0,
                        'sequence':20,
                    }))

                    # Write all line updates at once
                    move.write({'line_ids': line_updates})
                    
                    # Remove the deduction lines
                    rec.deduction_ids = [(5, 0, 0)]
                    #Revert the amount
                    rec.amount = rec.actual_amount
                    #False the Locked field
                    rec.is_locked = False

                #Customer Payment
                elif rec.payment_type == 'inbound':
                    move = rec.move_id
                    label = move.line_ids[0].name
                    move.line_ids.unlink()
                    
                    #reset line_ids
                    line_updates = []

                    # Credit line for the actual amount
                    line_updates.append((0, 0, {
                        'move_id': move.id,
                        'name': label or '',
                        'account_id': rec.destination_account_id.id,
                        'credit': rec.actual_amount,
                        'debit': 0.0,
                        'sequence':20,
                    }))

                    # Debit line for the actual amount
                    line_updates.append((0, 0, {
                        'move_id': move.id,
                        'name': label or '',
                        'account_id': rec.journal_id.default_account_id.id,
                        'debit': rec.actual_amount,
                        'credit': 0.0,
                        'sequence':10,
                    }))

                    # Write all line updates at once
                    move.write({'line_ids': line_updates})
                    
                    # Remove the deduction lines
                    rec.deduction_ids = [(5, 0, 0)]
                    #Revert the amount
                    rec.amount = rec.actual_amount
                    #False the Locked field
                    rec.is_locked = False


    @api.model
    def write(self, vals):
        # Prevent recursion by checking the context flag
        if self._context.get('no_recursion', False):
            return super(AccountPaymentInherited, self).write(vals)

        res = super(AccountPaymentInherited, self).write(vals)

        for rec in self:           
            # Update the Actual Amount field with Amount
            if 'deduction_ids' not in vals and 'amount' in vals:
                rec.actual_amount = rec.amount

           
        return res

    @api.constrains('deduction_ids', 'amount','is_locked','move_id','state')
    def _constrains_deduction_or_amount(self):
        # This method will trigger when deduction_ids or amount changes
        for rec in self:
            if not rec.is_locked and rec.move_id and rec.move_id.line_ids and rec.deduction_ids and rec.state == 'paid':
                # raise UserError(str([rec.deduction_ids, rec.amount, rec.is_locked, rec.move_id,rec.state]))
                if rec.payment_type in ['outbound', 'inbound']:
                    # Handle move line update logic
                    rec._handle_move_lines_update()
            
    def _handle_move_lines_update(self):
        # Update the journal lines based on payment type.
        for rec in self:
            move = rec.move_id
            if not move:
                continue
            if rec.state == 'paid':
                rec.with_context(no_recursion=True).action_draft()
            # Reset the move lines before adding new ones.
            label = move.line_ids[0].name if move.line_ids else 'Payment'
            move.with_context(no_recursion=True).line_ids.unlink()

            line_updates = []

            # Add debit line for actual amount
            line_updates.append((0, 0, {
                'move_id': move.id,
                'name': label,
                'account_id': rec.destination_account_id.id,
                'debit': rec.actual_amount if rec.payment_type == 'outbound' else 0.0,
                'credit': 0.0 if rec.payment_type == 'outbound' else rec.actual_amount,
                'sequence': 20,
            }))

            # Add credit lines for each deduction
            sequence = 30
            for line in rec.deduction_ids:
                line_updates.append((0, 0, {
                    'move_id': move.id,
                    'name': line.name or '',
                    'account_id': line.account_id.id,
                    'debit': 0.0 if rec.payment_type == 'outbound' else line.amount,
                    'credit': line.amount if rec.payment_type == 'outbound' else 0.0,
                    'sequence': sequence,
                }))
                sequence += 10

            # Add remaining amount if any (for outbound payments)
            remaining_amount = rec.actual_amount - sum(line.amount for line in rec.deduction_ids)
            if remaining_amount > 0:
                line_updates.append((0, 0, {
                    'move_id': move.id,
                    'name': label,
                    'account_id': rec.journal_id.default_account_id.id,
                    'debit': 0.0 if rec.payment_type == 'outbound' else remaining_amount,
                    'credit': remaining_amount if rec.payment_type == 'outbound' else 0.0,
                    'sequence': 10,
                }))

            # Write all line updates to the move
            move.with_context(no_recursion=True).write({'line_ids': line_updates})

            # Finalize the payment process if applicable
            if rec.deduction_ids:
                if rec.state != 'paid':
                    rec.action_post()
                    move.action_post()
                rec.with_context(no_recursion=True).write({
                    "is_locked": True
                    })
    