from ...utils import Metadata, File, get_path

MODEL_NAME = "hy_xcl"

DESC = Metadata(
        "Classical Armenian",
        MODEL_NAME,
        ["Chahan Vidal-Gorène", "Nadi Tomeh", "Victoria Khurshudyan"],
        "Pie Model for Lemmatization, POS Tagging, and Morphological Analysis of Classical Armenian, trained using Universal Dependencies for Classical Armenian.",
        "https://aclanthology.org/2024.nlp4dh-1.42/"
)

DOWNLOADS = [
        File("https://zenodo.org/records/14056139/files/xcl-ud-aspect-2024_11_05-03_24_48.tar?download=1", "aspect.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-case-2024_11_05-03_33_09.tar?download=1", "case.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-deixis-2024_11_05-03_38_12.tar?download=1", "deixis.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-lemma-2024_11_05-03_49_41.tar?download=1", "lemma.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-mood-2024_11_05-03_58_02.tar?download=1", "mood.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-number-2024_11_05-04_06_32.tar?download=1", "number.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-numtype-2024_11_05-04_08_02.tar?download=1", "numtype.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-person-2024_11_05-04_15_37.tar?download=1", "person.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-pos-2024_11_05-04_24_38.tar?download=1", "pos.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-poss-2024_11_05-04_25_45.tar?download=1", "poss.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-prontype-2024_11_05-04_31_17.tar?download=1", "prontype.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-reflex-2024_11_05-04_32_26.tar?download=1", "reflex.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-tense-2024_11_05-04_41_12.tar?download=1", "tense.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-verbform-2024_11_05-04_49_41.tar?download=1", "verbform.tar"),
        File("https://zenodo.org/records/14056139/files/xcl-ud-voice-2024_11_05-04_56_34.tar?download=1", "voice.tar")
]


Models = "<{},lemma><{},pos><{},aspect><{},case><{},deixis><{},mood><{},number><{},numtype><{},person><{},poss><{},prontype><{},reflex><{},tense><{},verbform><{},voice>".format(
        get_path(MODEL_NAME, "lemma.tar"),
        get_path(MODEL_NAME, "pos.tar"),
        get_path(MODEL_NAME, "aspect.tar"),
        get_path(MODEL_NAME, "case.tar"),
        get_path(MODEL_NAME, "deixis.tar"),
        get_path(MODEL_NAME, "mood.tar"),
        get_path(MODEL_NAME, "number.tar"),
        get_path(MODEL_NAME, "numtype.tar"),
        get_path(MODEL_NAME, "person.tar"),
        get_path(MODEL_NAME, "poss.tar"),
        get_path(MODEL_NAME, "prontype.tar"),
        get_path(MODEL_NAME, "reflex.tar"),
        get_path(MODEL_NAME, "tense.tar"),
        get_path(MODEL_NAME, "verbform.tar"),
        get_path(MODEL_NAME, "voice.tar")
)