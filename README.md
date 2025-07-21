# goldfinch

Climate service processes defined through CWL.

## Development

For quick setup of new CWL definitions, install the package.

```shell
pip install -e .
```

Install the specific dependencies of the relevant CLI to be generated.
Otherwise, the following can be used to install all dependencies across all locally defined CLI.

```shell
pip install -e ".[processes]"
```

Then, run the commands as follows for the desired process:

```bash
click2cwl --process <path/to/python.py> [--output <path/to/output.cwl>]
```

By default, the output CWL is named `package.cwl` and is placed next to the Python file.

> [!WARNING]
> Because the CLI tool attempts to load the other Python file to identify its CWL definition from `click` decorators,
> any packages or dependencies that Python script imports has to be installed in the environment where the tool is run.
