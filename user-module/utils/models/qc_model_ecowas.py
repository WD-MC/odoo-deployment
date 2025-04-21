from urllib import response

from odoo import models, fields
import qrcode

class Ecowas(models.Model):

    _name = 'qc.model.ecowas'
    _description = 'Model description of ecowas data'
    _order = "heading_id"
    _rec_name = 'commodity_description'

    '''Heading of ecowas record'''
    heading_id = fields.Many2one(comodel_name='qc.model.heading', string='Heading')

    '''TSN of ecowas record'''
    tsn = fields.Char('TSN')

    '''Description commodity of ecowas record'''
    commodity_description = fields.Char('Commodity description', required=True)

    '''Parent commodity of ecowas record'''
    parent_commodity_id = fields.Many2one(string='Parent Commodity', comodel_name='qc.model.ecowas')

    '''Standard Unit of ecowas record'''
    standard_unit = fields.Char('SU Standard Unit')

    '''ID Import Duty of ecowas record'''
    import_duty = fields.Char('ID Import Duty')

    '''ST of ecowas record'''
    st = fields.Char("ST")

    def generate_qr_code(self, txt=''):
        qr_code = qrcode.QRCode(version=4, box_size=4, border=1)
        qr_code.add_data(txt)
        qr_code.make(fit=True)
        qr_img = qr_code.make_image(fill_color="black", backcolor="white")
        qr_img.save("qr_code.png")

        print(qr_img)
        return "qr_code.png"

    def download_licence_pdf(self):
        return self.env.ref('utils.report_qc_model_ecowasss').report_action(self)