# Releases

### 0.0.27 (2021/02/01)

- (models/lasla) Support ignoring character tokens through `[IGN:char]`
- (pipeline/excluders) Made sure excluder would use the same replacement character through a CharRegistry dictionary 

### 0.0.26 (2021/01/14)

- (models/lasla) Use model LASLA+ from 0.0.5b trained on PyTorch 1.3.1

### 0.0.25 (2021/01/13)
- Added a `max_tokens` per sentence limit in DataIterators.

### 0.0.24 (2020/12/14)

- (models/fro) Updated model fro to 0.3.0 using multiple tasks

### 0.0.23 (2020/12/04)

- (models/dum) Added a new model with Middle Dutch thanks to Mike Kestemont
- (tokenizers) Added a SimpleTokenizer based on length

### 0.0.22 (2020/12/02)

- (models/lasla) Apply unidecode
- (models/lasla) Use model LASLA+ from 0.0.5alpha trained on PyTorch 1.3.1
- (models/lasla) Updated the abbreviation list
- (CI) Added Github Actions
- (Documentation) Added a warning about supported python versions
- (Documentation) Fixed the example
- (pipeline) Created `AbbreviationsRemoverExcluder`
- (dependencies) Cleaned the version requirements due to pip update

### 0.0.21 (2020/09/24) 

- (models/LASLA) Fixed a bug where clitics are not split correctly after nouns
- Fixed multiple typos in CHANGES.md in version numbers

### 0.0.20 (2020/09/22)

- **New Latin model** which handles capitalized input, entities and better disambiguation.

### 0.0.19 (2020/09/18)

- (Latin Model) Fixed a long standing bug where Latin would not tag Gender because I forgot it in the GlueProcessor... Big Facepalm

### 0.0.18 (2020/09/08) - Release named A2M

- Fixed the way the DataIterator deals with documents ending with a sentence formed of excluded tokens only.
- Fixed a typo in an import pattern
- (Latin Model) Dealt with some weird Unicode numerals which unexpectedly broke our `.isnumeric()` usage (e.g. ↀ )

### 0.0.17 (2020/07/26)

- Added a way to tag texts where word are already tokenized: new lines are word separator, 
double new lines are sentence separator
- Reworked the way preprocessing of special chars is done prior to sentence tokenization and after it. 
Creation of the class Excluder (pie_extended.pipeline.tokenizers.utils.excluder)
    - Allows for more code sharing across models.
- Fixed a typo that would prevent to tag with FREEM (and nobody saw that ! ;) )

### 0.0.16 (2020/06/22)

- Fixed Early Modern French Model (reusing processor and tokenizer of FR model)
- Added Ancient Greek Model (Very basic addition, need more work probably ?)

### 0.0.15 (2020/06/22)

- Added Early Modern French Model (reusing processor and tokenizer of FR model)

### 0.0.14 (2020/04/24)

- Hotfixed columns order in tsv output

### 0.0.13 (2020/04/24)

- Hotfixed lowercase for latin model

### 0.0.12 (2020/04/24)

*Unfilled* **TODO**

### 0.0.11 (2020/04/24)

*Unfilled* **TODO**

### 0.0.10 (2020/04/24)

- `PIE_EXTENDED_DOWNLOADS` environment variable can be used to set up a non default directory for models and linked data.
    - eg. `PIE_EXTENDED_DOWNLOADS=~/PieData pie-extended download fr`

## 0.0.9 (2020/04/24)

- (Breaking) Postprocessors now must return a list of dict instead of a dict with `.get_dict()` methods ([#c8be021](https://github.com/hipster-philology/nlp-pie-taggers/commit/c8be021fc1d253da84f01445ed5a99af7fa2ad2b))
- Added a better tokenizer for Classical French
    - Keeps *aujourd'hui* intact
    - Keeps union dash with pronouns for `-le` in sentence such as `mange-le`.
    - Keeps the `-t` euphonique together with the pronoun: `mange-t-il` becomes `mange` and `-t-il`
        - Its removed from lemmatization until a new model is trained (old model had `-t` on the verb)
        - Elision work as intended for non euphonique such as "Va-t'en" -> `va`, `-t'`, `en`
- Updated Classical French models ([#15](https://github.com/hipster-philology/nlp-pie-taggers/pull/15))
- Added a post-processor to split tokens ([#17](https://github.com/hipster-philology/nlp-pie-taggers/pull/17))
