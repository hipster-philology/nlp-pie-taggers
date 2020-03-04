import regex as re
from ...utils import get_path, ObjectCreator

from autocat import NeedsDisambiguation, StraightAutodisambiguation, CategoryAutodisambiguation, GroupAutodisambiguation
from ...pipeline.disambiguators.autocat import Autocat
from pie_extended.models.lasla.processor import LatinRulesProcessor, LatinGlueProcessor
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
from pie_extended.models.lasla.tokenizer import LatMemorizingTokenizer
from pie_extended.pipeline.iterators.proto import DataIterator, GenericExcludePatterns
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor

# Uppercase regexp
uppercase = re.compile(r"^[A-Z]$")


def get_iterator_and_processor():
    tokenizer = LatMemorizingTokenizer()
    processor = LatinRulesProcessor(
        apply_on_reinsert=True,
        head_processor=MemoryzingProcessor(
            tokenizer_memory=tokenizer,
            head_processor=LatinGlueProcessor(
                ProcessorPrototype()
            )
        )
    )
    iterator = DataIterator(
        tokenizer=tokenizer,
        exclude_patterns=[GenericExcludePatterns.Punctuation_and_Underscore]
    )
    return iterator, processor


def _get_disambiguator():
    pos = CategoryAutodisambiguation.from_file(
        get_path("lasla", "latin-pos.json"), category_key="pos", lemma_key="lemma")
    straight = StraightAutodisambiguation.from_file(
        get_path("lasla", "latin-straight.json"), lemma_key="lemma")
    impossible = NeedsDisambiguation.from_file(
        get_path("lasla", "latin-needs.json"), lemma_key="lemma")
    return Autocat(GroupAutodisambiguation(lemma_key="lemma", categorizers=(straight, pos, impossible)))


Disambiguator: ObjectCreator = ObjectCreator(_get_disambiguator)


def addons():
    from cltk.corpus.utils.importer import CorpusImporter

    corpus_importer = CorpusImporter('latin')
    corpus_importer.import_corpus('latin_models_cltk')