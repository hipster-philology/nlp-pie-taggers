from typing import Dict, List, Optional, Sequence, Tuple

from .soter import DEFAULT_REPO, CONVENTIONS, SoterLemmatizer
from .tagger import ExtensibleTagger

SOTER = "soter:"


class CompositeTagger(ExtensibleTagger):
    """ Tagger whose tasks come from different engines: each task is given by one of them.

    An engine is added like a model, with `add_model(name, *tasks)`, and in the same syntax as the other models
    (`<name,task,task>`), which is how it is chosen from the command (`--model_path`) or in a package of a model:

    - `soter:Zual/soter-mini` is the lemmatizer Sôtêr (it only gives `lemma`). `soter:Zual/soter-mini#proiel` gives the
      lemmas of the convention of PROIEL, `#ptnk` of PTNK (Perseus is the default);
    - any other name is a spaCy pipeline (`grc_perseus_sm`), see `SpacyTagger`.

    >>> CompositeTagger.engine_of("soter:Zual/soter-mini#proiel")
    ('soter', 'Zual/soter-mini', 'proiel')
    >>> CompositeTagger.engine_of("grc_perseus_sm")
    ('spacy', 'grc_perseus_sm', None)
    """
    def __init__(self, device: str = "cpu", batch_size: int = 100, lower: bool = False, disambiguation=None,
                 **ignored):
        # quantize/cache/cache_size/num_threads are PaPie options: they have no meaning here
        super(CompositeTagger, self).__init__(device=device, batch_size=batch_size, lower=lower,
                                              disambiguation=disambiguation, quantize=False, cache=False)
        self.engines: List[Tuple[object, List[str]]] = []
        self._owner: Dict[str, str] = {}

    @staticmethod
    def engine_of(model_path: str) -> Tuple[str, str, Optional[str]]:
        """ The kind of engine that a name designates, the name of the model, and its option """
        if model_path.startswith(SOTER):
            repo, _, convention = model_path[len(SOTER):].partition("#")
            return "soter", repo or DEFAULT_REPO, convention or None
        return "spacy", model_path, None

    def add_model(self, model_path: str, *tasks: str) -> None:
        """ Adds an engine, that gives `tasks`

        :raises ValueError: If a task is already given by another engine, or if the engine does not give it
        """
        taken = [task for task in tasks if task in self._owner]
        if taken:
            raise ValueError("{} already given by {}".format(", ".join(taken), ", ".join(sorted({self._owner[t] for t in taken}))))

        kind, name, option = self.engine_of(model_path)
        if kind == "soter":
            unknown = [task for task in tasks if task not in SoterLemmatizer.TASKS]
            if unknown:
                raise ValueError("Sôtêr only gives {}, not {}".format(", ".join(SoterLemmatizer.TASKS), ", ".join(unknown)))
            if option is not None and option not in CONVENTIONS:
                raise ValueError("Unknown convention {!r} for Sôtêr. Available: {}".format(option, ", ".join(CONVENTIONS)))
            engine = SoterLemmatizer(repo=name, convention=option or "perseus", device=self.device,
                                     batch_size=self.batch_size).load()
        else:
            from .spacy_tagger import SpacyTagger  # spaCy is an optional dependency
            engine = SpacyTagger(device=self.device, batch_size=self.batch_size, pipeline=name, tasks=tasks)

        self._owner.update({task: model_path for task in tasks})
        self.engines.append((engine, list(tasks)))

    def tag(self, sents: Sequence[Sequence[str]], lengths: Optional[Sequence[int]] = None, **kwargs
            ) -> Tuple[List[List[Tuple[str, Tuple[str, ...]]]], List[str]]:
        """ Same contract as PaPie's `Tagger.tag`: each engine tags the sentences, and the tasks are put together """
        answers = [engine.tag(sents, lengths=lengths) for engine, _ in self.engines]
        tasks = sorted(task for _, engine_tasks in answers for task in engine_tasks)
        tagged = []
        for index, sentence in enumerate(sents):
            tokens = []
            for position, token in enumerate(sentence):
                values: Dict[str, str] = {}
                for answer, engine_tasks in answers:
                    values.update(zip(engine_tasks, answer[index][position][1]))
                tokens.append((token, tuple(values[task] for task in tasks)))
            tagged.append(tokens)
        return tagged, tasks
