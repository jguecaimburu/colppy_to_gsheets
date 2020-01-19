""" To DOs:

Nice to have:
- Class encapsulation.
- Private variables and methods

"""

# IMPORTS
##############################################################################

import requests
import datetime
import copy
import iki_colppy_conf
import logging


# LOGGER
##############################################################################

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_formatter = logging.Formatter("%(levelname)s: %(name)s: %(asctime)s: %(message)s")
stream_formatter = logging.Formatter("%(levelname)s: %(message)s")

file_handler = logging.FileHandler(filename="call_colppy.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(stream_formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


# CLASSES
##############################################################################

# API CALLER
################

class Caller():
    def __init__(self, colppy_configuration=None, state="testing"):
        self.state = state
        self.payload_builder = PayloadBuilder(colppy_configuration)
        self.set_available_companies()

    def set_available_companies(self):
        self.available_companies = {}
        logger.info("Setting caller available companies...")
        try:
            for company in self.get_companies():
                company_id = company["IdEmpresa"]
                company_name = company["razonSocial"]
                self.available_companies[company_name] = company_id
            logger.info("Availables companies OK")
        except KeyError:
            self.available_companies["Query Error"] = None
            logger.exception("Got these companies:", self.available_companies)
            logger.error("Check keys for company id and name")

    def get_companies(self):
        self.get_session_key()
        logger.info("Preparing companies payload...")
        companies_payload = self.payload_builder.get_list_companies_payload(self.session_key)
        logger.info("Payload ok.")
        logger.info("Getting companies...")
        companies_requester = RequestMaker(self.state)
        companies_response = companies_requester.get_response(companies_payload)
        companies_content = ResponseParser(companies_response).get_response_content()
        companies_data = companies_content["data"]
        logger.info("Got %d companies." % len(companies_data))
        return companies_data

    def get_session_key(self):
        seconds_per_min = 60
        session_duration_in_mins = 25
        now = datetime.datetime.now()
        try:
            delta_mins = (now - self.login_time).total_seconds() / seconds_per_min
            if delta_mins > session_duration_in_mins:
                open_session = self.login()
                self.session_key = open_session["data"]["claveSesion"]
                self.login_time = datetime.datetime.now()
        except AttributeError:
            open_session = self.login()
            self.session_key = open_session["data"]["claveSesion"]
            self.login_time = datetime.datetime.now()
        return self.session_key

    def login(self):
        login_payload = self.payload_builder.get_login_payload()
        logger.info("Trying to log into Colppy as %s..." % self.state)
        login_requester = RequestMaker(self.state)
        login_response = login_requester.get_response(login_payload,
                                                      request_type="post")
        login_content = ResponseParser(login_response).get_response_content()
        logger.info("Login OK.")
        return login_content

    def get_invoices_for(self, dates_range=None, company_id=None):
        self.get_session_key()
        self.assert_company_is_available(company_id)
        invoices_payload_parameters = (dates_range, company_id, self.session_key)
        logger.info("Preparing invoices payload...")
        invoices_payload = self.payload_builder.get_list_invoices_payload(*invoices_payload_parameters)
        logger.info("Payload ok.")
        logger.info("Getting invoices...")
        invoices_requester = RequestMaker(self.state)
        invoices_response = invoices_requester.get_response(invoices_payload)
        invoices_content = ResponseParser(invoices_response).get_response_content()
        invoices_data = invoices_content["data"]
        logger.info("Got %d invoices." % len(invoices_data))
        return invoices_data

    def assert_company_is_available(self, company_id):
        if company_id:
            try:
                assert company_id in self.available_companies.values()
            except AssertionError:
                logger.exception("Company ID not in available companies.")
                logger.error("Available companies:")
                logger.error(self.available_companies)

    def get_diary_for(self, dates_range=None, company_id=None):
        self.get_session_key()
        self.assert_company_is_available(company_id)
        diary_payload_parameters = (dates_range, company_id, self.session_key)
        logger.info("Preparing diary payload...")
        diary_payload = self.payload_builder.get_list_diary_payload(*diary_payload_parameters)
        logger.info("Payload ok.")
        logger.info("Getting diary...")
        diary_requester = RequestMaker(self.state)
        diary_response = diary_requester.get_response(diary_payload)
        diary_content = ResponseParser(diary_response).get_response_content()
        diary_data = diary_content["movimientos"]
        logger.info("Got %d diary movements." % len(diary_data))
        return diary_data

    def get_inventory_for(self, company_id=None):
        self.get_session_key()
        self.assert_company_is_available(company_id)
        inventory_payload_parameters = (company_id, self.session_key)
        logger.info("Preparing inventory payload...")
        inventory_payload = self.payload_builder.get_list_inventory_payload(*inventory_payload_parameters)
        logger.info("Payload ok.")
        logger.info("Getting inventory...")
        inventory_requester = RequestMaker(self.state)
        inventory_response = inventory_requester.get_response(inventory_payload)
        inventory_content = ResponseParser(inventory_response).get_response_content()
        inventory_data = inventory_content["data"]
        logger.info("Got %d items." % len(inventory_data))
        return inventory_data

    def get_deposits_stock_for(self, item_id, company_id=None):
        self.get_session_key()
        self.assert_company_is_available(company_id)
        deposit_payload_parameters = (item_id, company_id, self.session_key)
        logger.info("Preparing deposit payload...")
        deposit_payload = self.payload_builder.get_list_deposits_stock_for_item_payload(*deposit_payload_parameters)
        logger.info("Payload ok.")
        logger.info("Getting deposits for %s..." % item_id)
        deposit_requester = RequestMaker(self.state)
        deposit_response = deposit_requester.get_response(deposit_payload)
        deposit_content = ResponseParser(deposit_response).get_response_content()
        deposit_data = deposit_content["data"]
        logger.info("Got deposits.")
        return deposit_data

    def get_ccosts_for_type(self, ccost_type_1_or_2, company_id=None):
        self.get_session_key()
        self.assert_company_is_available(company_id)
        ccost_payload_parameters = (ccost_type_1_or_2, company_id, self.session_key)
        logger.info("Preparing ccost payload...")
        ccost_payload = self.payload_builder.get_list_ccost_payload(*ccost_payload_parameters)
        logger.info("Payload ok.")
        logger.info("Getting dccost for type number %d..." % ccost_type_1_or_2)
        ccost_requester = RequestMaker(self.state)
        ccost_response = ccost_requester.get_response(ccost_payload)
        ccost_content = ResponseParser(ccost_response).get_response_content()
        ccost_data = ccost_content["data"]
        logger.info("Got ccosts.")
        return ccost_data


# PAYLOAD
##########

class PayloadBuilder():
    def __init__(self, colppy_conf=None):
        if not colppy_conf:
            logger.info("Taking default Colppy configuration...")
            colppy_conf = copy.deepcopy(iki_colppy_conf.defaults)

        self.configurator = PayloadBuilderBaseConfigurator(colppy_conf)
        self.payloads = self.configurator.get_payload_templates()

        self.session_key = None

    def get_login_payload(self):
        return copy.deepcopy(self.payloads["login"])

    def get_list_companies_payload(self, session_key=None):
        self.if_session_key_then_set_it_to_payloads(session_key)
        return copy.deepcopy(self.payloads["list_companies"])

    def if_session_key_then_set_it_to_payloads(self, session_key):
        if session_key:
            self.session_key = session_key
            self.payloads = SessionKeySetter(session_key).set_key_to_payloads(self.payloads)
        else:
            if not self.session_key:
                logger.error("Please provide a Session Key.")
                raise ValueError("No session key.")
            else:
                logger.info("Session key already set to %s." % self.session_key)

    def get_list_n_ccost_payload(self, ccost_type_1_or_2, company_id=None,
                                 session_key=None):
        self.payloads = CCostTypeSetter(ccost_type_1_or_2).set_ccost_type_to_payload(self.payloads)
        self.if_session_key_then_set_it_to_payloads(session_key)
        self.if_not_company_id_use_last_one_or_default(company_id)
        return copy.deepcopy(self.payloads["list_ccosts"])

    def if_not_company_id_use_last_one_or_default(self, company_id):
        if company_id:
            self.set_company_id_to_payloads(company_id)
        else:
            try:
                logger.info("Company ID already set to %s." % self.company_id)
            except AttributeError:
                self.use_default_company_id_for_first_build()

    def use_default_company_id_for_first_build(self):
        company_id = self.configurator.get_company_id()
        if company_id:
            self.set_company_id_to_payloads(company_id)
        else:
            logger.error("Please provide a Company ID.")
            raise ValueError("No company ID.")

    def set_company_id_to_payloads(self, company_id):
        self.payloads = CompanyIdSetter(company_id).set_company_id_from_input(self.payloads)
        self.company_id = company_id

    def get_list_invoices_payload(self, dates_range=None, company_id=None,
                                  session_key=None):
        self.if_session_key_then_set_it_to_payloads(session_key)
        self.if_not_company_id_use_last_one_or_default(company_id)
        self.if_dates_then_set_them_to_payloads(dates_range)
        return copy.deepcopy(self.payloads["list_invoices"])

    def if_dates_then_set_them_to_payloads(self, dates_range):
        if dates_range:
            self.payloads = DatesSetter(dates_range).set_dates_to_payloads(self.payloads)
            self.dates_range = dates_range
        else:
            try:
                logger.info("Dates range already set from %s to %s." % self.dates_range)
            except AttributeError:
                logger.exception("Please provide a dates range.")
                raise ValueError("No dates provided.")

    def get_list_diary_payload(self, dates_range=None, company_id=None,
                               session_key=None):
        self.if_session_key_then_set_it_to_payloads(session_key)
        self.if_not_company_id_use_last_one_or_default(company_id)
        self.if_dates_then_set_them_to_payloads(dates_range)
        return copy.deepcopy(self.payloads["list_diary"])

    def get_list_inventory_payload(self, company_id=None, session_key=None):
        self.if_session_key_then_set_it_to_payloads(session_key)
        self.if_not_company_id_use_last_one_or_default(company_id)
        return copy.deepcopy(self.payloads["list_inventory"])

    def get_list_deposits_stock_for_item_payload(self, item_id,
                                                 company_id=None, session_key=None):
        self.payloads = ItemIdSetter(item_id).set_item_id_to_payload(self.payloads)
        self.if_session_key_then_set_it_to_payloads(session_key)
        self.if_not_company_id_use_last_one_or_default(company_id)
        return copy.deepcopy(self.payloads["list_deposits_for_item"])


class PayloadBuilderBaseConfigurator():
    def __init__(self, colppy_conf):
        self.colppy_conf = colppy_conf
        self.parse_configuration()

    def parse_configuration(self):
        self.set_payload_templates_from_conf()
        self.set_company_id_from_conf()

    def set_payload_templates_from_conf(self):
        logger.info("Trying to load payload templates from configuration...")
        try:
            self.payload_templates = self.colppy_conf["payload_temps"]
            logger.info(f"Loaded services: {list(self.payload_templates.keys())}")
        except KeyError:
            logger.exception("'payload_temps' key not found in configuration.")
            raise KeyError("Payload templates not found.")

    def set_company_id_from_conf(self):
        try:
            logger.info("Trying to load Company ID from configuration...")
            self.company_id = self.colppy_conf["company_id"]
            logger.info("Loaded Company ID: %s" % self.company_id)
        except KeyError:
            self.company_id = None
            logger.info("Not found.")

    def get_payload_templates(self):
        return self.payload_templates

    def get_company_id(self):
        return self.company_id


class SessionKeySetter():
    def __init__(self, session_key):
        if not session_key:
            logger.error("No key to set.")
            raise ValueError("No key to set.")
        else:
            self.session_key = session_key

    def set_key_to_payloads(self, payloads):
        logger.info("Setting key for session...")
        session_dict = self.create_session_dict(payloads)
        for key, payload in payloads.items():
            try:
                payload["parameters"]["sesion"] = copy.deepcopy(session_dict)
            except KeyError:
                logger.exception("Could not find [parameters][session] in payloads.")
                raise KeyError("Could not set session key.")
        logger.info("Key set on payloads.")
        return payloads

    def create_session_dict(self, payloads):
        session_dict = {}
        session_dict["claveSesion"] = self.session_key
        try:
            session_dict["usuario"] = payloads["login"]["parameters"]["usuario"]
        except KeyError:
            logger.exception("Could not find [parameters][session] in payloads.")
            raise KeyError("Could not set session key.")
        return session_dict


class CompanyIdSetter():
    def __init__(self, company_id):
        if not company_id:
            logger.error("No company id to set.")
            raise ValueError("No company id to set.")
        else:
            self.check_company_id(company_id)
            self.company_id = company_id

    def check_company_id(self, company_id):
        try:
            assert isinstance(company_id, str)
            int(company_id)
        except AssertionError:
            logger.exception("Company ID should be str.")
            raise ValueError("Company ID is not a str.")
        except ValueError:
            logger.exception("Company ID must be a str of an int.")
            raise ValueError("Company ID str does not contain an int.")

    def set_company_id_from_input(self, payloads):
        avoid_payloads = ("login", "list_companies")
        try:
            logger.info("Setting company to %s..." % self.company_id)
            for key, payload in payloads.items():
                if key not in avoid_payloads:
                    payload["parameters"]["idEmpresa"] = self.company_id
            logger.info("Company set on payloads.")
        except KeyError:
            logger.exception("Could not find [parameters][idEmpresa] in payloads.")
            raise KeyError("Could not set company.")
        return payloads


class CCostTypeSetter():
    def __init__(self, ccost_type_1_or_2):
        if not ccost_type_1_or_2:
            logger.error("No ccost type to set.")
            raise ValueError("No ccost type to set.")
        else:
            self.check_ccost_type(ccost_type_1_or_2)
            self.ccost_type = ccost_type_1_or_2

    def check_ccost_type(self, ccost_type_1_or_2):
        try:
            assert isinstance(ccost_type_1_or_2, int)
            assert 0 < ccost_type_1_or_2 < 3
        except AssertionError:
            logger.exception("CCost type must be integer 1 or 2.")
            raise ValueError

    def set_ccost_type_to_payload(self, payloads):
        try:
            logger.info("Setting Ccost type to %s..." % self.ccost_type)
            payloads["list_ccosts"]["parameters"]["ccosto"] = self.ccost_type
            logger.info("Done.")
        except KeyError:
            logger.exception("Could not find [parameters][ccosto] in payloads.")
            raise KeyError("Could not set ccost type.")
        return payloads


class DatesSetter():
    def __init__(self, dates_range):
        if not dates_range:
            logger.error("No dates to set.")
            raise ValueError("No dates to set.")
        else:
            self.check_dates_range(dates_range)
            self.dates_range = dates_range

    def check_dates_range(self, dates_range):
        try:
            assert len(dates_range) == 2
        except AssertionError:
            logger.exception("Dates must be a tuple of 2 str: 'YYYY-MM-DD'.")
            raise ValueError("Not enought items in dates range.")
        for date in dates_range:
            self.is_valid_date(date)

    def is_valid_date(self, date):
        try:
            self.iso_str_to_date(date)
        except ValueError:
            logger.exception("Date %s non existent or wrong format" % date)
            logger.error("Date format should be 'YYYY-MM-DD'.")
            raise ValueError("Wrong date format.")

    def iso_str_to_date(self, iso_str):
        return datetime.date.fromisoformat(iso_str)

    def set_dates_to_payloads(self, payloads):
        self.reorder_dates()
        logger.info("Setting dates for data from  %s to %s...\n" % self.dates_range)
        start_date, end_date = self.dates_range
        try:
            payloads["list_diary"]["parameters"]["fromDate"] = start_date
            payloads["list_diary"]["parameters"]["toDate"] = end_date
            payloads["list_invoices"]["parameters"]["filter"][0]["value"] = start_date
            payloads["list_invoices"]["parameters"]["filter"][1]["value"] = end_date
        except KeyError:
            logger.exception("Could not find dates keys in payloads.")
            raise KeyError("Could not set dates.")
        return payloads

    def reorder_dates(self):
        logger.info("Checking dates order...")
        start_date, end_date = self.dates_range
        if self.iso_str_to_date(start_date) > self.iso_str_to_date(end_date):
            logger.warning("End date was older than start date. Correcting...")
            start_date, end_date = end_date, start_date
        self.dates_range = (start_date, end_date)
        logger.info("Done.")


class ItemIdSetter():
    def __init__(self, item_id):
        if not item_id:
            logger.error("No item id to set.")
            raise ValueError("No item id to set.")
        else:
            if isinstance(item_id, int):
                item_id = str(item_id)
            self.check_item_id(item_id)
            self.item_id = item_id

    def check_item_id(self, item_id):
        try:
            assert isinstance(item_id, str)
        except AssertionError:
            int(item_id)
            logger.exception("Item ID should be str.")
            raise ValueError("Item ID is not a str.")
        except ValueError:
            logger.exception("Item ID must be a str of an int.")
            raise ValueError("Item ID str does not contain an int.")

    def set_item_id_to_payload(self, payloads):
        try:
            logger.info("Setting item ID to %s..." % self.item_id)
            payloads["list_deposits_for_item"]["parameters"]["idItem"] = self.item_id
            logger.info("Done.")
        except KeyError:
            logger.exception("Could not find [parameters][idItem] in payloads.")
            raise KeyError("Could not set item id.")
        return payloads


# REQUEST AND RESPONSE
#######################

class RequestMaker():
    urls = {
            "testing": "https://staging.colppy.com/lib/frontera2/service.php",
            "production": "https://login.colppy.com/lib/frontera2/service.php"
            }

    request_types = {
                      "get": requests.get,
                      "post": requests.post
                      }

    def __init__(self, state):
        if self.is_valid_state(state):
            self.state = state
            self.call_url = self.urls[self.state]
        else:
            logger.error("%s is not a valid state. Valid states:" % state)
            logger.error(self.urls.keys(), "\n")
            raise ValueError

    def is_valid_state(self, state):
        return state in self.urls.keys()

    def get_response(self, payload, request_type="get"):
        if self.is_valid_request_type(request_type):
            self.request_type = request_type
            self.payload = payload
            logger.info("Calling API...   ")
            return self.request_types[request_type](self.call_url, json=payload)
        else:
            logger.error("Request type not valid.")
            logger.error("Valid requests:", self.request_types.keys())
            raise ValueError

    def is_valid_request_type(self, request_type):
        return request_type in self.request_types.keys()


class ResponseParser():
    def __init__(self, response_json):
        if self.request_was_successful(response_json):
            logger.info("Query successful.")
        else:
            logger.error("Query not successful. Response:")
            logger.error(self.parsed_response)
            raise ValueError

    def get_response_content(self):
        return self.parsed_response["response"]

    def request_was_successful(self, response_json):
        if self.check_not_raise_status(response_json):
            self.parse_response_json(response_json)
            return self.is_response_success()

    def check_not_raise_status(self, response_json):
        try:
            response_json.raise_for_status()
            return True
        except requests.HTTPError:
            logger.exception("Query response raised HTTP status error")
            logger.error(response_json)
            return False

    def parse_response_json(self, response_json):
        self.parsed_response = response_json.json()

    def is_response_success(self):
        try:
            self.parsed_response["response"]
        except KeyError:
            logger.exception("No [response] key in response.")
            return False

        if self.parsed_response["response"]:
            try:
                success = self.parsed_response["response"]["success"]
                return success
            except KeyError:
                logger.exception("Could not check response success. Check response.")
                return False
        else:
            logger.error("Response of query is None.")
            logger.error(self.parsed_response["result"])
            logger.error(self.parsed_response["response"])
            return False
