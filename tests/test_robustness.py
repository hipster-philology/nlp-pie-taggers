import os
import tempfile
import threading
import warnings
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from unittest import TestCase

import requests

from pie_extended.cli import utils
from pie_extended.models.lasla.processor import LatinGlueProcessor
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
from pie_extended.pipeline.tokenizers.memorizing import MemorizingTokenizer
from pie_extended.pipeline.tokenizers.utils.excluder import ExcluderPrototype
from pie_extended.testing_utils import FakeAutoTag
from pie_extended.cli.utils import get_model, get_imports


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):  # Do not pollute the tests output
        pass


class TestDownload(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        with open(os.path.join(self.directory.name, "model.tar"), "wb") as f:
            f.write(b"model-content")
        server = HTTPServer(("127.0.0.1", 0), partial(_QuietHandler, directory=self.directory.name))
        self.url = "http://127.0.0.1:{}".format(server.server_port)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.target = os.path.join(self.directory.name, "target", "out.tar")
        os.makedirs(os.path.dirname(self.target))

    def download(self, name):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            utils._download(self.url + "/" + name, self.target)

    def test_success(self):
        self.download("model.tar")
        with open(self.target, "rb") as f:
            self.assertEqual(f.read(), b"model-content")
        self.assertEqual(os.listdir(os.path.dirname(self.target)), ["out.tar"], "No temporary file is left")

    def test_http_error_does_not_leave_a_fake_model(self):
        with self.assertRaises(requests.HTTPError):
            self.download("does-not-exist.tar")
        self.assertEqual(os.listdir(os.path.dirname(self.target)), [], "The error page must not be kept as a model")

    def test_http_error_does_not_replace_a_good_model(self):
        self.download("model.tar")
        with self.assertRaises(requests.HTTPError):
            self.download("does-not-exist.tar")
        with open(self.target, "rb") as f:
            self.assertEqual(f.read(), b"model-content")


class TestTokenizerMemory(TestCase):
    def test_reset_and_refill_does_not_need_the_processor_to_be_reset(self):
        tokenizer = MemorizingTokenizer()
        processor = MemoryzingProcessor(tokenizer, ProcessorPrototype())
        processor.set_tasks(["t"])
        tokenizer.tokens = [(0, "a", "a"), (1, "b", "b"), (2, "c", "c")]
        for word in "abc":
            processor.get_dict(word, ["x"])

        tokenizer.reset()  # New document: only the tokenizer is reset
        tokenizer.tokens = [(0, "x", "x"), (1, "y", "y"), (2, "z", "z"), (3, "w", "w")]
        self.assertEqual(processor.get_dict("x", ["t"])[0]["form"], "x")
        self.assertEqual(processor.get_dict("y", ["t"])[0]["form"], "y")

    def test_running_out_of_memory_is_an_error(self):
        tokenizer = MemorizingTokenizer()
        processor = MemoryzingProcessor(tokenizer, ProcessorPrototype())
        processor.set_tasks(["t"])
        with self.assertRaises(IndexError):
            processor.get_dict("x", ["t"])


class TestTagFile(TestCase):
    def test_utf8_and_line_endings_are_independent_of_the_platform(self):
        module = get_model("fro")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tagger = FakeAutoTag.from_model_string(module.Models, batch_size=4)
            iterator, processor = get_imports(module).get_iterator_and_processor()
            with tempfile.TemporaryDirectory() as directory:
                path = os.path.join(directory, "text.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write("Qui fut dévôt, Θεός ἐστιν.")
                out = tagger.tag_file(path, iterator=iterator, processor=processor)
                with open(out, "rb") as f:
                    content = f.read()
        text = content.decode("utf-8")
        self.assertIn("dévôt", text)
        self.assertIn("Θεός", text)
        self.assertIn(b"\r\n", content)
        self.assertNotIn(b"\r\r\n", content)


class TestMisc(TestCase):
    def test_excluder_prototype_is_abstract(self):
        with self.assertRaises(TypeError):
            ExcluderPrototype()

    def test_lasla_empty_morph_default(self):
        processor = LatinGlueProcessor(head_processor=ProcessorPrototype())
        processor.set_tasks(["lemma", "pos", "Case", "Dis"])
        annotation = processor.get_dict("a", ["_", "a", "_", "x"])[0]
        self.assertEqual(annotation["morph"], "MORPH=empty")
