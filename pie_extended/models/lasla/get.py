import regex as re

from pie_extended.models.lasla.processor import LatinRulesProcessor, LatinGlueProcessor
from pie_extended.models.lasla.tokenizer import LatMemorizingTokenizer
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor

# Uppercase regexp
uppercase = re.compile(r"^[A-Z]$")


def get_iterator_and_processor():
    tokenizer = LatMemorizingTokenizer()
    processor = LatinRulesProcessor(
        MemoryzingProcessor(
            tokenizer_memory=tokenizer,
            head_processor=LatinGlueProcessor()
        )
    )
    iterator = DataIterator(
        tokenizer=tokenizer,
        remove_from_input=DataIterator.remove_punctuation
    )
    return iterator, processor
