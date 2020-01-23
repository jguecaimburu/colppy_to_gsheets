# IMPORTS
##############################################################################

import json
import logging
import copy

# LOGGER
##############################################################################

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_formatter = logging.Formatter("%(levelname)s: %(name)s: %(asctime)s: \
    %(message)s")
stream_formatter = logging.Formatter("%(levelname)s: %(message)s")

file_handler = logging.FileHandler(filename="app_configurator.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(stream_formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


# GLOBAL VARIABLES
##############################################################################


# CLASSES
##############################################################################

class ParseConfiguration():
    def __init__(self, config_json=None):
        if not config_json:
            config_json = "app_configuration.json"
        logger.info("Opening configuration file...")
        with open(config_json, "r") as f:
            self.config = json.load(f)
        if self.config:
            logger.info("File opened.")
        else:
            logger.error("Could not open file.")
            raise ValueError("Configuration file error.")

    def try_to_get_default_company_id(self):
        try:
            company_id = self.get_default_company_id()
            return company_id
        except KeyError:
            logger.info("Not found.")
            return ""
        except AssertionError:
            logger.exception("Configuration file company id is not in ",
                             "configuration file available companies.")
            raise AssertionError("Check Colppy configuration file.")

    def get_default_company_id(self):
        logger.info("Trying to get Company ID from configuration...")
        company_id = self.config["colppy"]["defaults"]["company_id"]
        self.if_available_companies_in_conf_then_check_id(company_id)
        logger.info("Got company ID: %s" % company_id)
        return company_id

    def if_available_companies_in_conf_then_check_id(self, company_id):
        try:
            assert company_id in (self.config["colppy"]["defaults"]
                                  ["available_companies"]).values()
        except KeyError:
            pass

    def try_to_get_default_available_companies(self):
        try:
            available_companies = self.get_default_available_companies()
            return available_companies
        except KeyError:
            logger.info("Not found.")
            return {}

    def get_default_available_companies(self):
        logger.info("Trying to get available companies from configuration...")
        available_companies = (self.config["colppy"]["defaults"]
                               ["available_companies"])
        logger.info(f"Got these companies: {str(available_companies)}")
        return available_companies

    def get_default_available_ccosts(self):
        try:
            return self.config["colppy"]["defaults"]["available_ccosts"]
        except KeyError:
            return {}

    def get_colppy_credentials(self):
        try:
            return self.config["colppy"]["credentials"]
        except KeyError:
            logger.exception("Missing credentials in configuration file.")
            raise KeyError

    def get_google_creds(self):
        try:
            return self.config["google"]["credentials"]
        except KeyError:
            logger.exception("Missing credentials in configuration file.")
            raise KeyError


class PayloadBuilderConfigurator():
    def __init__(self, payload_templates=None):
        if not payload_templates:
            payload_templates = "colppy_payload_templates.json"
        logger.info("Opening payload templates file...")
        with open(payload_templates, "r") as f:
            self.payload_templates = json.load(f)
        if self.payload_templates:
            logger.info("File opened.")
            logger.info("Services fpund:")
            logger.info(self.payload_templates.keys())
        else:
            logger.error("Could not open file.")
            raise ValueError("Configuration file error.")

    def get_configured_templates(self, colppy_credentials):
        self.set_credentials(colppy_credentials)
        self.set_user_credentials_to_login_payload()
        self.set_dev_user_credentials_to_payloads()
        return copy.deepcopy(self.payload_templates)

    def set_credentials(self, colppy_credentials):
        self.dev_user = colppy_credentials["dev_user"]
        self.user = colppy_credentials["user"]

    def set_dev_user_credentials_to_payloads(self):
        for payload in self.payload_templates.values():
            payload["auth"] = self.dev_user

    def set_user_credentials_to_login_payload(self):
        self.payload_templates["login"]["parameters"] = self.user
