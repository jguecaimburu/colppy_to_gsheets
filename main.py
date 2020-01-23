""" Inventory Updater To DOs:
- Test more situations
- Test with existing sheet
- Test in Jupyter

Future TO-DOs:
- Refactor updater module class
- Filter relevant INVENTORY
- Correct bare EXCEPTS
- Write comments if necessary
- Refactor configuration of classes in Colppy Api
- Mock external APIs in unittests

Future General:
- WRITE UNITTEST THAT DON'T DEPEND ON INTERNET CONNECTION
- Write comments to 3 modules where necessary
"""


from inventory_updater import DepositInventoryUpdater

state = "testing"
gsheet_name = "test_iki"
deposit_name = "Local"

if __name__ == "__main__":
    deposit_updater = DepositInventoryUpdater(state)
    deposit_updater.paste_deposit_inventory_to_gsheet(deposit_name,
                                                      gsheet_name)
