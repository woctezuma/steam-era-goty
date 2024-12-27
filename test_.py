import unittest

import anonymize_data
import bayesian_goty
import compute_bayesian_rating
import schulze_goty


class TestAnonymizeDataMethods(unittest.TestCase):
    def test_anonymize(self):
        example_filename = "data/anonymized_votes/steam_resetera_2017_goty_votes.csv"
        file_encoding = "cp1252"

        data = bayesian_goty.load_input(example_filename, file_encoding)

        # Assumption: the name of the author appears as the first token on each line of data
        author_name_token_index = 0

        anonymized_data = anonymize_data.anonymize(data, author_name_token_index)

        self.assertGreater(len(anonymized_data), 0)


class TestComputeBayesianRatingMethods(unittest.TestCase):
    def test_main(self):
        self.assertTrue(compute_bayesian_rating.main())


class TestBayesianGotyMethods(unittest.TestCase):
    def test_main(self):
        self.assertTrue(bayesian_goty.main())


class TestSchulzeGotyMethods(unittest.TestCase):
    def test_main(self):
        self.assertTrue(schulze_goty.main())


if __name__ == "__main__":
    unittest.main()
