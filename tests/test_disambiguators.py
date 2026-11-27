import json
import os
import subprocess
import sys
import tempfile
from unittest import TestCase

from click.testing import CliRunner

from pie_extended.cli.main import pie_ext
from pie_extended.pipeline.disambiguators import detector
from pie_extended.pipeline.disambiguators.autocat import Autocat
from pie_extended.pipeline.disambiguators.lexicons import (
    CategoryAutodisambiguation, GroupAutodisambiguation, NeedsDisambiguation, StraightAutodisambiguation
)

# Lemma, category, disambiguation index. `qui` is disambiguated by its POS, `sum` has only one possible index,
# `ago` has two but they cannot be told by POS, and `amo` is not disambiguated ("_").
CORPUS = "token\tlemma\tpos\tDis\n" + "".join(
    "{}\t{}\t{}\t{}\n".format(*row) for row in
    [("qui", "qui", "PROrel", "1")] * 3 + [("qui", "qui", "PROint", "2")] * 3 + [("est", "sum", "VER", "1")] * 2
    + [("ago", "ago", "VER", "1")] * 2 + [("ago", "ago", "VER", "2")] * 2 + [("amat", "amo", "VER", "_")] * 2
)


def write(directory, name, content) -> str:
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class TestLexicons(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def test_loaded_from_files(self):
        pos = write(self.directory.name, "pos.json", json.dumps({"qui": {"PROrel": "1", "PROint": "2"}}))
        straight = write(self.directory.name, "straight.json", json.dumps({"sum": "1"}))
        needs = write(self.directory.name, "needs.json", json.dumps(["qui", "sum", "ago"]))
        by_pos = CategoryAutodisambiguation.from_file(pos, category_key="pos")
        self.assertEqual(by_pos.disambiguate({"lemma": "qui", "pos": "PROint"}), "2")
        self.assertEqual(StraightAutodisambiguation.from_file(straight).disambiguate({"lemma": "sum"}), "1")
        marker = NeedsDisambiguation.from_file(needs, return_char="*")
        self.assertEqual(marker.disambiguate({"lemma": "ago"}), "*")
        self.assertIsNone(marker.disambiguate({"lemma": "amo"}))

    def test_files_are_read_as_utf8(self):
        path = write(self.directory.name, "straight.json", json.dumps({"ειμί": "1", "համար": "2"}, ensure_ascii=False))
        straight = StraightAutodisambiguation.from_file(path)
        self.assertEqual(straight.disambiguate({"lemma": "ειμί"}), "1")
        self.assertEqual(straight.known_tokens, {"ειμί", "համար"})

    def test_category_needs_to_know_which_annotation(self):
        path = write(self.directory.name, "pos.json", "{}")
        with self.assertRaises(AssertionError):
            CategoryAutodisambiguation.from_file(path)

    def test_group_asks_in_order_and_only_for_known_lemmas(self):
        first = StraightAutodisambiguation({"qui": "9"})
        second = CategoryAutodisambiguation("pos", {"qui": {"PROint": "2"}, "ago": {"VER": "1"}})
        group = GroupAutodisambiguation((first, second))
        self.assertEqual(group.known_tokens, {"qui", "ago"})
        self.assertEqual(group.disambiguate({"lemma": "qui", "pos": "PROint"}), "9", "The first one wins")
        self.assertEqual(group.disambiguate({"lemma": "ago", "pos": "VER"}), "1")
        self.assertIsNone(group.disambiguate({"lemma": "ago", "pos": "ADV"}))
        self.assertIsNone(group.disambiguate({"lemma": "amo", "pos": "VER"}))

    def test_a_sentence_is_disambiguated_row_by_row(self):
        group = GroupAutodisambiguation((StraightAutodisambiguation({"sum": "1"}),))
        rows = [{"lemma": "sum"}, {"lemma": "amo"}]
        self.assertEqual(list(group.disambiguate_rows(rows)), ["1", ""])

    def test_adapter_adds_the_disambiguation_to_the_lemma(self):
        group = GroupAutodisambiguation((
            StraightAutodisambiguation({"sum": "1"}),
            CategoryAutodisambiguation("pos", {"qui": {"PROint": "2"}}),
        ))
        autocat = Autocat(group, required=("lemma", "pos"))
        sentence = [("est", ("sum", "VER")), ("quis", ("qui", "PROint")), ("amat", ("amo", "VER"))]
        self.assertEqual(
            autocat(sentence, ["lemma", "pos"]),
            [("est", ["sum1", "VER"]), ("quis", ["qui2", "PROint"]), ("amat", ["amo", "VER"])]
        )
        self.assertTrue(autocat.can_run(["lemma", "pos", "Dis"]))
        self.assertFalse(autocat.can_run(["lemma"]))


class TestLexiconBuilder(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.corpus = write(self.directory.name, "corpus.tsv", CORPUS)

    def test_what_can_be_learned_from_the_pos(self):
        stats = detector.read_corpus([self.corpus])
        self.assertEqual(stats["qui"], {"1": {"PROrel": 3}, "2": {"PROint": 3}})
        self.assertNotIn("amo", stats, "No disambiguation, nothing to learn")
        dispatched = detector.dispatch(stats)
        self.assertEqual(dispatched.autodisambiguation, {"qui": {"PROrel": "1", "PROint": "2"}})
        self.assertEqual(dispatched.one_disambiguation_only, {"sum": "1"})
        self.assertEqual(dispatched.uncategorizable, ["ago"], "Two indexes with the same POS: a real ambiguity")

    def test_errors_are_ignored_below_the_limit(self):
        stats = {"qui": {"1": {"ADV": 1, "PROrel": 50}, "2": {"PROint": 87}}}
        self.assertEqual(
            detector.dispatch(stats).autodisambiguation, {"qui": {"PROrel": "1", "PROint": "2"}},
            "A POS seen once is an error"
        )

    def test_files_feed_the_lexicons(self):
        """ The whole way: corpus -> JSON -> lexicons -> disambiguation """
        prefix = os.path.join(self.directory.name, "latin-")
        detector.build_lexicons(prefix, "pos", "lemma", [self.corpus], "Dis")
        group = GroupAutodisambiguation((
            StraightAutodisambiguation.from_file(prefix + "straight.json"),
            CategoryAutodisambiguation.from_file(prefix + "pos.json", category_key="pos"),
        ))
        rows = [{"lemma": "qui", "pos": "PROint"}, {"lemma": "qui", "pos": "PROrel"}, {"lemma": "sum", "pos": "VER"},
                {"lemma": "ago", "pos": "VER"}, {"lemma": "amo", "pos": "VER"}]
        self.assertEqual(list(group.disambiguate_rows(rows)), ["2", "1", "1", "", ""])
        with open(prefix + "needs.json", encoding="utf-8") as f:
            self.assertEqual(sorted(json.load(f)), ["ago", "qui", "sum"])

    def test_summary(self):
        lines = detector.summary(detector.dispatch(detector.read_corpus([self.corpus])))
        self.assertIn("Lemma with 2 different sublemma", lines)
        self.assertIn("1 lemma with no automatization possible", lines)
        self.assertEqual(detector.summary(detector.dispatch({}))[-4:-3], ["--- Auto%: 0.00"])

    def test_no_file(self):
        with self.assertRaises(ValueError):
            detector.build_lexicons("x-", "pos", "lemma", [], "Dis")


class TestBuildLexiconsCommand(TestCase):
    def test_command(self):
        with tempfile.TemporaryDirectory() as directory:
            corpus = write(directory, "corpus.tsv", CORPUS)
            prefix = os.path.join(directory, "lat-")
            result = CliRunner().invoke(pie_ext, ["build-lexicons", "pos", corpus, "--prefix", prefix])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("--- Summary ---", result.output)
            with open(prefix + "pos.json", encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"qui": {"PROrel": "1", "PROint": "2"}})
            self.assertTrue(os.path.exists(prefix + "straight.json") and os.path.exists(prefix + "needs.json"))

    def test_command_needs_files(self):
        result = CliRunner().invoke(pie_ext, ["build-lexicons", "pos"])
        self.assertEqual(result.exit_code, 2)


class TestNoExternalLibrary(TestCase):
    def test_the_latin_model_does_not_need_autodisambiguator(self):
        """ `autocat`, the library the lexicons came from, is not a dependency anymore: forbid it """
        code = (
            "import sys; sys.modules['autocat'] = None; sys.modules['autocat.autocat'] = None\n"
            "import pie_extended.models.lasla.imports as imports\n"
            "from pie_extended.pipeline.disambiguators.autocat import Autocat, DisambiguationAsTask\n"
            "print('ok')\n"
        )
        result = subprocess.run([sys.executable, "-W", "ignore", "-c", code], capture_output=True, text=True,
                                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.assertEqual(result.stdout.strip(), "ok", result.stderr[-1500:])
