from odoo import _, models, fields, api
from odoo.exceptions import ValidationError


class QcModelReport(models.Model):
    _name = 'qc.model.report'
    _description = 'Model description of report data'
    _rec_name = 'id'
    _order = 'id desc'

    company_id = fields.Many2one('res.company', 'Company')
    '''Description of report'''
    description = fields.Html(string='Conclusion', required=False)
    '''Report attached document'''
    document_ids = fields.One2many('qc.model.report.document', 'report_id', string='Documents')
    status = fields.Selection([('1', 'Draft'), ('2', 'Valid')], required=True, default='1')
    is_valid = fields.Boolean(default=False)

    def write(self, vals):
        """Update action."""
        authorize_groups = self._context.get('check_group_list')

        if authorize_groups and not self._check_user_group(authorize_groups):
            raise ValidationError(_("You don't have the right to process this operation"))

        qc_model_report = super(QcModelReport, self).write(vals)

        return qc_model_report

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

    def validate_report(self, report_id):
        report = self.search([('id', '=', report_id)])
        report.write({
            'is_valid': True,
        })

    def invalidate_report(self, report_id):
        report = self.search([('id', '=', report_id)])
        report.write({
            'is_valid': False,
        })


class QcModelReportDocument(models.Model):
    _name = 'qc.model.report.document'
    _description = 'Documents attached on report data'
    _rec_name = 'ref_document'
    _order = 'id desc'

    '''Document reference number'''
    report_id = fields.Many2one('qc.model.report', 'Report')
    '''Document reference number'''
    ref_document = fields.Char(string='Document ref number', required=True)
    '''Document signing date'''
    date_document = fields.Date(string='Document Signing date', required=False)

    '''Scanned document attached'''
    file_id = fields.Many2one('dms.file', string='Attached document')
    file = fields.Binary('Attached document', required=True, related='file_id.content')
    file_name = fields.Char('Attached document', required=True)

    status = fields.Selection(string='Status', related='report_id.status')

    @api.model
    def create(self, vals):
        report = self.env['qc.model.report'].sudo().search([('id', '=', int(vals['report_id']))])
        partner = report.company_id.partner_id
        partner_enterprise_name = None
        partner_enterprise_id = None

        if partner:
            partner_enterprise_name = partner.name
            partner_enterprise_id = partner.id
        if 'file' in vals.keys():
            id = self.env['servicing.utils']._create_documents(vals['file'],
                                                               vals['file_name'],
                                                               partner_enterprise_name, partner_enterprise_id)
            if id:
                vals["file_id"] = id

        qc_model_report_document = super(QcModelReportDocument, self).create(vals)
        return qc_model_report_document
