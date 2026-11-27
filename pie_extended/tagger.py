import os
import warnings
from typing import Optional, Dict, Generator, Type, List

from pie.utils import shutup

with shutup():
    from pie.tagger import Tagger
    from pie import utils

from .pipeline.formatters.proto import Formatter
from .pipeline.disambiguators.proto import Disambiguator
from .pipeline.iterators.proto import DataIterator
from .pipeline.postprocessor.proto import ProcessorPrototype


class ExtensibleTagger(Tagger):
    """

    :param quantize: Use Int8 quantization
    :param cache: Use cache
    """
    def __init__(self, device='cpu', batch_size=100, lower=False, disambiguation=None,
                 quantize=True, cache=True, cache_size=None, num_threads=None):
        if quantize and device != "cpu":
            warnings.warn("Dynamic int8 quantization only works on CPU: disabling it for device " + str(device),
                          stacklevel=2)
            quantize = False
        extra = {}
        if cache_size is not None:
            extra["cache_size"] = cache_size
        if num_threads is not None:
            extra["num_threads"] = num_threads
        super(ExtensibleTagger, self).__init__(
            device=device,
            batch_size=batch_size,
            lower=lower,
            quantize=quantize,
            cache=cache,
            **extra
        )
        self.disambiguation: Optional[Disambiguator] = disambiguation

    def tag_file(self, fpath: str, iterator: DataIterator, processor: ProcessorPrototype, no_tokenizer: bool = False):
        # Read content of the file
        with open(fpath, encoding="utf-8") as f:
            data = f.read()

        _, ext = os.path.splitext(fpath)

        out_file = utils.ensure_ext(fpath, ext, 'pie')
        # newline="": the formatter writes its own line endings, they must not be translated by the platform
        with open(out_file, 'w', encoding="utf-8", newline="") as f:
            for line in self.iter_tag(data, iterator, processor=processor, no_tokenizer=no_tokenizer):
                f.write(line)

        return out_file

    def tag_str(self, data: str, iterator: DataIterator, processor: ProcessorPrototype,
                no_tokenizer: bool = False) -> List[Dict[str, str]]:
        return list(self.iter_tag_token(data, iterator, processor=processor, no_tokenizer=no_tokenizer))

    def iter_tag_token(self,
                       data: str,
                       iterator: DataIterator,
                       processor: ProcessorPrototype,
                       no_tokenizer: bool = False,
                       empty_token_on_sent_break: bool = False) -> Generator[Optional[Dict[str, str]], None, None]:
        """ Reads the string in [DATA] with [ITERATOR] and [PROCESSOR], then returns each token as a dict

        :param data: Textual
        :param iterator: Iterator used to read data
        :param processor: Processor used to post-process data
        :param no_tokenizer: Disable the tokenizer inside the iterator
        :param empty_token_on_sent_break: Returns a None token when going into a new sequence.
        :yield: Token in the form of a dict or, if [empty_token...] is True, a None value when changing "sentences"
        """
        # Reset at each document
        needs_spacing = getattr(processor, "needs_spacing", False)
        if needs_spacing and no_tokenizer:
            raise ValueError(
                "The space after each token cannot be known with `no_tokenizer`: the original spacing is "
                "lost in pre-tokenized input. Disable the SpaceAfter column (--no-space-after)."
            )
        processor.reset()
        iterator.tokenizer.reset()
        spacing_set = False
        # Iterate !
        for chunk in utils.chunks(
                iterator(data, lower=self.lower, no_tokenizer=no_tokenizer),
                size=self.batch_size):

            # Unzip the batch into the sentences, their sizes and the dictionaries of things that needs
            #  to be reinserted
            if needs_spacing and not spacing_set:
                # The iterator read the whole text before giving its first chunk
                spacing, missed = iterator.spacing()
                if missed:
                    warnings.warn("{} token(s) could not be aligned to the original text: "
                                  "SpaceAfter is not reliable for them".format(missed), stacklevel=2)
                processor.set_spacing(spacing)
                spacing_set = True

            sents, lengths, needs_reinsertion = zip(*chunk)
            is_empty = [not bool(sent) for sent in sents]

            tagged, tasks = self.tag(
                sents=[sent for sent in sents if sent],
                lengths=[l for l in lengths if l != 0]
            )

            if not processor.task_init:
                processor.set_tasks(tasks)

            tagged_iter = iter(tagged)

            # We keep a real sentence index
            for sents_index, sent_is_empty in enumerate(is_empty):
                if sent_is_empty:
                    sent = []
                else:
                    sent = next(tagged_iter)

                # Gets things that needs to be reinserted
                sent_reinsertion = needs_reinsertion[sents_index]

                # If we have a disambiguator, we run the results into it
                if self.disambiguation and sent and getattr(self.disambiguation, "can_run", lambda _: True)(tasks):
                    sent = self.disambiguation(sent, tasks)

                reinsertion_index = 0

                for index, (token, tags) in enumerate(sent):
                    # Before current index
                    while reinsertion_index + index in sent_reinsertion:
                        yield processor.reinsert(sent_reinsertion[reinsertion_index+index])
                        del sent_reinsertion[reinsertion_index + index]
                        reinsertion_index += 1

                    yield from processor.get_dict(token, tags)

                for reinsertion in sorted(list(sent_reinsertion.keys())):
                    yield processor.reinsert(sent_reinsertion[reinsertion])
                if empty_token_on_sent_break:
                    yield None

    def iter_tag(self, data: str, iterator: DataIterator, processor: ProcessorPrototype,
                 formatter_class: Type[Formatter] = Formatter, no_tokenizer: bool = False):
        formatter = None

        for annotation in self.iter_tag_token(data, iterator, processor, no_tokenizer = no_tokenizer):
            if not formatter:
                formatter = formatter_class(processor.tasks)
                yield formatter.write_headers()
            yield formatter.write_line(formatter.format_line(annotation))

        if formatter:
            yield formatter.write_footer()
