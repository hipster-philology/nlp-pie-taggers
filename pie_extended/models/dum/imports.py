from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.tokenizers.simple_tokenizer import LengthTokenizer


def get_iterator_and_processor():
    tokenizer = LengthTokenizer(35)
    processor = ProcessorPrototype()
    iterator = DataIterator(
        tokenizer=tokenizer
    )
    return iterator, processor

