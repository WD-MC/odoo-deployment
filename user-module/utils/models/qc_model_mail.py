from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
import threading
import time
import logging
_logger = logging.getLogger(__name__)



NOTIFICATION_TITLE = "Notification FINEX"

class QcModelmail(models.TransientModel):

    _name = 'qc.model.mail'
    _description = 'Model description of mail '

    _inherit = ['mail.thread.cc',
                'mail.thread.blacklist',
                'mail.activity.mixin',
                'format.address.mixin',
                ]

    email = fields.Char(string='Email')


    def send_finish_email(self, mail_template_id, attachment_content=False, attachment_label=False):
        try:
            mail_template = self.env.ref(mail_template_id)
            if not attachment_label: attachment_label = "attachment.pdf"
            data_record = (attachment_content)

            if attachment_content:
                attachment = self.env['ir.attachment'].sudo().create({
                    'name': attachment_label,
                    'type': 'binary',
                    'datas': data_record,
                    'store_fname': 'data_record',
                    'res_model': 'mail.template',
                })
                # mail_template.attachment_ids = [(4, attachment.id)]
                mail_template.attachment_ids = [(6, 0, [attachment.id])]

            mail_template.sudo().send_mail(self.id, force_send=True)

            mail_template.attachment_ids = [(3, attachment.id)]
        except Exception as e:
            print("Error")
            print(e)


    def notify_users(self, mail_template_id, attachment_content=False, attachment_label=False, role=False,
                     module=False):


        users = self.env['servicing.utils'].get_users_by_group_external_id(role)
        template_id = self.get_template_id_from_external_id(mail_template_id, module)
        for user in users:
            self.update_email_template_email_to(template_id, user.email)
            self.send_finish_email(mail_template_id, attachment_content, attachment_label)

    def update_email_template_email_to(self, template_id, new_email_to):
        # Find the email template you want to update
        template = self.env['mail.template'].browse(template_id)

        if template:
            # Update the email_to field with the new value
            template.email_to = new_email_to

            return True

        return False

    def get_template_id_from_external_id(self, external_template_id, module):
        # Search for the record with the specified external ID
        data = self.env['ir.model.data'].sudo().search([
            ('module', '=', module),  # Replace with your module name
            ('name', '=', external_template_id),  # Replace with the external ID
        ])

        if data:
            return data.res_id

        return False

    @api.model
    def send_odoo_and_email_notification(self, rec, group_to_notify_id, body):
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
        else:
            _logger.warning(
                f"Aucun serveur de mail n'a été configuré. Merci d'en configurer un pour les notifications")
        # Fetch the group by ID
        group = self.env['res.groups'].browse(group_to_notify_id)
        # Get the users in that group
        users_to_notify = group.users
        partner_ids = users_to_notify.mapped('partner_id').ids
        # Add followers (e.g., users with specific groups)
        #users_to_notify = self.env.ref('module_enregistrement.group_me_approuver').users
        #rec.message_subscribe(partner_ids=users_to_notify.mapped('partner_id').ids)
        rec.message_subscribe(partner_ids)
        _logger.info("users_to_notify1: %s", users_to_notify)
        # Post a custom notification in the chatter
        partner_name = self.env.user.partner_id.name
        rec.message_post(
            email_from=f"Notification  de:  {partner_name}",
            body=body,  # Utilise body_html pour du contenu HTML
            subject=f"Notification  de:  {partner_name}",
            message_type="notification",
            subtype_xmlid="mail.mt_note",
        )
        #self.action_send_notification()

        partner_ids = users_to_notify.mapped('partner_id').ids

        mail_values = {
            'subject': f"Tâche de la transaction n° {rec.model_application_number}",
            'body_html': self.get_registration_creation_notify_email_body(rec,body),
            'email_from': mail_server.from_filter,
            'recipient_ids': [(6, 0, partner_ids)],
        }
        # mail = self.env['mail.mail'].sudo().create(mail_values)
        # mail.sudo().send(auto_commit=False)
        # mail.sudo().with_delay().process_email_queue()
        threaded_mail = threading.Thread(
            target=self._run_email_thread, args=(mail_values,))
        threaded_mail.start()

    def _run_email_thread(self, mail_values):
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

    def _run_email_thread2(self, mail_template_id,record_id,attachments):
        """ Thread pour envoyer l'email de création """
        time.sleep(5)
        new_cr = None
        try:
            new_cr = self.pool.cursor()
            new_self = self.with_env(self.env(cr=new_cr))
            mail_template = new_self.env.ref(mail_template_id).sudo()
            # Créer un mail spécifique basé sur le template
            mail_id = mail_template.sudo().send_mail(record_id, force_send=False)  # Mettre en file d’attente
            if mail_id:
                mail = new_self.env['mail.mail'].sudo().browse(mail_id)
                mail.sudo().write({'attachment_ids': [(6, 0, attachments)]})
                # Forcer l'envoi si nécessaire
                mail.sudo().send(auto_commit=False)
            if new_cr:
                new_cr.commit()
                new_cr.close()
        except Exception as e:
            _logger.error(f"Erreur d'envoi d'email : {str(e)}")
            if new_cr:
                new_cr.commit()
                new_cr.close()


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
            else:
                _logger.warning(f"Aucun serveur de mail n'a été configuré. Merci d'en configurer un pour les notifications")

            threaded_mail = threading.Thread(
                target=self._run_email_thread, args=(mail_values,))
            threaded_mail.start()

            #mail = self.env['mail.mail'].sudo().create(mail_values)
            #mail.sudo().send(auto_commit=False)
            # if mail :
            #     mail = self.env['mail.mail'].search([('id', '=', mail.id), ('state', '=', 'outgoing')], limit=1)
            #mail.sudo().with_delay().process_email_queue()

        except Exception as e:
            _logger.error("Erreur lors de l'envoi de l'email pour l'enregistrement ID %s: %s", self.id, str(e))


    def action_send_notification(self , notification_number, notification_id,notification_module, notification_message , notification_title = NOTIFICATION_TITLE ):
        """ Envoie une notification à l'utilisateur """
        try:
            message = f"L'enregistrement {notification_number} a été mis à jour !"

            _logger.info("Notification ID %s", notification_id)

            # Envoie la notification à tous les utilisateurs connectés
            self.env['bus.bus']._sendone(
                self.env.user.partner_id,
                notification_module,
                {'title': notification_title, 'message': _(notification_message)}
            )

            _logger.info("_sendone ID %s", self.id)
        except Exception as e:
            _logger.error("Erreur lors de l'envoi de la notification ID %s: %s", self.id, str(e))



    def send_email_after_creation(self,record_id, mail_template_id, attachments_content=None, attachments_label=None):
        _logger.info("send_email_after_creation %s", mail_template_id)
        _logger.info("record_id %s", record_id)

        if attachments_label is None:
            attachments_label = []
        if attachments_content is None:
            attachments_content = []

        try:
            attachments = []

            for attach, label in zip(attachments_content, attachments_label):
                if attach:
                    attachment = self.env['ir.attachment'].sudo().create({
                        'name': label,
                        'type': 'binary',
                        'datas': attach,
                        'store_fname': False,  # Odoo gère automatiquement
                        'res_model': 'mail.mail',  # Lier aux emails et non aux templates
                        'res_id': record_id,  # Associer à un enregistrement spécifique
                    })
                    attachments.append(attachment.id)

            # Créer un mail spécifique basé sur le template
            # mail_id = mail_template.sudo().send_mail(record_id, force_send=False)  # Mettre en file d’attente
            # if mail_id:
            #     mail = self.env['mail.mail'].sudo().browse(mail_id)
            #     mail.sudo().write({'attachment_ids': [(6, 0, attachments)]})
            #
            #     # Forcer l'envoi si nécessaire
            #     mail.sudo().send(auto_commit=False)

            threaded_mail = threading.Thread(
                target=self._run_email_thread2, args=(mail_template_id,record_id,attachments,))
            threaded_mail.start()

        except Exception as e:
            _logger.error("Erreur lors de l'envoi de l'email pour l'enregistrement ID %s: %s", self.id, str(e))



    def get_registration_creation_notify_email_body(self, rec, body):

        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
            <h2 style="color: #4CAF50; text-align: center;">Bienvenue sur la plateforme FINEX</h2>

            <p style="font-size: 16px; color: #333;">
                Une nouvelle tâche  vous a été assignée dans votre espace de travail. <br/>
                <strong>Message</strong> : {body}
            </p>
           
            <div style="text-align: center; margin-top: 30px;">
                <p style="font-size: 14px; color: #777; margin-top: 20px;">
                    Cliquez sur le lien ci-dessous pour accéder à la tâche en cours dans votre espace de travail.
                </p>
                <a href="{rec.access_url}"
                   style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Accèder à la tâche
                </a>
            </div>

            <p style="font-size: 14px; color: #777; margin-top: 20px;">
                <strong style="color: #4CAF50;">
                    ⚠️ Merci de ne pas répondre à ce mail
                </strong>.
            </p>

            <p style="font-size: 12px; color: #aaa; text-align: center; margin-top: 30px;">
                © 2025 FINEX. Tous droits réservés.
            </p>
        </div>
        """

        return body_html

