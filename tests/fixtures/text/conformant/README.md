# conformant

Check one repo against the README canon.

## Problem

Without this repo, the canon is prose and not a gate.

## Install

    pip install conformant

## Usage

Run the tool against a repo directory and read the row it prints.

## Example

in : verify_text.py .
out: conformant OK

## Contracts

- input: a repo directory
- output: one row per repo

## Family

Consumed by every repo in the family.

## Status

Stable. The tool is not a formatter.

## License

Apache-2.0
