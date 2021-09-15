# fbs tutorial shim

This repository contains helper code for the
[fbs tutorial](https://github.com/mherrmann/fbs-tutorial).
Specifically: At the time of this writing, the open source version of
[fbs](https://build-system.fman.io/) only supports Python 3.5 and 3.6. If you
try to use it on later Python versions, then you get an error. The goal of this
repository is to work around this, so you can also play with fbs's tutorial from
later Python versions. We achieve this by replacing fbs's implementations of
commands such as `freeze` by ones that return pre-compiled binaries. As long as
you follow the tutorial precisely, this gives you the full experience even when
you are not on a supported Python version.