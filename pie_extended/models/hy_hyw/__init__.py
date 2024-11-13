from ...utils import Metadata, File, get_path

MODEL_NAME = "hy_hyw"

DESC = Metadata(
        "Western Armenian",
        MODEL_NAME,
        ["Chahan Vidal-Gorène", "Nadi Tomeh", "Victoria Khurshudyan"],
        "Pie Model for Lemmatization, POS Tagging, and Morphological Analysis of Western Armenian, trained using Universal Dependencies for Western Armenian.",
        "https://aclanthology.org/2024.nlp4dh-1.42/"
)

DOWNLOADS = [
        File("https://zenodo.org/records/14060082/files/hyw-ud-abbr-2024_11_04-23_21_46.tar?download=1", "abbr.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-adptype-2024_11_04-23_32_38.tar?download=1", "adptype.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-animacy-2024_11_04-23_46_09.tar?download=1", "animacy.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-aspect-2024_11_05-00_00_02.tar?download=1", "aspect.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-case-2024_11_05-00_13_40.tar?download=1", "case.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-connegative-2024_11_05-00_15_42.tar?download=1", "connegative.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-definite-2024_11_05-00_26_35.tar?download=1", "definite.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-degree-2024_11_05-00_28_25.tar?download=1", "degree.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-deixis-2024_11_05-00_35_20.tar?download=1", "deixis.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-echo-2024_11_05-00_37_23.tar?download=1", "echo.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-hyph-2024_11_05-00_41_02.tar?download=1", "hyph.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-lemma-2024_11_05-00_54_35.tar?download=1", "lemma.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-mood-2024_11_05-01_03_36.tar?download=1", "mood.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-number-2024_11_05-01_17_57.tar?download=1", "number.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-numform-2024_11_05-01_23_02.tar?download=1", "numform.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-numtype-2024_11_05-01_27_14.tar?download=1", "numtype.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-person-2024_11_05-01_39_52.tar?download=1", "person.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-person-psor-2024_11_05-01_41_42.tar?download=1", "person-psor.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-polarity-2024_11_05-01_54_03.tar?download=1", "polarity.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-polite-2024_11_05-01_55_54.tar?download=1", "polite.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-pos-2024_11_05-02_07_23.tar?download=1", "pos.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-poss-2024_11_05-02_12_00.tar?download=1", "poss.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-prontype-2024_11_05-02_21_41.tar?download=1", "prontype.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-reflex-2024_11_05-02_25_19.tar?download=1", "reflex.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-style-2024_11_05-02_27_10.tar?download=1", "style.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-subcat-2024_11_05-02_41_14.tar?download=1", "subcat.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-tense-2024_11_05-02_51_17.tar?download=1", "tense.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-typo-2024_11_05-02_53_08.tar?download=1", "typo.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-verbform-2024_11_05-03_02_55.tar?download=1", "verbform.tar"),
        File("https://zenodo.org/records/14060082/files/hyw-ud-voice-2024_11_05-03_15_54.tar?download=1", "voice.tar")
]


Models = "<{},lemma><{},pos><{},abbr><{},adptype><{},animacy><{},aspect><{},case><{},connegative><{},definite><{},degree><{},deixis><{},echo><{},hyph><{},mood><{},number><{},numform><{},numtype><{},person><{},person[psor]><{},polarity><{},polite><{},poss><{},prontype><{},reflex><{},style><{},subcat><{},tense><{},typo><{},verbform><{},voice>".format(
        get_path(MODEL_NAME, "lemma.tar"),
        get_path(MODEL_NAME, "pos.tar"),
        get_path(MODEL_NAME, "abbr.tar"),
        get_path(MODEL_NAME, "adptype.tar"),
        get_path(MODEL_NAME, "animacy.tar"),
        get_path(MODEL_NAME, "aspect.tar"),
        get_path(MODEL_NAME, "case.tar"),
        get_path(MODEL_NAME, "connegative.tar"),
        get_path(MODEL_NAME, "definite.tar"),
        get_path(MODEL_NAME, "degree.tar"),
        get_path(MODEL_NAME, "deixis.tar"),
        get_path(MODEL_NAME, "echo.tar"),
        get_path(MODEL_NAME, "hyph.tar"),
        get_path(MODEL_NAME, "mood.tar"),
        get_path(MODEL_NAME, "number.tar"),
        get_path(MODEL_NAME, "numform.tar"),
        get_path(MODEL_NAME, "numtype.tar"),
        get_path(MODEL_NAME, "person.tar"),
        get_path(MODEL_NAME, "person-psor.tar"),
        get_path(MODEL_NAME, "polarity.tar"),
        get_path(MODEL_NAME, "polite.tar"),
        get_path(MODEL_NAME, "poss.tar"),
        get_path(MODEL_NAME, "prontype.tar"),
        get_path(MODEL_NAME, "reflex.tar"),
        get_path(MODEL_NAME, "style.tar"),
        get_path(MODEL_NAME, "subcat.tar"),
        get_path(MODEL_NAME, "tense.tar"),
        get_path(MODEL_NAME, "typo.tar"),
        get_path(MODEL_NAME, "verbform.tar"),
        get_path(MODEL_NAME, "voice.tar")
)