import json

from odoo import models
from werkzeug.wrappers import Response
from odoo.http import Response as OdooResponse


class MessageAlertType:
    warning = "warning"
    info = "info"
    error = "error"
    success = "success"


class ResultType:
    list_result = "list"
    object_result = "object"


class ApiResultFormatter:
    _name = "api.result.formatter"
    """
        this class Allows to send results in unified formatted way for all apis endpoint
    """

    @classmethod
    def format_odoo_way(cls, data):
        return {
            "jsonrpc": 2.0,
            "id": None,
            "result": data
        }

    @classmethod
    def send_object(cls, *, data: object, status_code: int, success: bool, message: str,
                    message_type: str, odoo_request) -> Response:
        to_send = {"data": data, "type": ResultType.object_result, "status": status_code,
                   "success": success, "message": message, "message_type": message_type}
        if odoo_request.httprequest.method.lower() != "get":
            return to_send

        return Response(json.dumps(ApiResultFormatter.format_odoo_way(to_send), default=str), status=status_code,
                        content_type="application/json")

    @classmethod
    def send_list(cls, *, data: list, status_code: int, success: bool, message: str, message_type: str,
                  odoo_request) -> Response:
        to_send = {"data": data, "type": ResultType.list_result, "status": status_code, "length": len(data),
                   "success": success, "message": message, "message_type": message_type.lower()}
        if odoo_request.httprequest.method.lower() != "get":
            return to_send

        return Response(json.dumps(ApiResultFormatter.format_odoo_way(to_send), default=str), status=status_code,
                        content_type="application/json")
