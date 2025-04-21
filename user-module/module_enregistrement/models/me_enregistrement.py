# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import threading
import time

from odoo.exceptions import  ValidationError
from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.http import request

from ..utils.Utils import MeUtils

_logger = logging.getLogger(__name__)

PROCESS_PREFIXE_NUMBER = "ENR"
DEFAULT_TYPE_WORKFLOW ="01"
WORKFLOW_DRAFT_STAGE = "0101"
WORKFLOW_SUBMIT_STAGE = "0102"
WORKFLOW_APPROVED_STAGE = "0104"
WORKFLOW_VALID_STAGE = "0103"


class MeEnregistrement(models.Model):
    """
       Modèle représentant un enregistrement d'une entité.

       Ce modèle est utilisé pour stocker les informations relatives
       à une entité enregistrée. Il contient des champs comme le nom
       de l'entité, son email principal, son logo et  le compte du premier administrateur de cette entité.

       Attributs:
           name (str): Le nom complet de l'entité.
           login (str): Le login du premier administrateur de l'entité.
           email (str): L'adresse principal de l'entité.
           logo (image): Une image associée à l'entité.
    """


    _name = 'me.enregistrement'
    _rec_name = 'model_application_number'
    _order = 'id desc'
    _description = "Enregistrement d'une entité et administrateur délégué"


    _inherit = ['mail.thread.cc',
                'mail.thread.blacklist',
                'mail.activity.mixin',
                'format.address.mixin',
                ]

    _sql_constraints = [
        ('company_name_unique', 'UNIQUE(company_name)', _("Le champ company_name doit être unique .")),
    ]


    name = fields.Char(string='Nom', required=True, help="Nom du premier administrateur de l'entité ou administrateur délégué" , tracking=True, compute='_compute_name',
                            inverse='_inverse_name')
    """
    Le champ 'name' représente le nom de l'utilisateur qui sera le premier administrateur ou administrateur délégué.
    Il est obligatoire et doit contenir une chaîne de caractères.
    """

    def _compute_name(self):
        for rec in self:
            if rec.partner_name_id:
                rec.name = rec.partner_name_id.name

    def _inverse_name(self):
        """Permet la modification du champ file, mais ne fait rien"""
        pass

    partner_name_id = fields.Many2one('res.partner', 'Nom')
    """
       Le champ 'partner_name_id' représente l'id du partenaire premier administrateur.
    """


    company_name = fields.Char(string='Tiers', required=True, help="Nom de l'entité qui peut être (Sectorielle, AGEX, PTF, Banque,  etc..." , tracking=True,  compute='_compute_company_name',
                            inverse='_inverse_company_name')
    """
    Le champ 'company_name' représente le nom de du qui peut être (Sectorielle, AGEX, PTF, Banque,  etc....
    Il est obligatoire et doit contenir une chaîne de caractères.
    """

    def _compute_company_name(self):
        for rec in self:
            if rec.partner_id:
                rec.company_name = rec.partner_id.name

    def _inverse_company_name(self):
        """Permet la modification du champ file, mais ne fait rien"""
        pass

    partner_id = fields.Many2one('res.partner', 'Company')
    """
       Le champ 'partner_id' représente l'id de la compagnie.
    """

    numero_enregistrement = fields.Char(string='Numéro enregistrement', required=True,
                               help="Numéro  national d'enregistrement de la compagnie. Celà peut églement être un numéro de décret de création ou tout autre numéro d'identification de la compagnie  Ministère, Sectoriel, Agex, PF, Banque etc.....", tracking=True)
    """
    Le champ 'numero_enregistrement' représente le numéro  national d'enregistrement de la compagnie.
    Celà peut également être un numéro de décret de création ou tout autre numéro d'identification de la compagnie
    Ministère, Sectoriel, Agex, PF, Banque etc.....
    """

    date_enregistrement= fields.Date(string='Date enregistrement', required=True,
                                             help="Date  de création ou d'enregistrement de la compagnie au sein de l'état. Celà peut également être la date du décret etc...", tracking=True)
    """
    Le champ 'date_enregistrement' représente la date  de création ou d'enregistrement de la compagnie.
    Celà peut également être la date de décret de création
    """

    email = fields.Char(string='Email', required=True, help="Adresse email de l'entité. cet email servira également pour les notifications vers l'entité" ,  compute='_compute_email',
                            inverse='_inverse_email')
    """
      Le champ 'email' représente l'adresse email officiel de l'entité. cet email servira également pour les notifications vers l'entité.
      Ce champ est obligatoire
    """

    def _compute_email(self):
        for rec in self:
            if rec.partner_name_id:
                rec.email = rec.partner_name_id.email

    def _inverse_email(self):
        """Permet la modification du champ file, mais ne fait rien"""
        pass

    telephone = fields.Char(string='Téléphone', required=True, help="Téléphone de l'entité. ce tel servira également  pour les notifications et communication avec l'entité" ,  compute='_compute_telephone',
                            inverse='_inverse_telephone')
    """
     Le champ 'telephone' représente le tel officiel de l'entité. ce telephone servira également pour les notifications et communication avec l'entité.
     Ce champ est obligatoire
    """

    def _compute_telephone(self):
        for rec in self:
            if rec.partner_name_id:
                rec.telephone = rec.partner_name_id.phone

    def _inverse_telephone(self):
        """Permet la modification du champ file, mais ne fait rien"""
        pass


    username = fields.Char(string='Login', required=True, help="login du premier administrateur de l'entité." , tracking=True ,  compute='_compute_username',
                            inverse='_inverse_username')
    """
    Le champ 'login' représente le login de l'utilisateur.
    Il est obligatoire et doit contenir une chaîne de caractères.
    """

    def _compute_username(self):
        for rec in self:
            if rec.user_id:
                rec.username = rec.user_id.login

    def _inverse_username(self):
        """Permet la modification du champ file, mais ne fait rien"""
        pass

    user_id = fields.Many2one('res.users', 'Utilisateur')
    """
       Le champ 'user_id' représente l'id de l'utilisateur de login username.
    """


    password = fields.Char(string='Mot de passe', required=False, default="12345" ,store=False, help="mot de passe du premier administrateur de l'entité.")
    """
       Le champ 'password' représente le mot de passe  du premier administrateur de l'entité.
       Il est obligatoire et doit respecter la complexité définit pour le mot de passe.
    """

    document_ids = fields.One2many('document.enregistrement', 'enregistrement_id', string='Documents', help="Liste des documents requis.")
    """
       Le champ 'document_ids' consigne tous les documents requis.
    """

    access_url = fields.Char(string="Lien d'accès", compute="_compute_access_url", store=True)
    """
       Technical fields for record url. Champ technique pour consigner l'url de l'enregistrement sur lequel on peut faire des actions spécifiques
    """

    @api.depends('company_name')
    def _compute_access_url(self):
        for rec in self:
            if rec.id:
                base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or "https://localhost/"
                rec.access_url = f"{base_url}/web#id={rec.id}&model=me.enregistrement&view_type=form"
                _logger.info(f"Computed URL for {rec.id}: {rec.access_url}")
            else:
                rec.access_url = None
                _logger.warning(f"No ID for record: {rec}")

        # except Exception as e:
        #     _logger.error("Erreur lors de la construction de l'url pour le record %s: %s", self.id, str(e))

    model_workflow_id = fields.Many2one('qc.model.workflow', string='Workflow Model')
    """
    Workflow management fields.
    """

    stage_id = fields.Many2one(
        'qc.stage',
        string='Status',
        domain=lambda self: self._get_stage_id(),
        default=lambda self: self._default_stage_id(),
        compute='_compute_stage_id',
        inverse='_inverse_stage_id'
    )

    @api.model
    def _default_stage_id(self):
        workflow = self.env['qc.model.workflow'].with_context(default_type_workflow=DEFAULT_TYPE_WORKFLOW)._default_qc_workflow_id()
        if workflow:
            stage = self.env['qc.stage'].search([('qc_workflow_id', '=', workflow.id)], limit=1)
            return stage.id
        return False

    @api.model
    def _get_stage_id(self):
        stage_ids = []
        workflow = self.env['qc.model.workflow'].with_context(default_type_workflow=DEFAULT_TYPE_WORKFLOW)._default_qc_workflow_id()
        _logger.info("workflow: %s", workflow)
        if workflow:
            stage_ids = self.env['qc.stage'].search([('qc_workflow_id', '=', workflow.id)]).ids
        return [('id', 'in', stage_ids or [])]

    tracking_stage_id = fields.Many2one('qc.stage', string='Status', tracking=True)

    @api.depends('stage_id')
    def _compute_stage_id(self):
        for rec in self:
            rec.stage_id = rec.model_workflow_id.stage_id

    def _inverse_stage_id(self):
        for rec in self:
            rec.tracking_stage_id = rec.model_workflow_id.stage_id

    stage_code = fields.Char(string='Code', related='model_workflow_id.stage_code', readonly=True)

    model_application_number = fields.Char(string='Application N°',
                                           related='model_workflow_id.model_application_number')

    # owner_role = fields.Char(string='Owned By', related='model_workflow_id.owner_role', store=True, tracking=True)
    owner_role = fields.Char(string='Owned By', related='model_workflow_id.owner_role', store=False)

    create_uid = fields.Many2one('res.users', tracking=True)

    tracking_status = fields.Char(string='Tracking Status', related='model_workflow_id.tracking_status')

    check_position = fields.Boolean(related='model_workflow_id.check_position')
    task_status = fields.Char('#Task', compute='_compute_task_status')

    def _compute_task_status(self):
        for rec in self:
            if rec.check_position:
                rec.task_status = _("Task in process")
            else:
                rec.task_status = _("Task Completed")

    check_global_position = fields.Boolean(related='model_workflow_id.check_global_position')

    process_status = fields.Char('#Process', compute='_compute_process_status')

    def _compute_process_status(self):
        for rec in self:
            if rec.check_global_position:
                rec.process_status = _("Pocess Completed")
            else:
                rec.process_status = _("Pocess running")


    check_cancel_position = fields.Boolean(related='model_workflow_id.check_cancel_position')
    check_return_position = fields.Boolean(related='model_workflow_id.check_return_position')

    movement_ids = fields.One2many('qc.movement', related='model_workflow_id.movement_ids', string='Action Log')

    type_workflow = fields.Char(string='Type workflow', related='model_workflow_id.type_workflow', store=True)


    groups_id = fields.Many2many('res.groups', 'user_groups_rel', 'user_id', 'group_id')

    # Another fields
    is_portal_action = fields.Boolean('Portal Action', default=False)

    # this field is technical field used to hide view elements
    x_css = fields.Html(
        sanitize=False,
        compute='_compute_css',
        store=False,
    )

    def _compute_css(self):
        for rec in self:

            if rec.model_workflow_id.stage_id.name != 'draft' or (
                    rec.model_workflow_id.stage_id.name == "draft" and rec.is_portal_action) or (
                    not rec.check_position):
                rec.x_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                rec.x_css = False

    is_readonly = fields.Boolean(
        compute='_compute_is_readonly',
        store=False,
    )

    def _compute_is_readonly(self):
        for rec in self:
            if rec.model_workflow_id.stage_id.name != 'draft' or (
                    rec.model_workflow_id.stage_id.name == "draft" and rec.is_portal_action) or (
                    not rec.check_position):
                rec.is_readonly = True
            else:
                rec.is_readonly = False



    @api.model
    def create(self, vals):
        """Créer une entreprise, un responsable et un utilisateur associé."""
        try:
            company = self.env['res.company'].sudo().search([], limit=1)  # Récupère la première société

            # Création du partenaire pour l'entreprise
            company_partner_vals = {
                'name': vals.get('company_name'),
                'email': vals.get('email'),
                'phone': vals.get('telephone'),
                'is_company': True,
                'company_id': company.id,
                'additional_info': "portal",  # Permet d'identifier une personne morale portail
            }
            company_partner = self.env['res.partner'].sudo().create(company_partner_vals)
            _logger.info(f"Company Partner ID: {company_partner.id}")

            # Création du partenaire pour la personne responsable
            responsible_partner_vals = {
                'name': vals.get('name'),
                'email': vals.get('email'),
                'phone': vals.get('telephone'),
                'is_company': False,
                'parent_id': company_partner.id,  # Associe la personne à la société
                'company_id': company.id,
                'additional_info': "portal", # Permet d'identifier une personne physique portail

            }
            responsible_partner = self.env['res.partner'].sudo().create(responsible_partner_vals)
            _logger.info(f"Responsible Partner ID: {responsible_partner.id}")

            # Vérification de l'existence de l'utilisateur
            self.env.cr.flush()  # Force Odoo à synchroniser avec la BD
            existing_user = self.env['res.users'].with_context(active_test=False).sudo().search(
                [('login', '=', vals.get('username').strip())], limit=1)
            _logger.info(
                f"Vérification de l'existence de l'utilisateur [{vals.get('username')}]. Résultat: {existing_user}")

            if existing_user:
                _logger.info(
                    f"Un utilisateur avec le login {vals.get('username')} existe déjà avec l'ID {existing_user.id} !")
                raise ValidationError(f"Un utilisateur avec le login {vals.get('username')} existe déjà !")
            else:
                _logger.warning(f"Utilisateur [{vals.get('username')}] non trouvé  !")

            # Création de l'utilisateur associé
            user_vals = {
                'name': vals.get('name'),
                'login': vals.get('username'),
                'email': vals.get('email'),
                'company_ids': [(6, 0, [company.id])],
                'company_id': company.id,
                'partner_id': responsible_partner.id,
                'password': vals.get('password'),
                'active': True,
            }
            #  On désactive l'envoi automatique de l'email avec l'option  no_reset_password=True
            user_create = self.env['res.users'].with_context(no_reset_password=True, active_test=False).with_user(SUPERUSER_ID).sudo().create(user_vals)
            self.env.cr.flush()  #  Force la mise à jour immédiate en BD
            _logger.info(f"Utilisateur créé avec ID : {user_create.id}")

            # Vérifier si user_create contient un ID valide, sinon rechercher l'utilisateur
            if not user_create or not user_create.id:
                _logger.warning(
                    f"L'objet retourné par create() est vide. Recherche de l'utilisateur {vals.get('username')} en base...")
                user_create = self.env['res.users'].sudo().search([('login', '=', vals.get('username'))], limit=1)

            # Vérifier à nouveau et lever une exception si l'utilisateur n'existe toujours pas
            if not user_create:
                _logger.warning(
                    f"Impossible de récupérer l'utilisateur {vals.get('username')} après la création !")
                raise ValidationError(
                    f"Impossible de récupérer l'utilisateur {vals.get('username')} après la création !")

            group_portal_user_id = self.env.ref('module_enregistrement.group_portal_user').id
            if user_create:
                _logger.info(f"Désactivation de l'utilisateur après création : {user_create.id}")
                user_create.sudo().write({'active': False})
                # Récupère le groupe 'Portal User'
                user_create.groups_id = [(4, group_portal_user_id)]  # Ajoute l'utilisateur au groupe

            user_create_id = user_create.id
            _logger.info(f"Utilisateur créé avec ID : {user_create_id}")



            # Mise à jour de l'enregistrement
            vals.update({
                'partner_name_id': responsible_partner.id,
                'partner_id': company_partner.id,
                'user_id': user_create_id,
            })

            # Création du workflow associé
            audit_group_id = self.env.ref('module_enregistrement.group_me_auditor').id
            model_workflow = self.env['qc.model.workflow'].with_context(
                default_type_workflow=DEFAULT_TYPE_WORKFLOW,
                audit_group_id=audit_group_id,
                group_portal_user_id=group_portal_user_id,
                process_prefixe_number=PROCESS_PREFIXE_NUMBER
            ).create({})

            if model_workflow:
                vals['model_workflow_id'] = model_workflow.id
                # if vals.get('is_portal_action'):
                #     model_workflow.move_to_stage_after_start_event(WORKFLOW_SUBMIT_STAGE, model_workflow.id)

            meEnregistrement = super(MeEnregistrement, self).create(vals)
            # Envoi d'un email de notification après enregistrement depuis le portail
            #if meEnregistrement and vals.get('is_portal_action'):
            # L'email envoyé doit intégrer l'url angular de chargement d'un enregistrement en modification
            self._send_registration_email(vals, meEnregistrement)


            return meEnregistrement

        except Exception as e:
            _logger.error(f"Erreur lors de la création : {str(e)}")
            raise ValidationError(f"Erreur lors de l'enregistrement : {str(e)}")



    def _send_registration_email(self, vals, meEnregistrement):
        """ Envoie l'email via le système de messagerie Odoo (asynchrone) """
        try:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or "https://localhost/"
            update_url = f"{base_url}/web#id={meEnregistrement.id}&model=me.enregistrement&view_type=form"
            meUtils = MeUtils()
            mail_values = {
                'subject': meUtils.get_registration_creation_notify_email_subject( vals),
                'body_html': meUtils.get_registration_creation_notify_email_body(vals,update_url, meEnregistrement.model_application_number),
                'email_from': False,
                'email_to': vals['email'],
                'model': self._name,
                'res_id': meEnregistrement.id,  # Link to the created record
            }
            self.env['qc.model.mail'].send_email_on_creation(mail_values)
            _logger.info(f"Email envoyé à {vals['email']}")
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi de l'email : {str(e)}")



    def _run_email_thread(self, mail_values):
        """ Thread pour envoyer l'email de création """
        time.sleep(5)
        try:
            self.env['servicing.utils'].send_email_on_creation(mail_values)
            _logger.info(f"Email envoyé à {mail_values['email_to']}")
        except Exception as e:
            _logger.error(f"Erreur d'envoi d'email : {str(e)}")






    def write(self, vals):
        """Action de mise à jour d'une entité et execution des actions spécifiques sur les workflows et notifications des parties prenantes."""
        msg_error = None
        try:
            _logger.info(_(f"vals: {vals}"))
            meEnregistrement = super(MeEnregistrement, self).write(vals)
            _logger.info(_(f"meEnregistrement2: {meEnregistrement}"))
            for rec in self:

                # Mise à jour du partenaire de l'entreprise
                if any(key in vals for key in ['company_name', 'email', 'telephone']):
                    company_partner_vals = {}
                    if 'company_name' in vals:
                        company_partner_vals['company_name'] = vals['company_name']
                    if 'email' in vals:
                        company_partner_vals['email'] = vals['email']
                    if 'telephone' in vals:
                        company_partner_vals['phone'] = vals['telephone']
                    existing_company = self.env['res.partner'].sudo().search(
                        [('company_name', '=', vals['company_name']),('is_company', '=', True)], limit=1)
                    if existing_company and existing_company.id != rec.partner_id.id:
                        msg_error = _(f"La compagnie {vals['company_name']} existe déjà.")
                        _logger.warning(msg_error)
                        raise ValidationError(msg_error)
                    elif company_partner_vals and rec.partner_id:
                        rec.partner_id.sudo().write(company_partner_vals)
                        _logger.info(_(f"Partenaire de l'entreprise mis à jour: {rec.partner_id.id}"))

                # Mise à jour du partenaire responsable
                if any(key in vals for key in ['name', 'email', 'telephone']):
                    responsible_partner_vals = {}
                    if 'name' in vals:
                        responsible_partner_vals['name'] = vals['name']
                    if 'email' in vals:
                        responsible_partner_vals['email'] = vals['email']
                    if 'telephone' in vals:
                        responsible_partner_vals['phone'] = vals['telephone']

                    if responsible_partner_vals and rec.partner_name_id:
                        rec.partner_name_id.sudo().write(responsible_partner_vals)
                        _logger.info(_(f"Partenaire responsable mis à jour: {rec.partner_name_id.id}"))

                # Mise à jour de l'utilisateur associé
                if rec.user_id:
                    user_update_vals = {}

                    # Vérification du login uniquement si le login est modifié
                    if 'username' in vals:
                        # Vérifier si le login est unique
                        existing_user = self.env['res.users'].sudo().search(
                            [('login', '=', vals['username'])], limit=1)
                        if existing_user and existing_user.id != rec.user_id.id:
                            msg_error = _(f"Le login {vals['username']} existe déjà pour un autre utilisateur.")
                            _logger.warning(msg_error)
                            raise ValidationError(msg_error)

                        else:
                            user_update_vals['login'] = vals['username']
                            _logger.info(_(f"Login de l'utilisateur mis à jour vers : {vals['username']}"))

                    if 'name' in vals:
                        user_update_vals['name'] = vals['name']
                    if 'email' in vals:
                        user_update_vals['email'] = vals['email']

                    stage_code = rec.model_workflow_id.stage_id.code
                    if 'password' in vals and stage_code == WORKFLOW_DRAFT_STAGE:
                        user_update_vals['password'] = vals['password']

                    if user_update_vals:
                        rec.user_id.with_context(no_reset_password=True, active_test=False).sudo().write(user_update_vals)
                        _logger.info(_(f"Utilisateur mis à jour: {rec.user_id.id}"))

                qc_model_workflow = self.env['qc.model.workflow']
                next_stage = qc_model_workflow.get_next_stage(rec.model_workflow_id)
                if next_stage  and next_stage.code == WORKFLOW_APPROVED_STAGE:
                    _logger.info("start WORKFLOW_APPROVED_STAGE   %s", WORKFLOW_APPROVED_STAGE)
                    if rec.user_id:
                        rec.user_id.sudo().write({'active': True})
                    #self.action_send_notification()
                    _logger.info("start send_email_after_creation   %s", "send_email_after_creation")
                    documents = [doc.file_id.datas for doc in rec.document_ids if doc.file_id.datas]
                    labels = [doc.file_id.name for doc in rec.document_ids if doc.file_id.name]
                    self.env['qc.model.mail'].send_email_after_creation(rec.id,
                        'module_enregistrement.registration_approbation_notify_email_template',
                        documents,
                        labels)
                elif next_stage and next_stage.code == WORKFLOW_VALID_STAGE:

                    _logger.info("next_stage.code: %s", next_stage.code)


            return meEnregistrement


        except Exception as e:
            _logger.error(f"Erreur lors de la modification l'entité me.enregistrement %s:   %s" ,self.id, str(e))
            raise ValidationError(msg_error)

    def _run_email_thread2(self, mail_values):
        """ Thread pour envoyer l'email de création """
        time.sleep(5)
        new_cr = None
        try:
            new_cr = self.pool.cursor()
            new_self = self.with_env(self.env(cr=new_cr))
            mail = new_self.env['mail.mail'].sudo().create(mail_values)
            mail.sudo().send(auto_commit=False)
            _logger.info(f"Email envoyé à {mail_values['recipient_ids']}")
            if new_cr:
                new_cr.commit()
                new_cr.close()
        except Exception as e:
            _logger.error(f"Erreur d'envoi d'email : {str(e)}")
            if new_cr:
                new_cr.commit()
                new_cr.close()






    def unlink(self):
        """Action de suppression d'une entité et tous les objets associés."""
        for rec in self:
            try:
                # if rec.model_workflow_id.stage_id.code != WORKFLOW_DRAFT_STAGE or (
                #         rec.model_workflow_id.stage_id.code == WORKFLOW_DRAFT_STAGE and rec.is_portal_action) or (
                #         not rec.check_position):

                _logger.info(f"rec.model_workflow_id.stage_id.code: {rec.model_workflow_id.stage_id.code}")
                stage_code = rec.model_workflow_id.stage_id.code
                if stage_code != WORKFLOW_DRAFT_STAGE :
                    _logger.error(f"La suppression de l'entité me.enregistrement  n'est possible que à l'état brouillon: {rec.id}")
                    raise ValidationError(_(f"La suppression de l'entité me.enregistrement {rec.id} n'est possible que à l'état brouillon : Merci de contacter votre administrateur."))

                # Supprimer les documents liés
                _logger.info(f"Delete documents: {rec.document_ids}")
                if rec.document_ids:
                    rec.document_ids.unlink()


                # Supprimer l'utilisateur
                _logger.info(f"Delete users: {rec.user_id}")
                if rec.user_id:
                    rec.user_id.sudo().unlink()


                # Supprimer le partenaire personne physique associée à l'utilisateur créée
                _logger.info(f"Delete responsable partner: {rec.partner_name_id}")
                if rec.partner_name_id:
                    rec.partner_name_id.sudo().unlink()


                # Supprimer le partenaire personne morale créée
                _logger.info(f"Delete partner: {rec.partner_id}")
                if rec.partner_id:
                    rec.partner_id.sudo().unlink()


                # Supprimer le workflow
                _logger.info(f"Delete workflow: {rec.model_workflow_id}")
                if rec.model_workflow_id:
                   rec.model_workflow_id.sudo().unlink()


                # Validation de la transaction
            except Exception as e:
                _logger.error(f"Erreur lors de la suppression de l'entité me.enregistrement {rec.id} : {str(e)}")
                raise ValidationError(_("Une erreur est survenue lors de la suppression. Contactez l'administrateur."))


        return super(MeEnregistrement, self).unlink()

    @api.model
    def _search(self, args, offset=0, limit=None, order=None):
        """Action de recherche d'une ou de plusieurs entités avec ségrégation d'informations suivant les droits d'accès définis."""

        # Workflow filter
        if self.env.user and self.env.user.ensure_one():
            auditor = self.env.user.has_group('module_enregistrement.group_me_auditor')
        else:
            # Gérer le cas où aucun utilisateur n'est trouvé
            auditor = False

        tmp_args = list(args)  # Clone the args to avoid modifying the original list

        is_portal_action = self._context.get('is_portal_action')

        _logger.info("is_portal_action: %s", is_portal_action)

        # If not an auditor, add additional filters based on user groups

        #if not auditor and not (len(tmp_args) > 0 and 'is_portal_action' in tmp_args[0]):

        if not auditor :
            job_ids = []
            res_users = self.env['res.users']
            results_res_users = res_users.browse(self.env.user.id)
            if results_res_users:
                groups_id = results_res_users.groups_id
                for group in groups_id:
                    job_ids.append(group.id)
                if is_portal_action:
                    tmp_args += ['|', ('model_workflow_id.movement_ids.job_transmitter_id.id', 'in', job_ids),
                                 ('model_workflow_id.movement_ids.job_recipient_id.id', 'in', job_ids)]
                else :
                    # Récupère la première compagnie (souvent la principale/admin)
                    user_partner = self.env.user.partner_id
                    #Empecher aux utilisateurs portails d'avoir un accès direct aux données
                    if user_partner.parent_id and user_partner.additional_info=='portal':  # tester si c'est un utilisateur portal
                        tmp_args += [(0, '=', 1) ]
                    else :
                        tmp_args += ['|',
                                     ('model_workflow_id.movement_ids.job_transmitter_id.id', 'in', job_ids),
                                     ('model_workflow_id.movement_ids.job_recipient_id.id', 'in', job_ids),
                                     '!', '&',
                                     ('stage_code', '=', WORKFLOW_DRAFT_STAGE),
                                     ('is_portal_action', '=', True)
                                 ]



        # Add specific auditor filter if necessary
        if auditor:
            # You can replace print with logging if needed for production
            _logger.info("Auditor filter applied")
            _logger.info("tmp_args: %s", tmp_args)
            tmp_args = [('is_portal_action', 'in', (True, False))]

        _logger.info(f"tmp_args : {str(tmp_args)}")

        #tmp_args =[('id', '=', 200)]

        # Call super method with updated arguments
        return super(MeEnregistrement, self)._search(tmp_args, offset, limit, order)


    @api.model
    def _create_user(self, values):
        try:
            required_fields = [ 'login', 'email', 'password']
            for field in required_fields:
                if not values.get(field):
                    _logger.error("Champ obligatoire manquant : %s", field)
                    return False

            env_res_users = self.env['res.users']

            # Vérifier si un utilisateur existe déjà
            existing_user = env_res_users.sudo().search([('login', '=', values.get('login'))], limit=1)

            if existing_user:
                _logger.warning("Utilisateur déjà existant avec ce login : %s", values.get('login'))
                return existing_user  # On retourne l'utilisateur existant

            # Vérifier si le partner_id est valide
            partner = self.env['res.partner'].sudo().browse(values.get('partner_id'))
            if not partner.exists():
                _logger.error("Le partenaire avec ID %s n'existe pas.", values.get('partner_id'))
                return False

            # Vérifier si la company_id est valide
            company = self.env['res.company'].sudo().browse(values.get('company_id'))
            if not company.exists():
                _logger.error("La société avec ID %s n'existe pas.", values.get('company_id'))
                return False

            # Création de l'utilisateur
            _logger.info(f"/api/enregistrement/create post  values  : {str(values)}")
            #new_user = env_res_users.with_context(no_reset_password=True).sudo().create(values)
           # _logger.info(f"/api/enregistrement/create post  new_user  : {str(new_user)}")

            new_user = env_res_users.sudo().create({ 'login': 'console70', 'company_ids': [(6, 0, [1])], 'company_id': 1, 'password': '12345', 'partner_id': 432}
)

            if not new_user:
                _logger.error("La création de l'utilisateur a échoué, l'objet retourné est None.")
                return False

            _logger.info("Utilisateur créé avec succès : ID %s, login %s", new_user.id, new_user.login)
            return new_user

        except Exception as e:
            _logger.error("Erreur lors de la création de l'utilisateur : %s", str(e))
            return False


    # def _create_company(self, values):
    #     result = self.env['res.company'].with_user(SUPERUSER_ID).sudo().create(values)
    #     return result

    def _create_partner(self, values):
        try:
            result = self.env['res.partner'].sudo().create(values)
            return result
        except Exception as e:
            _logger.error("Erreur lors de la création du partenaire :  %s", str(e))

    def send_finish_email(self, mail_template_id, attachments_content=None, attachments_label=None):
        _logger.info("send_finish_email %s", mail_template_id)

        if attachments_label is None:
            attachments_label = []
        if attachments_content is None:
            attachments_content = []

        try:
            mail_template = self.env.ref(mail_template_id).sudo()
            attachments = []

            for attach, label in zip(attachments_content, attachments_label):
                if attach:
                    attachment = self.env['ir.attachment'].sudo().create({
                        'name': label,
                        'type': 'binary',
                        'datas': attach,
                        'store_fname': False,  # Odoo gère automatiquement
                        'res_model': 'mail.mail',  # Lier aux emails et non aux templates
                        'res_id': self.id,  # Associer à un enregistrement spécifique
                    })
                    attachments.append(attachment.id)

            # Créer un mail spécifique basé sur le template
            mail_id = mail_template.sudo().send_mail(self.id, force_send=False)  # Mettre en file d’attente
            if mail_id:
                mail = self.env['mail.mail'].sudo().browse(mail_id)
                mail.sudo().write({'attachment_ids': [(6, 0, attachments)]})

                # Forcer l'envoi si nécessaire
                mail.sudo().send()

        except Exception as e:
            _logger.error("Erreur lors de l'envoi de l'email pour l'enregistrement ID %s: %s", self.id, str(e))

    def send_email_on_creation(self, mail_values):
        try:
            # Recherche du serveur de mail par défaut (prioritaire)
            mail_server = self.sudo().env['ir.mail_server'].search([], limit=1)
            if mail_server:
                mail_server_info = {
                    'name': mail_server.name,
                    'smtp_host': mail_server.smtp_host,
                    'smtp_port': mail_server.smtp_port,
                    'smtp_user': mail_server.smtp_user,
                    'smtp_encryption': mail_server.smtp_encryption,
                    'smtp_pass': mail_server.smtp_pass,
                    'from_filter': mail_server.from_filter,
                    'active': mail_server.active,
                }
                mail_values['email_from'] = mail_server.from_filter
                _logger.info(f"mail_server_info : {mail_server_info}")
                _logger.info(f"mail_values : {mail_values}")
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.sudo().send()
        except Exception as e:
            _logger.error("Erreur lors de l'envoi de l'email pour l'enregistrement ID %s: %s", self.id, str(e))


    def action_send_notification(self):
        """ Envoie une notification à l'utilisateur """
        try:
            message = f"L'enregistrement {self.name} a été mis à jour !"

            _logger.info("Notification ID %s", self.id)

            # Envoie la notification à tous les utilisateurs connectés
            self.env['bus.bus']._sendone(
                self.env.user.partner_id,
                'module_enregistrement.notification',
                {'title': 'Notification FINEX', 'message': _(message)}
            )

            _logger.info("_sendone ID %s", self.id)
        except Exception as e:
            _logger.error("Erreur lors de l'envoi de la notification ID %s: %s", self.id, str(e))






