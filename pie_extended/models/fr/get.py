from .processor import FrRulesProcessor, FrGlueProcessor
from pie_extended.pipeline.postprocessor.proto import RenamedTaskProcessor
from .tokenizer import FrMemorizingTokenizer
from pie_extended.pipeline.iterators.proto import DataIterator, GenericExcludePatterns
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor


def get_iterator_and_processor():
    tokenizer = FrMemorizingTokenizer()
    processor = FrRulesProcessor(
        apply_on_reinsert=True,
        head_processor=MemoryzingProcessor(
            tokenizer_memory=tokenizer,
            head_processor=FrGlueProcessor(
                head_processor=RenamedTaskProcessor({"pos": "POS", "NOMB": "NOMB.", "PERS": "PERS."})
            )
        )
    )
    iterator = DataIterator(
        tokenizer=tokenizer,
        exclude_patterns=[GenericExcludePatterns.Punctuation_and_Underscore]
    )
    return iterator, processor

