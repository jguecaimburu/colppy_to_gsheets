""" To DOs:
- Filter relevant INVENTORY
- Refactor batch and update cells
- Think error handling
- Correct bare EXCEPTS
- Test more situations
- Test with existing sheet
- Test in Jupyter
- Think error handling
- Write comments
- Think unittests with some test worksheet


General:
- Write Gspread Panda encapsulation module comments and logs.
- Write Gspread pandas encapsulation unittests.
- Test py2exe in Windows.
- Check final logs
"""

# IMPORTS
##############################################################################

from call_colppy import ColppySession
from manipule_gsheets import Gsheet
import datetime
import pandas as pd
import logging
import copy
import sys

# LOGGER
##############################################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_formatter = logging.Formatter("%(levelname)s: %(name)s: %(asctime)s: %(message)s")
stream_formatter = logging.Formatter("%(levelname)s: %(message)s")

file_handler = logging.FileHandler(filename="main.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(stream_formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# GLOBAL VARIABLES
##############################################################################
global_state = "testing"   # Change for production once tested
batch_size = 100

# UPDATE INVENTORY CLASS
##############################################################################


class UpdateInventory(object):
    nonlocal global_state
    nonlocal batch_size
    item_id_col = "idItem"
    deposit_name_col = "nombre"
    col_name_dict = {
                     "idItem": "IdItem",
                     "nombre": "Nombre",
                     "codigo": "Código Item",
                     "descripcion": "Descripción Item",
                     "tipoItem": "Producto/Servicio",
                     "unidadMedida": "U. Medida",
                     "precioVenta": "Precio Venta",
                     "costoCalculado": "Costo Calculado",
                     "disponibilidad": "Disponible"
                     }
    duplicate_cols = ["disponibilidad"]

    def __init__(self, state=None):
        if state:
            self.state = state
        else:
            self.state = global_state

    def run_inventory_updating_for(self, deposit_name, spread_name):
        self.set_inventory_df()
        self.check_and_set_deposit_name(deposit_name)
        self.start_or_resume_inventory_updating(spread_name)
        input("Program finished. Press Enter to exit.")
        sys.exit()

    def set_inventory_df(self):
        self.set_updated_inventory()
        self.convert_inventory_data_to_df_with_header()

    def set_updated_inventory(self):
        logger.info("Setting updated inventory...")
        self.session = ColppySession()
        self.session.login_and_set_session_key_for(self.state)
        self.session.set_inventory()
        self.updated_inventory = copy.deepcopy(self.session.inventory)
        logger.info("Inventory set.")

    def convert_inventory_data_to_df_with_header(self):
        header = self.col_name_dict.keys()
        logger.info("Setting dataframe with headers: %s" % header)
        df = pd.DataFrame(self.updated_inventory)
        self.df = df.reindex(columns=header)
        self.df.set_index(self.item_id_col, inplace=True)
        logger.info("Dataframe OK.")

    def check_and_set_deposit_name(self, deposit_name):
        logger.info("Checking deposit name %s..." % deposit_name)
        if self.check_deposit_name(deposit_name):
            self.deposit_name = deposit_name
            logger.info("Deposit name set to %s." % deposit_name)
        else:
            raise ValueError("Wrong deposit name")

    def check_deposit_name(self, deposit_name):
        try:
            self.available_deposits
        except AttributeError:
            self.update_available_deposits()
        if deposit_name not in self.available_deposits:
            logger.warning("Deposit %s not in available deposits. Available deposits:" % deposit_name)
            logger.warning(self.available_deposits)
            return False
        else:
            return True

    def update_available_deposits(self):
        logger.info("Updating available deposits...")
        first_item_id = self.get_first_item_id()
        deposits = self.get_deposits_for_item(first_item_id)
        self.available_deposits = []
        for deposit in deposits:
            self.available_deposits.append(deposit[self.deposit_name_col])
        logger.info("Available deposits:")
        logger.info(self.available_deposits)

    def get_first_item_id(self):
        try:
            first_item_id = list(self.df.index)[0]
        except AttributeError:
            self.set_inventory_df()
            first_item_id = list(self.df.index)[0]
        return first_item_id

    def start_or_resume_inventory_updating(self, spread_name):
        self.setup_temp_worksheet(spread_name)
        if self.is_new_worksheet:
            self.spread.update_cells("A1", "B1", ["Updating sheet...", ""])
        self.update_empty_cells_with_deposit_data()
        self.post_final_df()
        self.erease_temp_worksheet()

    def setup_temp_worksheet(self, spread_name):
        logger.info("Setting up worksheet...")
        self.open_spread(spread_name)
        self.open_worksheet()
        self.set_data_and_worksheet_range()
        logger.info("Worksheet setup OK.")

    def open_spread(self, spread_name):
        try:
            logger.info("Opening Google spreadsheet %s..." % spread_name)
            self.spread = Gsheet(spread_name)
            logger.info("Spreadsheet opened.")
        except:  # Test error
            logger.error("There was a problem opening the Google spreadsheet.")
            raise ValueError

    def open_worksheet(self):
        try:
            self.set_temp_worksheet_name()
        except AttributeError:
            logger.exception("Please set deposit name first.")
            raise AttributeError("No deposit name.")

        self.find_temp_worksheet_or_create_new()

    def set_temp_worksheet_name(self):
        now_dt = datetime.datetime.now()
        now_str = now_dt.strftime("%d-%m-%Y")
        self.temp_worksheet_name = "_".join(["temp", self.deposit_name, now_str])

    def find_temp_worksheet_or_create_new(self):
        logger.info("Searching for worksheet %s" % self.temp_worksheet_name)
        temp_worksheet = self.spread.find_sheet(self.temp_worksheet_name)
        if temp_worksheet:
            self.is_new_worksheet = False
            logger.info("Found. Opening worksheet...")
        else:
            self.is_new_worksheet = True
            logger.info("Not found. Creating worksheet...")
        self.spread.open_sheet(self.temp_worksheet_name, create=True)
        logger.info("Done.")

    def set_data_and_worksheet_range(self):
        logger.info("Configuring cells ranges and setting up data to sheet...")
        self.start_cell = (3, 1)
        self.total_rows = len(self.df.index)
        self.last_row = self.start_cell[0] + self.total_rows

        if self.is_new_worksheet:
            self.spread.df_to_sheet(self.df.copy(), start_cell=self.start_cell)
        logger.info("Done.")

    def update_empty_cells_with_deposit_data(self):
        logger.info("Updating cells with %s deposit data..." % self.deposit_name)
        self.batch_size = batch_size
        self.set_update_range()
        items_to_update = list(self.df.index)[self.start_index:]
        total_items_to_update = len(items_to_update)
        logger.info("Total items to update: %d." % total_items_to_update)
        count_items = 0
        for item_id in items_to_update:
            count_items += 1
            try:
                deposits = self.get_deposits_for_item(item_id)
                deposit_name_row = self.get_row_for_deposit(deposits)
                for col in self.cols_to_update:
                    self.df.loc[item_id, col] = deposit_name_row[col]
            except:  # I don't know which error I could find.
                logger.exception("Some exception occurred for item %d" % item_id)
                for col in self.cols_to_update:
                    self.df.loc[item_id, col] = "Error"
            if count_items % self.batch_size == 0 or count_items == total_items_to_update:
                self.upload_batch_to_sheet()
            if count_items % 300 == 0:
                self.session.login_and_set_session_key_for(self.state)
            advance = (count_items / total_items_to_update) * 100
            logger.info(f"{'{:.2f}'.format(advance)}% done.")
        logger.info("All cells updated.")

    def set_update_range(self):
        self.set_cols_to_update()
        self.update_df_if_not_new()
        self.set_start_row()
        self.start_batch_row = self.start_row
        self.last_batch_row = self.start_batch_row + self.batch_size - 1
        self.update_range_dict = {}
        for col in self.cols_to_update:
            col_index = list(self.df.columns).index(col)
            col_num = self.start_cell[1] + col_index + 1
            self.update_range_dict[col] = [[self.start_batch_row, col_num],
                                           [self.last_batch_row, col_num]]

    def set_cols_to_update(self):
        empty_cols = self.get_empty_cols()
        self.cols_to_update = empty_cols + self.duplicate_cols
        logger.info("Columns to update:")
        logger.info(self.cols_to_update)

    def get_empty_cols(self):
        empty_cols = []
        for col in self.df.columns:
            if self.df[col].isnull().all():
                empty_cols.append(col)
        return empty_cols

    def update_df_if_not_new(self):
        if not self.is_new_worksheet:
            logger.info("Updating dataframe with spreadsheet data...")
            self.df = self.spread.sheet_to_df(start_row=self.start_cell[0])
            logger.info("Done.")

    def set_start_row(self):
        if self.is_new_worksheet:
            self.start_row = self.start_cell[0] + 1
            self.start_index = 0
        else:
            logger.info("Finding first row to update in previous worksheet...")
            first_empty_row_item_id = None
            for item_id in self.df.index:
                if self.df.loc[item_id, self.cols_to_update[0]] == "":
                    first_empty_row_item_id = item_id
                    logger.info("Found.")
                    break
            self.start_index = list(self.df.index).index(first_empty_row_item_id)
            self.start_row = self.start_cell[0] + 1 + self.start_index
            logger.info("Updating from row %d..." % self.start_row)
        self.batch_start_index = self.start_index

    def get_deposits_for_item(self, item_id):
        return self.session.get_deposits_for(str(item_id))

    def get_row_for_deposit(self, deposits):
        deposit_df = pd.DataFrame(deposits)
        deposit_df.set_index(self.deposit_name_col, drop=False, inplace=True)
        return deposit_df.loc[self.deposit_name]

    def upload_batch_to_sheet(self):
        logger.info("Uploading batch of new data to worksheet...")
        self.batch_end_index = self.batch_start_index + self.batch_size
        for col in self.cols_to_update:
            logger.info("Preparing batch for %s..." % col)
            if self.update_range_dict[col][1][0] > self.last_row:
                self.update_range_dict[col][1][0] = self.last_row
                logger.info("Getting batch series...")
                batch_series = self.df[col].iloc[self.batch_start_index:]
            else:
                logger.info("Getting batch series...")
                batch_series = self.df[col].iloc[self.batch_start_index: self.batch_end_index]
            logger.info("Preparing batch values...")
            batch_values = batch_series.fillna("").tolist()
            logger.info("Batch OK")

            logger.info("Batch values: %d" % len(batch_values))
            col_init = tuple(self.update_range_dict[col][0])
            col_end = tuple(self.update_range_dict[col][1])
            logger.info("Starting cell: %s. Last cell: %s" % (col_init,
                                                              col_end))
            logger.info("Updating column...")
            self.spread.update_cells(col_init, col_end, batch_values)
            logger.info("Updated.")

            logger.info("Configuring range for next batch...")
            self.update_range_dict[col][0][0] += self.batch_size
            self.update_range_dict[col][1][0] = self.update_range_dict[col][0][0] + self.batch_size - 1
            logger.info("Done.")
        logger.info("Updating index for next batch...")
        self.batch_start_index += self.batch_size
        logger.info("Done.")

        logger.info("Upload ok.")

    def post_final_df(self):
        self.final_worksheet_name = self.temp_worksheet_name[5:]
        logger.info("Uploading final data to %s..." % self.final_worksheet_name)
        self.change_header_names()
        self.spread.df_to_sheet(self.df.copy(), index=False,
                                start_cell=self.start_cell,
                                sheet=self.final_worksheet_name)
        now_dt = datetime.datetime.now()
        self.spread.update_cells("A1", "B1",
                                 ["Updated on:", str(now_dt)])
        logger.info("Data set to %s" % self.spread.spread_url)

    def change_header_names(self):
        self.df.rename(columns=self.col_name_dict, inplace=True)

    def erease_temp_worksheet(self):
        final_worksheet = self.spread.find_sheet(self.final_worksheet_name)
        if final_worksheet:
            self.spread.delete_sheet(self.temp_worksheet_name)


# GET MOVEMENTS CLASS
##############################################################################


class GetMovements(object):
    global state
    col_name_dict = {}  # readable name to Colppy name

    def __init__(self, state=None):
        if state:
            self.state = state
        else:
            self.state = global_state

    def get_invoices_for(self, dates, company_id=None):
        self.session = ColppySession()
        self.session.login_and_set_session_key_for(self.state)
        self.session.set_invoices_for(dates, company_id)
        return pd.DataFrame(self.session.invoices)

    def get_diary_for(self, dates, company_id=None):
        self.session = ColppySession()
        self.session.login_and_set_session_key_for(self.state)
        self.session.set_diary_for(dates, company_id)
        return pd.DataFrame(self.session.diary)

    def get_filtered_diary_for(self, dates,
                               company_id=None, ccost_1=None, ccost_2=None):
        diary_df = self.get_diary_for(dates, company_id)
        ccosts = self.get_valid_ccosts_tuple(ccost_1, ccost_2)
        return self.filter_diary_by_ccosts(diary_df, ccosts)

    def get_valid_ccosts_tuple(self, ccost_1=None, ccost_2=None):
        if not self.session.is_ccost_in_n_ccosts(ccost_1, 1):
            ccost_1 = None
        if not self.session.is_ccost_in_n_ccosts(ccost_2, 2):
            ccost_2 = None
        return (ccost_1, ccost_2)

    def filter_diary_by_ccosts(diary_df, ccosts):
        ccost_1_filter = diary_df['ccosto1'] == ccosts[0]
        ccost_2_filter = diary_df['ccosto2'] == ccosts[1]
        filtered_diary = diary_df.copy()
        if ccosts[0]:
            filtered_diary = filtered_diary.loc[ccost_1_filter]
        if ccosts[1]:
            filtered_diary = filtered_diary.loc[ccost_2_filter]
        return filtered_diary
