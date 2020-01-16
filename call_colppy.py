""" To DOs:
- Write comments to more functions if necesary.

Nice to have:
- Check return None on error handling - Clean Code.
- Class encapsulation.

"""

# IMPORTS
##############################################################################

import requests
import datetime
import copy
import colppy_configuration
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


# SESSION CLASS
##############################################################################


class ColppySession(object):
    def __init__(self, colppy_defaults=None):
        """A Colppy session object gets inititialized with a dictionary of dict
        containing some of the following information and keys:
        - "payload_temps" (optional): Templates for the different Colppy calls
            of the program. This version contains "login", "list_companies",
            "list_ccost", "list_diary", "list_invoices", "list_inventory" and
            "list_deposits_for_item". Each of these keys contain the dictionary
            form of a json payload according to the Colppy API documentation.
        - "ccosts" (optional): Dictionary containing the existing ccosts to
            filter the diary. First keys: 1, 2 (integers). Second keys:
            CCost name as str. Value: CCost ID as str, as it appears on the
            diary response.
        - "company_id" (optional): Str of the company ID as it appears on
            Colppy diary and invoices.
        Having these last two dicts avoid making calls to the API to get that
        data and set default values.
        If no input is given, takes the defaults from module colppy_defaults.
        Check colppy_configuration.py for default values.
        """

        if not colppy_defaults:
            colppy_defaults = colppy_configuration.colppy_defaults
        defaults = copy.deepcopy(colppy_defaults)
        self.payloads = defaults["payload_temps"]

        try:
            self.ccosts = defaults["ccosts"]
        except KeyError:
            self.ccosts = {}

        try:
            self.company_id = defaults["company_id"]
        except KeyError:
            self.company_id = None

    def __repr__(self):
        """Object description, including session key after login (if logged)
        and state of login (production or testing).
        """
        line_1 = "Colppy Session.\n"
        try:
            line_2 = "".join(["Session Key:", self.key, "\n",
                             "Session State:", self.state])
        except AttributeError:
            line_2 = "Unlogged."
        return "".join([line_1, line_2])

    def login_and_set_session_key_for(self, state):
        try:
            logger.info("Trying to log into Colppy as %s..." % state)
            self.login_call = ColppyCall(state)
            self.login_resp = self.login_call.get_response(
                                                        self.payloads["login"],
                                                        "post"
                                                        )
            logger.info("Login OK.")
            self.state = state
            self.set_session_key_to_payloads()
        except ValueError:
            logger.exception("An exception ocurred during login. Check call object.")

    def set_invoices_for(self, dates_range=None, company_id=None):
        """Dates range is a tuple of dates in str isoformat. The movements
        corresponding to this dates are included in the response.
        Company ID is a str of an int representing the company id in Colppy.
        If no arguments are given, the object searches for the ones used for
        the last call.
        Set the object variable "invoices" with the data part of the API
        response, which is a list of dictionaries. Each dictionary contains
        data for one invoice.
        """

        logger.info("Getting invoices...")
        self.set_input_for_call(company_id, dates_range)
        self.call_list_invoices()
        self.invoices = self.list_invoices_resp["data"]
        logger.info("Got %d invoices.\n" % len(self.invoices))

    def set_diary_for(self, dates_range=None, company_id=None):
        """Dates range is a tuple of dates in str isoformat. The movements
        corresponding to this dates are included in the response.
        Company ID is a str of an int representing the company id in Colppy.
        If no arguments are given, the object searches for the ones used for
        the last call.
        Set the object variable "diary" with the data part of the API
        response, which is a list of dictionaries. Each dictionary contains
        data for one diary movement.
        """

        logger.info("Getting diary movs...")
        self.set_input_for_call(company_id, dates_range)
        self.call_list_diary()
        self.diary = self.list_diary_resp["movimientos"]
        logger.info("Got %d diary movs." % len(self.diary))

    def set_inventory(self, company_id=None):
        """Company ID is a str of an int representing the company id in Colppy.
        If no arguments are given, the object searches for the ones used for
        the last call.
        Set the object variable "inventory" with the data part of the API
        response, which is a list of dictionaries. Each dictionary contains
        data for one inventory item.
        """

        logger.info("Getting inventory...")
        self.check_and_set_company_for_call(company_id)
        self.call_list_inventory()
        self.inventory = self.list_inventory_resp["data"]
        logger.info("Got %d items." % len(self.inventory))

    def get_deposits_for(self, item_id, company_id=None):
        """ Item ID is a str that represents the item id in Colppy.
        Company ID is a str of an int representing the company id in Colppy.
        If no company id is given, the object searches for the one used for
        the last call.
        Returns the data part of the API response, which is a list of dict.
        Each dictionary contains name of the deposit and the quantity of the
        item in that deposit.
        """

        logger.info("Getting deposits for %s..." % item_id)
        self.check_and_set_company_for_call(company_id)
        deposits_for_item_resp = self.call_list_deposits_for_item(item_id)
        try:
            deposits_for_item = deposits_for_item_resp["data"]
            logger.info("Got deposits.")
            return deposits_for_item
        except KeyError:
            logger.exception("Can't get data key for %s." % item_id)
            logger.error("Check deposits response:")
            logger.error(deposits_for_item_resp)
            raise KeyError

    def set_session_key_to_payloads(self):
        try:
            logger.info("Setting key for session...")
            self.set_session_dict()
        except KeyError:
            logger.exception("Check login payload response.")
            logger.error(self.login_resp)
            raise KeyError("Could not get session key.")

        try:
            for key, payload in self.payloads.items():
                payload["parameters"]["sesion"] = copy.deepcopy(self.session)
            logger.info("Key set on payloads.")
        except KeyError:
            logger.exception("Could not find [parameters][session] in payloads.")
            raise KeyError("Could not set session key.")

    def set_session_dict(self):
        self.session = {}
        self.key = self.login_resp["data"]["claveSesion"]
        self.session["usuario"] = self.payloads["login"]["parameters"]["usuario"]
        self.session["claveSesion"] = self.key

    def set_input_for_call(self, company_id=None, dates_range=None):
        try:
            self.check_and_set_company_for_call(company_id)
            self.check_and_set_dates_for_call(dates_range)
        except ValueError:
            logger.exception("Missing data.")
            raise ValueError("Missing data.")

    def check_and_set_company_for_call(self, company_id=None):
        if not company_id:
            self.set_default_company_id()
        else:
            self.check_company_id(company_id)
            self.last_call_company_id = company_id

        try:
            logger.info("Setting company to %s..." % self.last_call_company_id)
            for key, payload in self.payloads.items():
                payload["parameters"]["idEmpresa"] = self.last_call_company_id
            logger.info("Company set on payloads.")
        except KeyError:
            logger.exception("Could not find [parameters][idEmpresa] in payloads.")
            raise KeyError("Could not set company.")

    def set_default_company_id(self):
        try:
            self.last_call_company_id
        except AttributeError:
            if self.company_id:
                self.last_call_company_id = self.company_id
            else:
                logger.error("No company given. Please set a company for call and re-run method.\n")
                logger.error(self.get_available_companies())
                raise ValueError("No company given.")

    def check_company_id(self, company_id):
        try:
            assert isinstance(company_id, str)
            int(company_id)
        except AssertionError:
            logger.exception("Company ID should be str.")
            raise ValueError("Company ID should be str.")
        except ValueError:
            logger.exception("Company ID must be a str of an int.")
            raise ValueError("Company ID must be a str of an int.")

        try:
            assert self.is_valid_company(company_id)
        except AssertionError:
            logger.exception("Company not found in available companies: \n")
            logger.error(self.get_available_companies())

    def check_and_set_dates_for_call(self, dates_range=None):
        if not dates_range:
            try:
                dates_range = self.last_call_dates
            except AttributeError:
                logger.exception("No dates given.")
                raise ValueError("No dates given.")

        if self.is_valid_dates_range(dates_range):
            self.set_dates_for_call(dates_range)
        else:
            logger.exception("Check dates range and re-run method.")
            raise ValueError("Dates error.")

    def set_dates_for_call(self, dates_range):
        logger.info("Setting dates for data from  %s to %s...\n" % dates_range)
        start_date, end_date = self.reorder_dates(dates_range)
        self.payloads["list_diary"]["parameters"]["fromDate"] = start_date
        self.payloads["list_diary"]["parameters"]["toDate"] = end_date
        self.payloads["list_invoices"]["parameters"]["filter"][0]["value"] = start_date
        self.payloads["list_invoices"]["parameters"]["filter"][1]["value"] = end_date
        self.last_call_dates = (start_date, end_date)

    def call_list_invoices(self):
        try:
            self.list_invoices_call = ColppyCall(self.state)
            self.list_invoices_resp = self.list_invoices_call.get_response(self.payloads["list_invoices"])
            logger.info("Invoices query OK.")
        except ValueError:
            logger.exception("An exception ocurred during query. Check call object.")
            raise ValueError

    def call_list_diary(self):
        try:
            self.list_diary_call = ColppyCall(self.state)
            self.list_diary_resp = self.list_diary_call.get_response(self.payloads["list_diary"])
            logger.info("Diary query OK.")
        except ValueError:
            logger.exception("An exception ocurred during query. Check call object.")
            raise ValueError

    def call_list_companies(self):
        try:
            self.list_companies_call = ColppyCall(self.state)
            self.list_companies_resp = self.list_companies_call.get_response(self.payloads["list_companies"])
            logger.info("Companies query OK.")
        except ValueError:
            logger.exception("An exception ocurred during query. Check call object.")
            raise ValueError

    def call_list_ccost(self, n_ccost):
        logger.info("Getting ccosts %d...\n" % n_ccost)
        list_ccost_n_payload = copy.deepcopy(self.payloads["list_ccost"])
        list_ccost_n_payload["parameters"]["ccosto"] = n_ccost
        try:
            self.list_ccost_call = ColppyCall(self.state)
            self.list_ccost_resp = self.list_ccost_call.get_response(list_ccost_n_payload)
            logger.info("Ccost query OK.")
        except ValueError:
            logger.exception("An exception ocurred during query. Check call object.")
            raise ValueError

    def call_list_inventory(self):
        try:
            self.list_inventory_call = ColppyCall(self.state)
            self.list_inventory_resp = self.list_inventory_call.get_response(self.payloads["list_inventory"])
            logger.info("Inventory query OK.")
        except ValueError:
            logger.exception("An exception ocurred during query. Check call object.")
            raise ValueError

    def call_list_deposits_for_item(self, item_id):
        list_deposits_for_item_payload = copy.deepcopy(self.payloads["list_deposits_for_item"])
        list_deposits_for_item_payload["parameters"]["idItem"] = item_id
        try:
            list_deposits_for_item_call = ColppyCall(self.state)
            list_deposits_for_item_resp = list_deposits_for_item_call.get_response(list_deposits_for_item_payload)
            logger.info("Deposits query OK.")
            return list_deposits_for_item_resp
        except ValueError:
            logger.exception("An exception ocurred during query. Check call object.")
            raise ValueError

    def set_available_companies(self):
        try:
            self.list_companies_resp
        except AttributeError:
            self.call_list_companies()

        logger.info("Getting available companies...")

        self.available_companies = {}
        try:
            for company in self.list_companies_resp["data"]:
                comp_id = company["IdEmpresa"]
                comp_name = company["razonSocial"]
                self.available_companies[comp_name] = comp_id
            logger.info("Availables companies OK")
        except KeyError:
            self.available_companies["Query Error"] = None
            logger.exception("Got these companies:", self.available_companies, "\n")
            logger.error("Check keys for company id and name. Response:\n")
            logger.error(self.list_companies_resp)


    def update_available_companies(self):
        logger.info("Updating available companies...")
        self.call_list_companies()
        self.set_available_companies()

    def update_n_ccosts(self, n_ccost):
        try:
            self.last_call_company_id
        except AttributeError:
            self.check_and_set_company_for_call()
        self.call_list_ccost(n_ccost)
        try:
            for code in self.list_ccost_resp["codigos"]:
                if code["Codigo"] not in self.ccosts[n_ccost].keys():
                    self.ccosts[n_ccost][code["Codigo"]] = code["Id"]
        except KeyError:
            logger.warning("Could not find 'codigos', check response.")
            logger.warning(self.list_ccost_resp)

    def is_valid_company(self, company_id):
        try:
            self.available_companies
        except AttributeError:
            self.set_available_companies()
        if company_id not in self.available_companies.values():
            self.update_available_companies()
        return company_id in self.available_companies.values()

    def is_valid_dates_range(self, dates_range):
        try:
            assert len(dates_range) == 2
        except AssertionError:
            logger.exception("Dates must be a tuple of 2 str: 'YYYY-MM-DD'")
            return False
        for date in dates_range:
            if not self.is_valid_date(date):
                return False
        return True

    def is_valid_date(self, date):
        try:
            self.iso_str_to_date(date)
            return True
        except ValueError:
            logger.exception("Date %s non existent or wrong format" % date)
            logger.error("Date format should be 'YYYY-MM-DD'.")
            return False

    def is_ccost_in_n_ccosts(self, name_ccost, n_ccost):
        if name_ccost == "" or name_ccost == " " or name_ccost is None:
            return True
        if name_ccost not in self.ccosts[n_ccost].keys():
            self.update_n_ccosts(n_ccost)
        return name_ccost in self.ccosts[n_ccost].keys()

    def compare_ccost(self, ccost_filter, ccost_mov):
        if ccost_filter is None:
            return True
        else:
            return ccost_mov == ccost_filter

    def get_available_companies(self):
        try:
            self.available_companies
        except AttributeError:
            self.set_available_companies()
        return self.available_companies

    def reorder_dates(self, dates_range):
        start_date, end_date = dates_range
        if self.iso_str_to_date(start_date) > self.iso_str_to_date(end_date):
            start_date, end_date = end_date, start_date
            logger.warning("End date was older than start date. Correcting...",
                           "(stupid human)\n")
        return (start_date, end_date)

    def iso_str_to_date(self, iso_str):
        return datetime.date.fromisoformat(iso_str)


# CALL CLASS
#############################################################################

class ColppyCall(object):
    """ Get's inititialized with the state of the call ("testing" or
    "production" to select the correct url for the requests.
    """
    urls = {
            "testing": "https://staging.colppy.com/lib/frontera2/service.php",
            "production": "https://login.colppy.com/lib/frontera2/service.php"
            }

    call_requests = {
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

    def __repr__(self):
        """Object description, including state and the service of the payload
        given when making the request.
        """
        line_1 = "".join(["Colppy Call.", "\n",
                          "Call State:", self.state, "\n"])
        try:
            line_2 = "".join(["Call Service:", str(self.payload["service"])])
        except AttributeError:
            line_2 = "Call Service: Not made."
        return "".join([line_1, line_2])

    def get_response(self, payload, request_type="get"):
        """If no errors, returns the "response" value of the response
        dictionary it received from the API for the payload. By default makes
        a "get" http request.
        """
        try:
            self.response
        except AttributeError:
            self.call_api(payload, request_type)
        if self.is_call_successful():
            logger.info("Query successful.")
            return self.response["response"]
        else:
            logger.error("Query not successful. Response:")
            logger.error(self.response)
            raise ValueError

    def call_api(self, payload, request_type):
        """ Makes the given http request to the API with the input payload.
        Set payload and response_json (the response) as object variables.
        """
        if self.is_valid_request_type(request_type):
            logger.info("Calling API...   ")
            self.payload = payload
            self.response_json = self.call_requests[request_type](self.call_url,
                                                                  json=self.payload)
        else:
            logger.error("Request type not valid.")
            logger.error("Valid requests:", self.call_requests.keys())
            raise ValueError

    def is_valid_state(self, state):
        return state in self.urls.keys()

    def is_valid_request_type(self, request_type):
        return request_type in self.call_requests.keys()

    def is_call_successful(self):
        if self.check_not_raise_status():
            self.parse_response_json()
            return self.is_response_success()

    def check_not_raise_status(self):
        try:
            self.response_json.raise_for_status()
            return True
        except requests.HTTPError:
            logger.exception("Query response raised HTTP status error")
            logger.error(self.response_json)
            logger.error("URL:", self.call_url)
            logger.error("Payload:\n", self.payload)
            return False

    def is_response_success(self):
        if self.response["response"]:
            try:
                success = self.response["response"]["success"]
                return success
            except KeyError:
                logger.exception("Could not check response success. Check response.")
                return False
        else:
            logger.error("Response of query is None.")
            logger.error(self.response["result"])
            logger.error(self.response["response"])
            return False

    def parse_response_json(self):
        self.response = self.response_json.json()
