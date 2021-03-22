import os
from typing import Optional, Dict, Generator, Type

from pie.utils import shutup

with shutup():
    from pie.tagger import Tagger
    from pie import utils

from .pipeline.formatters.proto import Formatter
from .pipeline.disambiguators.proto import Disambiguator
from .pipeline.iterators.proto import DataIterator
from .pipeline.postprocessor.proto import ProcessorPrototype


class ExtensibleTagger(Tagger):
    def __init__(self, device='cpu', batch_size=100, lower=False, disambiguation=None):
        super(ExtensibleTagger, self).__init__(
            device=device,
            batch_size=batch_size,
            lower=lower
        )
        self.disambiguation: Optional[Disambiguator] = disambiguation

    def tag_file(self, fpath: str, iterator: DataIterator, processor: ProcessorPrototype, no_tokenizer: bool = False):
        # Read content of the file
        with open(fpath) as f:
            data = f.read()

        _, ext = os.path.splitext(fpath)

        out_file = utils.ensure_ext(fpath, ext, 'pie')
        with open(out_file, 'w+') as f:
            for line in self.iter_tag(data, iterator, processor=processor, no_tokenizer=no_tokenizer):
                f.write(line)

        return out_file

    def tag_str(self, data: str, iterator: DataIterator, processor: ProcessorPrototype,
                no_tokenizer: bool = False) -> str:
        return list(self.iter_tag_token(data, iterator, processor=processor, no_tokenizer=no_tokenizer))

    def iter_tag_token(self, data: str, iterator: DataIterator, processor: ProcessorPrototype,
                       no_tokenizer: bool = False) -> Generator[Dict[str, str], None, None]:
        # Reset at each document
        processor.reset()
        iterator.tokenizer.reset()
        # Iterate !
        for chunk in utils.chunks(
                iterator(data, lower=self.lower, no_tokenizer=no_tokenizer),
                size=self.batch_size):

            # Unzip the batch into the sentences, their sizes and the dictionaries of things that needs
            #  to be reinserted
            sents, lengths, needs_reinsertion = zip(*chunk)
            is_empty = [not bool(sent) for sent in sents]

            tagged, tasks = self.tag(
                sents=[sent for sent in sents if sent],
                lengths=[l for l in lengths if l != 0]
            )

            if not processor.task_init:
                processor.set_tasks(tasks)

            # We keep a real sentence index
            for sents_index, sent_is_empty in enumerate(is_empty):
                if sent_is_empty:
                    sent = []
                else:
                    sent = tagged.pop(0)

                # Gets things that needs to be reinserted
                sent_reinsertion = needs_reinsertion[sents_index]

                # If we have a disambiguator, we run the results into it
                if self.disambiguation and sent:
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
