# -*- coding: utf-8 -*-
import json
import pycountry
from odoo import http
from odoo.http import request
from .result_formater import ApiResultFormatter, MessageAlertType
from .constants import GHANA_STATES, GHANA_DISTRICTS, NATIONALITIES_EN

BASE_COMPAGNY = 1

class Utils(http.Controller):
    @http.route('/api/utils/countries/list', type='http', methods=['GET'], auth='public', cors="*")
    def list_country(self, **kw):
        list_countries = request.env['res.country'].sudo().search_read([], [])
        result = []
        for item in list_countries:
            result.append({
                'id': item['id'],
                'name': item['name'],
                'code': item['code'],
                'phone_code': item['phone_code']
            })
        # return request.env["api.result.formatter"].send_list(data=result, status_code=200, success=True, message="List of countries return with success", message_type=MessageAlertType.success)
        return ApiResultFormatter.send_list(data=result, status_code=200, success=True,
                                            message="List of countries return with success",
                                            message_type=MessageAlertType.success, odoo_request=request)

    @http.route('/api/utils/ecowas/list', type='http', auth='public', methods=['GET'], cors="*")
    def list_ecowas(self, **kw):
        ecowas_rec = request.env['qc.model.ecowas'].sudo().search_read([], [])
        result = []
        for val in ecowas_rec:
            result.append({
                "heading_id": val["heading_id"][1],
                "tsn": val["tsn"],
                "commodity_description": val["commodity_description"],
                "standard_unit": val["standard_unit"],
                "import_duty": val["import_duty"],
                "st": val["st"]
            })
        return ApiResultFormatter.send_list(data=result, status_code=200, success=True,
                                            message="List of ecowas return with success",
                                            message_type=MessageAlertType.success, odoo_request=request)
        # data = {'status': 200, 'response': result, 'message': 'Success'}
        # return Response(json.dumps(data), status=500, content_type="application/json")

    @http.route('/api/utils/countries/getCountryById', type='http', auth='public', methods=['GET'], cors="*")
    def get_country_by_id(self, **rec):
        countries = request.env['res.country'].sudo().search_read([('id', '=', rec['id'])])
        result = []
        for country in countries:
            result.append({
                'id': country['id'],
                'name': country['name'],
                'code': country['code'],
                'phone_code': country['phone_code']
            })

        return ApiResultFormatter.send_object(data=result[0] if len(result) > 0 else {}, status_code=200, success=True,
                                              message="country return with success" if len(result) > 0 else "Id "
                                                                                                            "doesn't "
                                                                                                            "exist",
                                              message_type=MessageAlertType.success if len(
                                                  result) > 0 else MessageAlertType.error,
                                              odoo_request=request)

    @http.route('/api/utils/countries/states', type='http', auth='public', methods=['GET'], cors="*")
    def get_country_states(self, **rec):
        code = rec['code']
        subdivisions = pycountry.subdivisions.get(country_code=code)
        result = []
        if subdivisions:
            for state in subdivisions:
                result.append({
                    'code': state.code,
                    'name': state.name,
                    'country': state.country.name,
                })
        return ApiResultFormatter.send_list(data=result, status_code=200, success=True,
                                            message="countries states return with success" if len(
                                                result) > 0 else "Code "
                                                                 "doesn't "
                                                                 "exist",
                                            message_type=MessageAlertType.success if len(
                                                result) > 0 else MessageAlertType.error,
                                            odoo_request=request)

    @http.route('/api/utils/countries/getCountryByCode', type='http', auth='public', methods=['GET'], cors="*")
    def get_country_by_code(self, **rec):
        countries = request.env['res.country'].sudo().search_read([('code', '=', rec['code'])])
        result = []
        for country in countries:
            result.append({
                'id': country['id'],
                'name': country['name'],
                'code': country['code'],
                'phone_code': country['phone_code']
            })

        return ApiResultFormatter.send_object(data=result[0] if len(result) > 0 else {}, status_code=200, success=True,
                                              message="country return with success" if len(result) > 0 else "Code "
                                                                                                            "doesn't "
                                                                                                            "exist",
                                              message_type=MessageAlertType.success if len(
                                                  result) > 0 else MessageAlertType.error,
                                              odoo_request=request)

    @http.route('/api/utils/ghana/states', type='http', auth='public', method=['GET'], cors='*')
    def get_ghana_state(self, **rec):
        return ApiResultFormatter.send_list(data=GHANA_STATES, status_code=200, success=True,
                                            message="List of Ghana states",
                                            message_type=MessageAlertType.success, odoo_request=request)

    @http.route('/api/utils/ghana/districts', type='http', auth='public', method=['GET'], cors='*')
    def get_ghana_districts(self, **rec):
        return ApiResultFormatter.send_list(data=GHANA_DISTRICTS, status_code=200, success=True,
                                            message="List of Ghana districts",
                                            message_type=MessageAlertType.success, odoo_request=request)

    @http.route('/api/utils/ghana/districts/byCode', type='http', auth='public', method=['GET'], cors='*')
    def get_ghana_districts_by_code(self, **rec):
        result = next((item for item in GHANA_DISTRICTS if item['code'] == rec['code']), [])
        print(result)
        return ApiResultFormatter.send_list(data=result['districts'] if len(result) > 0 else [], status_code=200,
                                            success=True,
                                            message="List of Ghana districts",
                                            message_type=MessageAlertType.success, odoo_request=request)

    @http.route('/api/utils/nationalities/list', type='http', auth='public', method=['GET'], cors='*')
    def get_nationalities(self, **rec):
        return ApiResultFormatter.send_list(data=NATIONALITIES_EN, status_code=200, success=True,
                                            message="List nationalities",
                                            message_type=MessageAlertType.success, odoo_request=request)

    @http.route('/api/utils/currency/list', type='http', auth='public', method=['GET'], cors='*')
    def get_currencies(self, **rec):
        result = []
        try:
            currencies = request.env['res.currency'].sudo().with_context({'company_id': BASE_COMPAGNY}).search_read([('active', '=', True),('status', '=', 'validated')])
            if len(currencies) > 0:
                message = "List of currencies return successfully"
                status_code = 200
                message_type = MessageAlertType.success
                for c in currencies:
                    result.append({
                        'id': c['id'],
                        'currency': c['name'],
                        'name': c['full_name'],
                        'symbol': c['symbol'],
                        'rate': c['rate'],
                        'date': c['date']
                    })
            else:
                message = "List of currencies is empty"
                status_code = 404
                message_type = MessageAlertType.success
        except Exception as e:
            message = "An error occurs during insertion in " \
                      "database. {}".format(e)
            status_code = 500
            message_type = MessageAlertType.error

        return ApiResultFormatter.send_list(data=result,
                                            status_code=status_code,
                                            success=True,
                                            message=message,
                                            message_type=message_type,
                                            odoo_request=request)

    @http.route('/api/utils/currency/rate', type='http', auth='public', method=['GET'], cors='*')
    def get_currency_rate(self, **rec):
        result = {}
        try:
            rates = request.env['res.currency.rate'].sudo().with_context({'company_id': BASE_COMPAGNY}).search_read(
                [('currency_id', '=', int(rec['currencyId'])), ('company_id', '=', int(rec['companyId']))],
                order='name desc',
                limit=1
            )
            if len(rates) == 1:
                message = "Rate return successfully"
                status_code = 200
                message_type = MessageAlertType.success
                rate = rates[0]
                result = {
                    'id': rate['id'],
                    'rate': rate['rate'],
                    'date': rate['name']
                }
            else:
                message = "Rate is empty"
                status_code = 404
                message_type = MessageAlertType.success
        except Exception as e:
            message = "An error occurs during insertion in " \
                      "database. {}".format(e)
            status_code = 500
            message_type = MessageAlertType.error

        return ApiResultFormatter.send_object(data=result,
                                              status_code=status_code,
                                              success=True,
                                              message=message,
                                              message_type=message_type,
                                              odoo_request=request)

    @http.route('/api/utils/company/list', type='http', auth='public', method=['GET'], cors='*')
    def get_list_company(self, **rec):
        result = []
        try:
            companies = request.env['res.company'].sudo().search_read()
            if len(companies) > 0:
                message = "Companies return successfully"
                status_code = 200
                message_type = MessageAlertType.success
                for c in companies:
                    result.append({
                        'id': c['id'],
                        'date': c['name']
                    })
            else:
                message = "Companies is empty"
                status_code = 200
                message_type = MessageAlertType.success

        except Exception as e:
            message = "An error occurs during insertion in " \
                      "database. {}".format(e)
            status_code = 500
            message_type = MessageAlertType.error

        return ApiResultFormatter.send_list(data=result,
                                            status_code=status_code,
                                            success=True,
                                            message=message,
                                            message_type=message_type,
                                            odoo_request=request)



    # add by console

    @http.route('/api/utils/title/list', type='http', methods=['GET'], auth='user', cors="*")
    def get_list_title(self, **rec):
        result = []
        status_code = 200
        message_type = MessageAlertType.success
        try:
            purposes = request.env['res.partner.title'].sudo().search_read([])
            if len(purposes) > 0:
                for purpose in purposes:
                    result.append({
                        'id': purpose['id'],
                        'name': purpose['name'],
                        'shortcut': purpose['shortcut'],
                    })
                message = "List of title return with success"
            else:
                message = "List of title is empty"
        except Exception as e:
            message = "An error occurs during insertion in " \
                      "database. {}".format(e)
            status_code = 500
            message_type = MessageAlertType.error
        return ApiResultFormatter.send_list(data=result,
                                            status_code=status_code,
                                            success=status_code == 200,
                                            message_type=message_type,
                                            message=message,
                                            odoo_request=request)

    @http.route('/api/utils/nationalities/list_items', type='http', auth='public', method=['GET'], cors='*')
    def get_nationalities_items(self, **rec):
        result = []
        status_code = 200
        message_type = MessageAlertType.success
        try:
            purposes  = request.env['servicing.utils'].get_nationalities()
            if len(purposes) > 0:
                for purpose in purposes:
                    result.append({
                        'id': purpose[0],
                        'name': purpose[1],
                    })
                message = "List of nationalities return with success"
            else:
                message = "List of nationalities is empty"
        except Exception as e:
            message = "An error occurs during insertion in " \
                      "database. {}".format(e)
            status_code = 500
            message_type = MessageAlertType.error
        return ApiResultFormatter.send_list(data=result,
                                            status_code=status_code,
                                            success=status_code == 200,
                                            message_type=message_type,
                                            message=message,
                                            odoo_request=request)
        
    @http.route('/api/utils/units/list', type='http', methods=['GET'], auth='public', cors="*")
    def unit_list(self, **kw):
        unit_list = request.env['uom.uom'].sudo().search_read([], [])
        result = []
        for item in unit_list:
            result.append({
                'id': item['id'] or False,
                'name': item['name'],
                'category_id': item['category_id'],
                'uom_type': item['uom_type'],
            })
        # return request.env["api.result.formatter"].send_list(data=result, status_code=200, success=True, message="List of countries return with success", message_type=MessageAlertType.success)
        return ApiResultFormatter.send_list(data=result, status_code=200, success=True,
                                            message="List of units return with success",
                                            message_type=MessageAlertType.success, odoo_request=request)
