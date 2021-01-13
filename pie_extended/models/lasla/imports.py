import regex as re
from ...utils import get_path, ObjectCreator

from autocat import NeedsDisambiguation, StraightAutodisambiguation, CategoryAutodisambiguation, GroupAutodisambiguation
from ...pipeline.disambiguators.autocat import Autocat, DisambiguationAsTask
from pie_extended.models.lasla.processor import LatinRulesProcessor, LatinGlueProcessor, MoodTenseVoice
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
from pie_extended.models.lasla.tokenizer import LatMemorizingTokenizer
from pie_extended.pipeline.iterators.proto import DataIterator, GenericExcludePatterns
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor
from pie_extended.pipeline.postprocessor.splitter import SplitterPostProcessor

# Uppercase regexp
uppercase = re.compile(r"^[A-Z]$")


def get_iterator_and_processor(max_tokens=256):
    tokenizer = LatMemorizingTokenizer()
    processor = LatinRulesProcessor(
        apply_on_reinsert=True,
        head_processor=SplitterPostProcessor(
            prefix="界",
            split_char="界",
            head_processor=MemoryzingProcessor(
                tokenizer_memory=tokenizer,
                head_processor=LatinGlueProcessor(
                    head_processor=MoodTenseVoice(
                        head_processor=ProcessorPrototype()
                    )
                )
            )
        )
    )
    iterator = DataIterator(
        tokenizer=tokenizer,
        exclude_patterns=[
                             excl.exclude_regexp
                             for excl in tokenizer.normalizers
                             if excl.exclude_regexp
                         ] + [
                            GenericExcludePatterns.Punctuation_and_Underscore
                         ],
        max_tokens=max_tokens
    )
    return iterator, processor


def _get_disambiguator():
    pos = CategoryAutodisambiguation.from_file(
        get_path("lasla", "latin-pos.json"), category_key="pos", lemma_key="lemma")
    straight = StraightAutodisambiguation.from_file(
        get_path("lasla", "latin-straight.json"), lemma_key="lemma")
    impossible = NeedsDisambiguation.from_file(
        get_path("lasla", "latin-needs.json"), lemma_key="lemma")
    tasks = DisambiguationAsTask(task_name="Dis", separator="", undisambiguated_marker="?",
                                 lemma_key="lemma", empty_value="_", impossible_disambiguator=impossible)
    return Autocat(GroupAutodisambiguation(lemma_key="lemma", categorizers=(straight, pos, tasks)))


Disambiguator: ObjectCreator = ObjectCreator(_get_disambiguator)


def addons():
    return True
