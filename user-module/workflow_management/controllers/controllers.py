# -*- coding: utf-8 -*-
# from odoo import http


# class WorkflowManagement(http.Controller):
#     @http.route('/workflow_management/workflow_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/workflow_management/workflow_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('workflow_management.listing', {
#             'root': '/workflow_management/workflow_management',
#             'objects': http.request.env['workflow_management.workflow_management'].search([]),
#         })

#     @http.route('/workflow_management/workflow_management/objects/<model("workflow_management.workflow_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('workflow_management.object', {
#             'object': obj
#         })
