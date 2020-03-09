from ...utils import Metadata, File, get_path

DESC = Metadata(
        "Français classique et moderne",
        "fr",
        ["Jean-Baptiste Camps", "Simon Gabay", "Thibault Clérice", "Florian Cafiero"],
        "Corpus and Models for Lemmatisation and POS-tagging of Classical French Theatre",
        "TODO: add arXiv link"
)

DOWNLOADS = [
        File("https://zenodo.org/record/3701294/files/fr-class-wembs-lemma-2020_03_06-01_52_24.tar?download=1", "lemma.tar"),
        File("https://zenodo.org/record/3701320/files/fr-class-pos-wembs_aux-pos-2020_03_03-18_52_52.tar?download=1", "pos.tar"),
        File("https://zenodo.org/record/3701320/files/fr-class-morph-wembs_aux-MODE-2020_03_08-17_46_05.tar?download=1", "mode.tar"),
        File("https://zenodo.org/record/3701320/files/fr-class-morph-wembs_aux-TEMPS-2020_03_08-19_03_26.tar?download=1", "temps.tar"),
        File("https://zenodo.org/record/3701320/files/fr-class-morph-wembs_aux-PERS-2020_03_08-18_24_29.tar?download=1", "pers.tar"),
        File("https://zenodo.org/record/3701320/files/fr-class-morph-wembs_aux-NOMB-2020_03_08-17_55_50.tar?download=1", "nomb.tar"),
        File("https://zenodo.org/record/3701320/files/fr-class-morph-wembs_aux-GENRE-2020_03_08-16_54_44.tar?download=1", "genre.tar"),
        File("https://zenodo.org/record/3701320/files/fr-class-morph-wembs_aux-CAS-2020_03_08-16_23_57.tar?download=1", "cas.tar")
]


Models = "<{},lemma><{},pos><{},MODE><{},TEMPS><{},PERS><{},NOMB><{},GENRE><{},CAS>".format(
        get_path("fr", "lemma.tar"),
        get_path("fr", "pos.tar"),
        get_path("fr", "mode.tar"),
        get_path("fr", "temps.tar"),
        get_path("fr", "pers.tar"),
        get_path("fr", "nomb.tar"),
        get_path("fr", "genre.tar"),
        get_path("fr", "cas.tar")
)
