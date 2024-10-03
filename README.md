# dt-misc

dt-misc is a python library used to support the set of dt_tools packages:
 - dt-console  [[repo]](https://github.com/JavaWiz1/dt-console)  [[docs]](https://htmlpreview.github.io/?https://github.com/JavaWiz1/dt-console/blob/develop/docs/html/index.html)
 - dt-net  [[repo]](https://github.com/JavaWiz1/dt-net)  [[docs]](https://htmlpreview.github.io/?https://github.com/JavaWiz1/dt-net/blob/develop/docs/html/index.html)
 - dt-cli-tools  [[repo]](https://github.com/JavaWiz1/dt-cli-tools)  [[docs]](https://htmlpreview.github.io/?https://github.com/JavaWiz1/dt-cli-tools/blob/develop/docs/html/index.html)

and others.

It contains helper packages for Geolocation, Weather and Text-to-Speech (TSS).

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

## Documentation
Package documentation can be found [here](https://htmlpreview.github.io/?https://github.com/JavaWiz1/dt-misc/blob/develop/docs/html/index.html).
