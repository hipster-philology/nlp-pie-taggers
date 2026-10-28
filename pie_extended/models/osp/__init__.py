from ...utils import Metadata, File, get_path

DESC = Metadata(
        "Old Castilian (dummy models)",
        "osp",
        ["Thibault Clérice"],
        "Placeholder lemmatisation and POS-tagging models for Old Castilian",
        "https://github.com/Biblissima-Textes-Global-Corpora/dummy-models/releases/tag/castillan"
)

_RELEASE = "https://github.com/Biblissima-Textes-Global-Corpora/dummy-models/releases/download/castillan/"

DOWNLOADS = [
        File(_RELEASE + "lemma-pos.best.tar", "lemma-pos.tar"),
        File(_RELEASE + "pos-lemma.best.tar", "pos-lemma.tar")
]


Models = "<{},lemma><{},POS>".format(
        get_path("osp", "lemma-pos.tar"),
        get_path("osp", "pos-lemma.tar")
)
