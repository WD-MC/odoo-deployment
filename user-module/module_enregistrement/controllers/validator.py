from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
import threading
import time
import logging
import re, base64
from datetime import datetime
_logger = logging.getLogger(__name__)

phone_regex = re.compile("^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$")
#email_regex = re.compile("^[a-zA-Z0-9.]+@[a-zA-Z0-9]+\.[a-zA-Z]+")
email_regex = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$")
#email_regex = re.compile(r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+$')
date_regex = re.compile("^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

LIST_OF_YEAR = ['1ST YEAR', '2ND YEAR', '3RD YEAR']


class Validator(models.TransientModel):

    _name = 'me.validator'
    _description = 'Validator'

    def _validate_payload(self, data):
        """Validation des données reçues du client"""
        required_fields = ['name', 'company_name', 'email', 'telephone', 'username']
        errors = {}

        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = f"{field} est requis."

        if 'company_registration_date' in data:
            try:
                datetime.strptime(data['company_registration_date'], "%Y-%m-%d")
            except ValueError:
                errors['company_registration_date'] = "Le format de la date doit être YYYY-MM-DD."

        if 'document_ids' in data:
            if not isinstance(data['document_ids'], list):
                errors['document_ids'] = "Le champ doit être une liste de documents."
            else:
                for doc in data['document_ids']:
                    if 'file' not in doc or 'file_name' not in doc:
                        errors['document_ids'] = "Chaque document doit contenir 'file' et 'file_name'."

        if errors:
            return {"status": "error", "errors": errors}, 400
        return None, None