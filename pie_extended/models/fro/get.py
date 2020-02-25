from .processor import FroRulesProcessor, FroGlueProcessor, FroMapProcessor
from .tokenizer import FroMemorizingTokenizer
from pie_extended.pipeline.iterators.proto import DataIterator, GenericExcludePatterns
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor


def get_iterator_and_processor():
    tokenizer = FroMemorizingTokenizer()
    processor = FroRulesProcessor(
        apply_on_reinsert=True,
        head_processor=MemoryzingProcessor(
            tokenizer_memory=tokenizer,
            head_processor=FroGlueProcessor(
                head_processor=FroMapProcessor()
            )
        )
    )
    iterator = DataIterator(
        tokenizer=tokenizer,
        exclude_patterns=[GenericExcludePatterns.Punctuation_and_Underscore]
    )
    return iterator, processor

