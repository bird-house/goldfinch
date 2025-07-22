#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib
import importlib.machinery
import importlib.util
import inspect
import os
import sys
from typing import cast

import click
import click2cwl
import json
import yaml
from click import Parameter, Context
from click2cwl.cltexport import CLTExport
from click2cwl.cwlexport import CWLExport
from click2cwl.cwlparam import CWLParam
from click2cwl.paramexport import ParamExport
from click_option_group import optgroup, MutuallyExclusiveOptionGroup


class FlagPath(click.Path):
    def convert(
        self,
        value: str | os.PathLike[str],
        param: Parameter | None,
        ctx: Context | None,
    ) -> str | bytes | os.PathLike[str] | bool:
        if isinstance(value, bool):
            return value
        return super().convert(value, param, ctx)


@click.command(
    "click2cwl",
    context_settings={"allow_extra_args": True},  # pass down job parameters to context
)
@click.pass_context
@click.help_option("-h", "--help")
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
    default=None,
    type=click.Path(exists=True, dir_okay=False),
    help="If the python script defines multiple commands, this can be used to specify which one to convert.",
)
@click.option(
    "-o", "--output",
    type=click.Path(exists=False, dir_okay=False),
    is_flag=False,
    help=(
        "Output filename for the generated CWL definition. "
        "YAML or JSON format is auto-detected based on the file extension unless explicitly overridden."
    )
)
@click.option(
    "--output-format", "output_format",
    type=click.Choice(["json", "yaml"]),
    help="Enforce the output format instead of auto-detecting based on file extension."
)
@optgroup.group(
    "Operation",
    cls=MutuallyExclusiveOptionGroup,
    help="Select the type of CWL document to generate.",
)
@optgroup.option(
    "-w", "--workflow", "--cwl", "cwl_type",
    help=(
        "Embed the generated CWL in a 'Workflow' document rather than the 'CommandLineTool' directly "
        "(default: CommandLineTool). "
    ),
    type=click.Choice(["clt", "cwl"]),
    is_flag=False,
    flag_value="cwl",  # Workflow
    default="clt",  # CommandLineTool
)
@optgroup.option(
    "-j", "--job", "--params", "job_params",
    help=(
        "Generate the Job Parameters for CWL submission (e.g.: 'cwltool package.cwl job.yml'). "
        "The specific arguments required to invoke the CLI being described as CWL should be provided as well. "
        "Omitted argument values without defaults will be indicated by literal '<value>' placeholders. "
        "A path to the YAML file location to generate job parameters (equivalent to --output for CWL) can be specified."
    ),
    type=FlagPath(exists=False, dir_okay=False),
    is_flag=False,
    flag_value=True,
    default=False,
)
def main(ctx: click.Context, **kwargs: str) -> None:
    """
    Extends another specified Click command line interface to generate a CWL document with specific features.
    """
    # resolve the module containing the Click command
    cli_file = kwargs["process"]
    cli_path = os.path.abspath(cli_file)
    cli_spec = importlib.util.spec_from_file_location("click2cwl.program", cli_path)
    sys.modules["click2cwl.program"] = cli_spec  # type: ignore
    cli_mod = importlib.util.module_from_spec(cli_spec)
    cli_spec.loader.exec_module(cli_mod)

    # find the decorated Click function to convert
    click_functions = [
        (name, member)
        for name, member in
        inspect.getmembers(cli_mod)
        if (not name.startswith("_") or kwargs["command"] == name) and isinstance(member, click.Command)
    ]
    if len(click_functions) != 1:
        names = [name for name, _ in click_functions]
        raise ValueError(
            f"Expected exactly one Click command, found {names}. "
            f"Use the --command option to specify a specific one to convert or make sure the module defines one."
        )
    cli_name, cli_cmd = click_functions[0]
    cli_prog_call = f"python {cli_file}"

    # add context arguments to generate the CWL contents
    cli_ctx = cli_cmd.context_class(info_name=cli_prog_call, command=cli_cmd)
    output_cwl = True  # stdout or override file path
    output_job = True
    is_output_params = kwargs.get("job_params")
    if is_output_params:
        cli_ctx.args.extend(["--dump", "params"])
        output_job = kwargs["job_params"]
    elif "cwl_type" in kwargs:
        cli_ctx.args.extend(["--dump", kwargs["cwl_type"]])
    if kwargs.get("output"):
        output_cwl = kwargs["output"]

    # convert the Click command to CWL
    cli_cwl = click2cwl.Click2CWL(cli_ctx)

    # export the CLI with added arguments
    # similar operation to 'click2cwl.dump()', but with better handling of the output
    options = {
        "cwl": (CWLExport, output_cwl),
        "clt": (CLTExport, output_cwl),
        "params": (ParamExport, output_job),
    }
    cli_cwl.extra_params.get("env", {}).pop("PATH", None)  # do not propagate local PATH
    for export in cli_cwl.extra_params["dump"]:
        export_class, export_output = options[export]

        # inject job parameters (as needed by the exporter)
        # this has to be done before export to apply the values
        # cannot override 'default' when generating the actual CWL to avoid creating a definition to true to the CLI
        if is_output_params:
            cli_ctx.command.parse_args(cli_ctx, ctx.args)
            for param in cast(list[CWLParam], cli_cwl.params):
                value = cli_ctx.params.get(param.name, None)
                if value is not None:
                    param.default = value  # hack: default is used to store the value for export

        exporter = export_class(cli_cwl)

        # perform output
        export_json = kwargs.get("output_format") == "json" or str(export_output).endswith(".json")
        export_type = json.dump if export_json else yaml.dump
        if export_output is not True:
            export_data = exporter.to_dict()
            with open(export_output, mode="w", encoding="utf-8") as out_file:
                export_type(export_data, out_file, indent=2)
            print("Document written to:", export_output)
        elif export_json:
            export_data = exporter.to_dict()
            json.dumps(export_data, indent=2)
        else:
            exporter.dump(stdout=True)


if __name__ == "__main__":
    main()
