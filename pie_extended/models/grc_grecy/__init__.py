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

# GreCy pipeline to use. Same format as the Pie models (`<model,task,task...>`): the "path" is the name of the
# spaCy pipeline. grc_perseus_{sm,lg,trf} and grc_proiel_{sm,lg,trf} are available (trf needs spacy-transformers).
SpacyModel = "grc_proiel_sm"
Models = "<{},lemma,morph,pos,tag>".format(SpacyModel)
