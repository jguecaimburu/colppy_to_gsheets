import unittest
from requests import HTTPError
from unittest.mock import patch, Mock
import json
import pandas as pd
import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from inventory_updater import DepositInventoryUpdater


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
        header = DepositInventoryUpdater.col_name_dict.keys()
        df = pd.DataFrame(data=self.mock_sheet_to_df, columns=header)
        df.set_index(DepositInventoryUpdater.item_id_col, inplace=True)
        return df

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


@patch("test.inventory_updater_test.DepositInventoryUpdater.end_program")
@patch("inventory_updater.Caller.get_inventory_for")
@patch("colppy_api.requests.post")
@patch("colppy_api.requests.get")
@patch("inventory_updater.GoogleSpread")
class DepositInventoryUpdaterTest(unittest.TestCase):
    ps = [
          [10963030, 'Local', '9789876377256', 'Arty Mouse: Tizas', 'P', 'Un', 1090, 539.4, '1.00000'],
          [10963031, 'Local', '9782733850398', 'Libros de stickers: Piratas', 'P', 'Un', 400, 215.4, '1.00000'],
          [10963035, 'Local', '9789876377249', 'Arty Mouse: Pintá con los dedos', 'P', 'Un', 1090, 539.4, '1.00000'],
          [10963036, 'Local', '9789876374347', 'Arty Mouse: Números', 'P', 'Un', 550, 329.4, '1.00000'],
          [10963037, 'Local', '9789876374354', 'Arty Mouse: Palabras', 'P', 'Un', 550, 329.4, '1.00000'],
          [11057897, 'Local', '9789876374248', 'ARTY MOUSE: FORMAS', 'P', 'Un', 1090, 539.4, '1.00000'],
          [11057898, '', '9789876376747', 'MIRA EN EL MAR', 'P', 'Un', 999, 539.4, '6.00000'],
          [11057899, '', '9789871078233', 'LIMPIAPIPAS SIN CONTROL', 'P', 'Un', 999, 479.4, '6.00000'],
          [11057903, '', '9789876377454', 'VEO EN EL OCEANO', 'P', 'Un', 860, 467.4, '6.00000'],
          [11057905, '', '9789876377447', 'VEO EN EL BOSQUE', 'P', 'Un', 860, 467.4, '6.00000'],
          [11057908, '', '9789876374231', 'ARTY MOUSE: ESTÉNCILES', 'P', 'Un', 1090, 539.4, '6.00000']
          ]
    find_ps = ("Mock", "Mock")
    deposit_name = "Local"
    spread_name = "mock_name"

    def test_paste_deposits_from_zero(self, mock_gspread, mock_get,
                                      mock_post, mock_inv, mock_end):
        with open("test/data/login_response.json") as f:
            login_data = json.load(f)
        with open("test/data/list_deposits_response.json") as f:
            deposits_data = json.load(f)
        with open("test/data/list_inventory_response.json") as f:
            inventory_response = json.load(f)
            inventory_data = inventory_response["response"]["data"]

        mock_post_resp = mock_requests_response(login_data)
        mock_post.return_value = mock_post_resp
        mock_get_resp = mock_requests_response(deposits_data)
        mock_get.return_value = mock_get_resp
        mock_inv.return_value = inventory_data
        mock_google_spread = GoogleSpreadMock()
        mock_gspread.return_value = mock_google_spread

        diu = DepositInventoryUpdater()
        diu.paste_deposit_inventory_to_gsheet(self.deposit_name,
                                              self.spread_name)

        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_get.call_count, 12)
        self.assertEqual(diu.spread.df_to_sheet_count, 2)
        self.assertEqual(diu.spread.sheet_to_df_count, 0)
        self.assertEqual(diu.spread.update_cells_count, 4)
        self.assertEqual(diu.spread.delete_sheet_count, 1)

    def test_paste_deposits_from_previous(self, mock_gspread, mock_get,
                                          mock_post, mock_inv, mock_end):
        with open("test/data/login_response.json") as f:
            login_data = json.load(f)
        with open("test/data/list_deposits_response.json") as f:
            deposits_data = json.load(f)
        with open("test/data/list_inventory_response.json") as f:
            inventory_response = json.load(f)
            inventory_data = inventory_response["response"]["data"]

        mock_post_resp = mock_requests_response(login_data)
        mock_post.return_value = mock_post_resp
        mock_get_resp = mock_requests_response(deposits_data)
        mock_get.return_value = mock_get_resp
        mock_inv.return_value = inventory_data

        mock_google_spread = GoogleSpreadMock(find_sheet=self.find_ps,
                                              sheet_to_df=self.ps)
        mock_gspread.return_value = mock_google_spread

        diu = DepositInventoryUpdater()
        diu.paste_deposit_inventory_to_gsheet(self.deposit_name,
                                              self.spread_name)

        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_get.call_count, 6)
        self.assertEqual(diu.spread.df_to_sheet_count, 1)
        self.assertEqual(diu.spread.sheet_to_df_count, 1)
        self.assertEqual(diu.spread.update_cells_count, 3)
        self.assertEqual(diu.spread.delete_sheet_count, 1)

    def test_new_equal_from_previous(self, mock_gspread, mock_get,
                                     mock_post, mock_inv, mock_end):
        with open("test/data/login_response.json") as f:
            login_data = json.load(f)
        with open("test/data/list_deposits_response.json") as f:
            deposits_data = json.load(f)
        with open("test/data/list_inventory_response.json") as f:
            inventory_response = json.load(f)
            inventory_data = inventory_response["response"]["data"]

        mock_post_resp = mock_requests_response(login_data)
        mock_post.return_value = mock_post_resp
        mock_get_resp = mock_requests_response(deposits_data)
        mock_get.return_value = mock_get_resp
        mock_inv.return_value = inventory_data

        mock_google_previous_spread = GoogleSpreadMock(find_sheet=self.find_ps,
                                                       sheet_to_df=self.ps)
        mock_gspread.return_value = mock_google_previous_spread
        diu_prev = DepositInventoryUpdater()
        diu_prev.paste_deposit_inventory_to_gsheet(self.deposit_name,
                                                   self.spread_name)

        mock_google_new_spread = GoogleSpreadMock()
        mock_gspread.return_value = mock_google_new_spread
        diu_new = DepositInventoryUpdater()
        diu_new.paste_deposit_inventory_to_gsheet(self.deposit_name,
                                                  self.spread_name)

        self.assertEqual(diu_prev.df.values.tolist(),
                         diu_new.df.values.tolist())
