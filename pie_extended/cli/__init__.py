import click

from . import sub


MODELS = [name for name, *_ in sub.get_list()]

@click.group("pie-ext")
def pie_ext():
    """ Extended commands """


@pie_ext.command("list")
@click.option("--full", is_flag=True, help="Display full information on models")
def print_list(full):
    click.echo("Available Models:")
    for module, desc in sub.get_list():
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
    for index, file in enumerate(sub.download(model)):
        if index == 0:
            click.echo("{} files to download".format(file))
        else:
            click.echo("- {} downloaded".format(file))
    click.echo(click.style("Finished !", bold=True))
