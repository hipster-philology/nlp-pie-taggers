from ...utils import Metadata

DESC = Metadata(
        "Ancient Greek (Sôtêr + GreCy)",
        "grc",
        ["Zual (Sôtêr)", "Jacobo Myerston (GreCy)"],
        "Ancient Greek: the lemma by Sôtêr mini (a 1.9 M parameters lemmatizer), the part of speech by a light spaCy "
        "pipeline of GreCy. Needs `pip install pie-extended[soter]`",
        "https://huggingface.co/Zual/soter-mini"
)

# Nothing to download: the lemmatizer comes from Hugging Face, the pipeline is a Python package (see `addons()`)
DOWNLOADS = []

# The tasks come from different engines: `get_tagger` builds a CompositeTagger
Backend = "composite"

# Each entry gives an engine and the tasks it is asked for, as for the other models. The lemma is given by Sôtêr
# (`soter:` + its repository on Hugging Face; `#proiel` after it would give the lemmas of PROIEL), the part of speech by
# a small GreCy pipeline of the Perseus treebank (grc_{perseus,proiel}_sm are the light ones).
Soter = "soter:Zual/soter-mini"
SpacyModel = "grc_perseus_sm"
Models = "<{},lemma><{},pos>".format(Soter, SpacyModel)
