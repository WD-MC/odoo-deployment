import odoo
import logging
from odoo import _, models, fields, api, SUPERUSER_ID
import re, base64

phone_regex = re.compile("^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$")
#email_regex = re.compile("^[a-zA-Z0-9.]+@[a-zA-Z0-9]+\.[a-zA-Z]+")
email_regex = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$")
#email_regex = re.compile(r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+$')
date_regex = re.compile("^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

LIST_OF_YEAR = ['1ST YEAR', '2ND YEAR', '3RD YEAR']


def is_double(str_to_check: str) -> bool:
    try:
        float(str_to_check)
        return True
    except Exception as e:
        return False


class MeUtils:

    def get_registration_creation_notify_email_subject(self, vals):
        subject = 'Nouvel entité créé : {}'.format(vals['company_name'])
        return subject

    def get_registration_creation_notify_email_body(self, vals, update_url,model_application_number):

        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
            <h2 style="color: #4CAF50; text-align: center;">Bienvenue sur la plateforme FINEX</h2>
            <p style="font-size: 16px; color: #333;">Cher {vals['name']},</p>

            <p style="font-size: 16px; color: #333;">
                Votre compte a été créé avec succès avec le nom d'utilisateur :
                <strong style="color: #4CAF50;">{vals['username']}</strong>.
                L'entité créé est :
                <strong style="color: #4CAF50;">{vals['company_name']}</strong>.
                Le numéro de la transaction de création est :
                <strong style="color: #4CAF50;">{model_application_number}</strong>.
            </p>

            <p style="font-size: 16px; color: #333;">
                Veuillez noter que vous devez soumettre votre demande si ce n'est pas encore le cas. Votre compte ne sera actif qu'après  vérification et  validation de votre identité.
            </p>

            <div style="text-align: center; margin-top: 30px;">
                <p style="font-size: 14px; color: #777; margin-top: 20px;">
                    Cliquez sur le lien ci-dessous si votre demande n'est pas encore soumise.
                </p>
                <a href="{update_url}"
                   style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Soumettre votre demande
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
