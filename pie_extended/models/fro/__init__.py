from ...utils import Metadata, File, get_path
from .get import get_iterator_and_processor
from ...pipeline.iterators.proto import DataIterator

DESC = Metadata(
    "Ancien Francais (ENC)",
    "fro",
    ["Jean-Baptiste Camps", "Ariane Pinche", "Thibault Clérice", "Frédéric Duval", "Lucence Ing"],
    "Model trained on diverse corpora (hagiography, geste, etc.)",
    "https://github.com/chartes/deucalion-model-af"
)

DOWNLOADS = [
    File("https://github.com/chartes/deucalion-model-af/raw/master/morph.tar", "morph.tar"),
    File("https://github.com/chartes/deucalion-model-af/raw/master/lemma-pos.tar", "lemma-pos.tar")
]


Models = "<{},MODE,TEMPS,PERS,NOMB,GENRE,CAS,DEGRE><{},lemma,pos>".format(
    get_path("fro", "morph.tar"),
    get_path("fro", "lemma-pos.tar")
)
