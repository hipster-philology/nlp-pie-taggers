from ...utils import Metadata, File, get_path

DESC = Metadata(
        "Ancient Greek",
        "grc",
        ["Thibault Clérice", "Enrique Manjavacas"],
        "Ancient Greek Model",
        "https://github.com/hipster-philology/greek-lemmatization-data"
)

DOWNLOADS = [
    File("https://github.com/hipster-philology/greek-lemmatization-data/releases/download/0.0.2/case.tar",
         "case.tar"),
    File("https://github.com/hipster-philology/greek-lemmatization-data/releases/download/0.0.2/degree.tar",
         "degree.tar"),
    File("https://github.com/hipster-philology/greek-lemmatization-data/releases/download/0.0.2/gend.tar",
         "gend.tar"),
    File("https://github.com/hipster-philology/greek-lemmatization-data/releases/download/0.0.2/lemma.tar",
         "lemma.tar"),
    File("https://github.com/hipster-philology/greek-lemmatization-data/releases/download/0.0.2/mood.tar",
         "mood.tar"),
    File("https://github.com/hipster-philology/greek-lemmatization-data/releases/download/0.0.2/num.tar",
         "num.tar"),
    File("https://github.com/hipster-philology/greek-lemmatization-data/releases/download/0.0.2/pers.tar",
         "pers.tar"),
    File("https://github.com/hipster-philology/greek-lemmatization-data/releases/download/0.0.2/pos.tar",
         "pos.tar"),
    File("https://github.com/hipster-philology/greek-lemmatization-data/releases/download/0.0.2/tense.tar",
         "tense.tar"),
    File("https://github.com/hipster-philology/greek-lemmatization-data/releases/download/0.0.2/voice.tar",
         "voice.tar")
]


Models = "<{},case><{},degree><{},gend><{},lemma><{},mood><{},num><{},pers><{},pos><{},tense><{},voice>".format(
    get_path("grc", "case.tar"),
    get_path("grc", "degree.tar"),
    get_path("grc", "gend.tar"),
    get_path("grc", "lemma.tar"),
    get_path("grc", "mood.tar"),
    get_path("grc", "num.tar"),
    get_path("grc", "pers.tar"),
    get_path("grc", "pos.tar"),
    get_path("grc", "tense.tar"),
    get_path("grc", "voice.tar")
)
