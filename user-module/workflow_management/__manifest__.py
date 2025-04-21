# -*- coding: utf-8 -*-
{
    'name': "workflow_management",

    'summary': """
        workflow module is a factories of consistent, repeatable set of activities within the enterprise""",

    'description': """
        Workflow management module have the goal of creating, documenting, monitoring and improving upon the series of steps, or workflow, 
        that is required to complete a specific task. The aim of workflow management is to optimize the steps in the workflow to ensure 
        the task is completed correctly, consistently and efficiently.
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
        'security/wm_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/qc_view_workflow_movement.xml',
        'views/qc_view_workflow_base.xml',
        'views/qc_menu_workflow.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
