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
            config_json = "config/app_configuration.json"
        logger.info("Opening configuration file...")
        try:
            with open(config_json, "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            logger.exception("Could not find file.")
            logger.error(config_json)
            raise FileNotFoundError

    def try_to_get_default_company_id(self):
        try:
            company_id = self._get_default_company_id()
            return company_id
        except KeyError:
            logger.info("Not found.")
            return ""
        except AssertionError:
            logger.exception("Configuration file company id is not in \
                             configuration file available companies.")
            raise AssertionError("Check Colppy configuration file.")

    def _get_default_company_id(self):
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
            available_companies = self._get_default_available_companies()
            return available_companies
        except KeyError:
            logger.info("Not found.")
            return {}

    def _get_default_available_companies(self):
        logger.info("Trying to get available companies from configuration...")
        available_companies = (self.config["colppy"]["defaults"]
                               ["available_companies"])
        logger.info(f"Got these companies: {str(available_companies)}")
        return available_companies

    def try_to_get_default_available_ccosts(self):
        try:
            available_ccosts = self._get_default_available_ccosts()
            return available_ccosts
        except KeyError:
            logger.info("Not found.")
            return {}

    def _get_default_available_ccosts(self):
        logger.info("Trying to get available ccosts from configuration...")
        available_ccosts = (self.config["colppy"]["defaults"]
                            ["available_ccosts"])
        logger.info(f"Got these ccosts: {str(available_ccosts)}")
        return available_ccosts

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
            payload_templates = "config/colppy_payload_templates.json"
        self.try_to_open_payload_templates(payload_templates)
        try:
            logger.info("Services found:")
            logger.info(self.payload_templates.keys())
        except AttributeError:
            logger.exception("Wrong json object in file.")
            logger.error(self.payload_templates)
            raise AttributeError

    def try_to_open_payload_templates(self, payload_templates):
        logger.info("Opening payload templates file...")
        try:
            with open(payload_templates, "r") as f:
                self.payload_templates = json.load(f)
            logger.info("File opened.")
        except FileNotFoundError:
            logger.exception("Could not find file.")
            logger.error(payload_templates)
            raise FileNotFoundError

    def get_configured_templates(self, colppy_credentials):
        self.set_credentials(colppy_credentials)
        self.set_user_credentials_to_login_payload()
        self.set_dev_user_credentials_to_payloads()
        return copy.deepcopy(self.payload_templates)

    def set_credentials(self, colppy_credentials):
        try:
            self.dev_user = colppy_credentials["dev_user"]
            self.user = colppy_credentials["user"]
        except KeyError:
            logger.exception("Wrong credentials format.")
            logger.error(colppy_credentials)
            raise KeyError

    def set_dev_user_credentials_to_payloads(self):
        try:
            for payload in self.payload_templates.values():
                payload["auth"] = self.dev_user
        except KeyError:
            logger.exception("Wrong payload format.")
            logger.error(self.payload_templates)
            raise KeyError

    def set_user_credentials_to_login_payload(self):
        try:
            self.payload_templates["login"]["parameters"] = self.user
        except KeyError:
            logger.exception("Wrong payload format.")
            logger.error(self.payload_templates)
            raise KeyError
