import odoo
import logging
from odoo import _, models, fields, api, SUPERUSER_ID
import re, base64
from datetime import datetime

phone_regex = re.compile("^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$")
#email_regex = re.compile("^[a-zA-Z0-9.]+@[a-zA-Z0-9]+\.[a-zA-Z]+")
email_regex = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$")
#email_regex = re.compile(r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+$')
date_regex = re.compile("^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

LIST_OF_YEAR = ['1ST YEAR', '2ND YEAR', '3RD YEAR']




class Transformer:

    @staticmethod
    def _transform_data(data):
        """Transformation des données avant insertion en base"""
        transformed_data = {
            'is_portal_action': True,
            'name': data.get('name', '').strip().upper(),
            'company_name': data.get('company_name', '').strip().upper(),
            'email': data.get('email', '').strip().lower(),
            'telephone': data.get('telephone', '').strip(),
            'username': data.get('username', '').strip().lower(),
            'password': data.get('password', '12345'),
            'numero_enregistrement': data.get('reference', f"REF-{int(datetime.timestamp(datetime.now()))}"),
            'date_enregistrement': data.get('company_registration_date', datetime.today().strftime("%Y-%m-%d")),
        }
        return transformed_data

