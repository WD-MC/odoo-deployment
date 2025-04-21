# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from datetime import datetime
from odoo.osv import expression

from datetime import datetime

from odoo.exceptions import  ValidationError


_logger = logging.getLogger(__name__)


class QcApplication(models.Model):
    """ Workflow model description.
    """
    _name = "qc.application"
    _description = "Qc APPLICATION"
    _rec_name = 'name'
    _order = "id"

    name = fields.Char('Application Name', required=True, translate=True)
    description = fields.Char('Description', required=False , translate=True)
    status = fields.Selection([('1', 'Active'), ('2', 'Inactive')], required=True, default='1')



class QcWorkflow(models.Model):
    """ Workflow model description.
    """
    _name = "qc.workflow"
    _description = "Qc WORKFLOW"
    _rec_name = 'name'
    _order = "id"

    name = fields.Char('Workflow Name', required=True, translate=True)
    code = fields.Char('Workflow Code', required=True)
    description = fields.Char('Description', required=False, translate=True)
    status = fields.Selection([('1', 'Active'), ('2', 'Inactive')], required=True, default='1')
    qc_application_id = fields.Many2one('qc.application', string="Application" , required=True)

    def get_workflow(self, code):
        workflow = None
        qc_workflow_env = self.env['qc.workflow']
        qc_workflow_results= qc_workflow_env.search([('code', '=', code)], limit=1)
        if qc_workflow_results :
            for qc_workflow_result in qc_workflow_results :
                 workflow = qc_workflow_result
        return workflow





class QcStage(models.Model):
    """ Model for case stages. This models the main stages of a document
        management flow. Main Qc objects will now use only stages, instead of state and stages.
        Stages are for example used to display the kanban view of records.
    """
    _name = "qc.stage"
    _description = "Qc Stages"
    _rec_name = 'tracking_status'
    _order = "sequence, name, id"

    name = fields.Char('Status Name', required=True, translate=True)  # name or status
    sequence = fields.Integer('Sequence', default=1,required=True, help="Used to order stages.")
    fold = fields.Boolean('Folded in Pipeline',
                          help='This stage is folded in the kanban view when there are no records in that stage to display.')

    code = fields.Char('Code', required=True)
    tracking_status = fields.Char('Status Display Name', required=True, translate=True)
    action = fields.Char('Action', required=False, translate=True)
    final_status = fields.Char('Final status', required=False, translate=True)
    type_workflow = fields.Char('Type Workflow', required=False, translate=True)
    qc_workflow_id = fields.Many2one('qc.workflow', string="Workflow" , required=True)
    status = fields.Selection([('1', 'Active'), ('2', 'Inactive')], required=True, default='1')
    description = fields.Char('Description', required=False, translate=True)

    _sql_constraints = [('code_qc_workflow_id_uniq',
                         'unique (qc_workflow_id,code)',
                         _("stage for this workflow already exists !"))]


    def get_stage_id(self,workflow_id, code):
        stage_id=False
        if workflow_id and  code :
            qc_stage_env = self.env['qc.stage']
            qc_stage_results= qc_stage_env.search(['&', ('qc_workflow_id', '=', workflow_id),('code', '=', code)])
            for qc_stage_result in qc_stage_results :
                stage_id = qc_stage_result.id
        return stage_id






class QcWorkflowApprovalStructure(models.Model):
    """ Workflow Approval Structure
    """
    _name = "qc.workflow.approval.structure"
    _description = "Qc WORKFLOW APPROVAL STRUCTURE"
    _rec_name = 'action_name'
    _order = "id"


    qc_workflow_id = fields.Many2one('qc.workflow', string="Workflow" , required=True)
    qc_current_stage_id = fields.Many2one('qc.stage', string="Workflow Current Status", required=True, domain="[('qc_workflow_id', '=', qc_workflow_id)]")
    #action_name = fields.Char('Action Name', required=True, translate=True)
    action_name = fields.Many2one('qc.workflow.action.list', string="Action Name", required=True, default=1, domain="[('status', '=', '1'),('qc_workflow_id', '=', qc_workflow_id)]" )
    qc_next_stage_id = fields.Many2one('qc.stage', string="Workflow Next Status", required=True , domain="[('qc_workflow_id', '=', qc_workflow_id)]")
    department_id = fields.Many2one('ir.module.category', string="Category name", required=True)
    job_id = fields.Many2one('res.groups', string="Role Name", required=True,   domain="[('category_id', '=', department_id)]")
    type_event = fields.Selection([('1', 'Start Event'), ('2', 'Intermediate Event'),  ('3', 'End Event')], required=True, default='2')

    _sql_constraints = [('qc_workflow_id_qc_current_stage_id_action_name_uniq', 'unique (qc_workflow_id,qc_current_stage_id, action_name)', _("stage and action name for this workflow already exists !"))]

    def get_start_event(self,code):
        stage = None
        qc_workflow = None
        qc_workflow_env = self.env['qc.workflow']
        qc_workflow_results = qc_workflow_env.get_workflow(code)
        for qc_workflow_result in qc_workflow_results :
             qc_workflow = qc_workflow_result

        if qc_workflow :
            qc_workflow_approval_structure_env = self.env['qc.workflow.approval.structure']
            qc_workflow_approval_structure_results= qc_workflow_approval_structure_env.search(['&', ('type_event', '=', '1'),('qc_workflow_id', '=', qc_workflow.id)], limit=1)
            for qc_workflow_approval_structure_result in qc_workflow_approval_structure_results :
                 stage = qc_workflow_approval_structure_result.qc_current_stage_id
        return stage

    def get_start_event_list(self, qc_workflow_id):
        start_events = []
        if qc_workflow_id:
            qc_workflow_approval_structure_env = self.env['qc.workflow.approval.structure']
            qc_workflow_approval_structure_results = qc_workflow_approval_structure_env.search(
                ['&', ('type_event', '=', '1'), ('qc_workflow_id', '=', qc_workflow_id)])
            for qc_workflow_approval_structure_result in qc_workflow_approval_structure_results:
                stage = qc_workflow_approval_structure_result.qc_current_stage_id
                start_events.append(stage.id)
        return start_events

    def get_end_event(self,qc_workflow_id):
        end_events = []
        if qc_workflow_id :
            qc_workflow_approval_structure_env = self.env['qc.workflow.approval.structure']
            qc_workflow_approval_structure_results= qc_workflow_approval_structure_env.search(['&', ('type_event', '=', '3'),('qc_workflow_id', '=', qc_workflow_id)])
            for qc_workflow_approval_structure_result in qc_workflow_approval_structure_results :
                 stage = qc_workflow_approval_structure_result.qc_next_stage_id
                 end_events.append(stage.id)
        return end_events

    def is_end_event(self, stage_event_id, qc_workflow_id):
        return stage_event_id in self.get_end_event(qc_workflow_id)

    def is_start_event(self, stage_event_id, qc_workflow_id):
        return stage_event_id in self.get_start_event_list(qc_workflow_id)

    def get_start_role_list(self, qc_workflow_id):
        start_events = []
        if qc_workflow_id:
            qc_workflow_approval_structure_env = self.env['qc.workflow.approval.structure']
            qc_workflow_approval_structure_results = qc_workflow_approval_structure_env.search(
                ['&', ('type_event', '=', '1'), ('qc_workflow_id', '=', qc_workflow_id)])

            if not qc_workflow_approval_structure_results:
                raise ValidationError(
                    _('Error:There is not start event. Please first initialize the start event for this process'))

            for qc_workflow_approval_structure_result in qc_workflow_approval_structure_results:
                role = qc_workflow_approval_structure_result.job_id
                start_events.append(role)
        return start_events







    def get_action_list(self,current_workflow, current_status):
        action_name_ids = []
        if current_workflow and  current_status :
            qc_workflow_approval_structure_env = self.env['qc.workflow.approval.structure']
            qc_workflow_approval_structure_results= qc_workflow_approval_structure_env.search(['&', ('qc_current_stage_id', '=', current_status),('qc_workflow_id', '=', current_workflow)])
            for qc_workflow_approval_structure_result in qc_workflow_approval_structure_results :
                 action_name_ids.append(qc_workflow_approval_structure_result.action_name.id)
        return action_name_ids

    def get_next_status_event(self, current_workflow, current_status, current_action) :

        next_stage = None
        if current_workflow and current_status and current_action:
            qc_workflow_approval_structure_env = self.env['qc.workflow.approval.structure']
            qc_workflow_approval_structure_results = qc_workflow_approval_structure_env.search(
                ['&',  ('qc_workflow_id', '=', current_workflow) ,  ('qc_current_stage_id', '=', current_status),  ('action_name', '=', current_action)], limit=1)
            for qc_workflow_approval_structure_result in qc_workflow_approval_structure_results:
                next_stage = qc_workflow_approval_structure_result.qc_next_stage_id
        return next_stage


    def get_next_role_event(self, current_workflow, next_status) :

        next_role = None
        if current_workflow and next_status :
            qc_workflow_approval_structure_env = self.env['qc.workflow.approval.structure']
            qc_workflow_approval_structure_results = qc_workflow_approval_structure_env.search(
                ['&',  ('qc_workflow_id', '=', current_workflow) ,  ('qc_current_stage_id', '=', next_status)], limit=1)
            for qc_workflow_approval_structure_result in qc_workflow_approval_structure_results:
                next_role = qc_workflow_approval_structure_result.job_id
        return next_role

    def get_current_role_event(self, current_workflow, current_status) :

        current_role = None
        if current_workflow and current_status :
            qc_workflow_approval_structure_env = self.env['qc.workflow.approval.structure']
            qc_workflow_approval_structure_results = qc_workflow_approval_structure_env.search(
                ['&',  ('qc_workflow_id', '=', current_workflow) ,  ('qc_current_stage_id', '=', current_status)], limit=1)
            for qc_workflow_approval_structure_result in qc_workflow_approval_structure_results:
                current_role = qc_workflow_approval_structure_result.job_id
        return current_role

    def get_current_approval(self, current_workflow, next_status) :
        current_approval = None
        if current_workflow and next_status :
            qc_workflow_approval_structure_env = self.env['qc.workflow.approval.structure']
            qc_workflow_approval_structure_results = qc_workflow_approval_structure_env.search( ['&',  ('qc_workflow_id', '=', current_workflow) ,  ('qc_next_stage_id', '=', next_status)], limit=1)
            for qc_workflow_approval_structure_result in qc_workflow_approval_structure_results:
                current_approval = qc_workflow_approval_structure_result
        return current_approval


    def get_nex_approval(self, current_workflow, next_status) :
        current_approval = None
        if current_workflow and next_status :
            qc_workflow_approval_structure_env = self.env['qc.workflow.approval.structure']
            qc_workflow_approval_structure_results = qc_workflow_approval_structure_env.search( ['&',  ('qc_workflow_id', '=', current_workflow) ,  ('qc_current_stage_id', '=', next_status)], limit=1)
            for qc_workflow_approval_structure_result in qc_workflow_approval_structure_results:
                current_approval = qc_workflow_approval_structure_result
        return current_approval



class QcWorkflowActionList(models.Model):
    """ Workflow model action list.
    """
    _name = "qc.workflow.action.list"
    _description = "Qc WORKFLOW ACTION LIST"
    _rec_name = 'description'
    _order = "id"

    name = fields.Char('Action Name', required=True, translate=True)
    description = fields.Char('Action Display Name', required=True , translate=True)
    status = fields.Selection([('1', 'Active'), ('2', 'Inactive')], required=True, default='1')
    qc_workflow_id = fields.Many2one('qc.workflow', string="Worflow Number", required=True)

    _sql_constraints = [('name_uniq', 'unique (qc_workflow_id,name)', _("Action name already exists !"))]



class QcHrDepartment(models.Model):
    _inherit = 'ir.module.category'
    _description = 'Department Managment'
    code = fields.Char(string='Code', required=False )

class QcHrJob(models.Model):
    _inherit = 'res.groups'
    _description = 'Job Managment'
    code = fields.Char(string='Code', required=False  )



class MessageWizard(models.TransientModel):
    """ Workflow show message.
       """
    _name = 'message.wizard'
    _description = 'message.wizard'

    message = fields.Text('Message', required=True)

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}



class QcCounter(models.Model):
    _name = 'qc.counter'
    _description = 'The Counter'
    _rec_name = 'counter'
    _order = 'id desc'

    qc_workflow_id = fields.Many2one('qc.workflow', string="Worflow Number" , required=True )
    year = fields.Integer(required=True)
    month = fields.Integer(required=True)
    counter = fields.Integer(string='Counter', required=True)


    def get_current_counter(self,qc_workflow_id):

            current_time = datetime.now()
            year = current_time.year
            month = current_time.month

            self._cr.execute(
                'SELECT id, counter FROM qc_counter WHERE qc_workflow_id = %s and year = %s and month= %s LIMIT 1 FOR NO KEY UPDATE ', (qc_workflow_id,year,month))
            result = self._cr.fetchall()
            if result:
                for compter in result:
                    return compter
            else :
                counterModel = self.env['qc.counter']
                newCounter = counterModel.create({
                    'qc_workflow_id': qc_workflow_id,
                    'year': year,
                    'month': month,
                    'counter': 0,

                })
                if newCounter :
                    self._cr.execute(
                        'SELECT id, counter FROM qc_counter WHERE qc_workflow_id = %s and year = %s and month= %s LIMIT 1 FOR NO KEY UPDATE ',
                        (qc_workflow_id, year, month))
                    result = self._cr.fetchall()
                    if result:
                        for compter in result:
                            return compter


    def update_current_counter(self, counter_id, new_counter):

        results_counter = self.env['qc.counter'].search([('id', '=', counter_id)])
        if results_counter:
            results_counter.write({
                'counter': new_counter,
            })

    def get_current_counter_id(self,qc_workflow_id):

            self._cr.execute(
                'SELECT id, counter FROM qc_counter WHERE qc_workflow_id = %s order by id desc LIMIT 1 FOR NO KEY UPDATE ', (qc_workflow_id,))
            result = self._cr.fetchall()
            if result:
                for compter in result:
                    return compter

    class QcRegion(models.Model):
        _name = 'qc.region'
        _description = 'The Region'
        _rec_name = 'name'

        name = fields.Char(string='Name', required=True, translate=True)
        code = fields.Char(string='Code', required=True, translate=True)  # internal code
        description = fields.Text(string='Description', required=False, translate=True)
        _sql_constraints = [('name_uniq', 'unique (name)', _("Region name already exists !")),
                            ('code_uniq', 'unique (code)', _("Region Code already exists !"))]

