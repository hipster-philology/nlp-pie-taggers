from ...utils import Metadata, File, get_path

DESC = Metadata(
        "Français classique et moderne",
        "fr",
        ["Jean-Baptiste Camps", "Simon Gabay", "Thibault Clérice", "Florian Cafiero"],
        "Corpus and Models for Lemmatisation and POS-tagging of Classical French Theatre",
        "TODO: add arXiv link"
)

DOWNLOADS = [
        File("https://zenodo.org/record/3696676/files/fr-class-pos-wembs_aux-pos-2020_03_03-18_52_52.tar?download=1", "pos-morph.tar"),
        File("https://zenodo.org/record/3696684/files/fr-class-lemma-2020_01_20-15_39_25.tar?download=1", "lemma.tar")
]


Models = "<{},pos,MODE,TEMPS,PERS,NOMB,GENRE,CAS><{},lemma>".format(
        get_path("fr", "pos-morph.tar"),
        get_path("fr", "lemma.tar")
)
