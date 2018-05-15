import unittest

import bayesian_goty
import compute_bayesian_rating
import schulze_goty


class TestComputeBayesianRatingMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(compute_bayesian_rating.main())


class TestBayesianGotyMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(bayesian_goty.main())


class TestSchulzeGotyMethods(unittest.TestCase):

    def test_main(self):
        self.assertTrue(schulze_goty.main())


if __name__ == '__main__':
    unittest.main()
