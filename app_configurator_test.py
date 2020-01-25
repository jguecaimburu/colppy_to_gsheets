import unittest
from app_configurator import ParseConfiguration, PayloadBuilderConfigurator

# MOCKED CLASSES AND FUNCTIONS
#########################################################################


# TESTS
#########################################################################


class ParseConfigurationTest(unittest.TestCase):
    def test_raises_error_non_existent_file_name(self):
        with self.assertRaises(FileNotFoundError):
            ParseConfiguration("non_existent.json")

    def test_raises_error_wrong_format_file(self):
        with self.assertRaises(ValueError):
            ParseConfiguration("file_with_format_error.json")

    def test_raises_error_if_comp_id_incompatible_with_availables(self):
        with self.assertRaises(AssertionError):
            pc = ParseConfiguration("incompatible_company_config.json")
            pc.try_to_get_default_company_id()

    def test_raises_error_if_no_colppy_credentials(self):
        with self.assertRaises(KeyError):
            pc = ParseConfiguration("almost_empty_config.json")
            pc.get_colppy_credentials()

    def test_raises_error_if_no_google_credentials(self):
        with self.assertRaises(KeyError):
            pc = ParseConfiguration("almost_empty_config.json")
            pc.get_google_creds()

    def test_no_company_id(self):
        pc = ParseConfiguration("almost_empty_config.json")
        id = pc.try_to_get_default_company_id()
        self.assertEqual(id, "")

    def test_no_available_companies(self):
        pc = ParseConfiguration("almost_empty_config.json")
        ac = pc.try_to_get_default_available_companies()
        self.assertEqual(ac, {})

    def test_no_available_ccosts(self):
        pc = ParseConfiguration("almost_empty_config.json")
        cc = pc.try_to_get_default_available_ccosts()
        self.assertEqual(cc, {})

    def test_all_methods_run_on_normal_config(self):
        pc = ParseConfiguration("app_configuration_test.json")
        pc.try_to_get_default_company_id()
        pc.try_to_get_default_available_companies()
        pc.try_to_get_default_available_ccosts()
        pc.get_google_creds()
        pc.get_colppy_credentials()

    def test_default_response_takes_default_file(self):
        explicit = ParseConfiguration("app_configuration.json")
        implicit = ParseConfiguration()
        self.assertEqual(explicit.config, implicit.config)


class PayloadBuilderConfiguratorTest(unittest.TestCase):
    def test_raises_error_non_existent_file_name(self):
        with self.assertRaises(FileNotFoundError):
            PayloadBuilderConfigurator("non_existent.json")

    def test_raises_error_wrong_format_file(self):
        with self.assertRaises(ValueError):
            PayloadBuilderConfigurator("file_with_format_error.json")

    def test_raises_error_on_unexpected_format_file(self):
        with self.assertRaises(AttributeError):
            PayloadBuilderConfigurator("only_one_list.json")

    def test_raises_error_if_wrong_payload_format(self):
        credentials = {"dev_user": {}, "user": {}}
        with self.assertRaises(KeyError):
            pbc = PayloadBuilderConfigurator("almost_empty_config.json")
            pbc.get_configured_templates(credentials)

    def test_raises_error_if_wrong_credentials_format(self):
        credentials = {}
        with self.assertRaises(KeyError):
            pbc = PayloadBuilderConfigurator("almost_empty_config.json")
            pbc.get_configured_templates(credentials)

    def test_get_configured_templates_with_normal_payload_file(self):
        credentials = {"dev_user": {}, "user": {}}
        pbc = PayloadBuilderConfigurator("colppy_payload_templates.json")
        pbc.get_configured_templates(credentials)

    def test_default_response_takes_default_file(self):
        explicit = PayloadBuilderConfigurator("colppy_payload_templates.json")
        implicit = PayloadBuilderConfigurator()
        self.assertEqual(explicit.payload_templates,
                         implicit.payload_templates)
