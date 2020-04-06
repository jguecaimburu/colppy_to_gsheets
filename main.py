from inventory_updater import DepositInventoryUpdater

state = "testing"
gsheet_name = "test_iki"
deposit_name = "Local"

if __name__ == "__main__":
    deposit_updater = DepositInventoryUpdater(state)
    deposit_updater.paste_deposit_inventory_to_gsheet(deposit_name,
                                                      gsheet_name)
