import regex as re

from pie_extended.models.lasla.processor import LatinRulesProcessor, LatinGlueProcessor
from pie_extended.pipeline.postprocessor.proto import RenamedTaskProcessor, ProcessorPrototype
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
