import contextlib
import importlib.util
import io
import json
import os
import tempfile
import subprocess
import sys
import warnings
from unittest import TestCase, skipUnless
from unittest.mock import patch

from click.testing import CliRunner

from pie_extended.cli.main import pie_ext
from pie_extended.models.grc_grecy import imports as grecy_imports

from pie_extended.cli.utils import get_model, get_pipeline, get_tagger
from pie_extended.models.grc_grecy.tokenizer import GreCyMemorizingTokenizer, MODIFIER_APOSTROPHE
from pie_extended.spacy_tagger import PipelineNotFound, SpacyTagger

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
        with self.assertRaises(PipelineNotFound) as raised:
            SpacyTagger().add_model("grc_this_pipeline_does_not_exist", "lemma")
        self.assertIsInstance(raised.exception, FileNotFoundError, "Callers that catch a missing model still work")
        self.assertIn("install-addons", str(raised.exception))
        self.assertIn("pip", str(raised.exception))

    @skipUnless(HAS_SPACY, "spaCy is needed")
    def test_command_tells_how_to_install_a_missing_pipeline(self):
        """ Not the advice for Pie models (`download`): it does nothing for a spaCy pipeline """
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "text.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("ἐν ἀρχῇ")
            result = CliRunner().invoke(
                pie_ext, ["tag", "grc_grecy", path, "--model_path", "<grc_this_pipeline_does_not_exist,lemma>"]
            )
        self.assertIn("is not installed", result.output)
        self.assertIn("install-addons", result.output)
        self.assertNotIn("pie-extended download", result.output)


class TestPipelineOfTheTagger(TestCase):
    """ At the level of the tagger: the pipeline can be given to the constructor """
    def loaded(self, **kwargs):
        with patch.object(SpacyTagger, "add_model") as add_model:
            SpacyTagger(**kwargs)
        return add_model.call_args[0] if add_model.called else None

    def test_nothing_is_loaded_without_a_pipeline(self):
        self.assertIsNone(self.loaded())

    def test_all_the_columns_until_some_are_asked_for(self):
        self.assertIsNone(SpacyTagger().selected_outputs)

    def test_all_the_tasks_by_default(self):
        self.assertEqual(self.loaded(pipeline="grc_proiel_sm"), ("grc_proiel_sm", "lemma", "morph", "pos", "tag"))

    def test_the_tasks_that_are_asked_for(self):
        self.assertEqual(self.loaded(pipeline="grc_proiel_sm", tasks=["lemma", "pos"]), ("grc_proiel_sm", "lemma", "pos"))

    def test_an_unknown_task_is_refused_at_once(self):
        with self.assertRaises(ValueError):
            SpacyTagger(pipeline="grc_proiel_sm", tasks=["nope"])


class TestRunAnotherPipeline(TestCase):
    """ Without touching the code: `--model_path`, `model_path=` """
    def loaded(self, **kwargs):
        """ What the tagger is asked to load, without loading anything (no spaCy needed) """
        with patch.object(SpacyTagger, "add_model") as add_model:
            get_tagger("grc_grecy", **kwargs)
        self.assertEqual(add_model.call_count, 1)
        return add_model.call_args[0]

    def test_default_pipeline_of_the_model(self):
        module = get_model("grc_grecy")
        self.assertEqual(self.loaded(), (module.SpacyModel, "lemma", "morph", "pos", "tag"))

    def test_the_name_of_a_pipeline_is_enough(self):
        self.assertEqual(self.loaded(model_path="grc_proiel_sm"), ("grc_proiel_sm", "lemma", "morph", "pos", "tag"))

    def test_with_the_columns_asked(self):
        self.assertEqual(self.loaded(model_path="grc_proiel_sm", tasks=["lemma", "pos"]), ("grc_proiel_sm", "lemma", "pos"))

    def test_the_full_syntax_still_works_to_choose_the_tasks(self):
        self.assertEqual(self.loaded(model_path="<grc_perseus_sm,lemma,pos>"), ("grc_perseus_sm", "lemma", "pos"))

    def test_command_option_is_documented(self):
        result = CliRunner().invoke(pie_ext, ["tag", "--help"])
        self.assertIn("name of a spaCy pipeline", " ".join(result.output.split()))


class TestChangingThePipeline(TestCase):
    """ The name of the pipeline is written once, in `SpacyModel`: everything else follows it """
    def install(self, *args, **kwargs):
        with patch.object(grecy_imports.subprocess, "call", return_value=0) as call:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(grecy_imports.addons(*args, **kwargs))
        return call.call_args[0][0]

    def test_models_follow_spacy_model(self):
        module = get_model("grc_grecy")
        self.assertEqual(module.Models, "<{},lemma,morph,pos,tag>".format(module.SpacyModel))

    def test_install_addons_installs_the_pipeline_of_the_model(self):
        command = self.install()
        self.assertEqual(command[-1].rsplit("/", 1)[1].split("-")[0], get_model("grc_grecy").SpacyModel)
        self.assertIn("github.com/jmyerston/greCy/releases", command[-1])

    def test_changing_spacy_model_changes_what_is_installed(self):
        with patch.object(grecy_imports, "SpacyModel", "grc_proiel_lg"):
            self.assertIn("/grc_proiel_lg-", self.install()[-1])
            self.assertIn("/grc_perseus_sm-", self.install("grc_perseus_sm")[-1], "A name can still be given")

    def test_extra_of_the_package_has_what_the_transformer_needs(self):
        import tomllib
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "pyproject.toml"), "rb") as f:
            extra = tomllib.load(f)["project"]["optional-dependencies"]["grecy"]
        if get_model("grc_grecy").SpacyModel.endswith("_trf"):
            self.assertIn("spacy-transformers", extra, "A transformer pipeline cannot run without it")


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

    def test_by_hand_or_with_get_tagger_the_same_columns(self):
        """ `tasks` of get_tagger are the columns: by hand, they are `selected_outputs` """
        def tsv(tagger):
            iterator, processor = get_pipeline("grc_grecy", tagger, space_after=False)
            return "".join(tagger.iter_tag("ἐν ἀρχῇ", iterator, processor=processor))

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            packaged = get_tagger("grc_grecy", tasks=["lemma", "pos"])
            by_hand = SpacyTagger(pipeline=MODEL, tasks=["lemma", "pos"])
            self.assertIn("treated", tsv(by_hand).split("\r\n")[0], "Nothing was asked for: every column is there")
            by_hand.selected_outputs = ["lemma", "pos"]
            self.assertEqual(tsv(by_hand), tsv(packaged))

    def test_tagger_made_in_one_line(self):
        tagger = SpacyTagger(pipeline=MODEL, tasks=["lemma", "pos"])
        iterator, processor = get_pipeline("grc_grecy", tagger, space_after=False)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            annotations = tagger.tag_str("ἐν ἀρχῇ", iterator=iterator, processor=processor)
        self.assertEqual([(a["form"], a["lemma"], a["pos"]) for a in annotations],
                         [("ἐν", "ἐν", "ADP"), ("ἀρχῇ", "ἀρχή", "NOUN")])

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
