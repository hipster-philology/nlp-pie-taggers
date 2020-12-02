from ...utils import Metadata, File, get_path


DESC = Metadata(
    "LASLA-ENC",
    "lat",
    ["Thibault Clérice"],
    "Model trained on LASLA data without disambiguation",
    "https://github.com/chartes/deucalion-model-lasla"
)

VERSION = "0.0.5alpha"
DOWNLOADS = [
    File("https://raw.githubusercontent.com/PonteIneptique/latin-lasla-models/"+VERSION+"/latin-straight.json",
         "latin-straight.json"),
    File("https://raw.githubusercontent.com/PonteIneptique/latin-lasla-models/"+VERSION+"/latin-pos.json",
         "latin-pos.json"),
    File("https://raw.githubusercontent.com/PonteIneptique/latin-lasla-models/"+VERSION+"/latin-needs.json",
         "latin-needs.json"),
    File("https://github.com/PonteIneptique/latin-lasla-models/releases/download/"+VERSION+"/model-lasla-plus.tar",
         "model.tar")
]

Models = "<{},lemma,Deg,Numb,Person,Mood_Tense_Voice,Case,Gend,Dis,pos>".format(get_path("lasla", "model.tar"))
