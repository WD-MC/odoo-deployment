from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    status = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('validated', 'Validated')
    ], default='draft', string='Status')

    def button_draft(self):
        for record in self:
            record.write({'status': 'draft'})


    def button_submit(self):
        for record in self:
            record.write({'status': 'submit'})

    def button_validate(self):
        for record in self:
            record.write({'status': 'validated'})

    is_readonly = fields.Boolean(
        compute='_compute_is_readonly',
        store=False,
    )

    def _compute_is_readonly(self):
        for rec in self:
            if rec.status == 'draft' and self.env.user.has_group('utils.group_exchange_rate_initiator'):
                rec.is_readonly = False
            else:
                rec.is_readonly = True

    x_css = fields.Html(
        sanitize=False,
        compute='_compute_css',
        store=False,
    )

    def _compute_css(self):
        for rec in self:
            if rec.status == 'draft' and self.env.user.has_group('utils.group_exchange_rate_initiator'):
                rec.x_css = False
            else:
                rec.x_css = '<style>.o_form_button_edit {display: none !important;}</style>'


    def unlink(self):
        """Delete action"""
        for rec in self:
            if not(rec.status == 'draft' and self.env.user.has_group('utils.group_exchange_rate_initiator')):
                raise ValidationError(_('Unable to delete: Please contact your administrator.'))
            else:
                resCurrency = super(ResCurrency, self).unlink()
                return resCurrency

    @api.model
    def _search(self, args, offset=0, limit=None, order=None):
        '''Search action.'''

        if self.env.user.has_group('utils.group_exchange_rate_approve'):
            args += [('status', 'in', ['submit', 'validated'])]
        elif self.env.user.has_group('utils.group_exchange_rate_initiator'):
            args += [('status', 'in',  ['draft','submit'])]




        return super(ResCurrency, self)._search(args, offset, limit, order)
