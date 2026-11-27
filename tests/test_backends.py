import os
import subprocess
import sys
import threading
import time
from unittest import TestCase
from unittest.mock import patch

from pie_extended.backends import (
    BACKENDS, CompositeTagger, ExtensibleTagger, PipelineNotFound, SoterLemmatizer, SpacyTagger
)
from pie_extended.cli.utils import get_model, get_pipeline, get_tagger

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestImportingTheBackends(TestCase):
    def test_one_place_for_all_of_them(self):
        self.assertEqual(BACKENDS, {"pie": ExtensibleTagger, "spacy": SpacyTagger, "composite": CompositeTagger})
        self.assertTrue(issubclass(PipelineNotFound, FileNotFoundError))
        self.assertEqual(SoterLemmatizer.TASKS, ("lemma",))

    def test_the_older_paths_give_the_same_classes(self):
        """ They were public (1.0.0, 1.0.1): they still are """
        import pie_extended.composite_tagger
        import pie_extended.soter
        import pie_extended.spacy_tagger
        import pie_extended.tagger
        self.assertIs(pie_extended.tagger.ExtensibleTagger, ExtensibleTagger)
        self.assertIs(pie_extended.spacy_tagger.SpacyTagger, SpacyTagger)
        self.assertIs(pie_extended.composite_tagger.CompositeTagger, CompositeTagger)
        self.assertIs(pie_extended.soter.SoterLemmatizer, SoterLemmatizer)

    def test_importing_them_needs_neither_spacy_nor_transformers(self):
        """ They are imported when a model is loaded: forbid them, and import everything """
        code = (
            "import sys; sys.modules['spacy'] = None; sys.modules['transformers'] = None\n"
            "from pie_extended.backends import ExtensibleTagger, SpacyTagger, CompositeTagger, SoterLemmatizer, BACKENDS\n"
            "print('ok')\n"
        )
        result = subprocess.run([sys.executable, "-W", "ignore", "-c", code], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.stdout.strip(), "ok", result.stderr[-1500:])


class TestTheBackendOfAModel(TestCase):
    def tagger_of(self, model, backend=None):
        """ The class that get_tagger makes for a model, without loading anything """
        module = get_model(model)
        with patch.object(ExtensibleTagger, "add_model"), patch.object(SpacyTagger, "add_model"), \
                patch.object(CompositeTagger, "add_model"):
            if backend is None:
                return type(get_tagger(model)).__name__
            with patch.object(module, "Backend", backend, create=True):
                return type(get_tagger(model)).__name__

    def test_the_tagger_follows_the_backend(self):
        self.assertEqual(self.tagger_of("fro"), "ExtensibleTagger")
        self.assertEqual(self.tagger_of("grc_grecy"), "SpacyTagger")
        self.assertEqual(self.tagger_of("grc_soter"), "CompositeTagger")

    def test_unknown_backend_is_an_error_and_not_the_pie_tagger(self):
        """ A typo (`"spaCy"`) used to make a Pie tagger, that then failed in a confusing way """
        with self.assertRaises(ValueError) as raised:
            self.tagger_of("grc_grecy", backend="spaCy")
        message = str(raised.exception)
        self.assertIn("'spaCy'", message)
        self.assertIn("composite, pie, spacy", message)


class Stateless:
    """ A tagger without a state (the weights of a model are only read), a little slow: threads overlap """
    lower = False
    batch_size = 8
    disambiguation = None
    selected_outputs = None
    iter_tag_token = ExtensibleTagger.iter_tag_token
    tag_str = ExtensibleTagger.tag_str

    def tag(self, sents, lengths=None, **kwargs):
        time.sleep(0.002)
        return [[(token, ("L-" + token,)) for token in sentence] for sentence in sents], ["lemma"]


class TestSeveralRequestsAtOnce(TestCase):
    """ What a service has to do: the pipeline keeps the state of the text it reads, one for each request """
    def test_one_pipeline_for_each_request(self):
        tagger = Stateless()
        texts = [" ".join("w{}x{}".format(t, i) for i in range(30)) + "." for t in range(8)]
        results, errors = {}, []

        def request(number):
            iterator, processor = get_pipeline("grc_grecy", tagger, space_after=False)   # cheap: made for each request
            try:
                results[number] = [a["form"] for a in tagger.tag_str(texts[number], iterator=iterator, processor=processor)]
            except Exception as error:  # pragma: no cover
                errors.append(error)

        threads = [threading.Thread(target=request, args=(number,)) for number in range(len(texts))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        for number, text in enumerate(texts):
            self.assertEqual(results[number], text.replace(".", " .").split())
