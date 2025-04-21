# -*- coding: utf-8 -*-
{
    'name': "utils",

    'summary': """
        This module is used to provide a simple python tools for interacting with another module""",

    'description': """
        This module is used to provide a simple python tools for interacting with another module
    """,

    'author': "Console NOUMEDEM NGNAM",
    'website': "https://qualisysconsulting.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'GFZA SW',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/utils_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/qc_views_ecowas.xml',
        'views/qc_views_heading.xml',
        'views/qc_currency_view.xml',
       # 'views/qc_unit_view.xml',
        'views/qc_views_counter.xml',
        'views/qc_menu_utils.xml',
        'web_report/report_template.xml',
        'web_report/report_deferred_letter.xml',
        'web_report/report_rejected_letter.xml',
        'web_report/report_approval_letter.xml',
        #'views/qc_view_report.xml',
        #'web_report/report.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3'
}
