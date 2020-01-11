# IMPORTS

import requests
import datetime
import time
import pandas as pd
import copy
import default_configuration


# GLOBAL VARIABLES
##############################################################################
colppy_defaults = default_configuration.colppy_defaults

# SESSION CLASS
##############################################################################


class ColppySession(object):
    def __init__(self, colppy_defaults):
        """A Colppy session object gets inititialized with a dictionary of dict
        containing some of the following information and keys:
        "payload_temps": Templates for the different Colppy calls of the
        program. The first version contains "login", "list_companies",
        "list_ccost", "list_diary", "list_invoices". Each of these keys
        contain the dictionary form of a json payload according to the Colppy
        API documentation.
        "ccosts" (optional): Dictionary containing the existing ccosts to
        filter the diary. First keys: 1, 2 (integers). Second keys: CCost name
        as str. Value: CCost ID as str, as it appears on the diary response.
        "company_id" (optional): Str of the company ID as it appears on Colppy
        diary and invoices.
        Having these last two dicts avoid making calls to the API to get that
        data and set default values.
        """
        defaults = copy.deepcopy(colppy_defaults)
        self.login_payload = defaults["payload_temps"]["login"]
        self.list_companies_payload = defaults["payload_temps"]["list_companies"]
        self.list_ccost_payload = defaults["payload_temps"]["list_ccost"]
        self.list_diary_payload = defaults["payload_temps"]["list_diary"]
        self.list_invoices_payload = defaults["payload_temps"]["list_invoices"]
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

    def login_for(self, state):
        print("Trying to log into Colppy...")
        try:
            self.login_call = ColppyCall(state)
            self.login_resp = self.login_call.get_response(
                                                        self.login_payload,
                                                        "post"
                                                        )
            print("Login OK.")
            self.state = state
            self.set_session_key_to_payloads()
        except ValueError:
            print("An exception ocurred during login. Check call object.")

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

        print("Getting invoices...")
        self.set_input_for_call(company_id, dates_range)
        self.call_list_invoices()
        self.invoices = self.list_invoices_resp["data"]
        print("Got %d invoices.\n" % len(self.invoices))

    def set_diary_for(self, dates_range=None, company_id=None):
        """Dates range is a tuple of dates in str isoformat. The movements
        corresponding to this dates are included in the response.
        Company ID is a str of an int representing the company id in Colppy.
        If no arguments are given, the object searches for the ones used for
        the last call.
        Set the object variable "diary_movs" with the data part of the API
        response, which is a list of dictionaries. Each dictionary contains
        data for one diary movement.
        """

        print("Getting diary movs...")
        self.set_input_for_call(company_id, dates_range)
        self.call_list_diary()
        self.diary_movs = self.list_diary_resp["movimientos"]
        print("Got %d diary movs." % len(self.diary_movs))

    def set_filtered_diary_for(self, dates_range=None,
                               company_id=None, ccost_1=None, ccost_2=None):
        """Dates range is a tuple of dates in str isoformat. The movements
        corresponding to this dates are included in the response.
        Company ID is a str of an int representing the company id in Colppy.
        This function overwrites the "diary_movs" object as it first call the
        set_diary_for() method. If no arguments are given, the object searches
        for the ones used for the last call.
        Set the object variable "diary_movs" with the data part of the API
        response, which is a list of dictionaries. Each dictionary contains
        data for one diary movement.
        Then it filters that by the ccost 1 and 2 given and sets the
        filtered_diary_by_ccosts variable. If the ccost are not in the default
        dictionary, a call to the API is made to update the ccosts. If it still
        can't find it, these arguments are set to None, which mean that they
        don't affect the filter. If not ccosts are given, then:
        diary_movs == filtered_diary_movs.
        """

        self.set_diary_for(dates_range, company_id)
        if not self.is_ccost_in_n_ccosts(ccost_1, 1):
            print("CCost_1 not found in CCosts. Set to None")
            ccost_1 = None
        if not self.is_ccost_in_n_ccosts(ccost_2, 2):
            print("CCost_2 not found in CCosts. Set to None")
            ccost_2 = None
        print("Filtering...\n")
        self.filter_diary_by(ccost_1, ccost_2)
        print("Filtered %d by (%s, %s)" % (len(self.filtered_diary_movs),
                                           ccost_1, ccost_2))

    def save_invoices_to_csv(self):
        try:
            invoices_as_pandas = pd.DataFrame(self.invoices)
            filename = self.set_csv_name("invoices")
            print("Saving %s..." % filename)
            invoices_as_pandas.to_csv(path_or_buf=filename)
        except AttributeError:
            print("First call invoices to save.")

    def save_diary_movs_to_csv(self):
        try:
            diary_movs_as_pandas = pd.DataFrame(self.diary_movs)
            filename = self.set_csv_name("diary_movs")
            print("Saving %s..." % filename)
            diary_movs_as_pandas.to_csv(path_or_buf=filename)
        except AttributeError:
            print("First call diary_movs to save.")

    def save_filtered_diary_movs_to_csv(self):
        try:
            filtered_diary_movs_as_pandas = pd.DataFrame(self.filtered_diary_movs)
            filename = self.set_csv_name("filtered_diary_movs")
            print("Saving %s..." % filename)
            filtered_diary_movs_as_pandas.to_csv(path_or_buf=filename)
        except AttributeError:
            print("First call filtered_diary_movs to save.")

    def get_invoices_as_pandas(self):
        try:
            return pd.DataFrame(self.invoices)
        except AttributeError:
            print("First call invoices to save.")

    def get_diary_movs_as_pandas(self):
        try:
            return pd.DataFrame(self.diary_movs)
        except AttributeError:
            print("First call diary_movs to save.")

    def get_filtered_diary_movs_as_pandas(self):
        try:
            return pd.DataFrame(self.filtered_diary_movs)
        except AttributeError:
            print("First call filtered_diary_movs to save.")

    def set_session_key_to_payloads(self):
        print("\nSetting key for session...")
        try:
            session = {}
            self.key = self.login_resp["data"]["claveSesion"]
            session["usuario"] = self.login_payload["parameters"]["usuario"]
            session["claveSesion"] = self.key
        except KeyError:
            print("Check login payload response.")
            print(self.login_resp)
            raise KeyError("Could not get session key.")
        self.list_companies_payload["parameters"]["sesion"] = session
        self.list_diary_payload["parameters"]["sesion"] = session
        self.list_invoices_payload["parameters"]["sesion"] = session
        self.list_ccost_payload["parameters"]["sesion"] = session
        print("Key set on payloads.")

    def set_input_for_call(self, company_id=None, dates_range=None):
        try:
            self.set_company_for_call(company_id)
            self.set_dates_for_call(dates_range)
        except ValueError:
            raise ValueError("Missing data.")

    def set_company_for_call(self, company_id=None):
        if company_id:
            try:
                assert isinstance(company_id, str)
                int(company_id)
            except AssertionError:
                print("Company ID should be str")
                raise ValueError
            except ValueError:
                print("Company ID must be a str of an int")
                raise ValueError
            try:
                assert self.is_valid_company(company_id)
            except AssertionError:
                print("Company not found in available companies: \n")
                print(self.available_companies)
            self.last_call_company_id = company_id
        else:
            try:
                self.last_call_company_id
            except AttributeError:
                if self.company_id:
                    self.last_call_company_id = self.company_id
                else:
                    print("Please set a company for call and re-run method.\n")
                    self.print_available_companies()
                    print("No company given.")
                    raise ValueError
        self.list_diary_payload["parameters"]["idEmpresa"] = self.last_call_company_id
        self.list_invoices_payload["parameters"]["idEmpresa"] = self.last_call_company_id
        self.list_ccost_payload["parameters"]["idEmpresa"] = self.last_call_company_id
        print("Setting company to %s..." % self.last_call_company_id)

    def set_dates_for_call(self, dates_range=None):
        if not dates_range:
            try:
                dates_range = self.last_call_dates
            except AttributeError:
                print("No dates given.")
                raise ValueError
        if self.is_valid_dates_range(dates_range):
            print("Setting dates for data from  %s to %s...\n" % dates_range)
            start_date, end_date = self.reorder_dates(dates_range)
            self.list_diary_payload["parameters"]["fromDate"] = start_date
            self.list_diary_payload["parameters"]["toDate"] = end_date
            self.list_invoices_payload["parameters"]["filter"][0]["value"] = start_date
            self.list_invoices_payload["parameters"]["filter"][1]["value"] = end_date
            self.last_call_dates = (start_date, end_date)
        else:
            print("Check dates range and re-run method.")
            raise ValueError

    def call_list_invoices(self):
        try:
            self.list_invoices_call = ColppyCall(self.state)
            self.list_invoices_resp = self.list_invoices_call.get_response(self.list_invoices_payload)
            print("Invoices query OK.")
        except ValueError:
            print("An exception ocurred during query. Check call object.")
            raise ValueError

    def call_list_diary(self):
        try:
            self.list_diary_call = ColppyCall(self.state)
            self.list_diary_resp = self.list_diary_call.get_response(self.list_diary_payload)
            print("Diary query OK.")
        except ValueError:
            print("An exception ocurred during query. Check call object.")
            raise ValueError

    def call_list_companies(self):
        try:
            self.list_companies_call = ColppyCall(self.state)
            self.list_companies_resp = self.list_companies_call.get_response(self.list_companies_payload)
            print("Companies query OK.")
        except ValueError:
            print("An exception ocurred during query. Check call object.")
            raise ValueError

    def call_list_ccost(self, n_ccost):
        print("Getting ccosts %d...\n" % n_ccost)
        list_ccost_n_payload = self.list_ccost_payload.copy()
        list_ccost_n_payload["parameters"]["ccosto"] = n_ccost
        try:
            self.list_ccost_call = ColppyCall(self.state)
            self.list_ccost_resp = self.list_ccost_call.get_response(list_ccost_n_payload)
            print("Ccost query OK.")
        except ValueError:
            print("An exception ocurred during query. Check call object.")
            raise ValueError

    def filter_diary_by(self, ccost_1=None, ccost_2=None):
        filtered_items = []
        ccost_1_code = self.ccosts[1][ccost_1]
        ccost_2_code = self.ccosts[2][ccost_2]
        for mov in self.diary_movs:
            if (self.compare_ccost(ccost_1_code, mov["ccosto1"])
                    and self.compare_ccost(ccost_2_code, mov["ccosto2"])):
                filtered_items.append(mov)
        self.filtered_diary_movs = filtered_items

    def set_available_companies(self):
        try:
            self.list_companies_resp
        except AttributeError:
            self.call_list_companies()
        print("Getting available companies...")
        self.available_companies = {}
        try:
            for company in self.list_companies_resp["data"]:
                comp_id = company["IdEmpresa"]
                comp_name = company["razonSocial"]
                self.available_companies[comp_name] = comp_id
            print("Availables companies OK")
        except KeyError:
            self.available_companies["Query Error"] = None
            print("Got these companies:", self.available_companies, "\n")
            print("Check keys for company id and name. Response:\n")
            print(self.list_companies_resp)

    def update_available_companies(self):
        print("Updating available companies...")
        self.call_list_companies()
        self.set_available_companies()

    def update_n_ccosts(self, n_ccost):
        try:
            self.last_call_company_id
        except AttributeError:
            self.set_company_for_call()
        self.call_list_ccost(n_ccost)
        for code in self.list_ccost_resp["codigos"]:
            if code["Codigo"] not in self.ccosts[n_ccost].keys():
                self.ccosts[n_ccost][code["Codigo"]] = code["Id"]

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
            print("Dates must be a tuple of 2 str: 'YYYY-MM-DD'")
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
            print("Date %s non existent or wrong format" % date)
            print("Date format should be 'YYYY-MM-DD'.")
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

    def print_available_companies(self):
        try:
            self.available_companies
        except AttributeError:
            self.set_available_companies()
        print(self.available_companies)

    def reorder_dates(self, dates_range):
        start_date, end_date = dates_range
        if self.iso_str_to_date(start_date) > self.iso_str_to_date(end_date):
            start_date, end_date = end_date, start_date
            print("End date was older than starting date. Correcting...",
                  "(stupid human)\n")
        return (start_date, end_date)

    def iso_str_to_date(self, iso_str):
        return datetime.date.fromisoformat(iso_str)

    def set_csv_name(self, comment):
        dates_str = ""
        for iso_str in self.last_call_dates:
            date_value = datetime.date.fromisoformat(iso_str)
            dates_str = "".join([dates_str, date_value.strftime("%Y%m%d"), "_"])
        now_dt = datetime.datetime.now()
        now_str = now_dt.strftime("%Y%m%d%H%M%S")
        return "".join([comment, "_", dates_str, now_str, ".csv"])

    def is_session_live(self):
        pass


# CALL CLASS
#############################################################################

class ColppyCall(object):
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
            raise ValueError

    def __repr__(self):
        line_1 = "".join(["Colppy Call.", "\n",
                          "Call State:", self.state, "\n"])
        try:
            line_2 = "".join(["Call Service:", str(self.payload["service"])])
        except AttributeError:
            line_2 = "Call Service: Not made."
        return "".join([line_1, line_2])

    def get_response(self, payload, request_type="get"):
        try:
            self.response
        except AttributeError:
            self.call_api(payload, request_type)
        if self.is_call_successful():
            print("Query successful.")
            return self.response["response"]
        else:
            print("Query not successful. Response:")
            print(self.response)
            raise ValueError

    def call_api(self, payload, request_type):
        if self.is_valid_request_type(request_type):
            print("Calling API...   ")
            self.payload = payload
            self.response_json = self.call_requests[request_type](self.call_url,
                                                                  json=self.payload)
        else:
            print("Request type not valid.")
            print("Valid requests:", self.call_requests.keys())
            raise ValueError

    def is_valid_state(self, state):
        try:
            self.urls[state]
            return True
        except KeyError:
            print("%s is not a valid state. Valid states:" % state)
            print(self.urls.keys(), "\n")
            return False

    def is_valid_request_type(self, request_type):
        return request_type in self.call_requests.keys()

    def is_call_successful(self):
        if self.check_raise_status():
            self.parse_response_json()
            return self.is_response_success()

    def check_raise_status(self):
        try:
            self.response_json.raise_for_status()
            return True
        except requests.HTTPError:
            print("Query response raised HTTP status error")
            print(self.response_json)
            print("URL:", self.call_url)
            print("Payload:\n", self.payload)
            return False

    def is_response_success(self):
        if self.response["response"]:
            try:
                success = self.response["response"]["success"]
                return success
            except KeyError:
                print("Could not check response success. Check response.")
                return False
        else:
            print("Response of query is None.")
            print(self.response["result"])
            print(self.response["response"])
            return False

    def parse_response_json(self):
        self.response = self.response_json.json()
