#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib
import importlib.machinery
import importlib.util
import inspect
import os
import sys
from collections import OrderedDict
from typing import Any, cast

import click
import click2cwl
import json
import yaml
from click import Parameter, Context
from click2cwl.cltexport import CLTExport
from click2cwl.cwlexport import CWLExport
from click2cwl.cwlparam import CWLParam
from click2cwl.metadata import WorkflowMetadata
from click2cwl.paramexport import ParamExport
from click_option_group import optgroup, MutuallyExclusiveOptionGroup


CWL_METADATA_FIELDS_EXTRAS = ["cwlVersion", "doc", "label", "id"]
CWL_METADATA_FIELDS_AUTO = ["version", "author", "organization"]
CWL_METADATA_FIELDS = CWL_METADATA_FIELDS_EXTRAS + CWL_METADATA_FIELDS_AUTO


class CWLMetadataExtended(WorkflowMetadata):
    def to_dict(self):
        meta = super().to_dict()
        for field in CWL_METADATA_FIELDS_EXTRAS:
            if field in self._fields:
                meta[field] = self._fields[field]
        if "schemas" in meta:
            meta["$schemas"] = meta.pop("schemas")
        return meta


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


class MetadataParam(click.types.StringParamType):
    def convert(self, value: str, param: Parameter | None, ctx: Context | None) -> str:
        args = value.split("=", 1)
        if len(args) != 2 or not args[0].strip() or not args[1].strip():
            raise click.BadParameter(
                "Metadata must be specified as '<field>=<value>'",
                param=param,
                ctx=ctx,
            )
        return super().convert(value, param, ctx)


def yaml_dump(data: dict[str, Any], *args: Any, **kwargs: Any) -> str:
    """
    Custom YAML dump function to ensure consistent formatting.
    """
    represent_dict_order = lambda self, _data: self.represent_mapping("tag:yaml.org,2002:map", _data.items())
    yaml.add_representer(OrderedDict, represent_dict_order)
    return yaml.dump(data, *args, **kwargs)


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
@click.option(
    "--cwl-version",
    help="Specific version to use for the CWL document.",
    default="v1.2",
)
@click.option(
    "-m", "--metadata",
    help=(
         "General metadata for the CWL document defined as '<field>=<value>' for each entry. "
         f"Can be repeated for multiple metadata field properties {CWL_METADATA_FIELDS}."
    ),
    type=MetadataParam(),
    multiple=True,
)
@click.option(
    "--docker",
    help="Specific docker image to use for the CWL command line tool.",
)
@click.option(
    "--coresMin", "coresMin",
    help="Minimum CPU cores resource requirement the CWL command line tool.",
    type=int,
)
@click.option(
    "--coresMax", "coresMax",
    help="Maximum CPU cores resource requirement the CWL command line tool.",
    type=int,
)
@click.option(
    "--ramMin", "ramMin",
    help="Minimum RAM resource requirement the CWL command line tool.",
    type=int,
)
@click.option(
    "--ramMax", "ramMax",
    help="Maximum RAM resource requirement the CWL command line tool.",
    type=int,
)
@click.option(
    "--wall-time",
    help="Maximum time limit requirement the CWL command line tool.",
    type=int,
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

    # add additional parameters to the CWL context
    for req in ["docker", "wall-time", "coresMin", "coresMax", "ramMin", "ramMax", "metadata", "cwl-version"]:
        val = kwargs.get(req) or kwargs.get(req.replace("-", "_"))
        if val:
            val = [val] if isinstance(val, str) else val
            for req_val in val:
                cli_ctx.args.extend([f"--{req}", req_val])

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
        export_type = json.dump if export_json else yaml_dump
        export_data = exporter.to_dict()

        # enforce certain metadata requirements
        # Workflow ('cwl') does it automatically, but CommandLineTool ('clt') does not
        cwl_meta = exporter.click2cwl.extra_params.get("metadata", {})
        if cwl_meta and any(
            key not in export_data and f"s:{key}" not in export_data
            for key in CWL_METADATA_FIELDS
        ):
            export_meta = CWLMetadataExtended(**cwl_meta).to_dict()
            export_data.update(export_meta)

        # write to file or print to stdout
        if export_output is not True:
            with open(export_output, mode="w", encoding="utf-8") as out_file:
                export_type(export_data, out_file, indent=2)
            print("Document written to:", export_output)
        elif export_json:
            print(json.dumps(export_data, indent=2))
        else:
            print(yaml_dump(export_data, indent=2))


if __name__ == "__main__":
    main()
