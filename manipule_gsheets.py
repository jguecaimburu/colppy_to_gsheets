from gspread_pandas import Spread
from gspread_pandas.conf import get_creds
import gsheet_configuration


class Gsheet(object):

    def __init__(self, spread, sheet=0, creds=None, create_sheet=False):
        if creds:
            self.creds = creds
        else:
            self.creds = get_creds(config=gsheet_configuration.base)
        self.spread = Spread(spread, sheet=sheet, creds=self.creds,
                             create_sheet=create_sheet)

    @property
    def spread_url(self):
        return self.spread.url

    @property
    def worksheet_name(self):
        return self.spread.sheet

    @property
    def spread_name(self):
        return self.spread.spread

    def df_to_sheet(self, df, index=True, headers=True, start_cell=(1, 1),
                    sheet=None, replace=False):
        self.spread.df_to_sheet(df, index=index, headers=headers,
                                start=start_cell, sheet=sheet, replace=replace)

    def sheet_to_df(self, index=1, header_rows=1, start_row=1, sheet=None):
        return self.spread.sheet_to_df(index=index, header_rows=header_rows,
                                       start_row=start_row, sheet=sheet)

    def find_sheet(self, sheet):
        return self.spread.find_sheet(sheet)

    def open_sheet(self, sheet, create=False):
        self.spread.open_sheet(sheet, create=create)

    def update_cells(self, start, end, vals, sheet=None):
        self.spread.update_cells(start, end, vals, sheet=sheet)

    def get_sheet_dims(self, sheet=None):
        return self.spread.get_sheet_dims(sheet=sheet)

    def clear_sheet(self, rows=1, cols=1, sheet=None):
        self.spread.clear_sheet(rows=rows, cols=cols, sheet=sheet)

    def create_sheet(self, name, rows=1, cols=1):
        self.spread.create_sheet(name, rows=rows, cols=cols)

    def delete_sheet(self, sheet):
        self.spread.delete_sheet(sheet)
