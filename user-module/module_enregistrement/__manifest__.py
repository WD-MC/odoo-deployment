# -*- coding: utf-8 -*-
{
    'name': "module_enregistrement",

    'summary': "Module pour la gestion et l'enregistrement des inscriptions",

    'description': """
Ce module fournit des fonctionnalités pour gérer les inscriptions, y compris la création,
la gestion et le suivi des enregistrements d'inscriptions. Il s'intègre avec d'autres modules Odoo 
afin d'améliorer le processus d'inscription
    """,

    'author': "Console NOUMEDEM NGNAM",
    'website': "https://qualisysconsulting.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Operations',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail',  'workflow_management'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/me_enregistrement_view.xml',
        'views/me_menu.xml',
        'data/me_mail_template_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',

}

