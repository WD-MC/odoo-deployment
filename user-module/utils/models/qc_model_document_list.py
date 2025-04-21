from odoo import _, models, fields, api
from odoo.exceptions import ValidationError


class QcModelDocumentList(models.Model):
    _name = 'qc.model.document.list'
    _description = 'Model description of list data'
    _rec_name = 'id'
    _order = 'id desc'

    company_id = fields.Many2one('res.partner', 'Company')
    '''Description of list'''
    title = fields.Char(string='Title', required=False)
    '''Title list document'''
    description = fields.Html(string='Conclusion', required=False)
    '''list attached document'''
    document_ids = fields.One2many('qc.model.document', 'list_id', string='Documents')
    status = fields.Selection([('1', 'Draft'), ('2', 'Valid')], required=True, default='1')
    is_valid = fields.Boolean(default=False)

    def write(self, vals):
        """Update action."""
        authorize_groups = self._context.get('check_group_list')

        if authorize_groups and not self._check_user_group(authorize_groups):
            raise ValidationError(_("You don't have the right to process this operation"))

        qc_model_list = super(QcModelDocumentList, self).write(vals)

        return qc_model_list

    def _check_user_group(self, check_group_list):
        success = False
        for rec in check_group_list:
            if self.env.user.has_group(rec):
                success = True
                break
        return success

    def button_validate(self):
        authorize_groups = self._context.get('check_group_list')
        if authorize_groups and self._check_user_group(authorize_groups):
            self.write({
                'status': '2',
            })
        else:
            raise ValidationError(_("You don't have the right to process this operation"))

    def button_draft(self):
        authorize_groups = self._context.get('check_group_list')
        if authorize_groups and self._check_user_group(authorize_groups):
            self.write({
                'status': '1',
            })
        else:
            raise ValidationError(_("You don't have the right to process this operation "))

    def validate_list(self, list_id):
        list = self.search([('id', '=', list_id)])
        list.write({
            'is_valid': True,
        })

    def invalidate_list(self, list_id):
        list = self.search([('id', '=', list_id)])
        list.write({
            'is_valid': False,
        })


class QcModelDocument(models.Model):
    _name = 'qc.model.document'
    _description = 'Documents attached on list data'
    _rec_name = 'file_name'
    _order = 'id desc'

    list_id = fields.Many2one('qc.model.document.list', 'list')
    '''Document list id'''
    res_model = fields.Char(string='Document Model', required=True)
    '''Document model'''
    res_id = fields.Integer(string='Model Id', required=False)
    '''Document Id'''
    file_id = fields.Many2one('ir.attachment', string='Document attaché')
    file = fields.Binary('Document attaché', required=True, related='file_id.datas')
    file_name = fields.Char('Document attaché', required=True , related='file_id.name')
    orignal_file_name = fields.Char('Original Attachment name', required=True , related='file_id.store_fname')
    mimetype = fields.Char('Mime Type', required=True, related='file_id.mimetype')
    '''Scanned document attached'''
    status = fields.Selection(string='Status', related='list_id.status')
    nature_id = fields.Many2one('qc.nature.document', string='Attached document')

    @api.model
    def create(self, vals):
        list = self.env['qc.model.document.list'].sudo().search([('id', '=', int(vals['list_id']))])
        partner = list.company_id
        partner_enterprise_name = None
        partner_enterprise_id = None
        if not  vals['mimetype']:
            vals['mimetype'] = 'application/octet-stream'
        if partner:
            partner_enterprise_name = partner.name
            partner_enterprise_id = partner.id
        if 'file' in vals.keys():
            id = self.env['servicing.utils']._create_documents(vals['file'],
                                                               vals['file_name'],
                                                               partner_enterprise_name,
                                                               partner_enterprise_id,
                                                               vals['orignal_file_name'],
                                                               vals['mimetype'])
            if id:
                vals["file_id"] = id

        qc_model_list_document = super(QcModelDocument, self).create(vals)
        return qc_model_list_document

class QcNatureDocument(models.Model):
    _name = 'qc.nature.document'
    _description = 'Nature de document'
    _rec_name = 'name'
    _order = 'id desc'

    process_id = fields.Many2one('qc.workflow', 'Associated process')
    '''Id of associated process'''
    name = fields.Char(string='Nature', required=True)
    '''Nature name'''
    description = fields.Integer(string='Nature decription', required=False)
    '''Nature description'''