from ..fr.tokenizer import FrMemorizingTokenizer
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype, RenamedTaskProcessor
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor
from ..fr.processor import FrGlueProcessor


def get_iterator_and_processor(max_tokens=256):
    tokenizer = FrMemorizingTokenizer()

    processor = MemoryzingProcessor(
            tokenizer_memory=tokenizer,
            head_processor=FrGlueProcessor(
                head_processor=RenamedTaskProcessor({"pos": "POS", "NOMB": "NOMB.", "PERS": "PERS."})
            )
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

