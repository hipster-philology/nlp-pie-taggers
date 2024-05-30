from ...utils import Metadata, File, get_path


DESC = Metadata(
    "OccitanContemporain",
    "occ_cont",
    ["Oriane Nédey", "Juliette Janès"],
    "Model trained on ...",
    "https://github.com/DEFI-COLaF/modeles-papie"
)

VERSION = "v0.0.1"
DOWNLOADS = [
    File("https://github.com/DEFI-COLaF/modeles-papie/releases/download/" + VERSION +
         "/PaPie_Lemma_finetune-WIKI2TTB-v0.0.1.tar",
         "lemma.tar"),
    File("https://github.com/DEFI-COLaF/modeles-papie/releases/download/" + VERSION +
         "/PaPie_POS_WIKITTB-v0.0.1.tar",
         "pos.tar"),
]

Models = "".join([
    "<{},lemma>".format(get_path("occ_cont", "lemma.tar")),
    "<{},pos>".format(get_path("occ_cont", "pos.tar"))
])
