import importlib.util
import warnings
from unittest import TestCase, skipUnless

from pie_extended.cli.utils import get_model, get_imports, get_pipeline, get_tagger
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

    def test_subset_of_tasks_gives_the_same_values_and_runs_less(self):
        full_tagger, full = self.tag()
        sub_tagger, sub = self.tag(tasks=["lemma", "pos"])
        self.assertEqual([(a["lemma"], a["pos"]) for a in sub], [(a["lemma"], a["pos"]) for a in full])
        self.assertEqual(sorted(sub_tagger._tasks), ["lemma", "pos"])
        enabled = set(sub_tagger.nlp.pipe_names)
        self.assertNotIn("parser", enabled)
        self.assertNotIn("ner", enabled)
        self.assertNotIn("tagger", enabled, "`tag` was not requested")
        self.assertIn("lemmatizer", enabled)

    def test_same_output_when_the_parser_is_skipped(self):
        """ Skipping what does not produce a task must not change any value """
        tagger, annotations = self.tag()
        self.assertNotIn("parser", tagger.nlp.pipe_names)
        import spacy
        from spacy.tokens import Doc
        reference = spacy.load(MODEL)
        words = ["ἐν", "ἀρχῇ", "ἦν", "ὁ", "λόγος"]
        doc = reference(Doc(reference.vocab, words=words))
        expected = [(t.lemma_, t.pos_, t.tag_, str(t.morph) or "_") for t in doc]
        tagged, tasks = tagger.tag([words])
        got = [dict(zip(tasks, tags)) for _, tags in tagged[0]]
        self.assertEqual([(g["lemma"], g["pos"], g["tag"], g["morph"]) for g in got], expected)

    def test_several_documents_with_one_pipeline(self):
        tagger = get_tagger("grc_grecy")
        iterator, processor = get_pipeline("grc_grecy", tagger)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            first = [tagger.tag_str(TEXT, iterator=iterator, processor=processor) for _ in range(2)]
        self.assertEqual(first[0], first[1])
