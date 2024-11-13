from ...utils import Metadata, File, get_path


MODEL_NAME = "hy_hye"

DESC = Metadata(
        "Eastern Armenian",
        MODEL_NAME,
        ["Chahan Vidal-Gorène", "Nadi Tomeh", "Victoria Khurshudyan"],
        "Pie Model for Lemmatization, POS Tagging, and Morphological Analysis of Eastern Armenian, trained using Universal Dependencies for Eastern Armenian.",
        "https://aclanthology.org/2024.nlp4dh-1.42/"
)
VERSION ="v1.0.0"
DOWNLOADS = [
        File("https://zenodo.org/records/14059437/files/hye-ud-abbr-2024_11_04-21_35_36.tar?download=1", "abbr.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-adptype-2024_11_04-21_39_05.tar?download=1", "adptype.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-animacy-2024_11_04-21_44_47.tar?download=1", "animacy.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-aspect-2024_11_04-21_50_42.tar?download=1", "aspect.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-case-2024_11_04-21_56_25.tar?download=1", "case.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-definite-2024_11_04-22_02_34.tar?download=1", "definite.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-degree-2024_11_04-22_03_22.tar?download=1", "degree.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-lemma-2024_11_04-22_13_33.tar?download=1", "lemma.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-mood-2024_11_04-22_19_24.tar?download=1", "mood.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-nametype-2024_11_04-22_21_58.tar?download=1", "nametype.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-number-2024_11_04-22_27_32.tar?download=1", "number.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-number-psor-2024_11_04-22_28_20.tar?download=1", "number-psor.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-numform-2024_11_04-22_29_36.tar?download=1", "numform.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-numtype-2024_11_04-22_33_42.tar?download=1", "numtype.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-person-2024_11_04-22_39_19.tar?download=1", "person.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-person-psor-2024_11_04-22_40_06.tar?download=1", "person-psor.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-polarity-2024_11_04-22_43_46.tar?download=1", "polarity.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-polite-2024_11_04-22_44_32.tar?download=1", "polite.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-pos-2024_11_04-22_49_22.tar?download=1", "pos.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-poss-2024_11_04-22_51_44.tar?download=1", "poss.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-prontype-2024_11_04-22_57_28.tar?download=1", "prontype.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-subcat-2024_11_04-23_03_26.tar?download=1", "subcat.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-tense-2024_11_04-23_08_31.tar?download=1", "tense.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-verbform-2024_11_04-23_13_30.tar?download=1", "verbform.tar"),
        File("https://zenodo.org/records/14059437/files/hye-ud-voice-2024_11_04-23_19_22.tar?download=1", "voice.tar")
]


Models = "<{},lemma><{},pos><{},abbr><{},adptype><{},animacy><{},aspect><{},case><{},definite><{},degree><{},mood><{},nametype><{},number><{},number[psor]><{},numform><{},numtype><{},person><{},person[psor]><{},polarity><{},polite><{},poss><{},prontype><{},subcat><{},tense><{},verbform><{},voice>".format(
        get_path(MODEL_NAME, "lemma.tar"),
        get_path(MODEL_NAME, "pos.tar"),
        get_path(MODEL_NAME, "abbr.tar"),
        get_path(MODEL_NAME, "adptype.tar"),
        get_path(MODEL_NAME, "animacy.tar"),
        get_path(MODEL_NAME, "aspect.tar"),
        get_path(MODEL_NAME, "case.tar"),
        get_path(MODEL_NAME, "definite.tar"),
        get_path(MODEL_NAME, "degree.tar"),
        get_path(MODEL_NAME, "mood.tar"),
        get_path(MODEL_NAME, "nametype.tar"),
        get_path(MODEL_NAME, "number.tar"),
        get_path(MODEL_NAME, "number-psor.tar"),
        get_path(MODEL_NAME, "numform.tar"),
        get_path(MODEL_NAME, "numtype.tar"),
        get_path(MODEL_NAME, "person.tar"),
        get_path(MODEL_NAME, "person-psor.tar"),
        get_path(MODEL_NAME, "polarity.tar"),
        get_path(MODEL_NAME, "polite.tar"),
        get_path(MODEL_NAME, "poss.tar"),
        get_path(MODEL_NAME, "prontype.tar"),
        get_path(MODEL_NAME, "subcat.tar"),
        get_path(MODEL_NAME, "tense.tar"),
        get_path(MODEL_NAME, "verbform.tar"),
        get_path(MODEL_NAME, "voice.tar")
)