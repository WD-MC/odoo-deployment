from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
import mimetypes
import logging

_logger = logging.getLogger(__name__)

class DocumentEnregistrement(models.Model):
    _name = 'document.enregistrement'
    _description = 'Documents attached on list data'
    _rec_name = 'file_name'
    _order = 'id desc'

    enregistrement_id = fields.Many2one('me.enregistrement', 'Id enregistrement')
    partner_enterprise_id = fields.Many2one('res.partner', compute='_compute_partner_enterprise_id' , inverse='_inverse_partner_enterprise_id' )

    def _compute_partner_enterprise_id(self):
        for rec in self:
            if rec.enregistrement_id:
                rec.partner_enterprise_id = rec.enregistrement_id.partner_id

    def _inverse_partner_enterprise_id(self):
        """Permet la modification du champ file, mais ne fait rien"""
        pass
    partner_enterprise_name = fields.Char('Partner Name',compute='_compute_partner_enterprise_name' , inverse='_inverse_partner_enterprise_name')
    def _compute_partner_enterprise_name(self):
        for rec in self:
            if rec.enregistrement_id:
                rec.partner_enterprise_name = rec.enregistrement_id.partner_id.name

    def _inverse_partner_enterprise_name(self):
        """Permet la modification du champ file, mais ne fait rien"""
        pass
    '''Document list id'''
    #res_model = fields.Char(string='Document Model', required=False)
    '''Document model'''
    #res_id = fields.Integer(string='Model Id', required=False)
    '''Document Id'''
    file_id = fields.Many2one('ir.attachment', string='Document attaché', store=True)
    #file_id = fields.Many2one('ir.attachment', string='Document attaché',  store=True, compute='_compute_file_id')

    # def _compute_file_id(self):
    #     for rec in self:
    #         if rec.file_id:
    #             rec.file = rec.file_id.datas
    #             rec.file_name = rec.file_id.name

    #file = fields.Binary('Document joint', store=False)


    #file = fields.Binary('Document attaché', required=True, related='file_id.datas')
    file = fields.Binary('Document joint', required=True, compute='_compute_file' , inverse='_inverse_file')
    def _compute_file(self):
        for rec in self:
            if rec.file_id:
                rec.file = rec.file_id.datas

    def _inverse_file(self):
        """Permet la modification du champ file, mais ne fait rien"""
        pass


    file_name = fields.Char('Document attaché', required=True  ,compute='_compute_file_name' , inverse='_inverse_file_name')
    #file_name = fields.Char('Document attaché', required=True, store=True)
    def _compute_file_name(self):
        for rec in self:
            if rec.file_id:
                rec.file_name = rec.file_id.name

    def _inverse_file_name(self):
        """Permet la modification du champ file, mais ne fait rien"""
        pass


    original_file_name = fields.Char('Original Attachment name', required=False , related='file_id.store_fname')
    mimetype = fields.Char('Mime Type', required=False, related='file_id.mimetype')
    '''Scanned document attached'''
    nature_id = fields.Many2one('qc.nature.document', string='Attached document')

    @api.model
    def create(self, vals):
        if 'file' in vals.keys() and vals.get('file'):
            # Extract file name from 'file_name' if provided, otherwise assign a default name
            file_name = vals.get('file_name') or 'document'
            original_file_name = file_name
            mimetype = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
            enregistrement = self.env['me.enregistrement'].search([('id', '=', int(vals['enregistrement_id']))])
            _logger.info(
                f"list : {list}   partner_enterprise_name {vals.get('partner_enterprise_name')}. partner_enterprise_id: {vals.get('partner_enterprise_id')}")

            partner_enterprise_name = vals.get(
                'partner_enterprise_name') or enregistrement.partner_id.name
            partner_enterprise_id = vals.get(
                'partner_enterprise_id') or enregistrement.partner_id.id
            attachment = self.env['servicing.utils']._create_documents(vals.get('file'),
                                                                   file_name,
                                                                   partner_enterprise_name,
                                                                   partner_enterprise_id,
                                                                   original_file_name,
                                                                   mimetype)
            if attachment:
                vals["file_id"] = attachment.id

        documentEnregistrement = super(DocumentEnregistrement, self).create(vals)
        return documentEnregistrement