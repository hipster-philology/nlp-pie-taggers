from pie_extended.models.fro.imports import get_iterator_and_processor
from pie_extended.testing_utils import FakeTagger
from typing import List, Tuple

from unittest import TestCase
from .test_lasla import make_fake_data


def make_controller(sentences: List[str]):
    # Add the lemmatizer routes
    tagger = FakeTagger(
        make_fake_data(sentences),
        tasks="lemma,MODE,TEMPS,PERS,NOMB,GENRE,CAS,DEGRE,POS".split(",")
    )
    iterator, processor = get_iterator_and_processor()
    return tagger, iterator, processor


class TestFro(TestCase):
    def test_elision_apostrophe(self):
        string = "q'il meurt"
        treated = ["q il meurt"]
        tagger, it, pro = make_controller(treated)
        out = tagger.tag_str(string, it, pro)
        self.assertEqual(out[0]["form"], "q'")
        self.assertEqual(out[0]["treated"], "q")

    def test_elision_apostrophe_and_quote(self):
        string = "'q'il meurt 'dit il'"
        treated = ["q il meurt dit il"]
        tagger, it, pro = make_controller(treated)
        out = tagger.tag_str(string, it, pro)
        self.assertEqual(out[0]["form"], "'")
        self.assertEqual(out[0]["treated"], "'")
        self.assertEqual(out[1]["form"], "q'")
        self.assertEqual(out[1]["treated"], "q")
        self.assertEqual(out[-1]["form"], "'", "Last apostrophe is kept")
        # Ending and starting apostrophe are not reinserted for some reason.
