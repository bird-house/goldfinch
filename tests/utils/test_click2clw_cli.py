#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from goldfinch.utils.click2cwl_cli import resolve_cli_command


@pytest.mark.parametrize(
    ["expected_command", "process", "docker", "docker_module"],
    [
        (
            "python -m xclim.cli",
            "xclim.cli",
            "bird-house/goldfinch:latest",
            None,
        ),
        (
            "python -m goldfinch.processes.subset.poly_subset",
            "goldfinch.processes.subset.poly_subset",
            "bird-house/goldfinch:latest",
            None,
        ),
        (
            "python -m goldfinch.processes.subset.poly_subset",
            "goldfinch/processes/subset/poly_subset.py",
            "bird-house/goldfinch:latest",
            None,
        ),
        (
            "python -m goldfinch.processes.subset.poly_subset",
            "src/goldfinch/processes/subset/poly_subset.py",
            "bird-house/goldfinch:latest",
            None,
        ),
        (
            "python -m goldfinch.processes.subset.poly_subset",
            "/home/user/goldfinch/processes/subset/poly_subset.py",
            "bird-house/goldfinch:latest",
            None,
        ),
        (
            "python -m goldfinch.processes.subset.poly_subset",
            "poly_subset.py",
            "bird-house/goldfinch:latest",
            "goldfinch.processes.subset.poly_subset",
        ),
        (
            "python -m xclim.cli",
            "goldfinch.processes.indicator.hdd",
            "bird-house/goldfinch:latest",
            "xclim.cli",
        ),
        (
            "python /home/user/goldfinch/processes/subset/poly_subset.py",
            "/home/user/goldfinch/processes/subset/poly_subset.py",
            None,
            None,
        ),
    ]
)
def test_resolve_cli_command(expected_command, process, docker, docker_module):
    result = resolve_cli_command(process, docker, docker_module)
    assert result == expected_command
