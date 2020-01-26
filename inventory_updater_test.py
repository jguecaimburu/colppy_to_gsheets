import unittest
from requests import HTTPError
from inventory_updater import DepositInventoryUpdater
from unittest.mock import patch, Mock
import json


"""
To do:
- Mock post login
- Mock GoogleSpread.find_sheet:
    if new ws: first None then True (end)
    if not new ws: both True
- Mock df_to_sheet to count:
    if new ws: 2
    if not new ws: 1
- Mock sheet_to_df to count:
    if not new ws: 1
- Mock update_cells to count:
    if new ws: 2 labels + n cols * batchs (roundup(n_total/batch_size))
    if not new ws: 1 label + n cols * batchs (roundup(n_to_upd/batch_size))
- Mock delete_sheet to count: 1
- Mock get request to count: - IDEA: Maybe get returns deposits and mock
Caller_get_inventory()
    1. Inventory
    2. Deposits for first id
    3. Deposits for each id to update
- Mock input to run test - SEARCH HOW TO

"""

# MOCKED CLASSES AND FUNCTIONS
#########################################################################


class GoogleSpreadMock():
    def __init__(self, find_sheet=None, sheet_to_df=None):
        self.setup_counters_to_zero()
        if not find_sheet:
            find_sheet = (None, "Mock")
        self.mock_find_sheet = find_sheet
        self.mock_sheet_to_df = sheet_to_df
        self.spread_url = "mock.com"

    def setup_counters_to_zero(self):
        self.find_sheet_count = 0
        self.sheet_to_df_count = 0
        self.df_to_sheet_count = 0
        self.update_cells_count = 0
        self.delete_sheet_count = 0

    def find_sheet(self, *args, **kwargs):
        find_response = self.mock_find_sheet[self.find_sheet_count]
        self.find_sheet_count += 1
        return find_response

    def sheet_to_df(self, *args, **kwargs):
        self.sheet_to_df_count += 1
        return self.mock_sheet_to_df

    def df_to_sheet(self, *args, **kwargs):
        self.df_to_sheet_count += 1
        pass

    def update_cells(self, *args, **kwargs):
        self.update_cells_count += 1
        pass

    def delete_sheet(self, *args, **kwargs):
        self.delete_sheet_count += 1
        pass

    def open_sheet(self, *args, **kwargs):
        pass


def mock_requests_response(json_data, raise_status=None):
    mocked_response = Mock()

    mocked_response.raise_status = Mock()
    if raise_status:
        mocked_response.raise_status.side_effect = HTTPError

    mocked_response.json = Mock(return_value=json_data)

    return mocked_response

# TESTS
#########################################################################


class DepositInventoryUpdaterTest(unittest.TestCase):
    @patch("inventory_updater_test.DepositInventoryUpdater.end_program")
    @patch("inventory_updater.Caller.get_inventory_for")
    @patch("colppy_api.requests.post")
    @patch("colppy_api.requests.get")
    @patch("inventory_updater.GoogleSpread")
    def test_list_deposits(self, mock_gspread, mock_get, mock_post,
                           mock_inv, mock_end):
        with open("login_response.json") as f:
            login_data = json.load(f)
        with open("list_deposits_response.json") as f:
            deposits_data = json.load(f)
        with open("list_inventory_response.json") as f:
            inventory_response = json.load(f)
            inventory_data = inventory_response["response"]["data"]

        mock_post_resp = mock_requests_response(login_data)
        mock_post.return_value = mock_post_resp
        mock_get_resp = mock_requests_response(deposits_data)
        mock_get.return_value = mock_get_resp
        mock_inv.return_value = inventory_data
        mock_google_spread = GoogleSpreadMock()
        mock_gspread.return_value = mock_google_spread

        deposit_name = "Local"
        spread_name = "mock_name"
        diu = DepositInventoryUpdater()
        diu.paste_deposit_inventory_to_gsheet(deposit_name, spread_name)

        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_get.call_count, 12)
        self.assertEqual(diu.spread.df_to_sheet_count, 2)
        self.assertEqual(diu.spread.sheet_to_df_count, 0)
        self.assertEqual(diu.spread.update_cells_count, 4)
        self.assertEqual(diu.spread.delete_sheet_count, 1)
