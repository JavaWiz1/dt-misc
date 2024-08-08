# dt-misc

dt-misc is a python library used to support the set of dt_tools packages:
 - [dt-console](https://github.com/JavaWiz1/dt-console)
 - [dt-net-tools](https://github.com/JavaWiz1/dt-net-tools)

It contains helper packages for logging, os detection and other common utilities.

## Installation

### Download source code from githup via git
```bash
git clone https://github.com/JavaWiz1/dt-misc.git
```
Note, when downloading source, [Poetry](https://python-poetry.org/docs/) was used as the package manager.  Poetry 
handles creating the virtual environment and all dependent packages installs with proper versions.

To setup virtual environment with required production __AND__ dev ([sphinx](https://www.sphinx-doc.org/en/master/)) dependencies:
```bash
poetry install
```

with ONLY production packages (no sphinx):
```bash
poetry install --without dev
```


### use the package manager [pip](https://pip.pypa.io/en/stable/) to install dt-misc.

```bash
pip install dt-misc [--user]
```

