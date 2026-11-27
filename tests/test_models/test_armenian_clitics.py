import contextlib
import io
import os
import tempfile
import warnings
from unittest import TestCase, skipUnless
from unittest.mock import patch

from pie_extended.models.hy_hye.imports import get_iterator_and_processor
from pie_extended.models.hy_hye.tokenizer import ArmenianTokenizer
from pie_extended.models.hy_xcl import imports as xcl_imports
from pie_extended.models.hy_xcl import segmenter as clitics
from pie_extended.pipeline.postprocessor.spacing import SpaceAfterProcessor
from pie_extended.testing_utils import FakeAutoTag
from pie_extended.cli.utils import get_model

NO = "No"

# Handwritten: the Classical Armenian treebank (CAVaL) is CC BY-NC-SA, it cannot be copied here.
# (text, words as the treebank would cut them)
SENTENCES = [
    ("զմեղս իւրեանց։", ["զ", "մեղս", "իւրեանց", "։"]),
    ("զճանապարհ նորա։", ["զ", "ճանապարհ", "նորա", "։"]),
    ("յանապատին ասէ։", ["յ", "անապատի", "ն", "ասէ", "։"]),
    ("յաշխարհին լսէ։", ["յ", "աշխարհի", "ն", "լսէ", "։"]),
    ("Ո՞ւր է նա։", ["Ուր", "՞", "է", "նա", "։"]),
    ("ցնոսա ասէ։", ["ց", "նոսա", "ասէ", "։"]),
    ("ասէ նոսա։", ["ասէ", "նոսա", "։"]),
    ("մեղս ճանապարհ։", ["մեղս", "ճանապարհ", "։"]),
    ("Spelling does not match", ["x"]),  # Cannot be rebuilt: skipped
]


def conllu(sentences) -> str:
    out = []
    for number, (text, words) in enumerate(sentences):
        out.append("# sent_id = s{}\n# text = {}".format(number, text))
        out.extend("{}\t{}\t_\t_\t_\t_\t_\t_\t_\t_".format(i, word) for i, word in enumerate(words, 1))
        out.append("")
    return "\n".join(out) + "\n"


class Stub:
    """ Segmenter that cuts what it is told """
    def __init__(self, cuts):
        self._cuts = cuts

    def cuts(self, word):
        return self._cuts.get(word, [])


class TestCliticSegmenter(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def trained(self):
        with open(os.path.join(self.directory.name, "t.conllu"), "w", encoding="utf-8") as f:
            f.write(conllu(SENTENCES))
        examples = clitics.training_examples(clitics.read_conllu(os.path.join(self.directory.name, "t.conllu")))
        return clitics.train(examples * 6, epochs=8)

    def test_training_examples_follow_our_tokens(self):
        """ Marks are moved by the tokenizer: examples are made of its words, cut as the treebank does """
        path = os.path.join(self.directory.name, "t.conllu")
        with open(path, "w", encoding="utf-8") as f:
            f.write(conllu(SENTENCES))
        examples = dict(clitics.training_examples(clitics.read_conllu(path)))
        self.assertEqual(examples["զմեղս"], {1})
        self.assertEqual(examples["յանապատին"], {1, 8})
        self.assertEqual(examples["մեղս"], set())
        self.assertEqual(examples["Ուր"], set(), "The mark is out of the word")
        self.assertNotIn("Spelling", examples, "A sentence that cannot be rebuilt is skipped")

    def test_learns_where_to_cut(self):
        segmenter = self.trained()
        self.assertEqual(segmenter.split("զմեղս"), ["զ", "մեղս"])
        self.assertEqual(segmenter.split("յանապատին"), ["յ", "անապատի", "ն"])
        self.assertEqual(segmenter.split("մեղս"), ["մեղս"])
        self.assertEqual(segmenter.split("ասէ"), ["ասէ"])

    def test_only_armenian_words_are_cut(self):
        segmenter = self.trained()
        for token in ("։", "1.000", "pensionnaire", "ց", "", "կ՚"):
            self.assertEqual(segmenter.cuts(token), [], token)

    def test_training_is_deterministic(self):
        self.assertEqual(self.trained().weights, self.trained().weights)

    def test_save_and_load(self):
        segmenter = self.trained()
        path = os.path.join(self.directory.name, "sub", "clitics.json")
        segmenter.save(path)
        loaded = clitics.CliticSegmenter.load(path)
        for word in ("զմեղս", "յանապատին", "մեղս", "ցնոսա"):
            self.assertEqual(loaded.cuts(word), segmenter.cuts(word))

    def test_evaluate(self):
        segmenter = self.trained()
        scores = clitics.evaluate(segmenter, [(t, w) for t, w in SENTENCES if t != "Spelling does not match"])
        self.assertEqual(scores["f1"], 1.0)
        self.assertEqual(scores["sentences_exact"], 1.0)
        empty = clitics.evaluate(clitics.CliticSegmenter(), [(t, w) for t, w in SENTENCES if "զ" in t])
        self.assertEqual(empty["recall"], 0.0)
        self.assertEqual(empty["sentences_exact"], 0.0)


class TestTokenizerWithSegmenter(TestCase):
    def tokenize(self, text, cuts):
        tokenizer = ArmenianTokenizer(Stub(cuts))
        return tokenizer.word_tokenizer(text), tokenizer.surface_tokens()

    def test_words_are_cut_and_written_where_they_are(self):
        tokens, written = self.tokenize("յանապատին ասէ", {"յանապատին": [1, 8]})
        self.assertEqual(tokens, ["յ", "անապատի", "ն", "ասէ"])
        self.assertEqual(written, ["յ", "անապատի", "ն", "ասէ"])

    def test_mark_stays_with_the_piece_it_follows(self):
        tokens, written = self.tokenize("զի՞նչ է", {"զինչ": [1]})
        self.assertEqual(tokens, ["զ", "ինչ", "՞", "է"])
        self.assertEqual(written, ["զ", "ի՞նչ", "", "է"])
        tokens, written = self.tokenize("ի՞ս", {"իս": [1]})
        self.assertEqual((tokens, written), (["ի", "ս", "՞"], ["ի՞", "ս", ""]))

    def test_without_segmenter_nothing_is_cut(self):
        self.assertEqual(ArmenianTokenizer().word_tokenizer("յանապատին"), ["յանապատին"])

    def test_pieces_are_glued_in_the_text(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            module = get_model("hy_xcl")
            tagger = FakeAutoTag.from_model_string(module.Models, batch_size=8)
            iterator, processor = get_iterator_and_processor(segmenter=Stub({"զմեղս": [1], "զինչ": [1]}))
            annotations = tagger.tag_str(
                "զմեղս նորա։ զի՞նչ է", iterator=iterator, processor=SpaceAfterProcessor(processor)
            )
        self.assertEqual(iterator.spacing()[1], 0)
        self.assertEqual(
            [(a["form"], a["SpaceAfter"]) for a in annotations],
            [("զ", NO), ("մեղս", "_"), ("նորա", NO), ("։", "_"), ("զ", NO), ("ինչ", NO), ("՞", "_"), ("է", "_")]
        )


class TestInstallation(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = os.path.join(self.directory.name, "hy_xcl", "clitics.json")

    def test_without_the_segmenter_clitics_are_not_split_and_the_user_is_told(self):
        with patch.object(clitics, "default_path", lambda: self.path):
            with self.assertWarns(UserWarning) as raised:
                iterator, _ = xcl_imports.get_iterator_and_processor()
        self.assertIsNone(iterator.tokenizer.segmenter)
        self.assertIn("install-addons hy_xcl", str(raised.warning))

    def test_addons_learn_from_the_treebank_and_the_pipeline_uses_it(self):
        def fake_download(url, filename):  # The treebank: handwritten sentences instead
            self.assertIn("UD_Classical_Armenian-CAVaL", url)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(conllu(SENTENCES * 6))

        output = io.StringIO()
        with patch.object(clitics, "default_path", lambda: self.path), \
                patch("pie_extended.cli.utils._download", fake_download), contextlib.redirect_stdout(output):
            self.assertTrue(xcl_imports.addons())
            with warnings.catch_warnings():
                warnings.simplefilter("error")  # Nothing to warn about anymore
                iterator, _ = xcl_imports.get_iterator_and_processor()
        self.assertTrue(os.path.exists(self.path))
        self.assertIn("cut points F1", output.getvalue())
        self.assertEqual(
            [token for sentence in iterator("զմեղս ասէ։") for token in sentence[0]],
            ["զ", "մեղս", "ասէ", "։"]
        )


@skipUnless(os.path.exists(clitics.default_path()), "`pie-extended install-addons hy_xcl` was not run")
class TestWithTheLearnedSegmenter(TestCase):
    """ Only where the segmenter was learned from the real treebank (it cannot be distributed) """
    segmenter = clitics.CliticSegmenter.load(clitics.default_path()) if os.path.exists(clitics.default_path()) else None

    def test_known_clitics(self):
        self.assertEqual(self.segmenter.split("զմեղս"), ["զ", "մեղս"])
        self.assertEqual(self.segmenter.split("զճանապարհ"), ["զ", "ճանապարհ"])
        self.assertEqual(self.segmenter.split("յանապատին"), ["յ", "անապատի", "ն"])
        self.assertEqual(self.segmenter.split("ցնոսա"), ["ց", "նոսա"])

    def test_words_that_are_not_cut(self):
        self.assertEqual(self.segmenter.split("ասէ"), ["ասէ"])
