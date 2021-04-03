from ...utils import Metadata, File, get_path


DESC = Metadata(
    "LASLA-ENC",
    "lat",
    ["Thibault Clérice"],
    "Model trained on LASLA data without disambiguation",
    "https://github.com/chartes/deucalion-model-lasla"
)

VERSION = "0.0.6"
DOWNLOADS = [
    File("https://raw.githubusercontent.com/PonteIneptique/latin-lasla-models/"+VERSION+"/latin-straight.json",
         "latin-straight.json"),
    File("https://raw.githubusercontent.com/PonteIneptique/latin-lasla-models/"+VERSION+"/latin-pos.json",
         "latin-pos.json"),
    File("https://raw.githubusercontent.com/PonteIneptique/latin-lasla-models/"+VERSION+"/latin-needs.json",
         "latin-needs.json"),
    File("https://github.com/PonteIneptique/latin-lasla-models/releases/download/" + VERSION +
         "/lasla-plus-Mood_Tense_Voice.tar",
         "Mood_Tense_Voice.tar"),
    File("https://github.com/PonteIneptique/latin-lasla-models/releases/download/" + VERSION + "/lasla-plus-Gend.tar",
         "Gend.tar"),
    File("https://github.com/PonteIneptique/latin-lasla-models/releases/download/" + VERSION + "/lasla-plus-Person.tar",
         "Person.tar"),
    File("https://github.com/PonteIneptique/latin-lasla-models/releases/download/" + VERSION + "/lasla-plus-Deg.tar",
         "Deg.tar"),
    File("https://github.com/PonteIneptique/latin-lasla-models/releases/download/" + VERSION + "/lasla-plus-lemma.tar",
         "lemma.tar"),
    File("https://github.com/PonteIneptique/latin-lasla-models/releases/download/" + VERSION + "/lasla-plus-pos.tar",
         "pos.tar"),
    File("https://github.com/PonteIneptique/latin-lasla-models/releases/download/" + VERSION + "/lasla-plus-Numb.tar",
         "Numb.tar"),
    File("https://github.com/PonteIneptique/latin-lasla-models/releases/download/" + VERSION + "/lasla-plus-Dis.tar",
         "Dis.tar"),
    File("https://github.com/PonteIneptique/latin-lasla-models/releases/download/" + VERSION + "/lasla-plus-Case.tar",
         "Case.tar")
]

Models = "".join([
    "<{},Mood_Tense_Voice>".format(get_path("lasla", "Mood_Tense_Voice")),
    "<{},Gend>".format(get_path("lasla", "Gend")),
    "<{},Person>".format(get_path("lasla", "Person")),
    "<{},Deg>".format(get_path("lasla", "Deg")),
    "<{},lemma>".format(get_path("lasla", "lemma")),
    "<{},pos>".format(get_path("lasla", "pos")),
    "<{},Numb>".format(get_path("lasla", "Numb")),
    "<{},Dis>".format(get_path("lasla", "Dis")),
    "<{},Case>".format(get_path("lasla", "Case"))
])
