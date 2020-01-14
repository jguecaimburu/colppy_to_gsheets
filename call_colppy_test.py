# # tests

# Ask for classes encapsulation for Session vs Call vs test modifying keys

import output_examples_v2
import unittest
from call_colppy import ColppySession
import copy


class ColppySessionTest(unittest.TestCase):
    state = "testing"
    dates = ("2019-11-10", "2019-11-17")
    new_dates = ("2019-11-21", "2019-11-28")

    def test_init_session(self):
        test_session = ColppySession()
        self.assertIsInstance(
                    test_session.payloads["list_diary"]["parameters"]["sesion"],
                    str
                    )
        test_session.login_and_set_session_key_for(self.state)
        self.assertIsInstance(
                    test_session.payloads["list_diary"]["parameters"]["sesion"],
                    dict
                    )

    def test_set_invoices(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        dates = self.dates
        test_session.set_invoices_for(dates)
        self.assertEqual(len(test_session.invoices),
                         output_examples_v2.invoices_len)
        self.assertEqual(test_session.invoices[:6],
                         output_examples_v2.first_invoices)
        self.assertEqual(test_session.invoices[len(test_session.invoices)-5:],
                         output_examples_v2.last_invoices)

    def test_set_diary(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        dates = self.dates
        test_session.set_diary_for(dates)
        self.assertEqual(len(test_session.diary),
                         output_examples_v2.diary_len)
        self.assertEqual(test_session.diary[:6],
                         output_examples_v2.first_diary)
        self.assertEqual(test_session.diary[len(test_session.diary)-5:],
                         output_examples_v2.last_diary)

    def test_set_invoices_diary_first_date(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        dates = self.dates
        test_session.set_invoices_for(dates)
        self.assertEqual(len(test_session.invoices),
                         output_examples_v2.invoices_len)
        self.assertEqual(test_session.invoices[:6],
                         output_examples_v2.first_invoices)
        self.assertEqual(test_session.invoices[len(test_session.invoices)-5:],
                         output_examples_v2.last_invoices)
        test_session.set_diary_for()
        self.assertEqual(len(test_session.diary),
                         output_examples_v2.diary_len)
        self.assertEqual(test_session.diary[:6],
                         output_examples_v2.first_diary)
        self.assertEqual(test_session.diary[len(test_session.diary)-5:],
                         output_examples_v2.last_diary)

    def test_set_invoices_diary_different_dates(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        dates = self.dates
        test_session.set_invoices_for(dates)
        new_dates = self.new_dates
        test_session.set_diary_for(new_dates)
        self.assertEqual(len(test_session.diary),
                         output_examples_v2.new_diary_len)
        self.assertEqual(test_session.diary[:6],
                         output_examples_v2.first_new_diary)
        self.assertEqual(test_session.diary[len(test_session.diary)-5:],
                         output_examples_v2.last_new_diary)

    def test_set_invoices_with_no_date_after_overwritting_date(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        dates = self.dates
        test_session.set_diary_for(dates)
        self.assertEqual(test_session.last_call_dates, dates)
        new_dates = self.new_dates
        test_session.set_invoices_for(new_dates)
        self.assertEqual(test_session.last_call_dates, new_dates)
        test_session.set_diary_for()
        self.assertEqual(test_session.last_call_dates, new_dates)
        self.assertEqual(len(test_session.diary),
                         output_examples_v2.new_diary_len)
        self.assertEqual(test_session.diary[:6],
                         output_examples_v2.first_new_diary)
        self.assertEqual(test_session.diary[len(test_session.diary)-5:],
                         output_examples_v2.last_new_diary)

    def test_unsorted_dates_response_equals_sorted(self):
        sorted_test_session = ColppySession()
        sorted_test_session.login_and_set_session_key_for(self.state)
        sorted_dates = self.dates
        sorted_test_session.set_invoices_for(sorted_dates)
        unsorted_test_session = ColppySession()
        unsorted_test_session.login_and_set_session_key_for(self.state)
        unsorted_dates = self.dates[::-1]
        unsorted_test_session.set_invoices_for(unsorted_dates)
        self.assertEqual(sorted_test_session.invoices[:6],
                         unsorted_test_session.invoices[:6])

    def test_set_invoices_for_company(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        test_session.company_id = None
        dates = self.dates
        company_id = '19459'
        test_session.set_invoices_for(dates, company_id)
        self.assertEqual(len(test_session.invoices),
                         output_examples_v2.invoices_len)
        self.assertEqual(test_session.invoices[:6],
                         output_examples_v2.first_invoices)
        self.assertEqual(test_session.invoices[len(test_session.invoices)-5:],
                         output_examples_v2.last_invoices)

    def test_set_inventory(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        test_session.set_inventory()
        self.assertGreater(len(test_session.inventory), 1000)

    def test_get_deposit_for_items(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        test_session.set_inventory()
        first_id = test_session.inventory[0]['idItem']
        number_of_deposits_in_call = len(test_session.get_deposits_for(first_id))
        len_inv = len(test_session.inventory)

        for item in test_session.inventory[1:4]:
            id = item['idItem']
            deposits = test_session.get_deposits_for(id)
            self.assertEqual(len(deposits), number_of_deposits_in_call)

        for item in test_session.inventory[int(len_inv/2):int(len_inv/2)+3]:
            id = item['idItem']
            deposits = test_session.get_deposits_for(id)
            self.assertEqual(len(deposits), number_of_deposits_in_call)

        for item in test_session.inventory[len_inv-3:]:
            id = item['idItem']
            deposits = test_session.get_deposits_for(id)
            self.assertEqual(len(deposits), number_of_deposits_in_call)

    # Raise corresponding error

    def test_set_invoices_no_date(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        with self.assertRaises(ValueError):
            test_session.set_invoices_for()

    def test_wrong_date_format(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        dates = ("10-12-2019", "20-12-2019")
        with self.assertRaises(ValueError):
            test_session.set_invoices_for(dates)

    def test_non_existent_date(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        dates = ("2019-02-20", "2019-02-30")
        with self.assertRaises(ValueError):
            test_session.set_invoices_for(dates)

    def test_no_company_if_default_none(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        test_session.company_id = None
        dates = self.dates
        with self.assertRaises(ValueError):
            test_session.set_invoices_for(dates)

    # def test_wrong_ccost_filter(self):
    #     test_session = ColppySession()
    #     test_session.login_and_set_session_key_for(self.state)
    #     dates = self.dates
    #     wrong_ccost_1 = "Sublimito"
    #     test_session.set_filtered_diary_for(dates, ccost_1=wrong_ccost_1)
    #     self.assertEqual(len(test_session.diary),
    #                      len(test_session.filtered_diary))

    # Test class extras

    def test_update_n_ccost(self):
        clean_ccosts = {1: {
                            '': None,
                            ' ': None,
                            None: None
                            },
                        2: {
                            '': None,
                            ' ': None,
                            None: None
                            }}
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        test_session_ccosts = copy.deepcopy(test_session.ccosts)
        clean_test_session = ColppySession()
        clean_test_session.login_and_set_session_key_for(self.state)
        clean_test_session.ccosts = clean_ccosts
        clean_test_session.update_n_ccosts(1)
        clean_test_session.update_n_ccosts(2)
        self.assertEqual(test_session_ccosts,
                         clean_test_session.ccosts)

    def test_update_wrong_n_ccost(self):
        test_session = ColppySession()
        test_session.login_and_set_session_key_for(self.state)
        with self.assertRaises(ValueError):
            test_session.update_n_ccosts(3)


if __name__ == '__main__':
    unittest.main()
