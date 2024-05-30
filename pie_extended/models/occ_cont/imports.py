from pie_extended.pipeline.iterators.proto import DataIterator, GenericExcludePatterns
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor
from pie_extended.models.occ_cont.tokenizer import OccMemorizingTokenizer
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype


def get_iterator_and_processor(max_tokens=256):
    tokenizer = OccMemorizingTokenizer()
    processor = MemoryzingProcessor(
        tokenizer_memory=tokenizer,
        head_processor=ProcessorPrototype()
    )
    iterator = DataIterator(
        tokenizer=tokenizer,
        max_tokens=max_tokens,
        exclude_patterns=[
            excl.exclude_regexp
            for excl in tokenizer.normalizers
            if excl.exclude_regexp
        ]
    )
    return iterator, processor

