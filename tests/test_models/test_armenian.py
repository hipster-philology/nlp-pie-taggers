import json
import os
import re
import warnings
from unittest import TestCase

from pie.utils import model_spec

from pie_extended.cli.utils import get_imports, get_model, resolve_tasks
from pie_extended.models import modules
from pie_extended.models.hy_hye.tokenizer import ArmenianTokenizer, MARKS
from pie_extended.pipeline.postprocessor.spacing import SpaceAfterProcessor
from pie_extended.testing_utils import FakeAutoTag

MODELS = {"hy_hye": "hye", "hy_hyw": "hyw", "hy_xcl": "xcl"}
NO = "No"


def tokenize(text: str):
    tokenizer = ArmenianTokenizer()
    return tokenizer.word_tokenizer(text), tokenizer.surface_tokens()


def tag(lang: str, text: str):
    """ Fake tagging through the whole pipeline: tokenization, SpaceAfter, formatting-ready dictionaries """
    module = get_model(lang)
    tagger = FakeAutoTag.from_model_string(module.Models, batch_size=8)
    iterator, processor = get_imports(module).get_iterator_and_processor()
    annotations = tagger.tag_str(text, iterator=iterator, processor=SpaceAfterProcessor(processor))
    return annotations, iterator


class TestArmenianModelsDefinition(TestCase):
    def test_registered_with_iso_codes(self):
        for name, code in MODELS.items():
            with self.subTest(model=name):
                self.assertIn(name, modules)
                self.assertEqual(get_model(name).DESC.lang, code)

    def test_downloads_and_models_are_consistent(self):
        """ Every file that is downloaded is a model, once, and all of a language come from the same record """
        for name in MODELS:
            with self.subTest(model=name):
                module = get_model(name)
                spec = list(model_spec(module.Models))
                in_models = [os.path.basename(path) for path, _ in spec]
                in_downloads = [file.name for file in module.DOWNLOADS]
                self.assertEqual(sorted(in_models), sorted(in_downloads))
                self.assertEqual(len(set(in_downloads)), len(in_downloads))
                self.assertEqual(len({re.search(r"records/(\d+)/", f.url).group(1) for f in module.DOWNLOADS}), 1)
                tasks = [task for _, model_tasks in spec for task in model_tasks]
                self.assertIn("lemma", tasks)
                self.assertIn("pos", tasks)

    def test_the_three_models_share_one_pipeline(self):
        iterators = {name: get_imports(get_model(name)).get_iterator_and_processor()[0] for name in MODELS}
        for name, iterator in iterators.items():
            self.assertIsInstance(iterator.tokenizer, ArmenianTokenizer, name)

    def test_asking_for_lemma_and_pos_only_loads_two_models(self):
        """ One Pie model per task: 25 for Eastern Armenian, only the two needed are loaded """
        for name in MODELS:
            with self.subTest(model=name):
                module = get_model(name)
                selected, reduced = resolve_tasks(name, ["lemma", "pos"], list(model_spec(module.Models)))
                self.assertEqual(selected, ["lemma", "pos"])
                self.assertEqual(len(reduced), 2)


class TestArmenianTokenizer(TestCase):
    def test_mark_on_a_vowel_is_moved_after_its_word(self):
        """ As in the UD treebanks: multiword token `Մի՞թե` -> words `Միթե`, `՞` """
        words, written = tokenize("Մի՞թե այդ")
        self.assertEqual(words, ["Միթե", "՞", "այդ"])
        self.assertEqual(written, ["Մի՞թե", "", "այդ"], "The moved mark is not written anywhere in the text")

    def test_all_three_marks_and_their_position(self):
        self.assertEqual(tokenize("թե՛ ես")[0], ["թե", "՛", "ես"])
        self.assertEqual(tokenize("Ինչպե՞ս")[0], ["Ինչպես", "՞"])
        self.assertEqual(tokenize("Վա՜յ")[0], ["Վայ", "՜"])
        self.assertEqual(tokenize("Իրա՞ւ։")[0], ["Իրաւ", "՞", "։"])
        self.assertEqual(set(MARKS), {"՛", "՜", "՞"})

    def test_a_mark_alone_stays_a_token(self):
        self.assertEqual(tokenize("՞")[0], ["՞"])
        self.assertEqual(tokenize("՞")[1], ["՞"])

    def test_armenian_punctuation(self):
        self.assertEqual(tokenize("ես՝ լավ։")[0], ["ես", "՝", "լավ", "։"])
        self.assertEqual(tokenize("«Բարև» (ես)")[0], ["«", "Բարև", "»", "(", "ես", ")"])

    def test_hyphen_splits_words(self):
        self.assertEqual(tokenize("ուսանող-ուսանողուհիները")[0], ["ուսանող", "-", "ուսանողուհիները"])

    def test_numbers_and_ellipsis_stay_in_one_piece(self):
        self.assertEqual(tokenize("1.000 դրամ, 2.37,8")[0], ["1.000", "դրամ", ",", "2.37,8"])
        self.assertEqual(tokenize("լավ... ես…")[0], ["լավ", "...", "ես", "…"])

    def test_western_clitic_apostrophe_stays_on_the_clitic(self):
        self.assertEqual(tokenize("կ՚ուզեմ")[0], ["կ՚", "ուզեմ"])

    def test_scripts_are_not_mixed(self):
        self.assertEqual(tokenize("pensionnaireները")[0], ["pensionnaire", "ները"])

    def test_sentences(self):
        sentences = list(ArmenianTokenizer().sentence_tokenizer("Բարև աշխարհ։ Ինչպե՞ս ես։ Լավ։"))
        self.assertEqual(sentences, [["Բարև", "աշխարհ", "։"], ["Ինչպես", "՞", "ես", "։"], ["Լավ", "։"]])
        # ASCII colon is a full stop too, and quotes close their sentence
        self.assertEqual(len(list(ArmenianTokenizer().sentence_tokenizer("Ո՞րն էր ելքը: Չգիտեմ։"))), 2)
        self.assertEqual(len(list(ArmenianTokenizer().sentence_tokenizer("Ասաց «ոչ։» Գնաց։"))), 2)

    def test_dot_is_not_the_end_of_a_sentence(self):
        """ Initials, abbreviations, numbers: counting the dot made 10 to 47% of the boundaries wrong on the treebanks """
        sentences = list(ArmenianTokenizer().sentence_tokenizer("Խ. Աբովյանը եկավ. Նա գնաց։"))
        self.assertEqual(len(sentences), 1)
        self.assertEqual(sentences[0][:3], ["Խ", ".", "Աբովյանը"])

    def test_empty_and_reset(self):
        tokenizer = ArmenianTokenizer()
        self.assertEqual(list(tokenizer.sentence_tokenizer("")), [])
        list(tokenizer.sentence_tokenizer("Մի՞թե այդ"))
        self.assertEqual(len(tokenizer.surface_tokens()), 3)
        list(tokenizer.sentence_tokenizer("Բարև"))
        self.assertEqual(tokenizer.surface_tokens(), ["Բարև"], "The surfaces are the ones of the last text")
        tokenizer.reset()
        self.assertEqual(tokenizer.surface_tokens(), [])


class TestArmenianSpaceAfter(TestCase):
    def values(self, lang, text):
        annotations, iterator = tag(lang, text)
        self.assertEqual(iterator.spacing()[1], 0, "Every token has to be found in the text")
        return [(a["form"], a["SpaceAfter"]) for a in annotations]

    def test_question_word(self):
        """ The mark is glued to its word, whatever its place in the written word """
        self.assertEqual(
            self.values("hy_hye", "Ո՞րն էր ելքը:"),
            [("Որն", NO), ("՞", "_"), ("էր", "_"), ("ելքը", NO), (":", "_")]
        )

    def test_punctuation_and_clitic(self):
        self.assertEqual(
            self.values("hy_hyw", "Եթէ կ՚ուզես՝ եկուր։"),
            [("Եթէ", "_"), ("կ՚", NO), ("ուզես", NO), ("՝", "_"), ("եկուր", NO), ("։", "_")]
        )

    def test_classical(self):
        """ Handwritten: the Classical Armenian treebank is not free enough to be copied """
        self.assertEqual(
            self.values("hy_xcl", "Ո՞ւր է եղբայրդ քո։"),
            [("Ուր", NO), ("՞", "_"), ("է", "_"), ("եղբայրդ", "_"), ("քո", NO), ("։", "_")]
        )


def _load_sample():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "armenian_ud_sample.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _normalize(text: str) -> str:
    """ Without the marks (they move) and without the differences of whitespace """
    return " ".join(re.sub("[{}]".format(MARKS), "", text).split())


class TestArmenianOnUniversalDependenciesSentences(TestCase):
    """ Real sentences of the Eastern and Western Armenian UD treebanks (ArmTDP, CC BY-SA 4.0): the models were trained
    on their words, so our tokens have to be theirs.

    On the whole dev sets (575 and 693 sentences) the exact same words are found for 99.5% and 99.4% of the
    sentences, and the punctuation matches for 99.8% and 99.9%. The Classical Armenian treebank also matches
    for the punctuation (100%) but it segments clitics (`զնա` -> `զ`, `նա`) which cannot be done without a lexicon.
    """
    sample = _load_sample()

    def sentences(self):
        for code, treebank in self.sample["treebanks"].items():
            for sentence in treebank["sentences"]:
                yield code, sentence

    def test_same_words_as_the_treebank(self):
        for code, sentence in self.sentences():
            with self.subTest(treebank=code, sent_id=sentence["sent_id"], feature=sentence["feature"]):
                self.assertEqual(tokenize(sentence["text"])[0], sentence["words"])

    def test_text_can_be_rebuilt_from_forms_and_spacing(self):
        for code, sentence in self.sentences():
            lang = "hy_hye" if code == "hye" else "hy_hyw"
            with self.subTest(treebank=code, sent_id=sentence["sent_id"], feature=sentence["feature"]):
                annotations, iterator = tag(lang, sentence["text"])
                self.assertEqual(iterator.spacing()[1], 0)
                rebuilt = "".join(a["form"] + ("" if a["SpaceAfter"] == NO else " ") for a in annotations)
                self.assertEqual(_normalize(rebuilt), _normalize(sentence["text"]))

    def test_one_document(self):
        """ All sentences as one text: tokens are found back in order, none is lost """
        for code, treebank in self.sample["treebanks"].items():
            with self.subTest(treebank=code):
                text = "\n".join(sentence["text"] for sentence in treebank["sentences"])
                words = [word for sentence in treebank["sentences"] for word in sentence["words"]]
                iterator = get_imports(get_model("hy_hye")).get_iterator_and_processor()[0]
                sentences = [tokens for tokens, _, _ in iterator(text)]
                self.assertEqual([token for sentence in sentences for token in sentence], words)
                self.assertEqual(iterator.spacing()[1], 0)

    def test_sample_covers_the_difficult_cases(self):
        features = {s["feature"] for _, s in self.sentences()}
        for expected in ("mark moved after its word", "hyphen", "number with separators", "clitic apostrophe",
                         "latin word glued to armenian suffix", "ellipsis", "guillemets"):
            self.assertIn(expected, features)
        self.assertTrue(self.sample["_license"].startswith("CC BY-SA"))

    def test_pipeline_runs_without_warnings_on_the_sample(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # "tokens could not be aligned" is a warning
            for code, sentence in self.sentences():
                tag("hy_hye" if code == "hye" else "hy_hyw", sentence["text"])
