from ...utils import Metadata

DESC = Metadata(
        "Ancient Greek (GreCy)",
        "grc",
        ["Jacobo Myerston"],
        "Ancient Greek spaCy pipelines (GreCy), run through spaCy instead of Pie. Needs `pip install pie-extended[grecy]`",
        "https://github.com/jmyerston/greCy"
)

# Nothing to download: spaCy pipelines are Python packages, see `addons()` in imports.py
DOWNLOADS = []

# Tells `get_tagger` to use `pie_extended.spacy_tagger.SpacyTagger` instead of the Pie tagger
Backend = "spacy"

# GreCy pipeline to use: the one of the Perseus treebank, with a transformer (needs spacy-transformers, see the
# extra `grecy`). Same format as the Pie models (`<model,task,task...>`): the "path" is the name of the spaCy pipeline.
# grc_perseus_{sm,lg,trf} and grc_proiel_{sm,lg,trf} are available. This name is the only place to change: it is the
# pipeline that `pie-extended tag` runs, and the one that `pie-extended install-addons grc_grecy` installs.
SpacyModel = "grc_perseus_trf"
Models = "<{},lemma,morph,pos,tag>".format(SpacyModel)
