"""
Check encapsulation. Some tests violate to avoid defaults values easily.

1 Item ID is set to 0. Maybe Colppy bug

"""

import colppy_api_output_examples
import unittest
from colppy_api import Caller


class CallerTest(unittest.TestCase):
    dates = ("2019-11-10", "2019-11-17")
    new_dates = ("2019-11-21", "2019-11-28")

    def test_get_invoices(self):
        test_caller = Caller()
        dates = self.dates
        invoices = test_caller.get_invoices_for(dates)
        self.assertEqual(len(invoices),
                         colppy_api_output_examples.invoices_len)
        self.assertEqual(invoices[:6],
                         colppy_api_output_examples.first_invoices)
        self.assertEqual(invoices[len(invoices)-5:],
                         colppy_api_output_examples.last_invoices)

    def test_get_diary(self):
        test_caller = Caller()
        dates = self.dates
        diary = test_caller.get_diary_for(dates)
        self.assertEqual(len(diary),
                         colppy_api_output_examples.diary_len)
        self.assertEqual(diary[:6],
                         colppy_api_output_examples.first_diary)
        self.assertEqual(diary[len(diary)-5:],
                         colppy_api_output_examples.last_diary)

    def test_get_invoices_diary_first_date(self):
        test_caller = Caller()

        dates = self.dates
        invoices = test_caller.get_invoices_for(dates)
        self.assertEqual(len(invoices),
                         colppy_api_output_examples.invoices_len)
        self.assertEqual(invoices[:6],
                         colppy_api_output_examples.first_invoices)
        self.assertEqual(invoices[len(invoices)-5:],
                         colppy_api_output_examples.last_invoices)
        diary = test_caller.get_diary_for(dates)
        self.assertEqual(len(diary),
                         colppy_api_output_examples.diary_len)
        self.assertEqual(diary[:6],
                         colppy_api_output_examples.first_diary)
        self.assertEqual(diary[len(diary)-5:],
                         colppy_api_output_examples.last_diary)

    def test_get_invoices_diary_different_dates(self):
        test_caller = Caller()
        dates = self.dates
        test_caller.get_invoices_for(dates)
        new_dates = self.new_dates
        diary = test_caller.get_diary_for(new_dates)
        self.assertEqual(len(diary),
                         colppy_api_output_examples.new_diary_len)
        self.assertEqual(diary[:6],
                         colppy_api_output_examples.first_new_diary)
        self.assertEqual(diary[len(diary)-5:],
                         colppy_api_output_examples.last_new_diary)

    def test_get_invoices_with_no_date_after_overwritting_date(self):
        test_caller = Caller()
        dates = self.dates
        test_caller.get_diary_for(dates)
        new_dates = self.new_dates
        test_caller.get_invoices_for(new_dates)
        diary = test_caller.get_diary_for()
        self.assertEqual(len(diary),
                         colppy_api_output_examples.new_diary_len)
        self.assertEqual(diary[:6],
                         colppy_api_output_examples.first_new_diary)
        self.assertEqual(diary[len(diary)-5:],
                         colppy_api_output_examples.last_new_diary)

    def test_unsorted_dates_response_equals_sorted(self):
        sorted_test_caller = Caller()
        sorted_dates = self.dates
        sorted_invoices = sorted_test_caller.get_invoices_for(sorted_dates)
        unsorted_test_caller = Caller()
        unsorted_dates = self.dates[::-1]
        unsorted_invoices = unsorted_test_caller.get_invoices_for(unsorted_dates)
        self.assertEqual(sorted_invoices[:6],
                         unsorted_invoices[:6])

    def test_get_invoices_for_company(self):
        test_caller = Caller()
        test_caller.payload_builder.company_id = None  # Encapsulation
        dates = self.dates
        company_id = '19459'
        invoices = test_caller.get_invoices_for(dates, company_id)
        self.assertEqual(len(invoices),
                         colppy_api_output_examples.invoices_len)
        self.assertEqual(invoices[:6],
                         colppy_api_output_examples.first_invoices)
        self.assertEqual(invoices[len(invoices)-5:],
                         colppy_api_output_examples.last_invoices)

    def test_get_inventory(self):
        test_caller = Caller()
        inventory = test_caller.get_inventory_for()
        self.assertGreater(len(inventory), 1000)

    def test_get_deposits_stock_for_items(self):
        test_caller = Caller()
        inventory = test_caller.get_inventory_for()
        first_id = inventory[0]['idItem']
        number_of_deposits_in_call = len(test_caller.get_deposits_stock_for(first_id))
        len_inv = len(inventory)

        for item in inventory[1:4]:
            id = item['idItem']
            deposits = test_caller.get_deposits_stock_for(id)
            self.assertEqual(len(deposits), number_of_deposits_in_call)

        for item in inventory[int(len_inv/2):int(len_inv/2)+3]:
            id = item['idItem']
            deposits = test_caller.get_deposits_stock_for(id)
            self.assertEqual(len(deposits), number_of_deposits_in_call)

        for item in inventory[len_inv-3:]:
            id = item['idItem']
            deposits = test_caller.get_deposits_stock_for(id)
            self.assertEqual(len(deposits), number_of_deposits_in_call)

    # Raise corresponding error

    def test_get_invoices_no_date(self):
        test_caller = Caller()
        with self.assertRaises(ValueError):
            test_caller.get_invoices_for()

    def test_wrong_date_format(self):
        test_caller = Caller()
        dates = ("10-12-2019", "20-12-2019")
        with self.assertRaises(ValueError):
            test_caller.get_invoices_for(dates)

    def test_non_existent_date(self):
        test_caller = Caller()
        dates = ("2019-02-20", "2019-02-30")
        with self.assertRaises(ValueError):
            test_caller.get_invoices_for(dates)

    def test_no_company_if_default_none(self):
        test_caller = Caller()
        test_caller.payload_builder.company_id = None  # Encapsulation
        dates = self.dates
        with self.assertRaises(ValueError):
            test_caller.get_invoices_for(dates)


if __name__ == '__main__':
    unittest.main()
