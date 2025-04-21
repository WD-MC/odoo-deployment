import odoo
from odoo import _, models, fields, api, SUPERUSER_ID
import requests
import time
import logging

HTTP_404 = 404
HTTP_401 = 401
HTTP_400 = 400
HTTP_200 = 200
ssl_verify = True

username = 'zent-freezones'
password = ''
dlr = 1
type_ = 0
source = 'GFZAAPI'
api_url = "http://rslr.connectbind.com:8080/bulksms/bulksms"



class SMSApiModel(models.TransientModel):
    _name = "sms.api"
    _description = "smsAPI"

    def send_sms(destination, message):   
        
        logging.info(
             time.ctime() + " TRY SENDING SMS TO: " + destination
        )     
        
        payload = {
            'username': username,
            'password': password,
            'type': type_,
            'dlr': dlr,
            'destination': destination,
            'source': source,
            'message': message
        }

        try:
            response = requests.get(api_url, params=payload)
            
            logging.info(
                    time.ctime() + " RESPONSE " + " - SEND SMS-" + repr(response)
            )            

            if response.status_code == HTTP_200:
                return response
            else:
                logging.warning(
                    time.ctime()
                    + " httpStatus"
                    + response["httpStatus"]
                    + "localDateTime"
                    + response["localDateTime"]
                    + "apiErr"
                    + response["apiErr"]
                    + "apiErrs"
                    + response["apiErrs"]
                )
                                
                return f"Failed to send SMS: {response.text}"

        except requests.RequestException as e:
            logging.warning(
                    time.ctime()
                    + " httpStatus"
                    + response["httpStatus"]
                    + "localDateTime"
                    + response["localDateTime"]
                    + "apiErr"
                    + response["apiErr"]
                    + "apiErrs"
                    + response["apiErrs"]
            )
                                    
            return f"Failed to send SMS: {str(e)}"