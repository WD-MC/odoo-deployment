from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
import threading
import time
import logging
import re, base64
from datetime import datetime
_logger = logging.getLogger(__name__)

class Handle(models.TransientModel):

    _name = 'me.handle'
    _description = 'Handle'

    def _handle_documents(self, enregistrement, documents):
        """Gestion des documents liés à un enregistrement.
           - Met à jour les documents existants.
           - Crée de nouveaux documents.
           - Supprime les documents qui ne sont plus postés.
        """
        document_model = self.env['document.enregistrement']

        # Récupérer tous les documents actuellement enregistrés pour cet enregistrement
        existing_docs = document_model.search([('enregistrement_id', '=', enregistrement.id)])

        # Extraire les IDs des documents postés par le client
        posted_doc_ids = {doc.get('id') for doc in documents if doc.get('id')}

        # Identifier les documents obsolètes (présents en base mais pas dans les données postées)
        docs_to_delete = existing_docs.filtered(lambda d: d.id not in posted_doc_ids)

        if docs_to_delete:
            _logger.info(f"Suppression des documents non postés : {docs_to_delete.mapped('file_name')}")
            docs_to_delete.unlink()  # Suppression des documents obsolètes

        # Traitement des documents postés (création ou mise à jour)
        for doc in documents:
            try:
                file_data = doc.get('file')
                file_name = doc.get('file_name', 'document.pdf')
                nature_id = doc.get('nature_id', None)
                file_id = doc.get('id')

                if not file_data:
                    _logger.warning(f"Aucun fichier reçu pour {file_name}, document ignoré.")
                    continue  # Ignore ce document s'il n'y a pas de fichier

                # Nettoyage de la chaîne Base64
                cleaned_base64 = re.sub(r"(\s)|(data:.*?;base64,)", "", file_data)

                # pas nécessaire de faire un encodage à revoir si nécessaire
                # try:
                #     file_bytes = base64.b64decode(cleaned_base64, validate=True)
                # except Exception as e:
                #     _logger.error(f"Erreur de décodage Base64 pour {file_name}: {e}")
                #     raise ValidationError(f"Fichier invalide pour {file_name}")

                file_bytes = cleaned_base64

                # Vérifier si un document similaire existe déjà
                existing_doc = None
                if file_id:
                    existing_doc = document_model.search([
                        ('enregistrement_id', '=', enregistrement.id),
                        ('id', '=', file_id)
                    ], limit=1)

                if existing_doc:
                    _logger.info(f"Mise à jour du document existant {existing_doc.id} : {file_name}")
                    existing_doc.write({
                        'enregistrement_id': enregistrement.id,
                        'partner_enterprise_id': enregistrement.partner_id.id,
                        'partner_enterprise_name': enregistrement.partner_id.name,
                        'file': file_bytes,
                        'file_name': file_name,
                        'nature_id': nature_id
                    })
                else:
                    _logger.info(f"Création d'un nouveau document : {file_name}")
                    document_model.create({
                        'enregistrement_id': enregistrement.id,
                        'partner_enterprise_id': enregistrement.partner_id.id,
                        'partner_enterprise_name': enregistrement.partner_id.name,
                        'file': file_bytes,
                        'file_name': file_name,
                        'nature_id': nature_id
                    })

            except Exception as e:
                _logger.error(f"Erreur lors du traitement du document {file_name} : {str(e)}")
                raise ValidationError(f"Erreur lors de l'ajout du document {file_name} : {str(e)}")
