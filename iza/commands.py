# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/99_commands.ipynb.

# %% auto 0
__all__ = ['nbdev_agg_app', 'aggregate_notebooks', 'callback']

# %% ../nbs/99_commands.ipynb 3
import os, typer
from rich.pretty import pprint
from typing import Optional, List, Union
from typing_extensions import Annotated

# %% ../nbs/99_commands.ipynb 4
from .rich import console
from .typer import app
from .nbs import NotebookAggregator

# %% ../nbs/99_commands.ipynb 5
nbdev_agg_app = typer.Typer()

@app.command('nbdev_agg')
def aggregate_notebooks(
    path: Annotated[str, typer.Option(
        '--path', '-p', help='The path to the directory of notebooks to aggregate.',
    )],
    module: Annotated[Optional[str], typer.Option(
        '--module', '-m', help='The name of the module to create.'
    )] =  None,
    output: Annotated[Optional[str], typer.Option(
        '--output', '-o', help='The path to where the save the aggregated notebook file name excluded.',
    )] =  None,    
    ignore: Annotated[Optional[List[str]], typer.Option(
        '--ignore', '-i', help='Name of files to ignore in the directory.',
    )] =  [],
    prefix: Annotated[Optional[bool], typer.Option(
        '--prefix', '-f', help='Whether to prefix the module name to the notebook names.',
    )] =  True, 
):
    if ignore is None:
        ignore = []

    aggregator = NotebookAggregator(path, module=module, output=output, ignore=ignore, prefix=prefix)
    aggregator.aggregate()
    console.print(f"Aggregated notebook saved to {aggregator.output}", style="bold green")


@app.callback()
def callback():
    """
    Aggregate the notebooks in the directory.

    Parameters
    ----------
    path : str
        The path to the directory containing the notebooks.
    module : Optional[str], optional
        The name of the module, by default None
    output : Optional[str], optional
        The path to the output notebook, by default None
    ignore : Optional[List[str]], optional
        A list of notebooks to ignore, by default None
    """
    pass
