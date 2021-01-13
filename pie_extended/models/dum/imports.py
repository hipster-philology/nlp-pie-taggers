from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.tokenizers.simple_tokenizer import LengthTokenizer


def get_iterator_and_processor(max_tokens=256):
    tokenizer = LengthTokenizer(35)
    processor = ProcessorPrototype()
    iterator = DataIterator(
        tokenizer=tokenizer,
        max_tokens=max_tokens
    )
    return iterator, processor

