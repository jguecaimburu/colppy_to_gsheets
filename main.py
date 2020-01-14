""" To DOs:
- Write unittests: create and update first 5 values and last 5 values
- Add functions to create Gspread
- Write comments

General:
- Write Gspread Panda encapsulation module
- Write Gspread pandas encapsulation unittests.
- Test py2exe in Windows.
- Check final logs
"""

# IMPORTS
##############################################################################

from call_colppy import ColppySession
import colppy_configuration
import pandas as pd
import logging
import copy

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


# UPDATE INVENTORY CLASS
##############################################################################

class UpdateInventory(object):
    state = colppy_configuration.state
    item_id_col = "idItem"
    deposit_name_col = "nombre"
    col_name_dict = {
                     "nombre": "Nombre",
                     "idItem": "Código Item",
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

    def set_updated_inventory(self):
        self.session = ColppySession()
        self.session.login_and_set_session_key_for(self.state)
        self.session.set_inventory()
        self.updated_inventory = copy.deepcopy(self.session.inventory)

    def set_inventory_df_with_header(self):
        header = self.col_name_dict.keys()
        df = pd.DataFrame(self.updated_inventory)
        self.df = df.reindex(columns=header)
        self.df.set_index(self.item_id_col, drop=False, inplace=True)

    def update_duplicate_and_empty_cols_with_deposit_data(self, deposit_name):
        self.check_deposit_name(deposit_name)
        empty_cols = self.get_empty_cols()
        cols_to_update = empty_cols + self.duplicate_cols
        count_items = 0
        total_items = len(self.df.index)
        for item_id in self.df.index:
            count_items += 1
            deposits = self.get_deposits_for_item(item_id)
            row = self.get_row_for_deposit(deposits, deposit_name)
            for col in cols_to_update:
                self.df.loc[item_id, col] = row[col]
            advance = count_items / total_items
            logger.info("%s % done." % "{:.2f}".format(advance))

    def check_deposit_name(self, deposit_name):
        try:
            self.available_deposits
        except AttributeError:
            self.update_available_deposits()
        if deposit_name not in self.available_deposits:
            logger.error("Deposit %s not in available deposits. Available deposits:" % deposit_name)
            logger.error(self.available_deposits)
            raise ValueError

    def get_empty_cols(self):
        empty_cols = []
        for col in self.df.columns:
            if self.df[col].isnull().all():
                empty_cols.append(col)
        return empty_cols

    def get_deposits_for_item(self, item_id):
        return self.session.get_deposits_for(str(item_id))

    def get_row_for_deposit(self, deposits, deposit_name):
        deposit_df = pd.DataFrame(deposits)
        deposit_df.set_index(self.deposit_name_col, drop=False, inplace=True)
        return deposit_df.loc[deposit_name]

    def change_header_names(self):
        self.df.rename(columns=self.col_name_dict, inplace=True)

    def update_available_deposits(self):
        first_item_id = self.get_first_item_id()
        deposits = self.get_deposits_for_item(first_item_id)
        self.available_deposits = []
        for deposit in deposits:
            self.available_deposits.append(deposit[self.deposit_name_col])

    def get_first_item_id(self):
        try:
            first_item_id = list(self.df.index)[0]
        except AttributeError:
            self.set_updated_inventory()
            self.set_inventory_df_with_header()
            first_item_id = list(self.df.index)[0]
        return first_item_id


# GET MOVEMENTS CLASS
##############################################################################


class GetMovements(object):
    state = colppy_configuration.state
    col_name_dict = {}  # readable name to Colppy name

    def __init__(self, state=None):
        if state:
            self.state = state

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
