from ...utils import Metadata, File, get_path


DESC = Metadata(
    "LASLA-ENC",
    "lat",
    ["Thibault Clérice"],
    "Model trained on LASLA data without disambiguation",
    "https://github.com/chartes/deucalion-model-lasla"
)

DOWNLOADS = [
    File("https://raw.githubusercontent.com/PonteIneptique/latin-lasla-models/0.0.1/latin-straight.json",
         "latin-straight.json"),
    File("https://raw.githubusercontent.com/PonteIneptique/latin-lasla-models/0.0.1/latin-pos.json",
         "latin-pos.json"),
    File("https://raw.githubusercontent.com/PonteIneptique/latin-lasla-models/0.0.1/latin-needs.json",
         "latin-needs.json"),
    File("https://raw.githubusercontent.com/PonteIneptique/latin-lasla-models/0.0.1/model.tar",
         "model.tar")
]

Models = "<{},lemma,Voice,Mood,Deg,Numb,Person,Tense,Case,Gend,pos>".format(get_path("lasla", "model.tar"))
