# # tests

# Ask for classes encapsulation for Session vs Call vs test modifying keys

import output_examples_v2
import unittest
from call_colppy_v2 import ColppySession, ColppyCall, colppy_defaults
import copy


class ColppySessionTest(unittest.TestCase):
    global colppy_defaults
    defaults = copy.deepcopy(colppy_defaults)
    state = "testing"

    def test_init_session(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        self.assertIsInstance(
                    test_session.list_diary_payload["parameters"]["sesion"],
                    str
                    )
        test_session.login_for(self.state)
        self.assertIsInstance(
                    test_session.list_diary_payload["parameters"]["sesion"],
                    dict
                    )

    def test_set_invoices(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        dates = ("2019-12-10", "2019-12-20")
        test_session.set_invoices_for(dates)
        self.assertEqual(len(test_session.invoices),
                         output_examples_v2.invoices_len)
        self.assertEqual(test_session.invoices[:6],
                         output_examples_v2.first_invoices)
        self.assertEqual(test_session.invoices[len(test_session.invoices)-5:],
                         output_examples_v2.last_invoices)

    def test_set_diary(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        dates = ("2019-12-10", "2019-12-20")
        test_session.set_diary_for(dates)
        self.assertEqual(len(test_session.diary_movs),
                         output_examples_v2.diary_movs_len)
        self.assertEqual(test_session.diary_movs[:6],
                         output_examples_v2.first_diary_movs)
        self.assertEqual(test_session.diary_movs[len(test_session.diary_movs)-5:],
                         output_examples_v2.last_diary_movs)

    def test_set_filtered_diary(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        dates = ("2019-12-10", "2019-12-20")
        test_session.set_filtered_diary_for(dates, ccost_1="Maquinas Sublim")
        self.assertEqual(len(test_session.filtered_diary_movs),
                         output_examples_v2.filtered_diary_movs_len)
        self.assertEqual(test_session.filtered_diary_movs[:6],
                         output_examples_v2.first_filtered_diary_movs)
        self.assertEqual(test_session.filtered_diary_movs[len(test_session.filtered_diary_movs)-5:],
                         output_examples_v2.last_filtered_diary_movs)

    def test_set_invoices_diary_filtered_first_date(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        dates = ("2019-12-10", "2019-12-20")
        test_session.set_invoices_for(dates)
        self.assertEqual(len(test_session.invoices),
                         output_examples_v2.invoices_len)
        self.assertEqual(test_session.invoices[:6],
                         output_examples_v2.first_invoices)
        self.assertEqual(test_session.invoices[len(test_session.invoices)-5:],
                         output_examples_v2.last_invoices)
        test_session.set_diary_for()
        self.assertEqual(len(test_session.diary_movs),
                         output_examples_v2.diary_movs_len)
        self.assertEqual(test_session.diary_movs[:6],
                         output_examples_v2.first_diary_movs)
        self.assertEqual(test_session.diary_movs[len(test_session.diary_movs)-5:],
                         output_examples_v2.last_diary_movs)
        test_session.set_filtered_diary_for(ccost_1="Maquinas Sublim")
        self.assertEqual(len(test_session.filtered_diary_movs),
                         output_examples_v2.filtered_diary_movs_len)
        self.assertEqual(test_session.filtered_diary_movs[:6],
                         output_examples_v2.first_filtered_diary_movs)
        self.assertEqual(test_session.filtered_diary_movs[len(test_session.filtered_diary_movs)-5:],
                         output_examples_v2.last_filtered_diary_movs)

    def test_set_invoices_diary_different_dates(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        dates = ("2019-12-10", "2019-12-20")
        test_session.set_invoices_for(dates)
        new_dates = ("2019-12-01", "2019-12-10")
        test_session.set_diary_for(new_dates)
        self.assertEqual(len(test_session.diary_movs),
                         output_examples_v2.new_diary_movs_len)
        self.assertEqual(test_session.diary_movs[:6],
                         output_examples_v2.first_new_diary_movs)
        self.assertEqual(test_session.diary_movs[len(test_session.diary_movs)-5:],
                         output_examples_v2.last_new_diary_movs)

    def test_set_invoices_with_no_date_after_overwritting_date(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        dates = ("2019-12-10", "2019-12-20")
        test_session.set_diary_for(dates)
        self.assertEqual(test_session.last_call_dates, dates)
        new_dates = ("2019-12-01", "2019-12-10")
        test_session.set_invoices_for(new_dates)
        self.assertEqual(test_session.last_call_dates, new_dates)
        test_session.set_diary_for()
        self.assertEqual(test_session.last_call_dates, new_dates)
        self.assertEqual(len(test_session.diary_movs),
                         output_examples_v2.new_diary_movs_len)
        self.assertEqual(test_session.diary_movs[:6],
                         output_examples_v2.first_new_diary_movs)
        self.assertEqual(test_session.diary_movs[len(test_session.diary_movs)-5:],
                         output_examples_v2.last_new_diary_movs)

    def test_unsorted_dates_response_equals_sorted(self):
        sorted_test_session = ColppySession(copy.deepcopy(self.defaults))
        sorted_test_session.login_for(self.state)
        sorted_dates = ("2019-12-10", "2019-12-20")
        sorted_test_session.set_invoices_for(sorted_dates)
        unsorted_test_session = ColppySession(copy.deepcopy(self.defaults))
        unsorted_test_session.login_for(self.state)
        unsorted_dates = ("2019-12-20", "2019-12-10")
        unsorted_test_session.set_invoices_for(unsorted_dates)
        self.assertEqual(sorted_test_session.invoices[:6],
                         unsorted_test_session.invoices[:6])

    def test_set_invoices_for_company(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        test_session.company_id = None
        dates = ("2019-12-10", "2019-12-20")
        company_id = '11157'
        test_session.set_invoices_for(dates, company_id)
        self.assertEqual(len(test_session.invoices),
                         output_examples_v2.invoices_len)
        self.assertEqual(test_session.invoices[:6],
                         output_examples_v2.first_invoices)
        self.assertEqual(test_session.invoices[len(test_session.invoices)-5:],
                         output_examples_v2.last_invoices)

    # Raise corresponding error

    def test_set_invoices_no_date(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        with self.assertRaises(ValueError):
            test_session.set_invoices_for()

    def test_wrong_date_format(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        dates = ("10-12-2019", "20-12-2019")
        with self.assertRaises(ValueError):
            test_session.set_invoices_for(dates)

    def test_non_existent_date(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        dates = ("2019-02-20", "2019-02-30")
        with self.assertRaises(ValueError):
            test_session.set_invoices_for(dates)

    def test_no_company_if_default_none(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        test_session.company_id = None
        dates = ("2019-12-10", "2019-12-20")
        with self.assertRaises(ValueError):
            test_session.set_invoices_for(dates)

    def test_wrong_ccost_filter(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        dates = ("2019-12-10", "2019-12-20")
        wrong_ccost_1 = "Sublimito"
        test_session.set_filtered_diary_for(dates, ccost_1=wrong_ccost_1)
        self.assertEqual(len(test_session.diary_movs),
                         len(test_session.filtered_diary_movs))

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
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        test_session_ccosts = copy.deepcopy(test_session.ccosts)
        clean_test_session = ColppySession(copy.deepcopy(self.defaults))
        clean_test_session.login_for(self.state)
        clean_test_session.ccosts = clean_ccosts
        clean_test_session.update_n_ccosts(1)
        clean_test_session.update_n_ccosts(2)
        self.assertEqual(test_session_ccosts,
                         clean_test_session.ccosts)

    def test_update_wrong_n_ccost(self):
        test_session = ColppySession(copy.deepcopy(self.defaults))
        test_session.login_for(self.state)
        with self.assertRaises(ValueError):
            test_session.update_n_ccosts(3)


if __name__ == '__main__':
    unittest.main()
