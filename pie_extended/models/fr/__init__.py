from ...utils import Metadata, File, get_path
from .get import get_iterator_and_processor
from ...pipeline.iterators.proto import DataIterator

DESC = Metadata(
        "Français classique et moderne",
        "fr",
        ["Jean-Baptiste Camps", "Simon Gabay", "Thibault Clérice", "Florian Cafiero"],
        "Corpus and Models for Lemmatisation and POS-tagging of Classical French Theatre",
        "TODO: add arXiv link"
)

DOWNLOADS = [
        File("TODO: Zenodo DL link", "pos-morph.tar"),
        File("TODO: Zenodo DL link", "lemma.tar")
]


Models = "<{},pos,MODE,TEMPS,PERS,NOMB,GENRE,CAS><{},lemma>".format(
        get_path("fr", "pos-morph.tar"),
        get_path("fr", "lemma.tar")
)
