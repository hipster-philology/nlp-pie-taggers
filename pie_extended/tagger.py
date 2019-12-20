import os
from typing import Optional

from pie.tagger import Tagger
from pie import utils

from .pipeline.formatters.proto import Formatter
from .pipeline.disambiguators.proto import Disambiguator
from .pipeline.iterators.proto import DataIterator


class ExtensibleTagger(Tagger):
    def __init__(self, device='cpu', batch_size=100, lower=False, disambiguation=None):
        super(ExtensibleTagger, self).__init__(
            device=device,
            batch_size=batch_size,
            lower=lower
        )
        self.disambiguation: Optional[Disambiguator] = disambiguation

    def reinsert_full(self, formatter, sent_reinsertion, tasks):
        yield formatter.write_sentence_beginning()
        # If a sentence is empty, it's most likely because everything is in sent_reinsertions
        for reinsertion in sorted(list(sent_reinsertion.keys())):
            yield formatter.write_line(
                formatter.format_line(
                    token=sent_reinsertion[reinsertion],
                    tags=[""] * len(tasks)
                )
            )
        yield formatter.write_sentence_end()

    def tag_file(self, fpath: str, iterator: DataIterator, formatter_class: type):
        # Read content of the file
        with open(fpath) as f:
            data = f.read()

        _, ext = os.path.splitext(fpath)

        with open(utils.ensure_ext(fpath, ext, 'pie'), 'w+') as f:
            for line in self.iter_tag(data, iterator, formatter_class):
                f.write(line)

    def tag_str(self, data: str, iterator: DataIterator, formatter_class: type) -> str:
        return "".join(list(self.iter_tag(data, iterator, formatter_class)))

    def iter_tag(self, data: str, iterator: DataIterator, formatter_class: type):
        header = False
        formatter = None

        for chunk in utils.chunks(
                iterator(data, lower=self.lower),
                size=self.batch_size):
            # Unzip the batch into the sentences, their sizes and the dictionaries of things that needs
            #  to be reinserted
            sents, lengths, needs_reinsertion = zip(*chunk)
            # Removing punctuation might create empty sentences !
            #  Which would crash Torch
            empty_sents_indexes = {
                index: []
                for index, sent in enumerate(sents)
                if len(sent) == 0
            }
            tagged, tasks = self.tag(
                sents=[sent for sent in sents if len(sent)],
                lengths=lengths
            )
            formatter: Formatter = formatter_class(tasks)

            # We keep a real sentence index
            real_sentence_index = 0
            for sent in tagged:
                if not sent:
                    continue
                # Gets things that needs to be reinserted
                sent_reinsertion = needs_reinsertion[real_sentence_index]

                # If the header has not yet be written, write it
                if not header:
                    yield formatter.write_headers()
                    header = True

                # Some sentences can be empty and would have been removed from tagging
                #  we check and until we get to a non empty sentence
                #  we increment the real_sentence_index to keep in check with the reinsertion map
                while real_sentence_index in empty_sents_indexes:
                    yield from self.reinsert_full(
                            formatter,
                            needs_reinsertion[real_sentence_index],
                            tasks
                    )
                    real_sentence_index += 1

                yield formatter.write_sentence_beginning()

                # If we have a disambiguator, we run the results into it
                if self.disambiguation:
                    sent = self.disambiguation(sent, tasks)

                reinsertion_index = 0
                index = 0

                for index, (token, tags) in enumerate(sent):
                    while reinsertion_index + index in sent_reinsertion:
                        yield formatter.write_line(
                            formatter.format_line(
                                token=sent_reinsertion[reinsertion_index + index],
                                tags=[""] * len(tasks)
                            )
                        )
                        del sent_reinsertion[reinsertion_index + index]
                        reinsertion_index += 1

                    yield formatter.write_line(
                        formatter.format_line(token, tags)
                    )

                for reinsertion in sorted(list(sent_reinsertion.keys())):
                    yield formatter.write_line(
                        formatter.format_line(
                            token=sent_reinsertion[reinsertion],
                            tags=[""] * len(tasks)
                        )
                    )

                yield formatter.write_sentence_end()

                real_sentence_index += 1

            while real_sentence_index in empty_sents_indexes:
                yield from self.reinsert_full(
                    formatter,
                    needs_reinsertion[real_sentence_index],
                    tasks
                )
                real_sentence_index += 1

        if formatter:
            yield formatter.write_footer()
