from .processor import FroRulesProcessor, FroGlueProcessor
from .tokenizer import FroMemorizingTokenizer
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor


def get_iterator_and_processor():
    tokenizer = FroMemorizingTokenizer()
    processor = FroRulesProcessor(
        MemoryzingProcessor(
            tokenizer_memory=tokenizer,
            head_processor=FroGlueProcessor()
        )
    )
    iterator = DataIterator(
        tokenizer=tokenizer,
        remove_from_input=DataIterator.remove_punctuation
    )
    return iterator, processor

