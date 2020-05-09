# Releases

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
