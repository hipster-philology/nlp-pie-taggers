import warnings

import regex as re

from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.postprocessor.memory import MemoryzingProcessor
from .processor import OspPunctProcessor
from ._params import KNOWN_PUNCTUATION
from .tokenizer import OspMemorizingTokenizer


# Punctuation and underscores, except what the model knows
UnknownPunctuation = re.compile(
    r"^(?!(?:" + "|".join(re.escape(p) for p in KNOWN_PUNCTUATION) + r")$)[_\W]+$"
)


def get_iterator_and_processor(max_tokens=256):
    warnings.warn(
        "The Old Castilian (osp) models are a proof of concept (dummy models): "
        "their output should not be relied upon.",
        UserWarning
    )
    tokenizer = OspMemorizingTokenizer()
    processor = MemoryzingProcessor(
        tokenizer_memory=tokenizer,
        head_processor=OspPunctProcessor()
    )

    iterator = DataIterator(
        tokenizer=tokenizer,
        exclude_patterns=[
            excluder.exclude_regexp
            for excluder in tokenizer.normalizers
            if excluder.exclude_regexp
        ] + [UnknownPunctuation],
        max_tokens=max_tokens
    )
    return iterator, processor
