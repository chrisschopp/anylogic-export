# anylogic-export

A CLI tool for exporting AnyLogic models to standalone Java applications.

Can be used as a [pre-commit](https://pre-commit.com/) (or [prek](https://prek.j178.dev/)) hook to run AnyLogic experiments in a continuous integration pipeline.

## Installation

```bash
uv add anylogic-export
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
