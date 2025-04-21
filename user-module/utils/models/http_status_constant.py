from odoo import _, models, fields, api , SUPERUSER_ID



class http_status_constant(models.TransientModel):
    _name = 'am.http.status.constant'

    HTTP_CREATED = {'code':201,'message':'Created' }
    HTTP_INTERNAL_SERVER_ERROR = {'code':500,'message':'Internal server error' }
