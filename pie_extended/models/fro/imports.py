from .processor import FroRulesProcessor, FroGlueProcessor
from pie_extended.pipeline.postprocessor.proto import RenamedTaskProcessor
from .tokenizer import FroMemorizingTokenizer
from pie_extended.pipeline.iterators.proto import DataIterator, GenericExcludePatterns
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor


def get_iterator_and_processor(max_tokens=256):
    tokenizer = FroMemorizingTokenizer()
    processor = FroRulesProcessor(
        apply_on_reinsert=True,
        head_processor=MemoryzingProcessor(
            tokenizer_memory=tokenizer,
            head_processor=FroGlueProcessor(
                head_processor=RenamedTaskProcessor({"pos": "POS", "NOMB": "NOMB.", "PERS": "PERS."})
            )
        )
    )
    iterator = DataIterator(
        tokenizer=tokenizer,
        exclude_patterns=[GenericExcludePatterns.Punctuation_and_Underscore],
        max_tokens=max_tokens
    )
    return iterator, processor

