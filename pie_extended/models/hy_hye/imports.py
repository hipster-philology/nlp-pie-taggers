from pie_extended.models.hy_hye.tokenizer import ArmenianTokenizer
from pie_extended.pipeline.iterators.proto import DataIterator
from pie_extended.pipeline.postprocessor.proto import ProcessorPrototype


def get_iterator_and_processor(max_tokens=256, segmenter=None):
    """ Shared by the three Armenian models (hy_hye, hy_hyw, hy_xcl): same tokenization, no pre/post-processing.

    Punctuation is tagged by the models (it is part of their training data) so nothing is excluded.

    :param segmenter: Cuts words in several words (the clitics of Classical Armenian), see hy_xcl
    """
    iterator = DataIterator(
        tokenizer=ArmenianTokenizer(segmenter=segmenter),
        max_tokens=max_tokens
    )
    return iterator, ProcessorPrototype()
