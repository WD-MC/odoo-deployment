import odoo
import logging
import random, string

from odoo import _, models, fields, api, SUPERUSER_ID
from odoo.http import request
from .constants import NATIONALITIES_EN, NATIONALITIES_FR, GHANA_STATES, GHANA_DISTRICTS

from datetime import datetime
from odoo.osv import expression
from odoo.exceptions import  ValidationError, UserError

from datetime import datetime, date,  timedelta
from dateutil.relativedelta import relativedelta

from werkzeug.exceptions import abort, BadRequest

given_date = '21/1/2021'
print('Give Date: ', given_date)

date_format = '%d/%m/%Y'
dtObj = datetime.strptime(given_date, date_format)

# Subtract 20 months from a given datetime object
n = 20
past_date = dtObj - relativedelta(months=n)

print('Past Date: ', past_date)
print('Past Date: ', past_date.date())

# Convert datetime object to string in required format
past_date_str = past_date.strftime(date_format)
print('Past Date as string object: ', past_date_str)
import base64
from odoo.tools.mimetypes import guess_mimetype

import codecs
import csv
import locale
import time
import calendar

import qrcode
import base64
from io import BytesIO

_logger = logging.getLogger(__name__)


DEFAULT_LOCALE = "en_US.UTF-8"
DEFAULT_FORMAT = "%d-%b-%y"
DEFAULT_FORMAT_2 ="%Y-%m-%d %H:%M:%S"
DEFAULT_FORMAT_3 = "%d-%b-%Y"

#Exemple format pour ce pattern : '140,000,555,444.22'
NUMERIC_PATTERN = "^(\d+?\,)*\d+?.\d+?$"

import re

# str1 = '140,000,000.22'
# print(bool(re.match(NUMERIC_PATTERN, str1)))

NOTIFICATION_TITLE = "Notification FINEX"

class Utils(models.TransientModel):
    _name = 'servicing.utils'
    _description = 'Model for utilities'

    def binary_to_csv(self, binarie_doc):
        """ Convert memory binary String to csv String
       Return csv memory string
       :param String  source: contains de reprentation string of .cvs file
       """

        file_string = False
        if binarie_doc:
            try:
                file = base64.b64decode(binarie_doc)
                file_string = file.decode('utf-8')
            except UnicodeDecodeError as e:
                 print(e)

            # process error
        return file_string


    def csv_to_binary(self, csv_doc):
        """ Convert memory csv String to binary String
       Return binary memory string
       :param String  source: contains de reprentation string of .cvs file
       """
        sample_string = csv_doc
        sample_string_bytes = sample_string.encode("ascii")

        base64_bytes = base64.b64encode(sample_string_bytes)
        base64_string = base64_bytes.decode("ascii")
        #print(f"Encoded string: {base64_string}")
        return base64_string


    def csv_to_dictionnary(self, source):
        """ Convert memory csv String to Dictionary
        Return dictionary
        :param String  source: contains de reprentation string of .cvs file
        """
        #_reader = codecs.getreader('utf-8')
        #dict = csv.DictReader(_reader(source), quotechar='"', delimiter=',')
        dict = csv.DictReader(source, quotechar='"', delimiter=',')
        return dict

    def dictionnary_to_csv(self, source, output, fieldnames, delimiter=','):
        """ Convert  Dictionary to  memory csv String
        Return emory csv String
        :param String  source: contains the dictionnary list
        """
        writer = csv.DictWriter(output, fieldnames, delimiter)
        writer.writeheader()
        writer.writerows(source)
        return output.getvalue()

    def read_chunks(self,infile, chunksize=4096):
        yield infile[0:chunksize]

    def setLocale(self, default_locale=DEFAULT_LOCALE):
        locale.setlocale(locale.LC_NUMERIC, default_locale)

    def string_to_number(self, string, default_locale=DEFAULT_LOCALE):
        self.setLocale(default_locale)
        if string!=False : string=string.strip()
        if string == '' :
            string = '0'
        number = locale.atof(string)
        return number


    def string_to_timestamp(self, string, default_format=DEFAULT_FORMAT, default_locale=DEFAULT_LOCALE):
        locale.setlocale(locale.LC_TIME, 'C')
        if string != False and  string != '':
            string = string.strip()
            element = datetime.strptime(string,default_format)
            # tuple = element.timetuple()
            # timestamp = time.mktime(tuple)
            # return timestamp
            return element
        else:
            return None

    def string_is_timestamp(self, string, default_format=DEFAULT_FORMAT, default_locale=DEFAULT_LOCALE):
        locale.setlocale(locale.LC_TIME, 'C')

        try:
            if string != False and  string != '':
                string = string.strip()
                element = datetime.strptime(string,default_format)
                return True
            else:
                return False
        except ValueError:
            return False

    def string_is_numeric(self, string,  default_numeric_pattern=NUMERIC_PATTERN):
        if string :
             string = string.strip()
             return (bool(re.match(default_numeric_pattern, string))  or  (string.isnumeric()))
        else :
             return  False

    def get_current_time(self):
        current_time = datetime.now()
        return current_time


    def init_list_with_non_numeric_field(self, row_number, field, row={}, log_liste_dict=[]):

        if not self.string_is_numeric(row.get(field)):
            log_dict = {}
            log_dict["line"] = "Line " + str(row_number)
            log_dict["column"] = " Column: "+ field
            log_dict[
                "description"] = "Error : Field '" + field + "' is not a numeric format (ie 140,000,555,444.22). Current value is : " + str(
                row.get(field))
            log_dict["status"] = "ERROR"
            log_dict["time"] = self.get_current_time()

            log_liste_dict.append(log_dict)

        return log_liste_dict


    def init_list_with_non_datetime_field(self, row_number, field, row={}, log_liste_dict=[]):

        if not self.string_is_timestamp(row.get(field)):
            log_dict = {}
            log_dict["line"] = "Line " + str(row_number)
            log_dict["column"] = " Column: "+ field
            log_dict[
                "description"] = "Error : Field '" + field + "' is not a datetime format (ie 14-Mar-23). Current value is : " + str(
                row.get(field))
            log_dict["status"] = "ERROR"
            log_dict["time"] = self.get_current_time()

            log_liste_dict.append(log_dict)

        return log_liste_dict

    def compare_date(self, string_date1, string_date2, default_format=DEFAULT_FORMAT):
        date1 = self.string_to_timestamp(string_date1, default_format)
        date2 = self.string_to_timestamp(string_date2, default_format)
        tuple1 = date1.timetuple()
        tuple2 = date2.timetuple()
        timestamp1 = time.mktime(tuple1)
        timestamp2 = time.mktime(tuple2)
        return   (timestamp2 >= timestamp1)

    def init_list_with_compare_date(self, row_number, field1, field2, date1, date2, log_liste_dict=[]):

        string_date1 = str(date1)
        string_date2 = str(date2)
        if not self.compare_date(string_date1, string_date2):
            log_dict = {}
            log_dict["line"] = "Line " + str(row_number)
            log_dict["column"] = " Column: " + field1 + " and Column: "  + field2
            log_dict["description"] = "Error : Field '" + field1 + " : " + str(date1) + " > "  + field2 + " : " + str(date2)
            log_dict["status"] = "ERROR"
            log_dict["time"] = self.get_current_time()

            log_liste_dict.append(log_dict)

        return log_liste_dict

    def convert_date(self, string, default_format=DEFAULT_FORMAT  , default_format_2=DEFAULT_FORMAT_2 ):
        timestamp = self.string_to_timestamp(string, default_format_2)
        return timestamp.strftime(default_format)



    def get_year_from_date(self, string, default_format=DEFAULT_FORMAT, default_locale=DEFAULT_LOCALE):
        locale.setlocale(locale.LC_TIME, 'C')
        if string != False and  string != '':
            string = string.strip()

            #element_string = datetime.strptime(string,default_format).strftime(DEFAULT_FORMAT_3)
            element = datetime.strptime(string,default_format)
            tuple = element.timetuple()
            return tuple.tm_year
        else:
            return None


    def get_month_from_date(self, string, default_format=DEFAULT_FORMAT, default_locale=DEFAULT_LOCALE):
        locale.setlocale(locale.LC_TIME, 'C')
        if string != False and  string != '':
            string = string.strip()
            element = datetime.strptime(string,default_format)
            tuple = element.timetuple()
            return  calendar.month_name[tuple.tm_mon]
        else:
            return None

    def is_last_month_date(self, string, current_month, current_year, default_format=DEFAULT_FORMAT, default_locale=DEFAULT_LOCALE):
        month = self.get_month_from_date(string, default_format)
        year = self.get_year_from_date(string, default_format)
        return (str(month)==current_month) and (str(year)==current_year)

    def init_list_with_not_last_month_date(self, row_number, field, string, current_month, current_year, log_liste_dict=[] , default_format=DEFAULT_FORMAT , default_locale=DEFAULT_LOCALE):

        if not self.is_last_month_date(string, current_month, current_year, default_format):
            log_dict = {}
            log_dict["line"] = "Line " + str(row_number)
            log_dict["column"] = " Column: " + field
            log_dict["description"] = "Error : Field '" + field + " : " + string + "  is not in range of  " + current_month + "-" + current_year
            log_dict["status"] = "ERROR"
            log_dict["time"] = self.get_current_time()

            log_liste_dict.append(log_dict)

        return log_liste_dict


    def get_list_from_object(self, objects):
        list = []
        for obj in objects:
            if obj.name != False and obj.name != '':
                string = (obj.name).strip()
            list.append(string)
        return  list
    def check_string_in_list(self, string,  list_of_string):
        if string != False and string != '':
            string = (string).strip()
        return string in  list_of_string

    def init_list_with_facilicities_not_check_contract_currencies(self, row_number, field, string, list_of_string,  log_liste_dict=[]):

        if not self.check_string_in_list(string, list_of_string):
            log_dict = {}
            log_dict["line"] = "Line " + str(row_number)
            log_dict["column"] = " Column: " + field
            log_dict["description"] = "Error : Field '" + field + " : " + string + "  is not in "  + ','.join(list_of_string)
            log_dict["status"] = "ERROR"
            log_dict["time"] = self.get_current_time()

            log_liste_dict.append(log_dict)

        return log_liste_dict


    def init_list_with_non_exist_sme(self, row_number, field, string, sme, log_liste_dict=[]):

        if not sme:
            log_dict = {}
            log_dict["line"] = "Line " + str(row_number)
            log_dict["column"] = " Column: " + field
            log_dict["description"] = "Error : Field '" + field + " : " + string + "  is not an existing SME or this SME has been excluded. First create or activate this SME in the system"
            log_dict["status"] = "ERROR"
            log_dict["time"] = self.get_current_time()

            log_liste_dict.append(log_dict)

        return log_liste_dict


    def compute_sme_total_facility_amount(self, test_list, grp_key, sum_keys):
        # Python3 code to demonstrate working of
        # Summation Grouping in Dictionary List
        # Using loop

        # initializing list
        # test_list = [{'Gfg': 1, 'id': 2, 'best': 8, 'geeks': 10},
        #              {'Gfg': 4, 'id': 4, 'best': 10, 'geeks': 12},
        #              {'Gfg': 4, 'id': 8, 'best': 11, 'geeks': 15}]

        # printing original list
        #print("The original list is : " + str(test_list))

        # initializing group key
        #grp_key = 'Gfg'

        # initializing sum keys
        #sum_keys = ['best', 'geeks']

        # Summation Grouping in Dictionary List
        # Using loop
        res = {}
        for sub in test_list:
            ele = sub[grp_key]
            if ele not in res:
                res[ele] = {x: 0 for x in sum_keys}
            for y in sum_keys:
                if  self.string_is_numeric(sub[y]):
                    res[ele][y] += int(self.string_to_number(sub[y]))
        # printing result
        #print("The grouped list : " + str(res))

        return res

    def init_list_with_compare_total_amount(self, row_number, field1, field2, amount1, amount2, log_liste_dict=[]):

        if not amount2 >=  amount1:
            log_dict = {}
            log_dict["line"] = "Line " + str(row_number)
            log_dict["column"] = " Column: " + field1 + " and Column: " + field2
            log_dict["description"] = "Error total amount per SME exceeded : Field '" + field1 + " : " + str(amount1) + " > " + field2 + " : " + str(
                amount2)
            log_dict["status"] = "ERROR"
            log_dict["time"] = self.get_current_time()

            log_liste_dict.append(log_dict)

        return log_liste_dict


    def init_list_with_non_existing_field(self, row_number, field, row={}, log_liste_dict=[]):

        if row.get(field)=="" or row.get(field)==False or row.get(field)==None:
            log_dict = {}
            log_dict["line"] = "Line " + str(row_number)
            log_dict["column"] = " Column: "+ field
            log_dict["description"] = "Error : Field '" + field + "' is  a mandatory field "
            log_dict["status"] = "ERROR"
            log_dict["time"] = self.get_current_time()

            log_liste_dict.append(log_dict)

        return log_liste_dict

    def get_number_of_days(self, date1, date2):
        # date1_todate = date1.date()
        # delta = date2-date1_todate
        delta = date2 - date1
        if delta :
         return delta.days
        else:
         return 0

    def get_number_of_days2(self, date1, date2):
        date2_todate = date2.date()
        delta = date2_todate - date1
        if delta:
            return delta.days
        else:
            return 0
    def get_number_of_days3(self, date1, date2):
        date1_todate = date1.date()
        delta = date2 - date1_todate
        if delta:
            return delta.days
        else:
            return 0
    def get_days_in_year(self,year=datetime.now().year):
        return 365 + calendar.isleap(year)

    def init_list_with_error(self, error, log_liste_dict=[]):

        log_dict = {}
        log_dict["line"] = "Line undefined"
        log_dict["column"] = " Column undefined"
        log_dict["description"] = "Program runtime error : "  +  str(error)
        log_dict["status"] = "ERROR"
        log_dict["time"] = self.get_current_time()
        log_liste_dict.append(log_dict)

        return log_liste_dict


    def get_range_projected(self, project_days_in_arrear):
        if  0<=project_days_in_arrear<=30 :
            return "0 - 30 Days"
        elif  31<=project_days_in_arrear<=60 :
            return "31 - 60 Days"
        elif  61<=project_days_in_arrear<=90 :
            return "61 - 90 Days"
        elif 91 <= project_days_in_arrear <= 180:
            return "91 - 180 Days"
        else:
            return  "Above 180 Days"


    def get_board_report(self, project_days_in_arrear):
        if  0<=project_days_in_arrear<=30 :
            return ""
        elif  31<=project_days_in_arrear<=60 :
            return ""
        elif  61<=project_days_in_arrear<=90 :
            return ""
        elif 91 <= project_days_in_arrear <= 180:
            return ""
        else:
            return  "NPL"


    def remove_month_from_date(self, date_generation, month):
        past_date = date_generation - relativedelta(months=month)
        return past_date

    def get_difference(self, date1, date2):
        delta = date2 - date1
        return delta.days


    def add_day_to_date(self, days, my_date):
        return my_date + relativedelta(days=days)

    def add_month_to_date(self, date_generation, month):
        futur_date = date_generation + relativedelta(months=month)
        return futur_date



    def get_first_company(self):
        """
            get first create company for an organisation
        """
        res = self.env['res.company'].sudo().search([], order='id asc', limit=1)

        return res

    def base64_decode(self, binary_data_64_encode):
        """ Decode previous encode binary data
       """
        # converting the base64 code into ascii characters
        convertbytes = binary_data_64_encode.encode("utf8")
        # converting into bytes from base64 system
        convertedbytes = base64.b64decode(convertbytes)
        # decoding the ASCII characters into alphabets
        decodedsample = convertedbytes.decode("utf8")
        return decodedsample

    def generate_random_password(length=12):
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for _ in range(length))
        return password

    # Example usage:
    password = generate_random_password()
    print(password)


    def get_users_by_role(self, role_name):
        # Define the name of the role/group you want to retrieve users from
        group = self.env['res.groups'].search([('name', '=', role_name)])
        if group:
            # Get the users belonging to the specified role
            users = self.env['res.users'].search([('groups_id', 'in', group.ids)])
            return users
        return False

    def get_users_by_group_external_id(self, group_external_id):
        # Search for the group with the specified external ID
        group = self.env.ref(group_external_id, raise_if_not_found=False)

        if group:
            # Get the users belonging to the specified group
            users = group.users

            return users

        return False

    def get_current_date(self):
        current_date = date.today()
        return current_date

    def get_current_date_time(self):
        current_date = date.today()
        now = datetime.now()
        return str(current_date)+'-'+str(now.hour)+':'+str(now.minute)+':'+str(now.second)+':'+str(now.microsecond)

    def get_timestamp(self):
        return time.time()


    # def _create_documents(self, content, name, partner_name, partner_id):
    #     default_root_directory = "Partners"
    #     if not (content or name or partner_name) :
    #         raise ValidationError(_('content, name and partner_name must be defined: Please contact your administrator.'))
    #
    #     directory_id = False
    #     res=self.env['dms.directory'].sudo().search([('name', 'like',partner_name)], order='id asc', limit=1)
    #     if res:
    #         directory_id = res.id
    #     else:
    #         res_directory = self.env['dms.directory'].sudo().search([('name', 'like', default_root_directory)], order='id asc', limit=1)
    #         if res_directory :
    #             values={
    #                 "name" : partner_name,
    #                 "storage_id": res_directory.storage_id.id,
    #                 "parent_id": res_directory.id,
    #                 "res_model": res_directory.res_model,
    #                 "res_id": partner_id,
    #             }
    #             result = self.env['dms.directory'].sudo().create(values)
    #             directory_id = result.id
    #
    #     document_values = {
    #         'name': str(self.get_timestamp())+"_"+name,
    #         'content': content,
    #         'directory_id' : directory_id,
    #
    #     }
    #     result = self.env['dms.file'].sudo().create(document_values)
    #     if result :
    #         return result.id
    #     else :
    #         raise ValidationError(_('Unable to create document: Please contact your administrator.'))

    def _create_documents(self, content, name, partner_name, partner_id, orignal_file_name, mimetype):
        if not (content and name and partner_name):
            raise ValidationError(
                _('Content, name, and partner_name must be defined. Please contact your administrator.'))

        # Vérification de l'existence du partenaire
        partner = self.env['res.partner'].browse(partner_id)
        if not partner.exists():
            raise ValidationError(_('The specified partner does not exist.'))

        # Nom du document avec horodatage
        document_name = f"{self.get_timestamp()}_{name}"

        # Création du document en tant que pièce jointe (ir.attachment)
        document = self.env['ir.attachment'].sudo().create({
            'name': document_name,
            #'datas': base64.b64encode(content.encode('utf-8')),  # Encodage en base64
            'datas': content.encode('utf-8'),  # Encodage en utf-8
            'res_model': 'res.partner',  # Lien avec le modèle partenaire
            'res_id': partner_id,
            'store_fname': orignal_file_name,
            'mimetype': mimetype,  # Définir le type MIME si connu
        })

        _logger.info(f"Document créé avec succès : {document.name} lié au partenaire ID {partner_id}")

        return document

    @api.model
    def check_user_route_permission(self, user_id, code):
        user_code_role = []
        # Get Admin User
        user_record = request.env['admin.custom.user'].sudo().search_read(
            [('custom_user_id', '=', int(user_id)), ('is_actif', '=', True)])
        if len(user_record) > 0:
            # Get User Profile
            profiles_ids = user_record[0]['profile_ids'][0]
            profiles_results = request.env['admin.users.profiles'].sudo().search_read([
                ('id', '=', int(profiles_ids))])
            if len(profiles_results) > 0:
                # Get User Role
                roles_id = profiles_results[0]['roles_ids']
                for id_role in roles_id:
                    role_result = request.env['admin.users.roles'].sudo().search_read([
                        ('id', '=', int(id_role))])
                    if len(role_result) > 0:
                        # Get User code role
                        for roles in role_result:
                            user_code_role.append(int(roles['code']))
                # Check if the code is in user code role
                print("User code role: ", user_code_role)
                if int(code) in user_code_role:
                    return True
                else:
                    return False
            else:
                return False
        else:
            user_record = self.env['res.users'].sudo().search_read(
                [('id', '=', int(user_id))])
            if len(user_record) > 0:
                user_record_login = user_record[0]['login']
                registration_record = self.env['rm.registration.model'].sudo().search_read([
                    ('portal', '=', True), ('username', '=', user_record_login)])
                if len(registration_record) > 0:
                    return True
                else:
                    return False
            else:
                return False

    def get_nationalities(self):
        return NATIONALITIES_EN

    def _generate_qr(self,recs, context):
        "method to generate QR code  + '&model=am.application.model&view_type=form&cids="
        for rec in recs:
            print("Context:",context)
            if qrcode and base64:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=3,
                    border=4,
                )
                link = self.get_current_url(rec, context)
                qr.add_data(link)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                # print("temp", link)
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue()).decode('ascii')
                # print("code", qr_image)
                rec.sudo().update({'qr_code': qr_image})
            else:
                raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))



    def get_current_url(self,rec, context):
        """Current base URL of the Odoo instancehttp://localhost:8069/report/pdf/application_form_module.report_application_form_model_gfza/1"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not 'localhost' in base_url:
            if 'http://' in base_url:
                base_url = base_url.replace('http://', 'https://')
        return base_url + context + str(rec.id) #rec.id

    def send_email_on_creation2(self, rec, mail_values, message_type='email', subtype_xmlid='mail.mt_comment'):
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
            rec.message_post(
                body=mail_values.get("body_html"),
                subject=mail_values.get("subject"),
                message_type=message_type,
                subtype_xmlid=subtype_xmlid,
                email_from=mail_values.get("email_from"),
                email_to=mail_values.get("email"),
            )
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
            else:
                _logger.warning(f"Aucun serveur de mail n'a été configuré. Merci d'en configurer un pour les notifications")
            mail = self.env['mail.mail'].sudo().create(mail_values)
            #mail.sudo().send()
            mail.sudo().send(auto_commit=False)
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
            mail_template = self.env.ref(mail_template_id).sudo()
            mail_id = mail_template.sudo().send_mail(record_id, force_send=False)  # Mettre en file d’attente
            if mail_id:
                mail = self.env['mail.mail'].sudo().browse(mail_id)
                mail.sudo().write({'attachment_ids': [(6, 0, attachments)]})

                # Forcer l'envoi si nécessaire
                mail.sudo().send(auto_commit=False)
                #mail.sudo().with_delay().process_email_queue()

        except Exception as e:
            _logger.error("Erreur lors de l'envoi de l'email pour l'enregistrement ID %s: %s", self.id, str(e))


    def authenticate_token(self):
        self._auth_method_rpc()

    def _auth_method_rpc(cls):
        access_token = request.httprequest.headers.get('Authorization')
        if not access_token:
            raise BadRequest('Access token missing')

        if access_token and (m := re.match(r"^bearer\s+(.+)$", access_token, re.IGNORECASE)):
            access_token = m.group(1)
        # if access_token.startswith('Bearer '):
        #     access_token = access_token[7:]

        user_id = request.env["res.users.apikeys"]._check_credentials(scope='rpc', key=access_token)
        if not user_id:
            raise BadRequest('Access token invalid')

        # take the identity of the API key user
        request.update_env(user=user_id)

        # switch to the user context
        request.update_context(**request.env.user.context_get())




