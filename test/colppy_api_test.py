import unittest
from requests import HTTPError
from unittest.mock import patch, Mock
import json
import datetime
import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from colppy_api import Caller, PayloadBuilder, RequestMaker, ResponseParser


# MOCKED CLASSES AND FUNCTIONS
#########################################################################


def mock_response(json_data, raise_status=None):
    mocked_response = Mock()

    mocked_response.raise_status = Mock()
    if raise_status:
        mocked_response.raise_status.side_effect = HTTPError

    mocked_response.json = Mock(return_value=json_data)

    return mocked_response


# TESTS
#########################################################################


class ResponseParserTest(unittest.TestCase):
    def test_raises_on_http_error(self):
        mock_response_input = mock_response({}, raise_status=True)
        with self.assertRaises(ValueError):
            ResponseParser(mock_response_input)

    def test_raises_if_not_success(self):
        mock_response_json = {"response": {"success": False}}
        mock_response_input = mock_response(mock_response_json)
        with self.assertRaises(ValueError):
            ResponseParser(mock_response_input)

    def test_raises_if_no_response(self):
        mock_response_json = {}
        mock_response_input = mock_response(mock_response_json)
        with self.assertRaises(ValueError):
            ResponseParser(mock_response_input)

    def test_raises_if_response_empty(self):
        mock_response_json = {"result": "some result",
                              "response": None}
        mock_response_input = mock_response(mock_response_json)
        with self.assertRaises(ValueError):
            ResponseParser(mock_response_input)

    def test_assert_not_raises(self):
        mock_response_json = {"response": {"success": True}}
        mock_response_input = mock_response(mock_response_json)
        response = ResponseParser(mock_response_input)
        self.assertTrue("success" in response.get_response_content().keys())


class RequestMakerTest(unittest.TestCase):
    def test_raises_on_invalid_state(self):
        invalid_state = "Testing"
        with self.assertRaises(ValueError):
            RequestMaker(invalid_state)

    def test_raises_on_invalid_request_type(self):
        invalid_request = "Get"
        payload = {"check": "check"}
        with self.assertRaises(ValueError):
            request_maker = RequestMaker()
            request_maker.get_response(payload, request_type=invalid_request)

    @patch("colppy_api.requests.get", return_value="GET")
    def test_get_request_if_no_request_type(self, mock_get):
        payload = {"check": "check"}
        request_maker = RequestMaker()
        answer = request_maker.get_response(payload)
        self.assertEqual(answer, "GET")

    @patch("colppy_api.requests.post", return_value="POST")
    def test_post_request_if_asked(self, mock_post):
        payload = {"check": "check"}
        request_type = "post"
        request_maker = RequestMaker()
        answer = request_maker.get_response(payload,
                                            request_type=request_type)
        self.assertEqual(answer, "POST")


class PayloadBuilderTest(unittest.TestCase):
    key = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    dates = ("2019-11-01", "2019-11-10")
    company_id = "19459"

    def test_get_login_payload(self):
        pb = PayloadBuilder()
        login_payload = pb.get_login_payload()
        self.assertEqual(login_payload["service"]["operacion"],
                         "iniciar_sesion")

    def test_get_list_companies_payload(self):
        pb = PayloadBuilder()
        payload = pb.get_list_companies_payload(self.key)
        self.assertEqual(payload["service"]["operacion"],
                         "listar_empresa")
        self.assertIsInstance(payload["parameters"]["sesion"],
                              dict)

    def test_get_list_n_ccost_payload(self):
        ccost = 1
        pb = PayloadBuilder()
        payload = pb.get_list_n_ccost_payload(ccost,
                                              self.company_id,
                                              self.key)
        self.assertEqual(payload["service"]["operacion"],
                         "listar_ccostos")
        self.assertIsInstance(payload["parameters"]["sesion"],
                              dict)
        self.assertEqual(payload["parameters"]["idEmpresa"],
                         self.company_id)
        self.assertEqual(payload["parameters"]["ccosto"],
                         ccost)

    def test_get_list_invoices_payload(self):
        pb = PayloadBuilder()
        payload = pb.get_list_invoices_payload(self.dates,
                                               self.company_id,
                                               self.key)
        self.assertEqual(payload["service"]["operacion"],
                         "listar_facturasventa")
        self.assertIsInstance(payload["parameters"]["sesion"],
                              dict)
        self.assertEqual(payload["parameters"]["idEmpresa"],
                         self.company_id)
        for index, filter in enumerate(payload["parameters"]["filter"]):
            self.assertEqual(filter["value"],
                             self.dates[index])

    def test_get_list_diary_payload(self):
        pb = PayloadBuilder()
        payload = pb.get_list_diary_payload(self.dates,
                                            self.company_id,
                                            self.key)
        self.assertEqual(payload["service"]["operacion"],
                         "listar_movimientosdiario")
        self.assertIsInstance(payload["parameters"]["sesion"],
                              dict)
        self.assertEqual(payload["parameters"]["idEmpresa"],
                         self.company_id)
        self.assertEqual(payload["parameters"]["fromDate"],
                         self.dates[0])
        self.assertEqual(payload["parameters"]["toDate"],
                         self.dates[1])

    def test_get_list_inventory_payload(self):
        pb = PayloadBuilder()
        payload = pb.get_list_inventory_payload(self.company_id,
                                                self.key)
        self.assertEqual(payload["service"]["operacion"],
                         "listar_itemsinventario")
        self.assertIsInstance(payload["parameters"]["sesion"],
                              dict)
        self.assertEqual(payload["parameters"]["idEmpresa"],
                         self.company_id)

    def test_get_list_deposits_stock_for_item_payload(self):
        item_id = "100000"
        pb = PayloadBuilder()
        payload = pb.get_list_deposits_stock_for_item_payload(item_id,
                                                              self.company_id,
                                                              self.key)
        self.assertEqual(payload["service"]["operacion"],
                         "listar_dispDeposito")
        self.assertIsInstance(payload["parameters"]["sesion"],
                              dict)
        self.assertEqual(payload["parameters"]["idEmpresa"],
                         self.company_id)
        self.assertEqual(payload["parameters"]["idItem"],
                         item_id)

    def test_second_get_with_implicit_key(self):
        pb = PayloadBuilder()
        payload_1 = pb.get_list_invoices_payload(self.dates,
                                                 self.company_id,
                                                 self.key)
        payload_2 = pb.get_list_diary_payload(self.dates,
                                              self.company_id)
        self.assertEqual(payload_1["parameters"]["sesion"],
                         payload_2["parameters"]["sesion"])

    def test_second_get_with_implicit_company_id(self):
        pb = PayloadBuilder()
        payload_1 = pb.get_list_invoices_payload(self.dates,
                                                 self.company_id,
                                                 self.key)
        payload_2 = pb.get_list_diary_payload(self.dates)
        self.assertEqual(payload_1["parameters"]["idEmpresa"],
                         payload_2["parameters"]["idEmpresa"])

    def test_second_get_with_implicit_input(self):
        pb = PayloadBuilder()
        payload_1 = pb.get_list_invoices_payload(self.dates,
                                                 self.company_id,
                                                 self.key)
        payload_2 = pb.get_list_invoices_payload()
        self.assertEqual(payload_1, payload_2)

    def test_no_key_raises_error(self):
        pb = PayloadBuilder()
        with self.assertRaises(ValueError):
            pb.get_list_invoices_payload(dates_range=self.dates,
                                         company_id=self.company_id)

    def test_no_dates_raises_error(self):
        pb = PayloadBuilder()
        with self.assertRaises(ValueError):
            pb.get_list_invoices_payload(company_id=self.company_id,
                                         session_key=self.key)

    def test_no_company_takes_default(self):
        pb = PayloadBuilder()
        payload = pb.get_list_invoices_payload(dates_range=self.dates,
                                               session_key=self.key)
        self.assertEqual(payload["parameters"]["idEmpresa"],
                         self.company_id)

    def test_no_company_raises_error_if_no_default(self):
        pb = PayloadBuilder(app_configuraton="test/data/no_defaults.json")
        with self.assertRaises(ValueError):
            pb.get_list_invoices_payload(dates_range=self.dates,
                                         session_key=self.key)

    def test_wrong_date_format_raises_error(self):
        pb = PayloadBuilder()
        dates = ("1/11/2019", "10/11/2019")
        with self.assertRaises(ValueError):
            pb.get_list_invoices_payload(dates_range=dates,
                                         session_key=self.key)

    def test_one_date_range_raises_error(self):
        pb = PayloadBuilder()
        dates = self.dates[0]
        with self.assertRaises(ValueError):
            pb.get_list_invoices_payload(dates_range=dates,
                                         session_key=self.key)

    def test_non_existent_date_raises_error(self):
        pb = PayloadBuilder()
        dates = ("2019-02-01", "2019-02-30")
        with self.assertRaises(ValueError):
            pb.get_list_invoices_payload(dates_range=dates,
                                         session_key=self.key)

    def test_unsorted_dates_get_same_payload(self):
        pb = PayloadBuilder()
        payload_1 = pb.get_list_invoices_payload(self.dates,
                                                 self.company_id,
                                                 self.key)
        dates = self.dates[::-1]
        payload_2 = pb.get_list_invoices_payload(dates,
                                                 self.company_id,
                                                 self.key)
        self.assertEqual(payload_1, payload_2)

    def test_wrong_ccost_raises_error(self):
        pb = PayloadBuilder()
        ccost = 3
        with self.assertRaises(ValueError):
            pb.get_list_n_ccost_payload(ccost,
                                        self.company_id,
                                        self.key)

    def test_wrong_ccost_format_raises_error(self):
        pb = PayloadBuilder()
        ccost = "1"
        with self.assertRaises(ValueError):
            pb.get_list_n_ccost_payload(ccost,
                                        self.company_id,
                                        self.key)

    def test_wrong_item_id_format_raises_error(self):
        item_id = "10000A"
        pb = PayloadBuilder()
        with self.assertRaises(ValueError):
            pb.get_list_deposits_stock_for_item_payload(item_id,
                                                        self.company_id,
                                                        self.key)

    def test_str_or_int_item_id_get_same_deposits(self):
        pb = PayloadBuilder()
        item_id_1 = "100000"
        pl_1 = pb.get_list_deposits_stock_for_item_payload(item_id_1,
                                                           self.company_id,
                                                           self.key)
        item_id_2 = 100000
        pl_2 = pb.get_list_deposits_stock_for_item_payload(item_id_2,
                                                           self.company_id,
                                                           self.key)
        self.assertEqual(pl_1, pl_2)


class CallerTest(unittest.TestCase):
    @patch("colppy_api.requests.post")
    def test_get_session_key_re_logs_after_duration(self, mock_post):
        with open("test/data/login_response.json") as f:
            json_data = json.load(f)
        mock_resp = mock_response(json_data)
        mock_post.return_value = mock_resp
        time_delta = datetime.timedelta(minutes=30)
        second_dt_now = datetime.datetime.now() + time_delta

        caller = Caller()
        caller.get_session_key()

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now = Mock()
            mock_datetime.now.return_value = second_dt_now
            caller.get_session_key()

        self.assertEqual(mock_post.call_count, 2)

    @patch("colppy_api.requests.post")
    def test_get_session_key_not_re_logs_before_duration(self, mock_post):
        with open("test/data/login_response.json") as f:
            json_data = json.load(f)
        mock_resp = mock_response(json_data)
        mock_post.return_value = mock_resp
        time_delta = datetime.timedelta(minutes=20)
        second_dt_now = datetime.datetime.now() + time_delta

        caller = Caller()
        caller.get_session_key()

        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now = Mock()
            mock_datetime.now.return_value = second_dt_now
            caller.get_session_key()

        self.assertEqual(mock_post.call_count, 1)

    @patch("colppy_api.requests.post")
    @patch("colppy_api.requests.get")
    def test_list_companies(self, mock_get, mock_post):
        with open("test/data/login_response.json") as f:
            login_data = json.load(f)
        with open("test/data/list_companies_response.json") as f:
            companies_data = json.load(f)

        mock_post_resp = mock_response(login_data)
        mock_post.return_value = mock_post_resp
        mock_get_resp = mock_response(companies_data)
        mock_get.return_value = mock_get_resp

        caller = Caller()
        self.assertEqual(caller.get_companies(),
                         companies_data["response"]["data"])

    @patch("colppy_api.requests.post")
    @patch("colppy_api.requests.get")
    def test_list_invoices(self, mock_get, mock_post):
        with open("test/data/login_response.json") as f:
            login_data = json.load(f)
        with open("test/data/list_invoices_response.json") as f:
            invoices_data = json.load(f)

        mock_post_resp = mock_response(login_data)
        mock_post.return_value = mock_post_resp
        mock_get_resp = mock_response(invoices_data)
        mock_get.return_value = mock_get_resp

        dates = ("2019-11-01", "2019-11-03")
        caller = Caller()
        self.assertEqual(caller.get_invoices_for(dates),
                         invoices_data["response"]["data"])

    @patch("colppy_api.requests.post")
    @patch("colppy_api.requests.get")
    def test_list_inventory(self, mock_get, mock_post):
        with open("test/data/login_response.json") as f:
            login_data = json.load(f)
        with open("test/data/list_inventory_response.json") as f:
            inventory_data = json.load(f)

        mock_post_resp = mock_response(login_data)
        mock_post.return_value = mock_post_resp
        mock_get_resp = mock_response(inventory_data)
        mock_get.return_value = mock_get_resp

        caller = Caller()
        self.assertEqual(caller.get_inventory_for(),
                         inventory_data["response"]["data"])

    @patch("colppy_api.requests.post")
    @patch("colppy_api.requests.get")
    def test_list_deposits(self, mock_get, mock_post):
        with open("test/data/login_response.json") as f:
            login_data = json.load(f)
        with open("test/data/list_deposits_response.json") as f:
            deposits_data = json.load(f)

        mock_post_resp = mock_response(login_data)
        mock_post.return_value = mock_post_resp
        mock_get_resp = mock_response(deposits_data)
        mock_get.return_value = mock_get_resp

        caller = Caller()
        self.assertEqual(caller.get_deposits_stock_for("100000"),
                         deposits_data["response"]["data"])


if __name__ == '__main__':
    unittest.main()
