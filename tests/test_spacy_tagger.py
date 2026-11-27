import importlib.util
import json
import os
import subprocess
import sys
import warnings
from unittest import TestCase, skipUnless

from pie_extended.cli.utils import get_model, get_pipeline, get_tagger
from pie_extended.models.grc_grecy.tokenizer import GreCyMemorizingTokenizer, MODIFIER_APOSTROPHE
from pie_extended.spacy_tagger import SpacyTagger

HAS_SPACY = importlib.util.find_spec("spacy") is not None


def has_pipeline(name: str) -> bool:
    if not HAS_SPACY:
        return False
    import spacy.util
    return spacy.util.is_package(name)


MODEL = get_model("grc_grecy").SpacyModel
NEEDS_MODEL = skipUnless(has_pipeline(MODEL), "spaCy and the {} pipeline are needed (grecy)".format(MODEL))
TEXT = "ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν. πάντα δι' αὐτοῦ ἐγένετο."


class TestGreCyDefinition(TestCase):
    """ What does not need spaCy """
    def test_model_uses_the_spacy_backend(self):
        module = get_model("grc_grecy")
        self.assertEqual(module.Backend, "spacy")
        self.assertEqual(module.DOWNLOADS, [])
        self.assertTrue(module.Models.startswith("<" + module.SpacyModel))

    def test_apostrophe_stays_in_its_word_and_is_normalized_only_for_the_model(self):
        tokenizer = GreCyMemorizingTokenizer()
        sentences = list(tokenizer.sentence_tokenizer("πάντα δι' αὐτοῦ ἐγένετο, δι᾽ αὐτῶν."))
        # What the model sees: elisions are kept in their word, written with the modifier letter apostrophe
        self.assertEqual(sentences, [["πάντα", "δι" + MODIFIER_APOSTROPHE, "αὐτοῦ", "ἐγένετο", ",",
                                      "δι" + MODIFIER_APOSTROPHE, "αὐτῶν", "."]])
        # What is given back: the original text
        self.assertEqual([original for _, original, _ in tokenizer.tokens],
                         ["πάντα", "δι'", "αὐτοῦ", "ἐγένετο", ",", "δι᾽", "αὐτῶν", "."])

    def test_unknown_task(self):
        with self.assertRaises(ValueError):
            SpacyTagger().add_model(MODEL, "nope")

    def test_a_single_pipeline(self):
        tagger = SpacyTagger()
        tagger.nlp = object()
        with self.assertRaises(ValueError):
            tagger.add_model(MODEL, "lemma")

    @skipUnless(HAS_SPACY, "spaCy is needed")
    def test_missing_pipeline_has_a_clear_error(self):
        with self.assertRaises(FileNotFoundError) as raised:
            SpacyTagger().add_model("grc_this_pipeline_does_not_exist", "lemma")
        self.assertIn("install-addons", str(raised.exception))


@NEEDS_MODEL
class TestGreCyTagging(TestCase):
    def tag(self, tasks=None, text=TEXT, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tagger = get_tagger("grc_grecy", tasks=tasks, **kwargs)
            iterator, processor = get_pipeline("grc_grecy", tagger)
            return tagger, tagger.tag_str(text, iterator=iterator, processor=processor)

    def test_all_tasks(self):
        tagger, annotations = self.tag()
        by_form = {a["form"]: a for a in annotations}
        self.assertEqual(sorted(tagger._tasks), ["lemma", "morph", "pos", "tag"])
        self.assertEqual(by_form["ἀρχῇ"]["lemma"], "ἀρχή")
        self.assertEqual(by_form["ἀρχῇ"]["pos"], "NOUN")
        self.assertEqual(by_form["ἀρχῇ"]["morph"], "Case=Dat|Gender=Fem|Number=Sing")
        self.assertEqual(by_form["ἐν"]["morph"], "_", "Empty features use the usual empty value")

    def test_elision(self):
        _, annotations = self.tag()
        elision = [a for a in annotations if a["form"] == "δι'"][0]
        self.assertEqual((elision["lemma"], elision["pos"]), ("διά", "ADP"))
        self.assertEqual(elision["treated"], "δι" + MODIFIER_APOSTROPHE)

    def test_excluded_tokens_and_space_after(self):
        _, annotations = self.tag(text="ἐν ἀρχῇ ἦν ὁ λόγος, καὶ")
        by_form = [(a["form"], a["SpaceAfter"]) for a in annotations]
        self.assertEqual(by_form[4:6], [("λόγος", "No"), (",", "_")])

    def test_subset_of_tasks_gives_the_same_values(self):
        _, full = self.tag()
        sub_tagger, sub = self.tag(tasks=["lemma", "pos"])
        self.assertEqual([(a["lemma"], a["pos"]) for a in sub], [(a["lemma"], a["pos"]) for a in full])
        self.assertEqual(sorted(sub_tagger._tasks), ["lemma", "pos"])

    def test_only_components_that_produce_nothing_are_skipped(self):
        tagger, _ = self.tag()
        enabled = set(tagger.nlp.pipe_names)
        self.assertFalse(enabled & SpacyTagger.UNUSED_COMPONENTS)
        self.assertIn("lemmatizer", enabled)
        self.assertIn("morphologizer", enabled)

    def test_several_documents_with_one_pipeline(self):
        tagger = get_tagger("grc_grecy")
        iterator, processor = get_pipeline("grc_grecy", tagger)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            first = [tagger.tag_str(TEXT, iterator=iterator, processor=processor) for _ in range(2)]
        self.assertEqual(first[0], first[1])


# Pipelines to compare with plain spaCy, if installed. The transformer ones have a component the small ones lack
# (`morpheus_lemmatizer`): dropping it once changed 24 lemmas out of 560.
PIPELINES = [name for name in ("grc_proiel_sm", "grc_proiel_trf", "grc_perseus_sm", "grc_perseus_trf")
             if has_pipeline(name)]
SENTENCES = [
    "ἐν ἀρχῇ ἦν ὁ λόγος , καὶ ὁ λόγος ἦν πρὸς τὸν θεόν .".split(),
    "μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος οὐλομένην , ἣ μυρίʼ Ἀχαιοῖς ἄλγεʼ ἔθηκε .".split(),
    "ἄνδρα μοι ἔννεπε μοῦσα πολύτροπον , ὃς μάλα πολλὰ πλάγχθη .".split(),
    "πάντα διʼ αὐτοῦ ἐγένετο , καὶ χωρὶς αὐτοῦ ἐγένετο οὐδὲ ἓν ὃ γέγονεν .".split(),
]


@skipUnless(PIPELINES, "No GreCy pipeline installed")
class TestSameAsPlainSpacy(TestCase):
    """ Whatever we skip, values must be the ones of the full spaCy pipeline.

    One subprocess per pipeline: two GreCy pipelines cannot live in the same process (see tests/spacy_compare.py)
    """
    def compare(self, name, tasks):
        script = os.path.join(os.path.dirname(__file__), "spacy_compare.py")
        env = dict(os.environ, PYTHONPATH=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        result = subprocess.run([sys.executable, script, json.dumps(SENTENCES), name, *tasks],
                                capture_output=True, text=True, env=env, timeout=600)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_all_tasks(self):
        for name in PIPELINES:
            with self.subTest(pipeline=name):
                result = self.compare(name, ["lemma", "pos", "tag", "morph"])
                self.assertEqual(result["ours"], result["plain"])

    def test_lemma_and_pos_only(self):
        for name in PIPELINES:
            with self.subTest(pipeline=name):
                result = self.compare(name, ["lemma", "pos"])
                self.assertEqual(
                    result["ours"],
                    [[{k: token[k] for k in ("lemma", "pos")} for token in sentence] for sentence in result["plain"]]
                )
