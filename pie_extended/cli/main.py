import click


from pie_extended.cli import utils
from typing import Iterable

MODELS = [name for name, *_ in utils.get_list()]


@click.group("pie-ext")
def pie_ext():
    """ Addon for Pie that allows you to download and install modules that you might be interested in """


@pie_ext.command("list")
@click.option("--full", is_flag=True, help="Display full information on models")
def print_list(full):
    """ List available model to download and use """
    click.echo("Available Models:")
    for module, desc in utils.get_list():
        click.echo("\t- {} ({}) : {}".format(
            click.style(module, bold=True),
            desc.lang,
            click.style(desc.title, underline=True)
        ))
        if full:
            click.echo("\t\tAuthor(s): {}".format(", ".join(desc.authors)))
            click.echo("\t\tDescription(s): {}".format(desc.description))
            click.echo("\t\tURL: {}".format(desc.link))


@pie_ext.command("download")
@click.argument("model", type=click.Choice(MODELS, case_sensitive=False))
def download(model):
    """ Download a [model] for future availability. Check list for available models"""
    click.echo(click.style("Starting downloading...", bold=True))
    for index, file in enumerate(utils.download(model)):
        if index == 0:
            click.echo("{} files to download".format(file))
        else:
            click.echo("- {} downloaded".format(file))
    click.echo(click.style("Finished !", bold=True))


@pie_ext.command("tag")
@click.argument("model", type=click.Choice(MODELS, case_sensitive=False))
@click.argument("filepath", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.option("--no-tokenizer", "no_tokenizer", is_flag=True,
              help="Do not apply advanced tokenizer: new line = one word, two new lines = one sentence")
@click.option("--allow-n-failures", "allowed_failure", type=int, default=5,
              help="Number of failures before things crash")
@click.option("--batch_size", type=int, default=16,
              help="Group of sentences tagged together")
@click.option("--device", type=str, default="cpu",
              help="Use cpu or gpu for prediction")
@click.option("--debug", is_flag=True,
              help="Raise error when a file is not tagged correctly")
@click.option("--model_path", type=str, default=None,
              help="Provide this with your own model path if you want to test it")
@click.option("--reset-exclude-patterns", "reset_patterns", is_flag=True, default=False,
              help="Reset exclude patterns")
@click.option("--add-pattern", "add_pattern",
              help="Add new exclude patterns  for token (Regular expression)", multiple=True)
@click.option("--max-tokens", "max_tokens",
              help="Maximum length of sentence", type=int, default=64)
def tag(model: str, filepath: str, allowed_failure: bool, batch_size: int, device: str, debug: bool,
        model_path: str,
        reset_patterns: bool, add_pattern: Iterable[str],
        no_tokenizer: bool = False,
        max_tokens: int = 64):
    """ Tag as many [filepath] as you want with [model] """
    from tqdm import tqdm
    click.echo(click.style("Getting the tagger", bold=True))
    try:
        tagger = utils.get_tagger(model, batch_size=batch_size, device=device, model_path=model_path)
    except FileNotFoundError as e:
        click.echo("Model not found: please make sure you have downloaded the model files with "
                   "pie-extended download " + model)
        if debug:
            raise e
        return
    failures = []
    for file in tqdm(filepath):
        try:
            utils.tag_file(
                model, tagger, file, reset_exclude_patterns=reset_patterns,
                exclude_patterns=add_pattern, no_tokenizer=no_tokenizer,
                max_tokens=max_tokens)
        except Exception as E:
            failures.append(E)
            click.echo("{} could not be lemmatized".format(file))
            if debug:
                raise E
            if len(failures) > allowed_failure:
                click.echo(
                    click.style("Too many errors, stopping the process", fg="red")
                )
                for failure in failures:
                    print(failure)
                break


@pie_ext.command("install-addons")
@click.argument("model", type=click.Choice(MODELS, case_sensitive=False))
def install(model):
    """ Install addons for specific models"""
    click.echo(click.style("Installing add-ons", bold=True))
    utils.get_addons(model)
    click.echo(click.style("Done", bold=True))


@pie_ext.command("details")
@click.argument("model", type=click.Choice(MODELS, case_sensitive=False))
@click.option("--model_path", type=str, default=None,
              help="Provide this with your own model path if you want to test it")
def details(model: str, model_path: str = None):
    """ Get details about known characters by the [model] """
    from tqdm import tqdm
    click.echo(click.style("Getting the tagger", bold=True))
    tagger = utils.get_tagger(model, model_path=model_path)
    for model, tasks in tagger.models:
        print(sorted(list(model.label_encoder.char.table.keys())))
