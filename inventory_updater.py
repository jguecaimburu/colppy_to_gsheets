""" To DOs:
- Test more situations
- Test with existing sheet
- Test in Jupyter

General:
- Test py2exe in Windows.
- Check final logs
- Get first working program

Future TO-DOs:
- Refactor main module class
- Filter relevant INVENTORY
- Correct bare EXCEPTS
- Write comments if necessary

Future General:
- WRITE UNITTEST THAT DON'T DEPEND ON INTERNET CONNECTION
- Write comments to 3 modules where necessary
"""

# IMPORTS
##############################################################################

from colppy_api import Caller
from manipule_gsheets import GoogleSpread
import datetime
import pandas as pd
import logging
import sys

# LOGGER
##############################################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_formatter = logging.Formatter("%(levelname)s: %(name)s: %(asctime)s: %(message)s")
stream_formatter = logging.Formatter("%(levelname)s: %(message)s")

file_handler = logging.FileHandler(filename="inventory_updater.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(stream_formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# GLOBAL VARIABLES
##############################################################################


# UPDATE INVENTORY CLASS
##############################################################################


class DepositInventoryUpdater():
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

    def __init__(self, state="testing"):
        if state:
            self.state = state

    def paste_deposit_inventory_to_gsheet(self, deposit_name, spread_name,
                                          batch_size=100, colppy_conf=None):
        self.setup_caller(colppy_conf)
        self.open_spread(spread_name)
        self.set_inventory_df()
        self.check_and_set_deposit_name(deposit_name)
        self.start_or_resume_inventory_updating(batch_size)
        input("Program finished. Press Enter to exit.")
        sys.exit()

    def setup_caller(self, colppy_conf):
        logger.info("Setting up Colppy Caller...")
        self.caller = Caller(colppy_conf, self.state)
        logger.info("Done.")

    def open_spread(self, spread_name):
        try:
            logger.info("Opening Google spreadsheet %s..." % spread_name)
            self.spread = GoogleSpread(spread_name)
            logger.info("Spreadsheet opened.")
        except:  # Test error
            logger.exception("There was a problem opening the Google spreadsheet.")
            raise ValueError

    def set_inventory_df(self):
        self.set_updated_inventory()
        self.convert_inventory_data_to_df_with_header()

    def set_updated_inventory(self):
        logger.info("Setting updated inventory...")
        self.updated_inventory = self.caller.get_inventory_for()
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
        deposits = self.get_deposits_stock_for(first_item_id)
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

    def start_or_resume_inventory_updating(self, batch_size):
        self.setup_temp_worksheet()
        if self.is_new_worksheet:
            self.spread.update_cells("A1", "B1", ["Updating sheet...", ""])
        self.update_empty_cells_with_deposit_data(batch_size)
        self.post_final_df()
        self.erease_temp_worksheet()

    def setup_temp_worksheet(self):
        logger.info("Setting up worksheet...")
        self.open_worksheet()
        self.set_data_and_worksheet_range()
        logger.info("Worksheet setup OK.")

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

    def update_empty_cells_with_deposit_data(self, batch_size):
        logger.info("Updating cells with %s deposit data..." % self.deposit_name)
        self.pre_update_setup(batch_size)
        items_to_update = self.get_items_to_update()
        total_items_to_update = len(items_to_update)
        count_items = 0
        for item_id in items_to_update:
            count_items += 1
            self.try_to_update_cells_for(item_id)
            if count_items % self.batch_size == 0 or count_items == total_items_to_update:
                self.upload_batch_to_sheet()
            advance = (count_items / total_items_to_update) * 100
            logger.info(f"{'{:.2f}'.format(advance)}% done.")
        logger.info("All cells updated.")

    def pre_update_setup(self, batch_size):
        self.batch_size = batch_size
        self.set_initial_update_range()

    def set_initial_update_range(self):
        self.set_cols_to_update()
        self.update_df_if_not_new()  # Always set cols to update first
        self.set_start_row()
        self.set_cells_for_initial_range()

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
            self.set_first_incomplete_row_index_from_previous_update()
        self.batch_start_index = self.start_index

    def set_first_incomplete_row_index_from_previous_update(self):
        logger.info("Finding first incomplete row from previous update...")
        first_incomplete_item_id = self.get_first_incomplete_item_id_from_previous_update()
        self.start_index = list(self.df.index).index(first_incomplete_item_id)
        self.start_row = self.start_cell[0] + 1 + self.start_index
        logger.info("Updating from row %d..." % self.start_row)

    def get_first_incomplete_item_id_from_previous_update(self):
        first_incomplete_item_id = None
        for item_id in self.df.index:
            if self.df.loc[item_id, self.cols_to_update[0]] == "":
                first_incomplete_item_id = item_id
                logger.info("Found.")
                break
        return first_incomplete_item_id

    def set_cells_for_initial_range(self):
        self.start_batch_row = self.start_row
        self.last_batch_row = self.start_batch_row + self.batch_size - 1
        self.update_range_dict = {}
        for col in self.cols_to_update:
            col_index = list(self.df.columns).index(col)
            col_num = self.start_cell[1] + col_index + 1
            self.update_range_dict[col] = [[self.start_batch_row, col_num],
                                           [self.last_batch_row, col_num]]

    def get_items_to_update(self):
        items_to_update = list(self.df.index)[self.start_index:]
        total_items_to_update = len(items_to_update)
        logger.info("Total items to update: %d." % total_items_to_update)
        return items_to_update

    def try_to_update_cells_for(self, item_id):
        try:
            self.update_cells_with_data(item_id)
        except:  # I don't know which error I could find.
            logger.exception("Some exception occurred for item %d" % item_id)
            self.update_cells_with_error(item_id)

    def update_cells_with_data(self, item_id):
        deposits = self.get_deposits_stock_for(item_id)
        deposit_name_row = self.get_row_for_deposit(deposits)
        for col in self.cols_to_update:
            self.df.loc[item_id, col] = deposit_name_row[col]

    def update_cells_with_error(self, item_id):
        for col in self.cols_to_update:
            self.df.loc[item_id, col] = "Error"

    def get_deposits_stock_for(self, item_id):
        if item_id != 0:
            return self.caller.get_deposits_stock_for(item_id)
        else:
            logger.error("Found 0 as item ID.")
            raise ValueError

    def get_row_for_deposit(self, deposits):
        deposit_df = pd.DataFrame(deposits)
        deposit_df.set_index(self.deposit_name_col, drop=False, inplace=True)
        return deposit_df.loc[self.deposit_name]

    def upload_batch_to_sheet(self):
        logger.info("Uploading batch of new data to worksheet...")
        self.batch_end_index = self.batch_start_index + self.batch_size
        for col in self.cols_to_update:
            batch_values = self.get_batch_values_for(col)
            self.update_column_with_values(col, batch_values)
            self.update_update_cells_for(col)
        logger.info("Updating index for next batch...")
        self.batch_start_index += self.batch_size
        logger.info("Done.")
        logger.info("Upload ok.")

    def get_batch_values_for(self, col):
        batch_series = self.get_batch_series_for(col)
        logger.info("Preparing batch values...")
        batch_values = batch_series.fillna("").tolist()
        logger.info("Batch OK")
        logger.info("Batch values: %d" % len(batch_values))
        return batch_values

    def get_batch_series_for(self, col):
        logger.info("Preparing batch for %s..." % col)
        if self.update_range_dict[col][1][0] > self.last_row:
            self.update_range_dict[col][1][0] = self.last_row
            logger.info("Getting batch series...")
            batch_series = self.df[col].iloc[self.batch_start_index:]
        else:
            logger.info("Getting batch series...")
            batch_series = self.df[col].iloc[self.batch_start_index: self.batch_end_index]
        return batch_series

    def update_column_with_values(self, col, batch_values):
        col_init = tuple(self.update_range_dict[col][0])
        col_end = tuple(self.update_range_dict[col][1])
        logger.info("Starting cell: %s. Last cell: %s" % (col_init,
                                                          col_end))
        logger.info("Updating column...")
        self.spread.update_cells(col_init, col_end, batch_values)
        logger.info("Updated.")

    def update_update_cells_for(self, col):
        logger.info("Configuring %s range for next batch..." % col)
        self.update_range_dict[col][0][0] += self.batch_size
        self.update_range_dict[col][1][0] = self.update_range_dict[col][0][0] + self.batch_size - 1
        logger.info("Done.")

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
