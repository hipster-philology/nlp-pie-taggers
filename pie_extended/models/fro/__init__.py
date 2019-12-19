from ...utils import Metadata, File


DESC = Metadata(
    "Ancien Francais (ENC)",
    "fro",
    ["Jean-Baptiste Camps", "Ariane Pinche", "Thibault Clérice", "Frédéric Duval", "Lucence Ing"],
    "Model trained on diverse corpora (hagiography, geste, etc.)",
    "https://github.com/chartes/deucalion-model-af"
)

DOWNLOADS = [
    File("https://github.com/chartes/deucalion-model-lasla/raw/master/latin-straight.json", "latin-straight.json"),
    File("https://github.com/chartes/deucalion-model-lasla/raw/master/latin-pos.json", "latin-pos.json"),
    File("https://github.com/chartes/deucalion-model-lasla/raw/master/latin-needs.json", "latin-needs.json"),
    File("https://github.com/chartes/deucalion-model-lasla/raw/master/model.tar", "model.tar")
]

