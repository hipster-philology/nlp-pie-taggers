""" Run in a subprocess by test_spacy_tagger: compares SpacyTagger with plain spaCy for ONE pipeline.

Two different GreCy pipelines cannot be loaded in the same process (each registers its own `grecy_*` component
factories: spaCy raises E004), hence the subprocess.

Usage: python tests/spacy_compare.py PIPELINE TASK [TASK...] -> prints a JSON {"plain": ..., "ours": ...}
"""
import json
import sys
import warnings

warnings.simplefilter("ignore")

import spacy  # noqa: E402
from spacy.tokens import Doc  # noqa: E402

from pie_extended.spacy_tagger import SpacyTagger  # noqa: E402

SENTENCES = json.loads(sys.argv[1])
name, tasks = sys.argv[2], sys.argv[3:]

# Ours first: it is the one that disables components
tagger = SpacyTagger(batch_size=2)
tagger.add_model(name, *tasks)
tagged, names = tagger.tag(SENTENCES)
ours = [[dict(zip(names, tags)) for _, tags in sentence] for sentence in tagged]

# Reference: the same pipeline with nothing disabled
nlp = spacy.load(name)
docs = nlp.pipe([Doc(nlp.vocab, words=words) for words in SENTENCES])
plain = [[{"lemma": t.lemma_, "pos": t.pos_, "tag": t.tag_, "morph": str(t.morph) or "_"} for t in doc]
         for doc in docs]

print(json.dumps({"plain": plain, "ours": ours}))
