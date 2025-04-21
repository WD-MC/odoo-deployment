import logging
from typing import List, Tuple

from odoo import _, models, fields, api,SUPERUSER_ID
from datetime import datetime
from odoo.osv import expression

#from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
from odoo.exceptions import ValidationError
_REGISTRATION_CONTEXT ="01"

_logger = logging.getLogger(__name__)

IN_PFI_DOCUMENT_UPLOADED_STATE = '10000'  # 'In Assessment Initiation'
NON_APPLICABLE = 'N/A'
APPLICATION_PREFIXE_NUMBER = 'PR'
LEFT_PADDING_CHARACTER = '0'
TOTAL_CHARACTER = 4
NBR_YEAR = 20
IN_UNDER_REVIEW_AT_BD_RMA_STATE = '10001'
IN_UNDER_REVIEW_AT_BD_RMA_STATE_DD = '20001'

IN_UNDER_CHECK_AND_VERIFY_RD_SCRA = '10004'

IN_UNDER_FINAL_APPROVAL_STATE = '10007'


class QcModelWorkflow(models.Model):
    _name = 'qc.model.workflow'
    _description = 'Qc Engine Workflow '
    _rec_name = 'model_application_number'
    _order = 'model_application_number desc, id desc'

    _inherit = ['mail.thread.cc',
                'mail.thread.blacklist',
                'mail.activity.mixin',
                'format.address.mixin',
                ]

    _primary_email = 'email_from'

    _sql_constraints = [
        ('model_name_uniq', 'UNIQUE(model_application_number,qc_workflow_id)',
         'This application number already exist. Please contact your administrator')
    ]

    model_application_number = fields.Char(string='Application N°', required=True, default='1')
    model_workflow_description = fields.Text(string='Model Workflow Description')
    status = fields.Selection([('1', 'Active'), ('2', 'Inactive')], required=True, default='1')

    email_from = fields.Char(
        'Email', tracking=40, index=True, readonly=False, store=True)

    # email_from = fields.Char(
    #     'Email', tracking=40, index=True,
    #     compute='_compute_email_from', inverse='_inverse_email_from', readonly=False, store=True)
    #
    # @api.depends('partner_id.email')
    # def _compute_email_from(self):Store
    #     for lead in self:
    #         if lead.partner_id.email and lead._get_partner_email_update():
    #             lead.email_from = lead.partner_id.email
    #
    # def _inverse_email_from(self):
    #     for lead in self:
    #         if lead._get_partner_email_update():
    #             lead.partner_id.email = lead.email_from

    phone = fields.Char('Phone', tracking=50, readonly=False, store=True)

    # phone = fields.Char(
    #     'Phone', tracking=50,
    #     compute='_compute_phone', inverse='_inverse_phone', readonly=False, store=True)
    #
    # @api.depends('partner_id.phone')
    # def _compute_phone(self):
    #     for lead in self:
    #         if lead.partner_id.phone and lead._get_partner_phone_update():
    #             lead.phone = lead.partner_id.phone
    #
    # def _inverse_phone(self):
    #     for lead in self:
    #         if lead._get_partner_phone_update():
    #             lead.partner_id.phone = lead.phone

    def _default_stage_id(self):
        default_qc_workflow = self._context.get('default_type_workflow')
        qc_workflow_approval_structure_env = self.env['qc.workflow.approval.structure']
        return qc_workflow_approval_structure_env.get_start_event(default_qc_workflow)

    @api.model
    def _group_expand_stages(self, stages, domain, order):
        states = None
        if self.qc_workflow_id.id:
            states = stages.search([('qc_workflow_id', '=', self.qc_workflow_id.id)], order=order)
        return states

    @api.model
    def _get_stage_id(self):
        stage_ids = []
        stages = self.env['qc.stage']
        if self.qc_workflow_id.id :
            results_stage = stages.search([('qc_workflow_id', '=', self.qc_workflow_id.id)])
            for rec in results_stage:
                stage_ids.append(rec.id)
        return [('id', 'in', stage_ids)]

    stage_id = fields.Many2one(
        'qc.stage', string='Status', index=True , tracking=True,  readonly=True,
        store=True, copy=False,
        default=_default_stage_id,
        domain=_get_stage_id,
        group_expand='_group_expand_stages'
    )

    stage_code = fields.Char(string='Code', related='stage_id.code', readonly=True)

    def _default_qc_workflow_id(self):
        default_qc_workflow = self._context.get('default_type_workflow')
        _logger.info("default_qc_workflow: %s", default_qc_workflow)
        qc_workflow_env = self.env['qc.workflow']
        return qc_workflow_env.get_workflow(default_qc_workflow)

    qc_workflow_id = fields.Many2one('qc.workflow', string="Workflow", default=_default_qc_workflow_id)

    # type_workflow = fields.Selection([
    #     ('WF001', 'Managment of qc'),], string='Type Workflow', required=True, default='WF001')

    type_workflow = fields.Char(string='Type workflow', related='qc_workflow_id.code', store=True)

    movement_ids = fields.One2many('qc.movement', 'qc_model_workflow_id', string='Action Log')
    last_movement_id = fields.Many2one('qc.movement', string="Last movement")

    position_id = fields.Many2one('res.groups', string="Current position")

    check_position = fields.Boolean(compute='_compute_check_position')

    @api.depends('check_position')
    def _compute_check_position(self):
        qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
        for rec in self:
            rec.check_position = rec.get_position(rec) and not qc_workflow_approval_structure.is_end_event(
                rec.stage_id.id, rec.qc_workflow_id.id)

    check_global_position = fields.Boolean(compute='_compute_check_global_position')
    @api.depends('check_global_position')
    def _compute_check_global_position(self):
        qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
        for rec in self:
            rec.check_global_position = qc_workflow_approval_structure.is_end_event(
                rec.stage_id.id, rec.qc_workflow_id.id)




    def get_position(self, qc_model_workflow):
        position = False
        res_users= self.env['res.users']
        results_res_users = res_users.browse(self.env.user.id)
        if  results_res_users :
            groups_id = results_res_users.groups_id
            for rec in qc_model_workflow:
                for group in groups_id:
                    position = (group.id == rec.position_id.id)
                    if position: break
                if position: break
        default_registration_context = self._context.get('default_registration_context')
        if default_registration_context == _REGISTRATION_CONTEXT :
            position = True
        return position

    check_cancel_position = fields.Boolean(compute='_compute_check_cancel_position')

    @api.depends('check_cancel_position')
    def _compute_check_cancel_position(self):
        qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
        for rec in self:
            rec.check_cancel_position = self.get_cancel_position(
                self) and not qc_workflow_approval_structure.is_end_event(self.stage_id.id, self.qc_workflow_id.id)

    def get_cancel_position(self, qc_model_workflow):

        position = False
        res_users = self.env['res.users']
        results_res_users = res_users.browse(self.env.user.id)
        if results_res_users:
            groups_id = results_res_users.groups_id
            for rec in qc_model_workflow:
                for group in groups_id:
                    movementModel = self.env['qc.movement']
                    results_movement = movementModel.search([('id', '=', rec.last_movement_id.id)])
                    position = (group.id != rec.position_id.id) and (
                            group.id == results_movement.job_transmitter_id.id) and (
                                       rec.date_last_modif == results_movement.date_last_modif)
                    if position: break
                if position: break
        return position

    check_return_position = fields.Boolean(compute='_compute_check_return_position')

    @api.depends('check_return_position')
    def _compute_check_return_position(self):
        qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
        for rec in self:
            rec.check_return_position = self.get_position(self) and not qc_workflow_approval_structure.is_end_event(
                self.stage_id.id, self.qc_workflow_id.id) and not qc_workflow_approval_structure.is_start_event(
                self.stage_id.id, self.qc_workflow_id.id)

    # def _default_department_id(self):
    #     employee_id = self.env.user.employee_id
    #     return employee_id.department_id.id
    #
    # department_id = fields.Many2one('ir.module.category', string="Department", default=_default_department_id)

    department_id = fields.Many2one('ir.module.category', string="Department")


    # def _default_role_id(self):
    #     employee_id = self.env.user.employee_id
    #     return employee_id.job_id.id
    #
    # role_id = fields.Many2one('res.groups', string="Role",
    #                           domain="[('category_id', '=', department_id)]",
    #                           default=_default_role_id)
    role_id = fields.Many2one('res.groups', string="Role",
                              domain="[('category_id', '=', department_id)]")

    tracking_status = fields.Char(string='Tracking Status', related='stage_id.tracking_status')
    process = fields.Char(string='Process', related='qc_workflow_id.name')
    owner_role = fields.Char(string='Owned By', related='role_id.name')

    date_last_modif = fields.Datetime()

    counter = fields.Integer(string='Counter', required=True)
    year = fields.Integer(string='Counter', required=True)
    month = fields.Integer(string='Counter', required=True)

    def get_current_employee(self):
        '''get current employee.'''
        employee = self.env.user.employee_id
        return employee

    def get_application_number(self, new_counter, vals, code,process_prefixe_number):
        current_time = datetime.now()
        year = current_time.year
        month = current_time.month
        vals['year'] = year
        vals['month'] = month
        if process_prefixe_number :
            return process_prefixe_number + "_" + code + "_" + str(year).rjust(4, LEFT_PADDING_CHARACTER) + str(
                month).rjust(2,
                             LEFT_PADDING_CHARACTER) + str(
                new_counter).rjust(TOTAL_CHARACTER, LEFT_PADDING_CHARACTER)
        else:

            return APPLICATION_PREFIXE_NUMBER + "_"+ code + "_" +str(year).rjust(4, LEFT_PADDING_CHARACTER) + str(month).rjust(2,
                                                                                                              LEFT_PADDING_CHARACTER) + str(
                new_counter).rjust(TOTAL_CHARACTER, LEFT_PADDING_CHARACTER)

    @api.model
    def create(self, vals):

        '''Create Action.'''


        default_qc_workflow = self._context.get('default_type_workflow')
        qc_workflow_env = self.env['qc.workflow']
        qc_workflow = qc_workflow_env.get_workflow(default_qc_workflow)

        audit_group_id = self._context.get('audit_group_id')
        process_prefixe_number = self._context.get('process_prefixe_number')

        group_portal_user_id =  self._context.get('group_portal_user_id'),

        if not qc_workflow:
            raise ValidationError(_('Error:There is not workflow attached. Pleased first attached worflow to this process'))

        qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
        start_role_list = qc_workflow_approval_structure.get_start_role_list(qc_workflow.id)
        start_role = False
        for rec in start_role_list:
            start_role= rec
        if start_role:
           vals['position_id'] = start_role.id
           vals['role_id'] = start_role.id
           department_id = start_role.category_id.id
           vals['department_id'] = department_id

        counter_model = self.env['qc.counter']

        counter = counter_model.get_current_counter(qc_workflow.id)

        if counter:
            new_counter = counter[1] + 1
            vals['counter'] = new_counter
            vals['model_application_number'] = self.get_application_number(new_counter, vals, qc_workflow.code,process_prefixe_number)
            qc_model_workflow = super(QcModelWorkflow, self).create(vals)
            stage_id = self._default_stage_id()
            if qc_model_workflow:
                id = qc_model_workflow.id

                # create movment for portal records
                movement_values = {
                    'qc_model_workflow_id': id,
                    'transmitter_id': department_id,
                    'recipient_id': department_id,
                    'job_transmitter_id': group_portal_user_id,
                    'job_recipient_id': group_portal_user_id,
                    'comments': NON_APPLICABLE,
                    'user_transmitter_id': False,
                    'date_transmitter': False,
                    'action_name': False,
                    'stage_id': stage_id.id,
                    'next_stage_id': stage_id.id,
                    'final_status': '1',

                }
                qc_model_workflows_movement_id = self.env['qc.movement'].sudo().create(
                    movement_values
                )

                # create movment for audit records
                movement_values = {
                    'qc_model_workflow_id': id,
                    'transmitter_id': department_id,
                    'recipient_id': department_id,
                    'job_transmitter_id': audit_group_id,
                    'job_recipient_id': audit_group_id,
                    'comments': NON_APPLICABLE,
                    'user_transmitter_id': False,
                    'date_transmitter': False,
                    'action_name': False,
                    'stage_id': stage_id.id,
                    'next_stage_id': stage_id.id,
                    'final_status': '1',

                }
                qc_model_workflows_movement_id = self.env['qc.movement'].sudo().create(
                    movement_values
                )

                # create movment for current workflow
                movement_values = {
                    'qc_model_workflow_id': id,
                    'transmitter_id': department_id,
                    'recipient_id': department_id,
                    'job_transmitter_id': vals['position_id'],
                    'job_recipient_id': vals['position_id'],
                    'comments': NON_APPLICABLE,
                    'user_transmitter_id': False,
                    'date_transmitter': False,
                    'action_name': False,
                    'stage_id': stage_id.id,
                    'next_stage_id': stage_id.id,
                    'final_status': '1',

                }
                qc_model_workflows_movement_id = self.env['qc.movement'].sudo().create(
                    movement_values
                )

                counter = counter_model.update_current_counter(counter[0], new_counter)


        else:
            raise ValidationError(_('Unable to create: Please contact your administrator.'))

        return qc_model_workflow

    # @api.model
    # def create(self, vals_list):
    #     '''Create Action in batch.'''
    #
    #     # Initialize results and errors lists
    #     created_records = []
    #     errors = []
    #
    #     for vals in vals_list:
    #         try:
    #             # Get the default workflow for the context
    #             default_qc_workflow = self._context.get('default_type_workflow')
    #             qc_workflow_env = self.env['qc.workflow']
    #             qc_workflow = qc_workflow_env.get_workflow(default_qc_workflow)
    #
    #             if not qc_workflow:
    #                 raise ValidationError(
    #                     _('Error:There is no workflow attached. Please first attach workflow to this process'))
    #
    #             # Get start roles for the workflow
    #             qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
    #             start_role_list = qc_workflow_approval_structure.get_start_role_list(qc_workflow.id)
    #             start_role = False
    #             for rec in start_role_list:
    #                 start_role = rec
    #
    #             # Assign values based on the start role
    #             if start_role:
    #                 vals['position_id'] = start_role.id
    #                 vals['role_id'] = start_role.id
    #                 department_id = start_role.category_id.id
    #                 vals['department_id'] = department_id
    #
    #             # Handle the counter logic
    #             counter_model = self.env['qc.counter']
    #             counter = counter_model.get_current_counter(qc_workflow.id)
    #
    #             if counter:
    #                 new_counter = counter[1] + 1
    #                 vals['counter'] = new_counter
    #                 vals['model_application_number'] = self.get_application_number(new_counter, vals, qc_workflow.code)
    #
    #                 # Call the parent create method to create the workflow model
    #                 qc_model_workflow = super(QcModelWorkflow, self).create(vals)
    #
    #                 # Create movement for the workflow if the creation was successful
    #                 stage_id = self._default_stage_id()
    #                 if qc_model_workflow:
    #                     id = qc_model_workflow.id
    #                     movement_values = {
    #                         'qc_model_workflow_id': id,
    #                         'transmitter_id': department_id,
    #                         'recipient_id': department_id,
    #                         'job_transmitter_id': vals['position_id'],
    #                         'job_recipient_id': vals['position_id'],
    #                         'comments': NON_APPLICABLE,
    #                         'user_transmitter_id': False,
    #                         'date_transmitter': False,
    #                         'action_name': False,
    #                         'stage_id': stage_id.id,
    #                         'next_stage_id': stage_id.id,
    #                         'final_status': '1',
    #                     }
    #                     self.env['qc.movement'].sudo().create(movement_values)
    #
    #                     # Update counter
    #                     counter_model.update_current_counter(counter[0], new_counter)
    #
    #                 # Store the successfully created record
    #                 created_records.append(qc_model_workflow)
    #             else:
    #                 errors.append(_('Unable to create: Please contact your administrator.'))
    #
    #         except Exception as e:
    #             errors.append(str(e))
    #
    #     # Handle errors or return created records
    #     if errors:
    #         raise ValidationError('\n'.join(errors))
    #
    #     return created_records


    def write(self, vals):
        '''Update action.'''
        # vals['stage_id'] = self._default_in_process_stage_id()
        if not "date_last_modif" in vals.keys():
            now = datetime.now()
            vals['date_last_modif'] = now
        # if self.stage_code == IN_UNDER_REVIEW_AT_BD_RMA_STATE or self.stage_code == IN_UNDER_REVIEW_AT_BD_RMA_STATE_DD:
        #     vals['check_save_bd_rma'] = True
        #
        # if self.stage_code == IN_UNDER_CHECK_AND_VERIFY_RD_SCRA:
        #     vals['check_save_rm_scra'] = True

        qc_model_workflow = super(QcModelWorkflow, self).write(vals)
        return qc_model_workflow

    # def get_last_insert_transaction(self,workflow_id, counter):
    #     results_qc_mode_workflow= self.env['qc.model.workflow'].search(['&', ('workflow_id', '=', workflow_id) , ('counter', '=', counter)] , order='date desc', limit=1)
    #     for result_qc_mode_workflow in results_qc_mode_workflow :
    #         return result_qc_mode_workflow

    def get_last_insert_transaction(self, workflow_id):
        results_qc_mode_workflow = self.env['qc.model.workflow'].search([('qc_workflow_id', '=', workflow_id)],
                                                                            order='id desc', limit=1)
        for result_qc_mode_workflow in results_qc_mode_workflow:
            return result_qc_mode_workflow

    def can_unlink(self):
        check = False
        qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
        qc_movement = self.env['qc.movement']
        for rec in self:
            # check = rec.get_position(self) and  qc_workflow_approval_structure.is_start_event(rec.stage_id.id, rec.qc_workflow_id.id) and qc_movement.is_delete_movement(rec.id)
            check = rec.get_position(self) and qc_workflow_approval_structure.is_start_event(rec.stage_id.id,
                                                                                               rec.qc_workflow_id.id)
        return check

    def unlink(self):

        '''Delete action'''
        qc_workflow_id = False

        for rec in self:
            qc_workflow_id = rec.qc_workflow_id.id

        result = self.get_last_insert_transaction(qc_workflow_id)
        if result and result.model_application_number == self.model_application_number:
            new_counter = self.counter - 1
            counter_model = self.env['qc.counter']
            counter = counter_model.get_current_counter_id(qc_workflow_id)
            result = counter_model.update_current_counter(counter[0], new_counter)

        for rec in self:
            # if rec.stage_id.code != IN_PFI_DOCUMENT_UPLOADED_STATE:
            if not rec.can_unlink():
                raise ValidationError(_('Unable to delete: Please contact your administrator.'))
            else:
                results_movement = self.env['qc.movement'].search([('qc_model_workflow_id', '=', rec.id)])
                if results_movement:
                    results_movement.unlink()
                results_movement_cancelled = self.env['qc.movement.cancelled'].search(
                    [('qc_model_workflow_id', '=', rec.id)])
                if results_movement_cancelled:
                    results_movement_cancelled.unlink()
        qc_model_workflow = super(QcModelWorkflow, self).unlink()
        return qc_model_workflow

    @api.model
    def _search(self, args, offset=0, limit=None, order=None):
        '''Search action.'''


        job_ids = []
        res_users = self.env['res.users']
        results_res_users = res_users.browse(self.env.user.id)
        tmp = list(args)
        if results_res_users and not (self.env.uid == SUPERUSER_ID):
            groups_id = results_res_users.groups_id
            for group in groups_id:
                job_ids.append(group.id)
            args += ['|', ('movement_ids.job_transmitter_id.id', 'in', job_ids), ('movement_ids.job_recipient_id.id', 'in', job_ids)]
        if len(tmp) > 0:
            if 'portal' in tmp[0]:
                tmp.pop(0)
                args = tmp
            if 'is_portal_action' in tmp[0]:
                tmp.pop(0)
                args = tmp
                _logger.info("tmp: %s", tmp)

        _logger.info("args: %s", args)

       # return super(QcModelWorkflow, self)._search(args, offset, limit, order, count=count,     access_rights_uid=access_rights_uid)
        return super(QcModelWorkflow, self)._search(args, offset, limit, order)

    def get_next_stage(self, model_workflow):
        next_stage = None
        if model_workflow:
            next_stage = model_workflow.last_movement_id.next_stage_id
        return next_stage

    def get_current_stage(self, model_workflow):
        current_stage = None
        if model_workflow:
            current_stage = model_workflow.last_movement_id.stage_id
        return current_stage


    def move_to_next(self, workflow_id, category_transmitter_id , category_recipient_id, transmitter_id, recipient_id,comments,action_id,current_stage_id,next_stage_id,final_status):
        qc_movement_wizard_env = self.env['qc.movement.wizard']
        qc_movement_wizard_env.move_to_next(workflow_id, category_transmitter_id , category_recipient_id, transmitter_id, recipient_id,comments,action_id,current_stage_id,next_stage_id,final_status)

    @api.model
    def move_to_stage_after_start_event(self, next_stage_code, workflow_model_id, comments=None):

        '''move acion.'''
        default_qc_workflow = self._context.get('default_type_workflow')
        qc_workflow_env = self.env['qc.workflow']
        qc_workflow = qc_workflow_env.get_workflow(default_qc_workflow)

        if not qc_workflow:
            raise ValidationError(
                _('Error:There is not workflow attached. Pleased first attached worflow to this process'))

        workflow_id = qc_workflow.id
        qc_stage_env = self.env['qc.stage']
        next_stage_id = qc_stage_env.get_stage_id(workflow_id, next_stage_code)

        qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']
        start_role_list = qc_workflow_approval_structure.get_start_role_list(workflow_id)
        start_role = False
        for rec in start_role_list:
            start_role = rec
        if start_role:
            job_transmitter_id = start_role.id
            transmitter_id = start_role.category_id.id

        next_role_list = qc_workflow_approval_structure.get_nex_approval(workflow_id, next_stage_id)
        next_role = False
        for rec in next_role_list:
            next_role = rec
        if next_role:
            job_receiver_id = next_role.job_id.id
            receiver_id = next_role.department_id.id

        stage_id = self._default_stage_id().id
        self.move_to_next(workflow_model_id, transmitter_id, receiver_id, job_transmitter_id, job_receiver_id, comments, False, stage_id, next_stage_id, False)

    @api.model
    def move_from_one_stage_to_another_stage(self, current_stage_code, next_stage_code, workflow_model_id, comments = None):

        '''move acion.'''
        default_qc_workflow = self._context.get('default_type_workflow')
        qc_workflow_env = self.env['qc.workflow']
        qc_workflow = qc_workflow_env.get_workflow(default_qc_workflow)

        if not qc_workflow:
            raise ValidationError(
                _('Error:There is not workflow attached. Pleased first attached worflow to this process'))

        workflow_id = qc_workflow.id
        qc_stage_env = self.env['qc.stage']
        next_stage_id = qc_stage_env.get_stage_id(workflow_id, next_stage_code)
        current_stage_id = qc_stage_env.get_stage_id(workflow_id, current_stage_code)

        qc_workflow_approval_structure = self.env['qc.workflow.approval.structure']

        current_role_list = qc_workflow_approval_structure.get_current_approval(workflow_id, current_stage_id)
        current_role = False
        for rec in current_role_list:
            current_role = rec
        if current_role:
            job_transmitter_id = current_role.job_id.id
            transmitter_id = current_role.department_id.id
        # start_role_list = qc_workflow_approval_structure.get_start_role_list(workflow_id)
        # start_role = False
        # for rec in start_role_list:
        #     start_role = rec
        # if start_role:
        #     job_transmitter_id = start_role.id
        #     transmitter_id = start_role.category_id.id

        next_role_list = qc_workflow_approval_structure.get_nex_approval(workflow_id, next_stage_id)
        next_role = False
        for rec in next_role_list:
            next_role = rec
        if next_role:
            job_receiver_id = next_role.job_id.id
            receiver_id = next_role.department_id.id

        # stage_id = self._default_stage_id().id
        self.move_to_next(workflow_model_id, transmitter_id, receiver_id, job_transmitter_id, job_receiver_id, comments,
                          False, current_stage_id, next_stage_id, False)




