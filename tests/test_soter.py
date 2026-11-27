import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from unittest import TestCase, skipUnless
from unittest.mock import patch

from click.testing import CliRunner

from pie_extended.cli.main import pie_ext
from pie_extended.cli.utils import get_model, get_tagger, resolve_tasks
from pie.utils import model_spec
from pie_extended.composite_tagger import CompositeTagger
from pie_extended.models import modules
from pie_extended.soter import SoterLemmatizer, build_input
from pie_extended.spacy_tagger import SpacyTagger

HAS_TRANSFORMERS = importlib.util.find_spec("transformers") is not None
HAS_SPACY = importlib.util.find_spec("spacy") is not None


class Echo(SoterLemmatizer):
    """ Sôtêr without the model: the "lemma" is the target form of the input, so that what is given can be checked """
    def __init__(self, **kwargs):
        super(Echo, self).__init__(**kwargs)
        self.batches = []

    def load(self):
        return self

    def _generate(self, inputs):
        self.batches.append(list(inputs))
        return [text.split("<tgt> ")[1].split(" </tgt>")[0] + "-lemma" for text in inputs]


class Stub:
    """ An engine that gives what it is told """
    def __init__(self, tasks, value):
        self.tasks, self.value = tasks, value

    def tag(self, sents, lengths=None, **kwargs):
        return [[(token, tuple(self.value + str(i) for _ in self.tasks)) for i, token in enumerate(sentence)]
                for sentence in sents], list(self.tasks)


class TestSoterLemmatizer(TestCase):
    def test_what_the_model_is_given(self):
        forms = "Ἀλέξανδρος ἐγένετο βασιλεύς".split()
        self.assertEqual(build_input(forms, 1), "ἐ γ έ ν ε τ ο <sep> Ἀλέξανδρος <tgt> ἐγένετο </tgt> βασιλεύς")
        self.assertEqual(build_input(forms, 0), "Ἀ λ έ ξ α ν δ ρ ο ς <sep>  <tgt> Ἀλέξανδρος </tgt> ἐγένετο βασιλεύς")

    def test_context_is_limited(self):
        forms = list("abcdefghijklmnopqrst")
        self.assertEqual(build_input(forms, 10, context=2), "k <sep> i j <tgt> k </tgt> l m")

    def test_nfc_and_the_apostrophe_of_the_treebanks(self):
        """ NFD gives gibberish; and the apostrophe GreCy needs (U+02BC) makes the model right 46% of the time instead of 100% """
        decomposed = "έ"  # NFD
        self.assertEqual(SoterLemmatizer.normalize(decomposed), "έ")
        for apostrophe in ("'", "ʼ", "᾽", "’"):
            self.assertEqual(SoterLemmatizer.normalize("δι" + apostrophe), "δι’", repr(apostrophe))

    def test_each_token_is_lemmatized_and_the_order_is_kept(self):
        """ Batches are made of inputs of similar length: the lemmas are still given back in order """
        echo = Echo(batch_size=2)
        sentences = [["a", "bbbbbbbb", "cc"], ["dddd", "e"]]
        self.assertEqual(echo.lemmas(sentences), [["a-lemma", "bbbbbbbb-lemma", "cc-lemma"], ["dddd-lemma", "e-lemma"]])
        self.assertEqual([len(batch) for batch in echo.batches], [2, 2, 1])
        lengths = [len(text) for batch in echo.batches for text in batch]
        self.assertEqual(lengths, sorted(lengths), "Sorted by length")

    def test_contract_of_a_tagger(self):
        tagged, tasks = Echo().tag([["a", "b"], ["c"]])
        self.assertEqual(tasks, ["lemma"])
        self.assertEqual(tagged, [[("a", ("a-lemma",)), ("b", ("b-lemma",))], [("c", ("c-lemma",))]])

    def test_forms_are_given_back_as_they_were(self):
        """ The normalization is for the model: the token of the output is the one that was given """
        tagged, _ = Echo().tag([["διʼ"]])
        self.assertEqual(tagged[0][0][0], "διʼ")

    def test_convention_of_another_treebank_is_restored_from_the_table(self):
        echo = Echo(convention="proiel")
        echo.table = {("a", "a-lemma"): "A-PROIEL"}
        self.assertEqual(echo.lemmas([["a", "b"]]), [["A-PROIEL", "b-lemma"]])

    def test_table_is_read_from_the_folder_of_the_model(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, "tables"))
            with open(os.path.join(directory, "tables", "proiel.json"), "w", encoding="utf-8") as f:
                json.dump({"εἶπεν\tεἶπον": "λέγω"}, f, ensure_ascii=False)
            self.assertEqual(SoterLemmatizer._load_table(directory, "proiel"), {("εἶπεν", "εἶπον"): "λέγω"})

    def test_unknown_convention(self):
        with self.assertRaises(ValueError):
            SoterLemmatizer(convention="lsj")

    def test_transformers_is_optional_and_the_error_says_how_to_install_it(self):
        with patch.dict(sys.modules, {"transformers": None}):
            with self.assertRaises(ImportError) as raised:
                SoterLemmatizer().load()
        self.assertIn("pie-extended[soter]", str(raised.exception))


class TestCompositeTagger(TestCase):
    def composite(self, *engines):
        tagger = CompositeTagger()
        tagger.engines = [(engine, list(engine.tasks)) for engine in engines]
        return tagger

    def test_tasks_of_the_engines_are_put_together_sorted(self):
        tagger = self.composite(Stub(["pos"], "P"), Stub(["lemma"], "L"))
        tagged, tasks = tagger.tag([["a", "b"], ["c"]])
        self.assertEqual(tasks, ["lemma", "pos"])
        self.assertEqual(tagged, [[("a", ("L0", "P0")), ("b", ("L1", "P1"))], [("c", ("L0", "P0"))]])

    def test_an_engine_with_several_tasks(self):
        tagged, tasks = self.composite(Stub(["pos", "morph"], "S"), Stub(["lemma"], "L")).tag([["a"]])
        self.assertEqual(tasks, ["lemma", "morph", "pos"])
        self.assertEqual(tagged, [[("a", ("L0", "S0", "S0"))]])

    def test_which_engine(self):
        self.assertEqual(CompositeTagger.engine_of("soter:Zual/soter-mini"), ("soter", "Zual/soter-mini", None))
        self.assertEqual(CompositeTagger.engine_of("soter:Zual/soter-mini#proiel"), ("soter", "Zual/soter-mini", "proiel"))
        self.assertEqual(CompositeTagger.engine_of("soter:"), ("soter", "Zual/soter-mini", None), "The default repository")
        self.assertEqual(CompositeTagger.engine_of("grc_perseus_sm"), ("spacy", "grc_perseus_sm", None))

    def test_engines_are_made_from_their_names(self):
        tagger = CompositeTagger()
        with patch.object(SoterLemmatizer, "load", lambda self: self), \
                patch.object(SpacyTagger, "add_model"):
            tagger.add_model("soter:Zual/soter-mini#proiel", "lemma")
            tagger.add_model("grc_perseus_sm", "pos")
        (soter, soter_tasks), (spacy_engine, spacy_tasks) = tagger.engines
        self.assertIsInstance(soter, SoterLemmatizer)
        self.assertEqual((soter.repo, soter.convention, soter_tasks), ("Zual/soter-mini", "proiel", ["lemma"]))
        self.assertIsInstance(spacy_engine, SpacyTagger)
        self.assertEqual(spacy_tasks, ["pos"])

    def test_a_task_comes_from_one_engine_only(self):
        tagger = CompositeTagger()
        with patch.object(SoterLemmatizer, "load", lambda self: self), patch.object(SpacyTagger, "add_model"):
            tagger.add_model("soter:Zual/soter-mini", "lemma")
            with self.assertRaises(ValueError) as raised:
                tagger.add_model("grc_perseus_sm", "lemma", "pos")
        self.assertIn("lemma already given by soter:Zual/soter-mini", str(raised.exception))

    def test_the_conflict_is_found_before_a_model_is_loaded(self):
        tagger = CompositeTagger()
        tagger._owner["lemma"] = "somewhere"
        with patch.object(SoterLemmatizer, "load") as load:
            with self.assertRaises(ValueError):
                tagger.add_model("soter:Zual/soter-mini", "lemma")
        load.assert_not_called()

    def test_soter_only_gives_the_lemma(self):
        with self.assertRaises(ValueError) as raised:
            CompositeTagger().add_model("soter:Zual/soter-mini", "pos")
        self.assertIn("only gives lemma", str(raised.exception))

    def test_unknown_convention(self):
        with self.assertRaises(ValueError):
            CompositeTagger().add_model("soter:Zual/soter-mini#lsj", "lemma")


class TestGraecoSoterModel(TestCase):
    """ `grc_soter`, and what `get_tagger` does with engines """
    def loaded(self, model="grc_soter", **kwargs):
        """ What the tagger is asked to load, without loading anything """
        with patch.object(CompositeTagger, "add_model") as add_model:
            tagger = get_tagger(model, **kwargs)
        return type(tagger).__name__, [call[0] for call in add_model.call_args_list]

    def test_registered(self):
        self.assertIn("grc_soter", modules)
        module = get_model("grc_soter")
        self.assertEqual(module.Backend, "composite")
        self.assertEqual(list(model_spec(module.Models)), [("soter:Zual/soter-mini", ["lemma"]), ("grc_perseus_sm", ["pos"])])

    def test_lemma_by_soter_and_pos_by_spacy(self):
        self.assertEqual(self.loaded(), ("CompositeTagger", [("soter:Zual/soter-mini", "lemma"), ("grc_perseus_sm", "pos")]))

    def test_only_the_engines_that_are_needed_are_loaded(self):
        self.assertEqual(self.loaded(tasks=["pos"])[1], [("grc_perseus_sm", "pos")])
        self.assertEqual(self.loaded(tasks=["lemma"])[1], [("soter:Zual/soter-mini", "lemma")])

    def test_unknown_column(self):
        spec = list(model_spec(get_model("grc_soter").Models))
        with self.assertRaises(ValueError):
            resolve_tasks("grc_soter", ["morph"], spec)

    def test_another_combination_without_touching_the_code(self):
        """ The syntax of the models: it works for a model that runs spaCy as well """
        spec = "<soter:Zual/soter-mini#proiel,lemma><grc_proiel_sm,pos,morph>"
        kind, calls = self.loaded("grc_grecy", model_path=spec)
        self.assertEqual(kind, "CompositeTagger")
        self.assertEqual(calls, [("soter:Zual/soter-mini#proiel", "lemma"), ("grc_proiel_sm", "pos", "morph")])

    def test_a_spacy_model_keeps_its_tagger(self):
        with patch.object(SpacyTagger, "add_model") as add_model:
            tagger = get_tagger("grc_grecy", model_path="grc_proiel_sm")
        self.assertEqual(type(tagger).__name__, "SpacyTagger")
        self.assertEqual(add_model.call_args[0][0], "grc_proiel_sm")

    def test_addons_install_the_pipeline_and_fetch_the_model(self):
        from pie_extended.models.grc_soter import imports
        with patch.object(imports.grecy, "addons", return_value=True) as pipeline, \
                patch.dict(sys.modules, {"huggingface_hub": type("Hub", (), {"snapshot_download": staticmethod(
                    lambda repo, **kwargs: calls.append(repo))})}):
            calls = []
            self.assertTrue(imports.addons())
        pipeline.assert_called_once_with("grc_perseus_sm")
        self.assertEqual(calls, ["Zual/soter-mini"])

    def test_extra_has_what_it_needs(self):
        import tomllib
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "pyproject.toml"), "rb") as f:
            extra = tomllib.load(f)["project"]["optional-dependencies"]["soter"]
        for needed in ("transformers", "grecy"):
            self.assertIn(needed, extra)

    def test_documented_in_the_command(self):
        result = CliRunner().invoke(pie_ext, ["list"])
        self.assertIn("grc_soter", result.output)


def _soter_available() -> bool:
    """ Sôtêr in the cache of Hugging Face (no download in a test) and the pipeline of spaCy """
    if not (HAS_TRANSFORMERS and HAS_SPACY):
        return False
    try:
        from transformers import AutoTokenizer
        AutoTokenizer.from_pretrained("Zual/soter-mini", local_files_only=True)
        import spacy.util
        return spacy.util.is_package("grc_perseus_sm")
    except Exception:
        return False


@skipUnless(_soter_available(), "Sôtêr (in the cache of Hugging Face) and grc_perseus_sm are needed")
class TestWithTheRealModels(TestCase):
    """ In a subprocess, because of `grc_perseus_sm`: see tests/soter_check.py """
    @classmethod
    def setUpClass(cls):
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "soter_check.py")
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=600,
                                env=dict(os.environ, PYTHONPATH=root))
        assert result.returncode == 0, result.stderr[-2000:]
        cls.out = json.loads(result.stdout.strip().splitlines()[-1])

    def test_lemma_by_soter_and_pos_by_spacy(self):
        annotations = {a["form"]: a for a in self.out["beginning"]}
        self.assertEqual(annotations["ἀρχῇ"]["lemma"], "ἀρχή")
        self.assertEqual(annotations["ἀρχῇ"]["pos"], "NOUN")
        self.assertEqual(annotations["ἦν"]["lemma"], "εἰμί")

    def test_example_of_the_model_card(self):
        self.assertEqual(self.out["card"][1]["lemma"], "γίγνομαι")

    def test_elision_is_given_to_each_engine_as_it_needs_it(self):
        """ GreCy needs U+02BC and Sôtêr U+2019: the tokenizer gives the first, and Sôtêr converts for itself.
        (The part of speech of such a rare form is not guaranteed with a light pipeline: only the lemma is checked) """
        annotations = {a["form"]: a for a in self.out["elision"]}
        self.assertEqual(annotations["δι'"]["lemma"], "διά")
        self.assertEqual(annotations["δι'"]["treated"], "δι\u02bc", "What the model of spaCy is given")

    def test_only_the_lemma_does_not_even_load_spacy(self):
        self.assertEqual(self.out["lemma_only_engines"], ["SoterLemmatizer"])
        self.assertEqual([a["lemma"] for a in self.out["lemma_only"]], ["ἐν", "ἀρχή"])
        self.assertTrue(all("pos" not in a for a in self.out["lemma_only"]))
