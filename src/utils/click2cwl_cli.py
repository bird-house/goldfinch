#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib
import importlib.machinery
import importlib.util
import os
import sys

import click
from click2cwl import dump


@click.command("click2cwl")
@click.option(
    "-p", "--process",
    metavar="PYTHON_FILE",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the Python script defining the Click command line interface to convert to CWL.",
)
@click.option(
    "-c", "--command",
    metavar="COMMAND",
    type=click.Path(exists=True, dir_okay=False),
    help="If the python script defines multiple commands, this can be used to specify which one to convert.",
)
@click.option(
    "-o", "--output",
    type=click.Path(exists=False, dir_okay=False),
    default="package.cwl",
    help="Output filename for the generated CWL definition."
)
def main(**kwargs: str) -> None:
    cli_file = kwargs["process"]
    cli_path = os.path.abspath(cli_file)
    cli_spec = importlib.util.spec_from_file_location("click2cwl.program", cli_path)
    sys.modules["click2cwl.program"] = cli_spec
    cli_mod = importlib.util.module_from_spec(cli_spec)
    cli_spec.loader.exec_module(cli_mod)

    cli_func = dir(cli_mod)





if __name__ == "__main__":
    main()
