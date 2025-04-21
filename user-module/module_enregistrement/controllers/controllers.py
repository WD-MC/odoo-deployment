# -*- coding: utf-8 -*-
# from odoo import http


# class ModuleEnregistrement(http.Controller):
#     @http.route('/module_enregistrement/module_enregistrement', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/module_enregistrement/module_enregistrement/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('module_enregistrement.listing', {
#             'root': '/module_enregistrement/module_enregistrement',
#             'objects': http.request.env['module_enregistrement.module_enregistrement'].search([]),
#         })

#     @http.route('/module_enregistrement/module_enregistrement/objects/<model("module_enregistrement.module_enregistrement"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('module_enregistrement.object', {
#             'object': obj
#         })

