from odoo import models, fields


class Heading(models.Model):

    _name = 'qc.model.heading'
    _description = 'Modele heading'
    _rec_name = 'heading_code'

    '''Code of Heading'''
    heading_code = fields.Char(string='Heading Code', required=True)

    '''Description of Heading'''
    description = fields.Char(string='Description')


