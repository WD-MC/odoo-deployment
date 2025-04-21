# -*- coding: utf-8 -*-
from odoo import http, SUPERUSER_ID
from odoo.http import request, Response
import json
import logging
from datetime import datetime
import base64
import re
from odoo.exceptions import  ValidationError
from werkzeug.exceptions import abort, BadRequest
from .transformer import Transformer
from ...utils.models.result_formatter import *
import traceback

DEFAULT_TYPE_WORKFLOW ="01"
WORKFLOW_SUBMIT_STAGE = "0102"
_MESSAGE = "Pour traitement"

_logger = logging.getLogger(__name__)


class MeEnregistrementAPI(http.Controller):

    @http.route('/api/enregistrement/create', type='json', auth='public', methods=['POST'], csrf=False)
    def create_enregistrement(self, **post):
        cr = request.env.cr
        try:
            request.env["servicing.utils"].authenticate_token()

            # Validation
            validation_errors, status = request.env['me.validator']._validate_payload(post)
            if validation_errors:
                return ApiResultFormatter.send_object(
                    data={}, message=json.dumps(validation_errors), status_code=status,
                    message_type=MessageAlertType.warning, success=False, odoo_request=request
                )



            # Transformation + Création
            transformed_data = Transformer._transform_data(post)
            cr.execute("BEGIN;")
            enregistrement = request.env['me.enregistrement'].with_context(is_portal_action=True).create(
                transformed_data)

            if 'document_ids' in post:
                request.env['me.handle']._handle_documents(enregistrement, post['document_ids'])


            cr.commit()

            return ApiResultFormatter.send_object(
                data={
                    "id": enregistrement.id,
                    "model_application_number": enregistrement.model_application_number,
                },
                message="Enregistrement créé avec succès.",
                status_code=201,
                message_type=MessageAlertType.success,
                success=True,
                odoo_request=request
            )

        except Exception as e:
            cr.rollback()
            _logger.error("Erreur lors de la transaction : %s\n%s", str(e), traceback.format_exc())
            return ApiResultFormatter.send_object(
                data={}, message = "Une erreur est survenue pendant la transaction. veuillez contacter le service support. {}".format(e),
                status_code=500, message_type=MessageAlertType.error, success=False, odoo_request=request
            )

    @http.route('/api/enregistrement/edit/<int:record_id>', type='json', auth='public', methods=['PUT'], csrf=False)
    def update_enregistrement(self, record_id, **post):
        """ ✅ Modification d'un enregistrement """
        cr = request.env.cr  # Curseur de la transaction
        try:
            request.env["servicing.utils"].authenticate_token()
            _logger.info(f"id : {str(record_id)}")
            enregistrement = request.env['me.enregistrement'].with_context(is_portal_action=True).search( [ ('id', '=', record_id)])
            _logger.info(f"enregistrement : {str(enregistrement)}")
            if not enregistrement.exists():
                return ApiResultFormatter.send_object(
                    data={}, message=json.dumps({"status": "error", "message": "Enregistrement non trouvé."}), status_code=404,
                    message_type=MessageAlertType.warning, success=False, odoo_request=request
                )

            # Validation
            validation_errors, status = request.env['me.validator']._validate_payload(post)
            if validation_errors:
                return ApiResultFormatter.send_object(
                    data={}, message=json.dumps(validation_errors), status_code=status,
                    message_type=MessageAlertType.warning, success=False, odoo_request=request
                )

            transformed_data = Transformer._transform_data(post)

            #  Début de la transaction
            cr.execute("BEGIN;")

            enregistrement.write(transformed_data)

            # Mettre à jour ou ajouter les documents
            if 'document_ids' in post:
                request.env['me.handle']._handle_documents(enregistrement, post['document_ids'])

            # Validation de la transaction
            cr.commit()

            return ApiResultFormatter.send_object(
                data={
                    "id": enregistrement.id,
                    "model_application_number": enregistrement.model_application_number,
                },
                message="Modification effectuée avec succès.",
                status_code=200,
                message_type=MessageAlertType.success,
                success=True,
                odoo_request=request
            )

        except Exception as e:
            cr.rollback()
            _logger.error("Erreur lors de la transaction : %s\n%s", str(e), traceback.format_exc())
            return ApiResultFormatter.send_object(
                data={},
                message="Une erreur est survenue pendant la transaction. veuillez contacter le service support. {}".format(
                    e),
                status_code=500, message_type=MessageAlertType.error, success=False, odoo_request=request
            )


    @http.route('/api/enregistrement/unlink/<int:record_id>', type='json', auth='public', methods=['DELETE'])
    def delete_enregistrement(self, record_id):
        """ ✅ Supprimer un enregistrement avec ses documents associés """
        cr = request.env.cr  # Curseur de la transaction

        _logger.info(f"delete_enregistrement: {record_id}")
        request.env["servicing.utils"].authenticate_token()


        enregistrement = request.env['me.enregistrement'].with_context(is_portal_action=True).search(
            [('id', '=', record_id)])
        if not enregistrement.exists():
            return ApiResultFormatter.send_object(
                data={}, message=json.dumps({"status": "error", "message": "Enregistrement non trouvé."}),
                status_code=404,
                message_type=MessageAlertType.warning, success=False, odoo_request=request
            )


        _logger.info(f"Suppression des enregistrements {enregistrement}")

        try:

            model_application_number = enregistrement.model_application_number

            cr.execute("BEGIN;")

            # Supprimer l'enregistrement
            enregistrement.unlink()

            # Validation de la transaction
            cr.commit()

            return ApiResultFormatter.send_object(
                data={
                    "id": record_id,
                    "model_application_number": model_application_number,
                },
                message="Suppression effectuée avec succès.",
                status_code=204,
                message_type=MessageAlertType.success,
                success=True,
                odoo_request=request
            )

        except Exception as e:
            cr.rollback()
            _logger.error("Erreur lors de la transaction : %s\n%s", str(e), traceback.format_exc())
            return ApiResultFormatter.send_object(
                data={},
                message="Une erreur est survenue pendant la transaction. veuillez contacter le service support. {}".format(
                    e),
                status_code=500, message_type=MessageAlertType.error, success=False, odoo_request=request
            )


    @http.route('/api/enregistrement/list', type='http', auth='public', methods=['GET'])
    def get_enregistrements(self, partner_id=None):
        """
        Récupère tous les enregistrements.
        """
        try:
            request.env["servicing.utils"].authenticate_token()
            partner_id = request.params.get('partner_id')

            if not partner_id :
                # Récupérer tous les enregistrements
                _logger.info(f"not partner_id {partner_id}")
                enregistrements = request.env['me.enregistrement'].with_context(is_portal_action=True).search([])
            else:
                # Récupérer tous les enregistrements
                _logger.info(f"partner_id {partner_id}")
                enregistrements = request.env['me.enregistrement'].with_context(is_portal_action=True).search( [('partner_id', '=', partner_id)])

            # Construire la réponse
            result = []
            for enr in enregistrements:

                result.append({
                    'id': enr.id,
                    'company_name': enr.company_name,  # Nom de l'entité
                    'numero_enregistrement': enr.numero_enregistrement,  # Numéro d'enregistrement
                    'date_enregistrement': enr.date_enregistrement.strftime(
                        '%Y-%m-%d') if enr.date_enregistrement else None,
                    'email': enr.email,
                    'telephone': enr.telephone,
                    'username': enr.username,
                    'access_url': enr.access_url,

                })
            return ApiResultFormatter.send_list(data=result,
                                                status_code=200,
                                                success=True,
                                                message_type=MessageAlertType.success,
                                                message="Liste des enregistrements retournée avec succès",
                                                odoo_request=request)


        except Exception as e:
            _logger.error("Erreur lors de la transaction : %s\n%s", str(e), traceback.format_exc())

            return ApiResultFormatter.send_list(
                data={},
                message="Une erreur est survenue pendant la transaction. veuillez contacter le service support. {}".format(
                    e),
                status_code=500, message_type=MessageAlertType.error, success=False, odoo_request=request
            )





    @http.route('/api/enregistrement/<int:enregistrement_id>', auth='public', methods=['GET'], type='http')
    def get_one_enregistrement(self, enregistrement_id):
        """Retourne un enregistrement avec ses documents associés"""
        try:
            request.env["servicing.utils"].authenticate_token()
            enregistrement = request.env['me.enregistrement'].with_context(is_portal_action=True).search([('id', '=', enregistrement_id)], limit=1)
            if not enregistrement:
                return {'error': 'Enregistrement non trouvé'}

            # Récupération des documents associés
            documents = []
            for doc in enregistrement.document_ids:
                documents.append({
                    'id': doc.id,
                    'name': doc.file_name,
                    'type': doc.mimetype,
                    'nature_id': doc.nature_id.id,
                    'file_url': f"/api/document-enregistrement/download/{doc.id}" if doc.id else None,
                })

            # Construction de la réponse
            data = {
                'id': enregistrement.id,
                'name': enregistrement.name,
                'company_name': enregistrement.company_name,
                'numero_enregistrement': enregistrement.numero_enregistrement,
                'date_enregistrement': enregistrement.date_enregistrement.strftime(
                    '%Y-%m-%d') if enregistrement.date_enregistrement else None,
                'email': enregistrement.email,
                'telephone': enregistrement.telephone,
                'login': enregistrement.username,
                'access_url': enregistrement.access_url,
                'documents': documents
            }

            return ApiResultFormatter.send_list(data=data,
                                                status_code=200,
                                                success=True,
                                                message_type=MessageAlertType.success,
                                                message="Liste des enregistrements retournée avec succès",
                                                odoo_request=request)


        except Exception as e:
            _logger.error("Erreur lors de la transaction : %s\n%s", str(e), traceback.format_exc())

            return ApiResultFormatter.send_list(
                data={},
                message="Une erreur est survenue pendant la transaction. veuillez contacter le service support. {}".format(
                    e),
                status_code=500, message_type=MessageAlertType.error, success=False, odoo_request=request
            )

    @http.route('/api/document-enregistrement/download/<int:document_id>', type='http', methods=['GET'], auth='public', cors="*")
    def download_document(self, document_id=None, **kwargs):
        """ Télécharge un fichier attaché à un document.enregistrement """
        request.env["servicing.utils"].authenticate_token()

        document = request.env['document.enregistrement'].sudo().search([('id', '=', document_id)], limit=1)

        if not document:
            return Response("Document introuvable", status=404)

        if not document.file or not document.file_name:
            return Response("Aucun fichier attaché à cet enregistrement", status=404)

        try:
            # Décodage du fichier Base64
            file_content = base64.b64decode(document.file)
        except Exception as e:
            return Response(f"Erreur lors du décodage du fichier : {str(e)}", status=500)

        file_name = document.file_name
        mimetype = document.mimetype or 'application/octet-stream'

        headers = [
            ('Content-Type', mimetype),
            ('Content-Disposition', f'attachment; filename="{file_name}"')
        ]

        return Response(file_content, headers=headers)


    @http.route('/api/enregistrement/submit/<int:record_id>', type='json', auth='public', methods=['PUT'],
                csrf=False)
    def submit_enregistrement(self, record_id=None, **post):
        """ Soumet un enregistrement au système """
        cr = request.env.cr  # Curseur de la transaction
        try:
            request.env["servicing.utils"].authenticate_token()
            _logger.info(f"id : {str(record_id)}")
            enregistrement = request.env['me.enregistrement'].with_context(is_portal_action=True).search(
                [('id', '=', record_id)])
            _logger.info(f"enregistrement : {str(enregistrement)}")

            if not enregistrement.exists():
                return ApiResultFormatter.send_object(
                    data={}, message=json.dumps({"status": "error", "message": "Enregistrement non trouvé."}),
                    status_code=404,
                    message_type=MessageAlertType.warning, success=False, odoo_request=request
                )

                # Validation
            validation_errors, status = request.env['me.validator']._validate_payload(post)
            if validation_errors:
                return ApiResultFormatter.send_object(
                    data={}, message=json.dumps(validation_errors), status_code=status,
                    message_type=MessageAlertType.warning, success=False, odoo_request=request
                )


            # if not enregistrement.exists():
            #     return Response(json.dumps({"status": "error", "message": "Enregistrement non trouvé."}), status=404,
            #                     content_type='application/json')
            #
            # validation_errors, status_code = request.env['me.validator']._validate_payload(post)
            # if validation_errors:
            #     return Response(json.dumps(validation_errors), status=status_code, content_type='application/json')

            transformed_data = Transformer._transform_data(post)

            #  Début de la transaction
            cr.execute("BEGIN;")

            enregistrement.write(transformed_data)

            # Mettre à jour ou ajouter les documents
            if 'document_ids' in post:
                request.env['me.handle']._handle_documents(enregistrement, post['document_ids'])

            model_workflow = request.env['qc.model.workflow'].with_context(
                default_type_workflow=DEFAULT_TYPE_WORKFLOW, active_id=record_id,active_model='me.enregistrement',
            )
            model_workflow.move_to_stage_after_start_event(WORKFLOW_SUBMIT_STAGE, enregistrement.model_workflow_id.id,_MESSAGE)
            # To move from one stage to another one used this one below
            #qc_model_workflow.with_context(default_type_workflow='31').move_from_one_stage_to_another_stage("3105", "3102", rec.model_workflow_id.id)

            # Validation de la transaction
            cr.commit()

            # Send notification email
            _logger.info("start send_email_after_creation   %s", "send_email_after_creation")
            documents = [doc.file_id.datas for doc in enregistrement.document_ids if doc.file_id.datas]
            labels = [doc.file_id.name for doc in enregistrement.document_ids if doc.file_id.name]
            request.env['qc.model.mail'].send_email_after_creation(enregistrement.id,
                                                                  'module_enregistrement.registration_submit_notify_email_template',
                                                                  documents,
                                                                  labels)

            return ApiResultFormatter.send_object(
                data={
                    "id": enregistrement.id,
                    "model_application_number": enregistrement.model_application_number,
                },
                message="Soumission effectuée avec succès.",
                status_code=200,
                message_type=MessageAlertType.success,
                success=True,
                odoo_request=request
            )

        except Exception as e:
            cr.rollback()
            _logger.error("Erreur lors de la transaction : %s\n%s", str(e), traceback.format_exc())
            return ApiResultFormatter.send_object(
                data={},
                message="Une erreur est survenue pendant la transaction. veuillez contacter le service support. {}".format(
                    e),
                status_code=500, message_type=MessageAlertType.error, success=False, odoo_request=request
            )
