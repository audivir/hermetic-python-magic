# hermetic-python-magic

A hermetic fork of [python-magic](https://github.com/ahupp/python-magic) that bundles a
prebuilt `libmagic` and its `magic.mgc` database, so no system-wide libmagic install is
required. The public API is the same as `python-magic`, imported as `hermetic.magic`.

## Prerequisites

- Python 3.10 or later.

## Installation

```shell
pip install hermetic-python-magic
```

## Usage

```python
import hermetic.magic as magic

magic.from_file("test.pdf")
# 'PDF document, version 1.2'
magic.from_file("test.pdf", mime=True)
# 'application/pdf'
magic.from_buffer(open("test.pdf", "rb").read(1024))
# 'PDF document, version 1.2'
```

## Acknowledgments

The Python bindings are ported from [python-magic](https://github.com/ahupp/python-magic)
by Adam Hupp. The bundled `libmagic` and `magic.mgc` database are built from
[file](https://github.com/file/file) by Ian F. Darwin and Christos Zoulas. See `NOTICE`
for full attribution and `LICENSE` for the licenses of both projects.

## License

MIT, see `LICENSE`.
