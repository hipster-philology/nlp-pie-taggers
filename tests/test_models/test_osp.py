from typing import List
from unittest import TestCase

from pie_extended.models import modules
from pie_extended.models import osp
from pie_extended.models.osp.imports import get_iterator_and_processor
from pie_extended.testing_utils import FakeTagger


def make_fake_data(sentences: List[str], nb_tasks: int = 2):
    return [
        [(token, tuple([token, *["fake"] * nb_tasks])) for token in sentence.split()]
        for sentence in sentences
    ]


def make_controller(sentences: List[str]):
    tagger = FakeTagger(make_fake_data(sentences, nb_tasks=1), tasks="lemma,POS".split(","))
    iterator, processor = get_iterator_and_processor()
    return tagger, iterator, processor


class TestOspRegistration(TestCase):
    def test_registered(self):
        self.assertIn("osp", modules)
        self.assertEqual(osp.DESC.lang, "osp")

    def test_models_use_downloads(self):
        self.assertEqual(len(osp.DOWNLOADS), 2)
        for file in osp.DOWNLOADS:
            self.assertIn(file.name, osp.Models)
            self.assertIn("/castillan/", file.url)
        self.assertEqual(osp.Models.count("<"), 2)
        self.assertTrue(osp.Models.endswith(",POS>"))


class TestOspExcluders(TestCase):
    def test_excluded_tokens_are_not_tagged(self):
        tagger, it, pro = make_controller(["El rey don Alfonso ?"])
        out = tagger.tag_str("[REF:1.2] El rey ΛΟΓΟΣ don ² Alfonso ?", it, pro)
        self.assertEqual(
            [o["form"] for o in out],
            ["[REF:1.2]", "El", "rey", "ΛΟΓΟΣ", "don", "²", "Alfonso", "?"]
        )
        self.assertEqual(tagger.seen, [["El", "rey", "don", "Alfonso", "?"]])

    def test_ign(self):
        tagger, it, pro = make_controller(["El rey"])
        out = tagger.tag_str("El [IGN:xyz] rey", it, pro)
        self.assertEqual([o["form"] for o in out], ["El", "[IGN:xyz]", "rey"])
        self.assertEqual(tagger.seen, [["El", "rey"]])

    def test_abbreviation_is_kept_with_dot_and_not_tagged(self):
        tagger, it, pro = make_controller(["Dixo Cid ."])
        out = tagger.tag_str("Dixo Sr. Cid.", it, pro)
        self.assertEqual([o["form"] for o in out], ["Dixo", "Sr.", "Cid", "."])
        self.assertEqual(tagger.seen, [["Dixo", "Cid", "."]])

    def test_output_keys(self):
        tagger, it, pro = make_controller(["El rey"])
        out = tagger.tag_str("El rey", it, pro)
        self.assertEqual(set(out[0].keys()) >= {"form", "lemma", "POS"}, True)

    def test_known_punctuation_is_seen_by_the_model(self):
        tagger, it, pro = make_controller(["El & rey , non ."])
        out = tagger.tag_str("El & rey, non.", it, pro)
        self.assertEqual(tagger.seen, [["El", "&", "rey", ",", "non", "."]])
        self.assertEqual([o["lemma"] for o in out], ["El", "&", "rey", ",", "non", "."])
        self.assertNotIn("--IGN.--", [o["treated"] for o in out])

    def test_unknown_punctuation_is_its_own_lemma_and_punct(self):
        tagger, it, pro = make_controller(["El rey"])
        out = tagger.tag_str("El ¶ rey «", it, pro)
        self.assertEqual(tagger.seen, [["El", "rey"]])
        for o in (out[1], out[3]):
            self.assertEqual(o["lemma"], o["form"])
            self.assertEqual(o["POS"], "PUNCT")
            self.assertEqual(o["treated"], "--IGN.--")

    def test_other_excluded_tokens_stay_empty(self):
        tagger, it, pro = make_controller(["El"])
        out = tagger.tag_str("El [REF:1.2]", it, pro)
        self.assertEqual(out[1]["lemma"], "_")
        self.assertEqual(out[1]["POS"], "_")


class TestOspWarning(TestCase):
    def test_poc_warning_on_load(self):
        with self.assertWarnsRegex(UserWarning, "proof of concept"):
            get_iterator_and_processor()
