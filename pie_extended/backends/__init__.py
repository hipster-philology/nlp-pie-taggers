""" The backends: what turns tokens into predictions. One place to import them from.

>>> from pie_extended.backends import ExtensibleTagger, SpacyTagger, CompositeTagger, SoterLemmatizer

| `Backend` of a model | Tagger | Is given | Needs |
|---|---|---|---|
| `"pie"` (the default) | `ExtensibleTagger` | files of Pie models | nothing more than the package |
| `"spacy"` | `SpacyTagger` | the name of a spaCy pipeline | spaCy (`pie-extended[grecy]`) |
| `"composite"` | `CompositeTagger` | engines: spaCy pipelines, `soter:...` | what each engine needs |

`SoterLemmatizer` is an engine (it gives the lemma, with a model of Hugging Face): it needs `transformers`
(`pie-extended[soter]`). Importing these classes needs none of spaCy and `transformers`: they are imported when a model
is loaded.

`BACKENDS` maps the value of `Backend` to its tagger, and `get_tagger` (in `pie_extended.cli.utils`) is what builds a tagger
for a model.

>>> sorted(BACKENDS)
['composite', 'pie', 'spacy']
>>> BACKENDS["pie"] is ExtensibleTagger
True
"""
from typing import Dict, Type

from ..composite_tagger import CompositeTagger
from ..soter import SoterLemmatizer
from ..spacy_tagger import PipelineNotFound, SpacyTagger
from ..tagger import ExtensibleTagger

BACKENDS: Dict[str, Type[ExtensibleTagger]] = {
    "pie": ExtensibleTagger,
    "spacy": SpacyTagger,
    "composite": CompositeTagger,
}

__all__ = ["BACKENDS", "CompositeTagger", "ExtensibleTagger", "PipelineNotFound", "SoterLemmatizer", "SpacyTagger"]
