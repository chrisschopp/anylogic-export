[![PyPi version](https://img.shields.io/pypi/v/anylogic-export)](https://pypi.org/project/anylogic-export/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![prek](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/j178/prek/master/docs/assets/badge-v0.json)](https://github.com/j178/prek)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
# anylogic-export

A CLI tool for exporting AnyLogic models to standalone Java applications.

Can be used as a [pre-commit](https://pre-commit.com/) (or [prek](https://prek.j178.dev/)) hook to run AnyLogic experiments in a continuous integration pipeline.

## Installation

To install from PyPI using [uv](https://docs.astral.sh/uv/), run:

```bash
uv add anylogic-export
```

Alternatively, to install with pip, run:

```bash
pip install anylogic-export
```

## Commands

Show help.

```bash
anylogic -h
```

Initialize an AnyLogic model repository for use with `anylogic-export` as a pre-commit hook.

```bash
anylogic init
```

## Export an AnyLogic model from the terminal

Assumes:

1. There is only one AnyLogic model in the current directory.
2. The model has an experiment named `CustomExperiment`, the default name for an experiment that doesn't display the model window.

```bash
anylogic export
```

## Prek Quickstart

Create `.pre-commit-config.yaml` in your project's root directory with the following contents:

```yaml
repos:
 - repo: https://github.com/chrisschopp/anylogic-export
   rev: v0.1.0
   hooks:
    - id: anylogic-export
      args: [export, --experiments=CustomExperiment]
      files: ModelName/*
```

Install the hook with:

```bash
prek install
```

## Benchmarking

Originally developed for one of the biggest AnyLogic models in the world. Exporting should take less time for most projects.

## Bitbucket repo

https://bitbucket.org/chris-schopp/anylogic-export/src/main/

Used for testing Bitbucket continuous integration.
