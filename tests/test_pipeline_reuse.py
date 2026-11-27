import warnings
from unittest import TestCase

from pie_extended.cli.utils import get_model, get_imports
from pie_extended.testing_utils import FakeAutoTag

TEXTS = [
    "Mio Cid [IGN:x] dixo, \"bien\" 12 e lo que fizo. Otra frase aqui, con 3 palabras.",
    "Segundo documento; con otra puntuacion... y mas texto aqui.",
    "Tercero.",
]

# Languages whose pipeline is exercised without needing downloaded data
LANGS = ["osp", "fro", "fr", "grc", "dum", "freem", "frm", "occ_cont"]


def _new(lang):
    module = get_model(lang)
    tagger = FakeAutoTag.from_model_string(module.Models, batch_size=4)
    return tagger, get_imports(module).get_iterator_and_processor()


class TestPipelineReuse(TestCase):
    def test_reused_pipeline_gives_same_output_as_fresh_ones(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for lang in LANGS:
                with self.subTest(lang=lang):
                    tagger, (iterator, processor) = _new(lang)
                    reused = []
                    for text in TEXTS:
                        tagger.tokens, tagger.lengths = [], []
                        reused.append(tagger.tag_str(text, iterator=iterator, processor=processor))
                    fresh = []
                    for text in TEXTS:
                        tagger, (it, proc) = _new(lang)
                        fresh.append(tagger.tag_str(text, iterator=it, processor=proc))
                    self.assertEqual(reused, fresh)

    def test_reuse_after_interrupted_document(self):
        """ A document that stops halfway (failure) must not leak its memory in the next one """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for lang in LANGS:
                with self.subTest(lang=lang):
                    tagger, (iterator, processor) = _new(lang)
                    generator = tagger.iter_tag_token(TEXTS[0], iterator=iterator, processor=processor)
                    next(generator)  # consumed one token only
                    generator.close()
                    tagger.tokens, tagger.lengths = [], []
                    reused = tagger.tag_str(TEXTS[1], iterator=iterator, processor=processor)

                    tagger, (it, proc) = _new(lang)
                    self.assertEqual(reused, tagger.tag_str(TEXTS[1], iterator=it, processor=proc))
