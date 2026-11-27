import warnings
from unittest import TestCase

from pie.utils import model_spec

from pie_extended.cli.utils import get_model, get_imports, resolve_tasks
from pie_extended.models import modules
from pie_extended.pipeline.postprocessor.proto import SelectTasksProcessor


def _spec(lang):
    return list(model_spec(get_model(lang).Models))


def _outputs(lang):
    processor = get_imports(get_model(lang)).get_iterator_and_processor()[1]
    available = sorted({t for _, tasks in _spec(lang) for t in tasks})
    return list(processor.set_tasks(available))


class TestTaskSubset(TestCase):
    def run_subset(self, lang, requested):
        spec = _spec(lang)
        selected, reduced = resolve_tasks(lang, requested, spec)
        produced = sorted({t for _, tasks in reduced for t in tasks})
        iterator, processor = get_imports(get_model(lang)).get_iterator_and_processor()
        processor = SelectTasksProcessor(processor, selected)
        processor.set_tasks(produced)
        # Fake tagging of one token and one reinserted token must not raise
        tags = ["x"] * len(produced)
        # Memory-based processors consume tokenizer memory
        iterator.tokenizer.tokens = [(0, "tok", "tok"), (1, "$", "$")] if hasattr(iterator.tokenizer, "tokens") else []
        annotations = processor.get_dict("tok", tags)
        self.assertTrue(annotations)
        reinserted = processor.reinsert("$")
        for task in processor.tasks:
            self.assertIn(task, annotations[0])
            self.assertIn(task, reinserted)
        return selected, reduced, processor

    def test_every_language_every_single_output(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for lang in modules:
                for output in _outputs(lang):
                    if output == "treated":
                        continue
                    with self.subTest(lang=lang, output=output):
                        selected, reduced, processor = self.run_subset(lang, [output])
                        self.assertEqual(selected, [output])
                        self.assertIn(output, processor.tasks)

    def test_lemma_pos_skips_other_models(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for lang in modules:
                outputs = {o.lower(): o for o in _outputs(lang)}
                if "lemma" not in outputs or "pos" not in outputs:
                    continue
                with self.subTest(lang=lang):
                    _, reduced, _ = self.run_subset(lang, ["lemma", "pos"])
                    kept = {t for _, tasks in reduced for t in tasks}
                    full = {t for _, tasks in _spec(lang) for t in tasks}
                    self.assertTrue({"lemma"} <= {t.lower() for t in kept})
                    if len(full) > 2 and lang != "lasla":
                        # Morphology models are neither loaded nor run
                        self.assertLess(len(kept), len(full))

    def test_unknown_task(self):
        with self.assertRaises(ValueError):
            resolve_tasks("fro", ["nope"], _spec("fro"))

    def test_case_insensitive(self):
        selected, _ = resolve_tasks("fro", ["LEMMA", "pos"], _spec("fro"))
        self.assertEqual(selected, ["lemma", "POS"])
