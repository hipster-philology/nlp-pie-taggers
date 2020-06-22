from ...utils import Metadata, File, get_path

DESC = Metadata(
        "Ancient Greek",
        "grc",
        ["Thibault Clérice", "Enrique Manjavacas"],
        "Ancient Greek Model",
        "https://github.com/hipster-philology/greek-lemmatization-data"
)

DOWNLOADS = [
    File("https://github.com/hipster-philology/greek-lemmatization-data/raw/10eea6a2bf4aa1690844a28a8f1e40bc6a898b02/"
         "greek.lemma.tar", "lemma.tar"),
    File("https://github.com/hipster-philology/greek-lemmatization-data/raw/10eea6a2bf4aa1690844a28a8f1e40bc6a898b02/"
         "greek.pos.tar", "pos.tar"),
]


Models = "<{},lemma><{},pos>".format(
        get_path("grc", "lemma.tar"),
        get_path("grc", "pos.tar")
)
