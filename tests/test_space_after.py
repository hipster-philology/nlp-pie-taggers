import os
import tempfile
import warnings
from unittest import TestCase

from click.testing import CliRunner

from pie_extended.cli.main import pie_ext
from pie_extended.cli.utils import get_model, get_imports, get_pipeline
from pie_extended.models import modules
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.tokenizers.simple_tokenizer import SimpleTokenizer
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
from pie_extended.pipeline.postprocessor.spacing import SpaceAfterProcessor
from pie_extended.pipeline.postprocessor.splitter import SplitterPostProcessor
from pie_extended.testing_utils import FakeAutoTag

# Glued punctuation, apostrophes, brackets, quotes, double spaces, new lines, excluded tokens and a glued new sentence
TEXT = (
    "Arma virumque: cano, Troiae qui primus ab oris (Italiam) fato profugus;  l'ostal d'aquel \"quid est?\" ... fin.\n"
    "Nova linea [IGN:x] sine spatio.Altera"
)
NO = "No"


def build(lang: str, text_processor=SpaceAfterProcessor):
    module = get_model(lang)
    tagger = FakeAutoTag.from_model_string(module.Models, batch_size=16)
    iterator, processor = get_imports(module).get_iterator_and_processor()
    return tagger, iterator, text_processor(processor)


def rebuild(annotations) -> str:
    """ Writes the text back from the forms and their SpaceAfter column """
    return "".join(a["form"] + ("" if a["SpaceAfter"] == NO else " ") for a in annotations).strip()


class TestSpaceAfterEveryModel(TestCase):
    def tag(self, lang, text=TEXT):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tagger, iterator, processor = build(lang)
            return tagger.tag_str(text, iterator=iterator, processor=processor), iterator

    def test_all_tokens_are_aligned_and_text_can_be_rebuilt(self):
        for lang in modules:
            with self.subTest(lang=lang):
                annotations, iterator = self.tag(lang)
                _, missed = iterator.spacing()
                self.assertEqual(missed, 0, "Every token should be found in the original text")
                self.assertEqual(rebuild(annotations), " ".join(TEXT.split()))

    def test_column_is_last_and_has_only_two_values(self):
        for lang in modules:
            with self.subTest(lang=lang):
                annotations, _ = self.tag(lang)
                self.assertTrue(all(a["SpaceAfter"] in {NO, "_"} for a in annotations))
                self.assertIn("_", {a["SpaceAfter"] for a in annotations})
                if lang != "dum":  # dum only splits on spaces: nothing can be glued
                    self.assertIn(NO, {a["SpaceAfter"] for a in annotations})

    def test_glued_punctuation(self):
        """ virumque is glued to `:`, `:` is followed by a space """
        for lang in modules:
            if lang == "dum":  # Only splits on spaces: virumque: is one token
                continue
            with self.subTest(lang=lang):
                annotations, _ = self.tag(lang)
                forms = [a["form"] for a in annotations]
                at = forms.index("virumque")
                self.assertEqual(forms[at + 1], ":")
                self.assertEqual(annotations[at]["SpaceAfter"], NO)
                self.assertEqual(annotations[at + 1]["SpaceAfter"], "_")

    def test_dum_keeps_punctuation_inside_the_token(self):
        annotations, _ = self.tag("dum")
        forms = [a["form"] for a in annotations]
        self.assertIn("virumque:", forms)
        self.assertEqual(annotations[forms.index("virumque:")]["SpaceAfter"], "_")

    def test_excluded_tokens_are_given_a_value_too(self):
        """ Punctuation is not tagged by the model but reinserted: it still needs its spacing """
        for lang in ("fro", "lasla", "osp"):
            with self.subTest(lang=lang):
                annotations, _ = self.tag(lang)
                by_form = [(a["form"], a["SpaceAfter"]) for a in annotations]
                at = by_form.index((":", "_"))
                self.assertEqual(by_form[at - 1], ("virumque", NO))
                # `spatio.Altera`: the dot is glued to the next sentence, not to the previous word
                dot = [i for i, (form, _) in enumerate(by_form) if form == "." and by_form[i + 1][0] == "Altera"][0]
                self.assertEqual(by_form[dot - 1], ("spatio", NO))
                self.assertEqual(by_form[dot], (".", NO))

    def test_end_of_text_and_end_of_line(self):
        annotations, _ = self.tag("fro", "Arma cano.\nVirumque")
        self.assertEqual([(a["form"], a["SpaceAfter"]) for a in annotations],
                         [("Arma", "_"), ("cano", NO), (".", "_"), ("Virumque", "_")])

    def test_reuse_over_several_documents(self):
        """ Spacing of a document should never leak in the next one """
        texts = [TEXT, "Un autre document,sans rapport. Fin", "a:b"]
        for lang in ("fro", "lasla", "osp", "dum"):
            with self.subTest(lang=lang):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    tagger, iterator, processor = build(lang)
                    reused = []
                    for text in texts:
                        tagger.tokens, tagger.lengths = [], []
                        reused.append(tagger.tag_str(text, iterator=iterator, processor=processor))
                    fresh = []
                    for text in texts:
                        tagger, iterator, processor = build(lang)
                        fresh.append(tagger.tag_str(text, iterator=iterator, processor=processor))
                self.assertEqual(reused, fresh)

    def test_lowered_input(self):
        """ If a tokenizer lowers the tokens (no model does today), they are still found in the original text """
        iterator = DataIterator(tokenizer=SimpleTokenizer())
        sentences = list(iterator("Arma  Virumque: Cano", lower=True))
        self.assertEqual(sentences[0][0], ["arma", "virumque", ":", "cano"])
        self.assertEqual(iterator.spacing(), ([True, False, True, True], 0))


class TestSpaceAfterProcessing(TestCase):
    def test_tokens_split_by_a_processor_are_glued_together(self):
        """ The first parts of an enclitic split are glued to the next one, the last one gets the real value """
        processor = SpaceAfterProcessor(SplitterPostProcessor())
        processor.set_tasks(["lemma"])
        processor.set_spacing([False, True])
        self.assertEqual(
            processor.get_dict("praedicatione", ["praedicatio界-ne"]),
            [{"form": "praedicatione", "lemma": "praedicatio", "SpaceAfter": NO},
             {"form": "praedicatione", "lemma": "-ne", "SpaceAfter": NO}]
        )
        self.assertEqual(
            processor.get_dict("est", ["sum"]),
            [{"form": "est", "lemma": "sum", "SpaceAfter": "_"}]
        )

    def test_missing_values_default_to_a_space(self):
        processor = SpaceAfterProcessor(ProcessorPrototype())
        processor.set_tasks(["lemma"])
        self.assertEqual(processor.get_dict("a", ["b"])[0]["SpaceAfter"], "_")

    def test_header_and_lines(self):
        tagger, iterator, processor = build("fro")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lines = list(tagger.iter_tag("Arma virumque: cano", iterator, processor=processor))
        header = lines[0].rstrip("\r\n").split("\t")
        self.assertEqual(header[0], "token")
        self.assertEqual(header[-1], "SpaceAfter")
        values = [line.rstrip("\r\n").split("\t") for line in lines[1:] if line.strip()]
        self.assertEqual([(v[0], v[-1]) for v in values],
                         [("Arma", "_"), ("virumque", NO), (":", "_"), ("cano", "_")])

    def test_not_present_without_the_processor(self):
        """ Library users calling the model processors directly keep their previous output """
        tagger, iterator, processor = build("fro", text_processor=lambda x: x)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            annotations = tagger.tag_str("Arma virumque: cano", iterator=iterator, processor=processor)
        self.assertTrue(all("SpaceAfter" not in a for a in annotations))

    def test_pretokenized_input_is_refused(self):
        tagger, iterator, processor = build("fro")
        with self.assertRaises(ValueError):
            tagger.tag_str("Arma\nvirumque", iterator=iterator, processor=processor, no_tokenizer=True)


class TestSpaceAfterPipeline(TestCase):
    def tagger(self, lang="fro", selected=None):
        tagger = FakeAutoTag.from_model_string(get_model(lang).Models, batch_size=16)
        tagger.selected_outputs = selected
        return tagger

    def test_default_pipeline_has_the_column(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tagger = self.tagger()
            iterator, processor = get_pipeline("fro", tagger)
            annotations = tagger.tag_str("Arma virumque: cano", iterator=iterator, processor=processor)
        self.assertIn("SpaceAfter", annotations[0])

    def test_can_be_disabled(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tagger = self.tagger()
            iterator, processor = get_pipeline("fro", tagger, space_after=False)
            annotations = tagger.tag_str("Arma virumque: cano", iterator=iterator, processor=processor)
        self.assertNotIn("SpaceAfter", annotations[0])

    def test_kept_when_a_subset_of_tasks_is_requested(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tagger = self.tagger(selected=["lemma"])
            iterator, processor = get_pipeline("fro", tagger)
            lines = list(tagger.iter_tag("Arma virumque: cano", iterator, processor=processor))
        rows = [line.rstrip("\r\n").split("\t") for line in lines if line.strip()]
        self.assertEqual(rows[0], ["token", "lemma", "SpaceAfter"])
        self.assertEqual([(row[0], row[-1]) for row in rows[1:]],
                         [("Arma", "_"), ("virumque", NO), (":", "_"), ("cano", "_")])


class TestSpaceAfterCli(TestCase):
    def test_no_tokenizer_requires_to_disable_space_after(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "text.txt")
            with open(path, "w") as f:
                f.write("Arma\nvirumque\n")
            result = CliRunner().invoke(pie_ext, ["tag", "fro", path, "--no-tokenizer"])
        self.assertEqual(result.exit_code, 2)
        self.assertIn("--no-space-after", result.output)

    def test_options_are_documented(self):
        result = CliRunner().invoke(pie_ext, ["tag", "--help"])
        self.assertIn("--space-after / --no-space-after", result.output)
