from unittest import TestCase

from ISO_model.scripts.extract_OCL import *


class TestParseOCL(TestCase):
    def test_summation_regex(self):
        print(r_summation)
        self.check_test(
            'the functional safety requirements shall be derived from the safety goals and safe states , considering the preliminary architectural assumptions , functional concept , operating modes , extra dummy and system states')
        self.check_test(
            'the functional safety requirements shall be derived from the safety goals and safe states , considering the preliminary architectural assumptions, functional concept , operating modes , extra dummy and system states')
        self.check_test(
            'the functional safety requirements shall be derived from the safety goals and safe states , considering the preliminary architectural assumptions ,functional concept , operating modes , extra dummy and system states')
        self.check_test(
            'the functional safety requirements shall be derived from the safety goals and safe states , considering the preliminary architectural assumptions,functional concept , operating modes , extra dummy and system states')

    def check_test(self, txt):
        print(txt)
        matches = extract_summations(txt)
        assert len(matches) == 2
        assert len(matches[0]) == 2
        assert matches[0][0] == 'the safety goals'
        assert matches[0][1] == 'safe states'
        assert len(matches[1]) == 5
        assert matches[1][0] == 'the preliminary architectural assumptions'
        assert matches[1][1] == 'functional concept'
        assert matches[1][2] == 'operating modes'
        assert matches[1][3] == 'extra dummy'
        assert matches[1][4] == 'system states'
