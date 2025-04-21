# -*- coding: utf-8 -*-
import logging
from odoo import _, models, fields, api
from datetime import datetime
from odoo.osv import expression
from odoo.exceptions import ValidationError

IN_RECEIVED_STATE = '10003'  # 'In Received'
IN_PROCESS_STATE = '10004'  # 'In process'
IN_COMMITTEE_STATE = '10005'  # 'In committee'
IN_APPROVED_STATE = '10006'  # 'In Approved'
IN_REJECTED_STATE = '10007'  # 'In Rejected'

IN_UNDER_REVIEW_AT_BD_RMA_STATE = '10001'
IN_UNDER_REVIEW_AT_BD_RMA_STATE_DD = '20001'
IN_UNDER_FINAL_APPROVAL_STATE = '10007'  # Final Approval
IN_UNDER_DD_FINAL_APPROVAL_STATE = '20007'

IN_UNDER_CHECK_AMP_VERIFY_RD_SCRA_STATE = '10005'

FINAL_STATUS = [
    ('1', 'N/A'),
    ('2', 'Opened'),
    ('3', 'Closed'),
    ('4', 'Follow-up'),
]

_logger = logging.getLogger(__name__)


class QcMovement(models.Model):
    _name = 'qc.movement'
    _description = 'Qc movement'


    qc_model_workflow_id = fields.Many2one('qc.model.workflow', required=True)
    transmitter_id = fields.Many2one('ir.module.category', string="Transmitter", required=True)
    recipient_id = fields.Many2one('ir.module.category', string="Recipient", required=True)
    job_transmitter_id = fields.Many2one('res.groups', string="Transmitter", required=True,
                                         domain="[('category_id', '=', transmitter_id)]")
    job_recipient_id = fields.Many2one('res.groups', string="Recipient", required=True,
                                       domain="[('category_id', '=', recipient_id)]")

    comments = fields.Html('Instructions/Observations')
    reason_for_cancelled = fields.Html('Reason For Cancelled')

    user_transmitter_id = fields.Integer('res.users')
    date_transmitter = fields.Datetime()

    date_last_modif = fields.Datetime()

    action_name = fields.Many2one('qc.workflow.action.list', string="Action Name", required=False,
                                  domain="[('status', '=', '1')]")

    stage_id = fields.Many2one(
        'qc.stage', string='Current Status'
    )

    next_stage_id = fields.Many2one(
        'qc.stage', string='Next Stage'
    )
    final_status = fields.Selection(FINAL_STATUS, default='1', store=True, string='Final status')
    date_last_modif = fields.Datetime()

    def _default_fullname(self):
        employee_id = self.env.user.employee_id
        return employee_id.name

    # @api.depends('create_uid')
    # def _compute_fullname(self):
    #     """ compute the new values when create_uid has changed """
    #     for movement in self:
    #         fullname = self.create_uid.employee_id.name
    #         movement.fullname = fullname

    #fullname = fields.Char('Comments', related='create_uid.employee_id.name', default=_default_fullname, store=False)

    def is_delete_movement(self, workflow_id):
        qc_movement = self.env['qc.movement']
        results_movement = qc_movement.search([('qc_model_workflow_id', '=', workflow_id)])
        is_delete = len(results_movement) == 1
        for rec in results_movement:
            is_delete = is_delete and rec.job_transmitter_id == rec.job_recipient_id

        return is_delete

    # qc_acceptance_term = fields.One2many('qc.acceptance.term', 'qc_movement_id', string="Description")

    def get_last_movement(self, workflow_id):
        qc_movement = self.env['qc.movement']
        results_movement = qc_movement.search([('qc_model_workflow_id', '=', workflow_id)], order='id desc', limit=1)
        for rec in results_movement:
            return rec

        return False


class QcMovementCancelled(models.Model):
    _name = 'qc.movement.cancelled'
    _description = 'Qc movement cancelled '


    qc_model_workflow_id = fields.Many2one('qc.model.workflow', required=True)
    transmitter_id = fields.Many2one('ir.module.category', string="Transmitter", required=True)
    recipient_id = fields.Many2one('ir.module.category', string="Recipient", required=True)
    job_transmitter_id = fields.Many2one('res.groups', string="Transmitter", required=True,
                                         domain="[('category_id', '=', transmitter_id)]")
    job_recipient_id = fields.Many2one('res.groups', string="Recipient", required=True,
                                       domain="[('category_id', '=', recipient_id)]")
    comments = fields.Html('comments')
    reason_for_cancelled = fields.Html('Reason For Cancelled')

    user_transmitter_id = fields.Integer('res.users')
    date_transmitter = fields.Datetime()

    user_cancel_transmitter = fields.Integer('res.users')
    date_cancel_transmitter = fields.Datetime()


class QcMovementWizard(models.TransientModel):
    _name = 'qc.movement.wizard'
    _description = 'Qc movement wizard '



    # def get_model_data(self):
    #     model_data = False
    #     id = self._context.get('active_id', False)
    #     model = self._context.get('active_model')
    #     if model :
    #         env = self.env[model]
    #         model_data = env.browse(id)
    #     return model_data

    def get_model_data(self):
        """Retrieve the active record from the context."""
        model_data = False
        active_id = self._context.get('active_id', False)
        active_model = self._context.get('active_model')
        if active_model:
            env = self.env[active_model]
            model_data = env.browse(active_id)

        _logger.info("Active ID: %s, Active Model: %s , model_data: %s", active_id, active_model, model_data)

        return model_data

    def _default_model_workflow(self):
       # if self._context.get('active_model') == 'qc.model.workflow':
        model_workflow_id = False
        model_data = self.get_model_data()
        if model_data:
            model_workflow_id = model_data.model_workflow_id.id

        return model_workflow_id

    qc_model_workflow_id = fields.Many2one('qc.model.workflow', default=_default_model_workflow)

    # qc_model_workflow_id = fields.Many2one('qc.model.workflow')

    def _default_Transmitter(self):

        model_data = self.get_model_data()
        if model_data :
            stage_id = model_data.stage_id
            model_workflow_id = model_data.model_workflow_id
            if stage_id  and model_workflow_id :
                role = self.env['qc.workflow.approval.structure'].get_current_role_event(model_workflow_id.qc_workflow_id.id, stage_id.id)
                if role :
                    return role.category_id.id
                else :
                    raise ValidationError(_('current category role not exists: Please contact your administrator.'))



    transmitter_id = fields.Many2one('ir.module.category', string="Transmitter department", default=_default_Transmitter,
                                     readonly=True)

    # recipient_id = fields.Many2one('ir.module.category', string="Receiving department", domain="[('id', '!=', transmitter_id)]")

    @api.model
    def _get_recipient_id(self):
        default_type = self._context.get('default_type_action')
        recipient_ids = []
        departments = []
        qc_model_workflow_env = self.env['qc.model.workflow']

        if default_type == "1":
            departments = qc_model_workflow_env.get_parent_hierarchie_departments_list()
        elif default_type == "2":
            departments = qc_model_workflow_env.get_child_hierarchie_departments_list()
        else:
            departments = self.env['ir.module.category'].sudo().search([])

        for rec in departments:
            recipient_ids.append(rec.id)
        return [('id', 'in', recipient_ids)]

    recipient_id = fields.Many2one('ir.module.category', string="Receiving department", domain=_get_recipient_id)

    def _default_job_Transmitter(self):
        model_data = self.get_model_data()
        if model_data:
            stage_id = model_data.stage_id
            model_workflow_id = model_data.model_workflow_id
            if stage_id and model_workflow_id:
                role = self.env['qc.workflow.approval.structure'].get_current_role_event(model_workflow_id.qc_workflow_id.id, stage_id.id)
                if role:
                    return role.id
                else:
                    raise ValidationError(_('current role not exists: Please contact your administrator.'))

    # job_transmitter_id = fields.Many2one('res.groups', string="Transmitter station", domain="[('category_id', '=', transmitter_id)]" , default=_default_job_Transmitter,  compute='_compute_job_transmitter_id')

    job_transmitter_id = fields.Many2one('res.groups', string="Transmitter station",
                                         domain="[('category_id', '=', transmitter_id)]",
                                         default=_default_job_Transmitter, readonly=True)
    job_recipient_id = fields.Many2one('res.groups', string="Receiver station",
                                       domain="['&',('category_id', '=', recipient_id),('id', '!=', job_transmitter_id)]",
                                       compute='_compute_job_recipient_id', readonly=False, store=True)
    # job_recipient_id = fields.Many2one('res.groups', string="Receiver station", domain="[('category_id', '=', recipient_id)]" ,  compute='_compute_job_recipient_id' , readonly=False, store=True)
    # job_recipient_id = fields.Many2one('res.groups', string="Receiver station",domain="[('category_id', '=', recipient_id)]" )
    comments = fields.Html('comments/Remarks')
    reason_for_cancelled = fields.Html('Reason For Cancelled')

    user_transmitter_id = fields.Integer('res.users')
    date_transmitter = fields.Datetime()
    user_cancel_transmitter = fields.Integer('res.users')
    date_cancel_transmitter = fields.Datetime()

    def _default_stage_id(self):
        default_stage_id = None
        model_data = self.get_model_data()
        if model_data:
            qc_model_workflow_id = model_data.model_workflow_id.id

            if qc_model_workflow_id:
                qc_model_workflow = self.env['qc.model.workflow'].browse(qc_model_workflow_id)
                default_stage_id = qc_model_workflow.stage_id.id
            self.next_stage_id = default_stage_id
        return default_stage_id

    stage_id = fields.Many2one(
        'qc.stage', string='Current Status', default=_default_stage_id
    )

    next_stage_id = fields.Many2one(
        'qc.stage', string='Next Stage'
    )

    final_status = fields.Selection(FINAL_STATUS, default='1', store=True, string='Final status')



    # action_name = fields.Many2one('qc.workflow.action.list', string="Select Action")
    #
    # @api.onchange('action_name')
    # def _onchange_action_name(self):
    #     model_data = self.get_model_data()
    #     action_name_ids = []
    #     if model_data:
    #         qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
    #         action_name_ids = qc_workflow_approval_structure.get_action_list(
    #             model_data.model_workflow_id.qc_workflow_id.id,
    #             model_data.model_workflow_id.stage_id.id
    #         )
    #     return {
    #         'domain': {'action_name': [('id', 'in', action_name_ids)]}
    #     }

    # action_name = fields.Many2one(
    #     'qc.workflow.action.list',
    #     string="Select Action",
    #     required=False,
    #     domain=lambda self: self._compute_action_domain()
    # )
    #
    # def _compute_action_domain(self):
    #     """Return a domain for the action_name field."""
    #     action_ids = self.get_action_ids()
    #     _logger.info("Computed action domain: %s", action_ids)
    #     return [('id', 'in', action_ids)]
    #
    # @api.model
    # def get_action_ids(self):
    #     """Compute a list of action IDs dynamically."""
    #     some_action_ids = []
    #
    #     # Retrieve active_id and active_model from the context
    #     active_id = self.env.context.get('active_id')
    #     active_model = self.env.context.get('active_model')
    #
    #     _logger.info("Context: active_id=%s, active_model=%s", active_id, active_model)
    #
    #     if active_id and active_model:
    #         model_record = self.env[active_model].browse(active_id)
    #
    #         if model_record.exists() and model_record.model_workflow_id:
    #             workflow_id = model_record.model_workflow_id.qc_workflow_id.id
    #             stage_id = model_record.model_workflow_id.stage_id.id
    #
    #             qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
    #             some_action_ids = qc_workflow_approval_structure.get_action_list(workflow_id, stage_id)
    #
    #             _logger.info("Workflow ID: %s, Stage ID: %s", workflow_id, stage_id)
    #             _logger.info("Computed action IDs: %s", some_action_ids)
    #         else:
    #             _logger.warning("Model record or workflow ID not found.")
    #     else:
    #         _logger.warning("Active ID or Active Model missing in context.")
    #
    #     return some_action_ids

    # @api.model
    # def get_action_ids(self):
    #     """Return a hardcoded list of action IDs for testing."""
    #     some_action_ids = [1, 2, 3]  # Replace with valid IDs from your database
    #     return some_action_ids

    # action_name = fields.Many2one(
    #     'qc.workflow.action.list',
    #     string="Select Action",
    #     required=False
    # )
    #
    # @api.model
    # def default_get(self, fields):
    #     res = super().default_get(fields)
    #     active_id = self.env.context.get('active_id')
    #     active_model = self.env.context.get('active_model')
    #     _logger.info("record found for model %s with ID %s", active_model, active_id)
    #     if active_id and active_model:
    #         record = self.env[active_model].browse(active_id)
    #         if record:
    #             qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
    #             action_name_ids = qc_workflow_approval_structure.get_action_list(
    #                 record.model_workflow_id.qc_workflow_id.id,
    #                 record.model_workflow_id.stage_id.id
    #             )
    #             _logger.info("action_name_ids %s ", action_name_ids)
    #             res['action_name_domain'] = [('id', 'in', action_name_ids)]
    #     return res


    @api.depends('stage_id')
    def _compute_action_domain(self):
        for record in self:
            action_name_ids = []
            if record.stage_id:
                active_id = self.env.context.get('active_id')
                active_model = self.env.context.get('active_model')
                if active_model and active_id:
                    obj = self.env[active_model].browse(active_id)
                    if obj and obj.model_workflow_id:
                        action_name_ids = self.env['qc.workflow.approval.structure'].get_action_list(
                            obj.model_workflow_id.qc_workflow_id.id,
                            obj.model_workflow_id.stage_id.id
                        )
            record.action_domain = [('id', 'in', action_name_ids)]

    action_name = fields.Many2one('qc.workflow.action.list', string="Select Action")
    action_domain = fields.Char(compute="_compute_action_domain", store=False)


    # @api.onchange('stage_id')  # Replace with the relevant field triggering the change
    # def _onchange_some_related_field(self):
    #     """Compute domain dynamically."""
    #     active_id = self.env.context.get('active_id')
    #     active_model = self.env.context.get('active_model')
    #     _logger.info("record found for model %s with ID %s", active_model, active_id)
    #
    #     action_name_ids = []
    #
    #     if active_model and active_id:
    #         record = self.env[active_model].browse(active_id)
    #         if record:
    #             qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
    #             action_name_ids = qc_workflow_approval_structure.get_action_list(
    #                 record.model_workflow_id.qc_workflow_id.id,
    #                 record.model_workflow_id.stage_id.id
    #             )
    #     _logger.info("action_name_ids %s ", action_name_ids)
    #
    #     self.update({
    #         'action_name': False,  # Clear current value
    #     })
    #
    #     return {
    #         'domain': {
    #             'action_name': [('id', 'in', action_name_ids)]
    #         }
    #     }

    #
    # @api.onchange('stage_id', 'action_name')
    # def _onchange_action_name(self):
    #     if self.stage_id:
    #         model_data = self.get_model_data()
    #         action_name_ids = []
    #         if model_data:
    #             qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
    #             action_name_ids = qc_workflow_approval_structure.get_action_list(
    #                 model_data.model_workflow_id.qc_workflow_id.id,
    #                 model_data.model_workflow_id.stage_id.id
    #             )
    #         # Fallback to an empty list if no valid IDs are found
    #         return {
    #             'domain': {'action_name': []}
    #         }
    #         return {
    #             'domain': {'action_name': [('id', 'in', action_name_ids or [])]}
    #         }
    #     else:
    #         # No stage selected, reset the domain
    #         return {
    #             'domain': {'action_name': []}
    #         }

    # @api.onchange('stage_id', 'action_name')
    # def stage_id_or_action_name_or_next_stage_id_onchange(self):
    #     qc_workflow_id = None
    #     stage_id = None
    #     qc_model_workflow_id = self._context.get('active_id') if self._context.get(
    #         'active_model') == 'qc.model.workflow' else None
    #
    #     if not qc_model_workflow_id:
    #         model_data = self.get_model_data()
    #         if model_data:
    #             stage_id = model_data.stage_id.id
    #             qc_model_workflow_id = model_data.model_workflow_id.id
    #
    #     if qc_model_workflow_id:
    #         qc_model_workflow = self.env['qc.model.workflow'].browse(qc_model_workflow_id)
    #         qc_workflow_id = qc_model_workflow.qc_workflow_id.id
    #         stage_id = qc_model_workflow.stage_id.id
    #
    #     if qc_workflow_id and stage_id:
    #         qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
    #         action_name_ids = qc_workflow_approval_structure.get_action_list(qc_workflow_id, stage_id)
    #         #if action_name_ids and not self.action_name:
    #         if action_name_ids :
    #             self.action_name = self.env['qc.workflow.action.list'].browse(action_name_ids[0])
    #
    #         next_status_events = qc_workflow_approval_structure.get_next_status_event(qc_workflow_id, stage_id,
    #                                                                                   self.action_name.id)
    #         if next_status_events:
    #             next_stage = next_status_events[0]
    #             self.next_stage_id = next_stage.id
    #             if qc_workflow_approval_structure.is_end_event(next_stage.id, qc_workflow_id):
    #                 self.recipient_id = self.transmitter_id
    #                 self.job_recipient_id = self.job_transmitter_id
    #             else:
    #                 next_roles = qc_workflow_approval_structure.get_next_role_event(qc_workflow_id, next_stage.id)
    #                 if next_roles:
    #                     self.recipient_id = next_roles[0].category_id.id
    #                     self.job_recipient_id = next_roles[0].id
    #
    #     return {
    #         'value': {
    #             'next_stage_id': self.next_stage_id,
    #             'recipient_id': self.recipient_id,
    #             'job_recipient_id': self.job_recipient_id,
    #             'action_name': self.action_name,
    #         }
    #     }

    @api.onchange('stage_id', 'action_name')
    def stage_id_or_action_name_or_next_stage_id_onchange(self):
        qc_model_workflow_id = self._context.get('active_id') if self._context.get(
            'active_model') == 'qc.model.workflow' else None

        if not qc_model_workflow_id:
            model_data = self.get_model_data()
            if not model_data:
                return
            qc_model_workflow_id = model_data.model_workflow_id.id

        qc_model_workflow = self.env['qc.model.workflow'].browse(qc_model_workflow_id)
        qc_workflow_id = qc_model_workflow.qc_workflow_id.id
        stage_id = qc_model_workflow.stage_id.id

        if not (qc_workflow_id and stage_id):
            return

        structure = self.env['qc.workflow.approval.structure']
        action_ids = structure.get_action_list(qc_workflow_id, stage_id)
        if action_ids:
            if not self.action_name  or self.action_name.id not in action_ids:
                self.action_name = self.env['qc.workflow.action.list'].browse(action_ids[0])

        next_events = structure.get_next_status_event(qc_workflow_id, stage_id, self.action_name.id)
        if not next_events:
            return

        next_stage = next_events[0]
        self.next_stage_id = next_stage.id

        if structure.is_end_event(next_stage.id, qc_workflow_id):
            self.recipient_id = self.transmitter_id
            self.job_recipient_id = self.job_transmitter_id
        else:
            next_roles = structure.get_next_role_event(qc_workflow_id, next_stage.id)
            if next_roles:
                self.recipient_id = next_roles[0].category_id.id
                self.job_recipient_id = next_roles[0].id

    # @api.model
    # def _get_action_name_list(self):
    #
    #     action_name_ids = []
    #     # qc_model_workflow_id = None
    #     model_data = self.get_model_data()
    #     if model_data:
    #         # qc_model_workflow_id = model_data.model_workflow_id.id
    #         qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
    #         action_name_ids = qc_workflow_approval_structure.get_action_list(
    #             model_data.model_workflow_id.qc_workflow_id.id,
    #             model_data.model_workflow_id.stage_id.id)
    #     return [('id', 'in', action_name_ids)]
    #
    # action_name = fields.Many2one('qc.workflow.action.list', string="Select Action", required=False,
    #                               domain=_get_action_name_list)
    #
    # @api.onchange('stage_id', 'action_name')
    # def stage_id_or_action_name_or_next_stage_id_onchange(self):
    #
    #     qc_model_workflow_id = None
    #     qc_workflow_id = None
    #     if self._context.get('active_model') == 'qc.model.workflow':
    #         qc_model_workflow_id = self._context.get('active_id', False)
    #     else:
    #         model_data = self.get_model_data()
    #         if model_data:
    #             stage_id = model_data.stage_id.id
    #             qc_model_workflow_id = model_data.model_workflow_id.id
    #     if qc_model_workflow_id:
    #         qc_model_workflow = self.env['qc.model.workflow'].browse(qc_model_workflow_id)
    #         qc_workflow_id = qc_model_workflow.qc_workflow_id.id
    #         stage_id = qc_model_workflow.stage_id.id
    #     if qc_workflow_id and stage_id:
    #         qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
    #         if not self.action_name:
    #             action_name_ids = qc_workflow_approval_structure.get_action_list(qc_workflow_id, stage_id)
    #             if action_name_ids and action_name_ids[0]:
    #                 self.action_name = self.env['qc.workflow.action.list'].browse(action_name_ids[0])
    #         qc_workflow_approval_structure_results = qc_workflow_approval_structure.get_next_status_event(
    #             qc_workflow_id, stage_id, self.action_name.id)
    #         if qc_workflow_approval_structure_results:
    #             for qc_workflow_approval_structure_result in qc_workflow_approval_structure_results:
    #                 self.next_stage_id = qc_workflow_approval_structure_result.id
    #                 if qc_workflow_approval_structure.is_end_event(qc_workflow_approval_structure_result.id,
    #                                                                  qc_workflow_id):
    #                     self.recipient_id = self.transmitter_id
    #                     self.job_recipient_id = self.job_transmitter_id
    #                 else:
    #                     qc_workflow_approval_structure_roles_results = qc_workflow_approval_structure.get_next_role_event(
    #                         qc_workflow_id, qc_workflow_approval_structure_result.id)
    #                     if qc_workflow_approval_structure_roles_results:
    #                         for qc_workflow_approval_structure_roles_result in qc_workflow_approval_structure_roles_results:
    #                             self.recipient_id = qc_workflow_approval_structure_roles_result.category_id.id
    #                             self.job_recipient_id = qc_workflow_approval_structure_roles_result.id

        #return self.init_qc_acceptance_term_data()

    stage_code = fields.Char(string='Code', related='stage_id.code', readonly=True)

    def add_qc_movement(self):
        '''Transmission action'''

        current_time = datetime.now()

        movementModel = self.env['qc.movement']
        workflowModel = self.env['qc.model.workflow']
        for movement in self:
            results_workflow = workflowModel.search([('id', '=', movement.qc_model_workflow_id.id)])

            check_position = workflowModel.get_position(results_workflow)

            if check_position == False:
                raise ValidationError(_('Transmission not possible: Please contact your administrator.'))
            newmovement = movementModel.create({
                'qc_model_workflow_id': movement.qc_model_workflow_id.id,
                'transmitter_id': movement.transmitter_id.id,
                'recipient_id': movement.recipient_id.id,
                'job_transmitter_id': movement.job_transmitter_id.id,
                'job_recipient_id': movement.job_recipient_id.id,
                'comments': movement.comments,
                'user_transmitter_id': self._uid,
                'date_transmitter': current_time,
                'date_last_modif': current_time,
                'action_name': movement.action_name.id,
                'stage_id': movement.stage_id.id,
                'next_stage_id': movement.next_stage_id.id,
                'final_status': movement.final_status,

            })

            active_id = self._context.get('active_id', False)
            active_model = self._context.get('active_model')
            if active_model and active_id:
                env = self.env[active_model]
                rec = env.browse(active_id)
                _logger.info("Active ID: %s, Active Model: %s", active_id, active_model)
                self.env['qc.model.mail'].send_odoo_and_email_notification(rec, movement.job_recipient_id.id, movement.comments)

            # Send notification to recipients


            # if movement.stage_id.code == IN_UNDER_REVIEW_AT_BD_RMA_STATE or movement.stage_id.code == IN_UNDER_REVIEW_AT_BD_RMA_STATE_DD:
            #
            #     qc_acceptance_term = []
            #
            #     if newmovement:
            #
            #         for rec in movement.qc_acceptance_term:
            #             if rec.check != True:
            #                 raise ValidationError(
            #                     _('Please validate qc Acceptance Term before move to the next stage.'))
            #             if rec:
            #                 value = {
            #                     'description_id': rec.description_id.id,
            #                     'check': rec.check,
            #                     'comments': rec.comments,
            #                     'qc_model_workflow_id': movement.qc_model_workflow_id.id,
            #
            #                 }
            #                 qc_acceptance_term.append((0, 0, value))
            #
            #         results_workflow.write({
            #             'last_movement_id': newmovement.id,
            #             'stage_id': movement.next_stage_id.id,
            #             'position_id': movement.job_recipient_id.id,
            #             'date_last_modif': current_time,
            #             'role_id': movement.job_recipient_id.id,
            #             'qc_acceptance_term': qc_acceptance_term
            #         })
            # else:

            if newmovement:
                results_workflow.write({
                    'last_movement_id': newmovement.id,
                    'stage_id': movement.next_stage_id.id,
                    'position_id': movement.job_recipient_id.id,
                    'date_last_modif': current_time,
                    'role_id': movement.job_recipient_id.id,
                })

        #self.update_imis()
        # callback method
        model_data = self.get_model_data()
        if model_data:
            model_data.write({})

        message = _("Action performed successfully")

        message_id = self.env['message.wizard'].create({'message': message})

        return {
            'name': _('Successfully'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.wizard',
            # pass the id
            'res_id': message_id.id,
            'target': 'new'
        }

    def move_to_next(self, workflow_id, category_transmitter_id , category_recipient_id, transmitter_id, recipient_id,comments,action_id,current_stage_id,next_stage_id,final_status):
        '''Transmission action'''
        success = False
        current_time = datetime.now()

        movementModel = self.env['qc.movement']
        workflowModel = self.env['qc.model.workflow']
        results_workflow = workflowModel.search([('portal','=', True), ('id', '=', workflow_id)])

        # check_position = workflowModel.get_position(results_workflow)
        #
        # if check_position == False:
        #     raise ValidationError(_('Transmission not possible: Please contact your administrator.'))
        newmovement = movementModel.create({
            'qc_model_workflow_id':workflow_id,
            'transmitter_id': category_transmitter_id,
            'recipient_id': category_recipient_id,
            'job_transmitter_id': transmitter_id,
            'job_recipient_id': recipient_id,
            'comments': comments,
            'user_transmitter_id': self._uid,
            'date_transmitter': current_time,
            'date_last_modif': current_time,
            'action_name': action_id,
            'stage_id': current_stage_id,
            'next_stage_id': next_stage_id,
            'final_status': final_status

        })

        # Send notification to recipients
        active_id = self._context.get('active_id', False)
        active_model = self._context.get('active_model')
        if active_model and active_id:
            env = self.env[active_model]
            rec = env.browse(active_id)
            _logger.info("Active ID: %s, Active Model: %s", active_id, active_model)
            self.env['qc.model.mail'].send_odoo_and_email_notification(rec,recipient_id, comments)


        if newmovement:
            results_workflow.write({
                'last_movement_id': newmovement.id,
                'stage_id': next_stage_id,
                'position_id': recipient_id,
                'date_last_modif': current_time,
                'role_id': recipient_id,
            })
            success = True


        return success



    def update_imis(self):
        crmModel = self.env['crm.lead']
        crmModelCategorization = self.env['agf.categorization']
        for movement in self:
            if movement.next_stage_id.code == IN_UNDER_FINAL_APPROVAL_STATE:
                results_crm = crmModel.search([('id', '=', movement.qc_model_workflow_id.opportunity_id.id)])
                results_crm.write({
                    'country_qc': movement.qc_model_workflow_id.qc_models_simulation.weighted_product_score,
                    'borrow_qc': movement.qc_model_workflow_id.qc_models_simulation.weighted_product_score_lender,
                    'transaction_qc': movement.qc_model_workflow_id.qc_models_simulation.weighted_product_score_borrower,
                    'lender_qc': movement.qc_model_workflow_id.qc_models_simulation.weighted_product_score_transaction,
                    'guarantee_tenor': movement.qc_model_workflow_id.qc_models_simulation.period_id.period,
                    'warf': movement.qc_model_workflow_id.qc_models_simulation.sum_weighted_product_score,
                    'qc_currency': movement.qc_model_workflow_id.qc_models_simulation.facility_currency.name,
                    'raac_validation': 'pass',
                })
            elif movement.next_stage_id.code == IN_UNDER_DD_FINAL_APPROVAL_STATE:
                results_crm = crmModel.search([('id', '=', movement.qc_model_workflow_id.opportunity_id.id)])
                results_crm.write({
                    'country_qc': movement.qc_model_workflow_id.qc_models_simulation.weighted_product_score,
                    'borrow_qc': movement.qc_model_workflow_id.qc_models_simulation.weighted_product_score_lender,
                    'transaction_qc': movement.qc_model_workflow_id.qc_models_simulation.weighted_product_score_borrower,
                    'lender_qc': movement.qc_model_workflow_id.qc_models_simulation.weighted_product_score_transaction,
                    'guarantee_tenor': movement.qc_model_workflow_id.qc_models_simulation.period_id.period,
                    'warf': movement.qc_model_workflow_id.qc_models_simulation.sum_weighted_product_score,
                    'qc_currency': movement.qc_model_workflow_id.qc_models_simulation.facility_currency.name,
                    'dd_validation': 'pass',
                })

            elif movement.next_stage_id.code == IN_UNDER_CHECK_AMP_VERIFY_RD_SCRA_STATE:
                crmModelqcEAndSCategorization = self.env['qc.e.and.s.categorization']
                crmModelqcSummaryOfMainTaskRequiredForDD = self.env['qc.summary.of.main.task.required.for.dd']

                results_crmModelqcEAndSCategorization1 = crmModelqcEAndSCategorization.search(
                    ['&', ('qc_model_workflow_id', '=', movement.qc_model_workflow_id.id),
                     ('check_category_name', '=', True)])
                results_crmModelqcEAndSCategorization2 = crmModelqcEAndSCategorization.search(
                    ['&', ('qc_model_workflow_id', '=', movement.qc_model_workflow_id.id),
                     ('check_associated_dd_category_name', '=', True)])
                results_crmModelqcSummaryOfMainTaskRequiredForDD = crmModelqcSummaryOfMainTaskRequiredForDD.search(
                    ['&', ('qc_model_workflow_id', '=', movement.qc_model_workflow_id.id), ('check', '=', True)])

                es_category = ''
                es_due_dilligence = ''
                summary_of_tasks = ''

                for rec in results_crmModelqcEAndSCategorization1:
                    if not es_category:
                        es_category = rec.category_name_id.category_name
                    else:
                        es_category = es_category + ',' + rec.category_name_id.category_name

                for rec in results_crmModelqcEAndSCategorization2:
                    if not es_due_dilligence:
                        es_due_dilligence = rec.associated_dd_category_name
                    else:
                        es_due_dilligence = es_due_dilligence + ',' + rec.associated_dd_category_name

                for rec in results_crmModelqcSummaryOfMainTaskRequiredForDD:
                    if not summary_of_tasks:
                        summary_of_tasks = rec.name_id.name
                    else:
                        summary_of_tasks = summary_of_tasks + ',' + rec.name_id.name

                results_crm = crmModelCategorization.search(
                    [('id', '=', movement.qc_model_workflow_id.agf_screening_id.id)])
                results_crm.write({
                    'executed_by': movement.qc_model_workflow_id.executed_by,
                    'executed_date': movement.qc_model_workflow_id.es_date,
                    'product_type': movement.qc_model_workflow_id.product_type.name,
                    'category': movement.qc_model_workflow_id.category.name,
                    'es_category': es_category,
                    'es_due_dilligence': es_due_dilligence,
                    # 'summary_of_tasks': summary_of_tasks,
                    'summary_of_tasks': 'Support From E&S specialists,Documentation Review,Site visit',
                    'comments': movement.qc_model_workflow_id.comments,

                })

    def reset_qc_movement(self):
        '''Action to reset movement.'''

        now = datetime.now()

        movementModel = self.env['qc.movement']
        movementAnnulModel = self.env['qc.movement.cancelled']
        workflowModel = self.env['qc.model.workflow']
        for movement in self:

            results_workflow = workflowModel.search([('id', '=', movement.qc_model_workflow_id.id)])

            check_position = workflowModel.get_cancel_position(results_workflow)

            if check_position == False:
                raise ValidationError(_('Cancel Emission not possible: Please contact your administrator.'))

            if results_workflow:
                results_movement = movementModel.search([('id', '=', results_workflow.last_movement_id.id)])
                if results_movement:
                    newmovement = movementAnnulModel.create({
                        'qc_model_workflow_id': results_movement.qc_model_workflow_id.id,
                        'transmitter_id': results_movement.transmitter_id.id,
                        'recipient_id': results_movement.recipient_id.id,
                        'job_transmitter_id': results_movement.job_transmitter_id.id,
                        'job_recipient_id': results_movement.job_recipient_id.id,
                        'comments': results_movement.comments,
                        'user_transmitter_id': self._uid,
                        'date_transmitter': datetime.now(),
                        'user_cancel_transmitter': self._uid,
                        'date_cancel_transmitter': now,
                        'reason_for_cancelled': movement.reason_for_cancelled,
                    })

                    # Send notification to recipients
                    active_id = self._context.get('active_id', False)
                    active_model = self._context.get('active_model')
                    if active_model and active_id:
                        env = self.env[active_model]
                        rec = env.browse(active_id)
                        _logger.info("Active ID: %s, Active Model: %s", active_id, active_model)
                        self.env['qc.model.mail'].send_odoo_and_email_notification(rec, results_movement.job_recipient_id.id, results_movement.comments)

                    results_workflow.write({
                        'stage_id': results_movement.stage_id.id,
                        'position_id':  results_movement.job_transmitter_id.id,
                        'date_last_modif': now,
                        'role_id':  results_movement.job_transmitter_id.id,
                    })
                    results_movement.unlink()

                    # callback method
                    model_data = self.get_model_data()
                    if model_data:
                        model_data.write({})

    def return_qc_movement(self):
        '''Return action'''

        current_time = datetime.now()

        movementModel = self.env['qc.movement']
        workflowModel = self.env['qc.model.workflow']
        for movement in self:
            results_workflow = workflowModel.search([('id', '=', movement.qc_model_workflow_id.id)])

            check_position = workflowModel.get_position(results_workflow)

            if check_position == False:
                raise ValidationError(_('Transmission not possible: Please contact your administrator.'))

            if results_workflow:
                for rec in results_workflow:
                    stage_id = rec.stage_id.id
                    qc_workflow_id = rec.qc_workflow_id.id

                    qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']

                    current_approval = qc_workflow_approval_structure.get_current_approval(qc_workflow_id, stage_id)

                    newmovement = movementModel.create({
                        'qc_model_workflow_id': rec.id,
                        'transmitter_id': movement.transmitter_id.id,
                        'recipient_id': current_approval.department_id.id,
                        'job_transmitter_id': movement.job_transmitter_id.id,
                        'job_recipient_id': current_approval.job_id.id,
                        'comments': movement.comments,
                        'user_transmitter_id': self._uid,
                        'date_transmitter': current_time,
                        'date_last_modif': current_time,
                        # 'action_name': movement.action_name.id,
                        'stage_id': stage_id,
                        'next_stage_id': current_approval.qc_current_stage_id.id,
                        'final_status': movement.final_status,

                    })

                    active_id = self._context.get('active_id', False)
                    active_model = self._context.get('active_model')
                    if active_model and active_id:
                        env = self.env[active_model]
                        rec = env.browse(active_id)
                        _logger.info("Active ID: %s, Active Model: %s", active_id, active_model)
                        self.env['qc.model.mail'].send_odoo_and_email_notification(rec, current_approval.job_id.id,
                                                          movement.comments)

                    if newmovement:
                        results_workflow.write({
                            'last_movement_id': newmovement.id,
                            'stage_id': current_approval.qc_current_stage_id.id,
                            'position_id': current_approval.job_id.id,
                            'date_last_modif': current_time,
                            'role_id': current_approval.job_id.id,
                        })

                # callback method
                model_data = self.get_model_data()
                if model_data:
                    model_data.write({})

                message = _("Action performed successfully")

                message_id = self.env['message.wizard'].create({'message': message})
                return {
                    'name': _('Successfull'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'message.wizard',
                    # pass the id
                    'res_id': message_id.id,
                    'target': 'new'
                }

    @api.depends('recipient_id')
    def _compute_job_recipient_id(self):
        """ compute the new values when recipient_id has changed """
        for movement in self:
            if self.recipient_id.id:
                res = self.env['res.groups'].search(
                    ['&', ('category_id', '=', self.recipient_id.id), ('id', '!=', self.job_transmitter_id.id)],
                    limit=1)
                if res and res[0]:
                    movement.job_recipient_id = res[0]
                else:
                    movement.job_recipient_id = False

    def _get_default_stage_id(self):
        Stage = self.env['qc.stage']
        return Stage.search([('code', '=', IN_PROCESS_STATE)], limit=1)

    #qc_acceptance_term = fields.One2many('qc.acceptance.term.transient', 'qc_movement_id', string="Description")

    # @api.onchange('final_status')
    # def  init_qc_acceptance_term_data_onchange(self):
    #     return self.init_qc_acceptance_term_data()
    def init_qc_acceptance_term_data(self):

        ligne_qc_acceptance_term_ids = []

        for rec in self:
            rec.write({'qc_acceptance_term': [(5, 0, 0)]})

        query_model = self.env['qc.param.acceptance.term']
        query_model_results = query_model.search([('status', '=', '1')])
        for rec in query_model_results:
            if rec:
                value = {
                    'description_id': rec.id,

                }
                ligne_qc_acceptance_term_ids.append((0, 0, value))

        return {'value': {
            'qc_acceptance_term': ligne_qc_acceptance_term_ids,
        }
        }




