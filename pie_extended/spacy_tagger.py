from typing import Callable, Dict, List, Optional, Set, Tuple

from .tagger import ExtensibleTagger

EMPTY = "_"


class SpacyTagger(ExtensibleTagger):
    """ Tagger that runs a spaCy pipeline (GreCy, for example) instead of PaPie models.

    Everything that is not the prediction itself is inherited from `ExtensibleTagger`: tokenization and exclusion
    (iterator), post-processing, `SpaceAfter`, disambiguation, formatting. Only `add_model` and `tag` change:
    the data iterator already gives pre-tokenized sentences, they are given to spaCy as `Doc` objects so spaCy's
    own tokenizer is never used.

    spaCy is an optional dependency (`pip install pie-extended[grecy]`), it is only imported when a model is loaded.

    The tasks are the spaCy token attributes: `lemma`, `pos` (universal POS), `tag` (language specific POS) and
    `morph` (UD features, `_` if empty).
    """
    # How to read each task from a spaCy token
    EXTRACTORS: Dict[str, Callable] = {
        "lemma": lambda token: token.lemma_,
        "pos": lambda token: token.pos_,
        "tag": lambda token: token.tag_,
        "morph": lambda token: str(token.morph),
    }
    # spaCy components that never produce one of the tasks: they are not run. This is a deliberate blacklist: pipelines
    # differ a lot (the transformer models have a `morpheus_lemmatizer` that the small ones lack, and dropping it changes
    # lemmas), so a component that is not known to be useless is kept.
    # The gain is small: the shared encoder (tok2vec/transformer) costs much more than the parser.
    UNUSED_COMPONENTS: Set[str] = {
        "parser", "ner", "entity_ruler", "entity_linker", "span_ruler", "spancat", "textcat", "textcat_multilabel",
        "coref", "span_resolver",
    }

    def __init__(self, device: str = "cpu", batch_size: int = 100, lower: bool = False, disambiguation=None,
                 **ignored):
        # quantize/cache/cache_size/num_threads are PaPie options: they have no meaning here
        super(SpacyTagger, self).__init__(device=device, batch_size=batch_size, lower=lower,
                                          disambiguation=disambiguation, quantize=False, cache=False)
        self.nlp = None
        self._tasks: List[str] = []

    def add_model(self, model_path: str, *tasks: str) -> None:
        """ Loads a spaCy pipeline (without the components that do not produce a task, see UNUSED_COMPONENTS)

        :param model_path: Name of an installed spaCy pipeline (grc_proiel_sm) or path to one
        :param tasks: Tasks to output (see EXTRACTORS)
        """
        if self.nlp is not None:
            raise ValueError("A SpacyTagger runs a single spaCy pipeline")
        unknown = [task for task in tasks if task not in self.EXTRACTORS]
        if unknown:
            raise ValueError("Unknown spaCy task(s): {}. Available: {}".format(
                ", ".join(unknown), ", ".join(sorted(self.EXTRACTORS))))
        try:
            import spacy
        except ImportError as error:
            raise ImportError("spaCy is needed for this model: pip install pie-extended[grecy]") from error

        if self.device != "cpu":
            spacy.prefer_gpu()
        try:
            self.nlp = spacy.load(model_path)
        except OSError as error:  # spaCy's way to say the pipeline is not installed
            raise FileNotFoundError(
                "spaCy pipeline {!r} not found: install it with `pie-extended install-addons`".format(model_path)
            ) from error

        self.nlp.select_pipes(disable=[name for name in self.nlp.pipe_names if name in self.UNUSED_COMPONENTS])
        self._tasks = sorted(tasks)  # PaPie also sorts its tasks

    def tag(self, sents: List[List[str]], lengths: Optional[List[int]] = None, **kwargs
            ) -> Tuple[List[List[Tuple[str, Tuple[str, ...]]]], List[str]]:
        """ Same contract as PaPie's `Tagger.tag`: tagged sentences ([(token, (tag for each task))]) and the tasks """
        from spacy.tokens import Doc

        docs = [Doc(self.nlp.vocab, words=list(sentence)) for sentence in sents]
        extractors = [self.EXTRACTORS[task] for task in self._tasks]
        tagged = []
        for sentence, doc in zip(sents, self.nlp.pipe(docs, batch_size=self.batch_size)):
            tagged.append([
                (word, tuple(extract(token) or EMPTY for extract in extractors))
                for word, token in zip(sentence, doc)
            ])
        return tagged, list(self._tasks)
