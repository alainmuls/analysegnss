
## Usage of Python logging class
The  [Python logging class](https://docs.python.org/3/howto/logging.html) is used to log messages to a file and to the console. The logger methods are named after the level or severity of the events they are used to tracking. The standard levels and their applicability are described below (in increasing order of severity):

| Level    | When it's used                                                                                                                                                         |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DEBUG    | Detailed information, typically of interest only when diagnosing problems.                                                                                             |
| INFO     | Confirmation that things are working as expected.                                                                                                                      |
| WARNING  | An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low'). The software is still working as expected. |
| ERROR    | Due to a more serious problem, the software has not been able to perform some function.                                                                                |
| CRITICAL | A serious error, indicating that the program itself may be unable to continue running.                                                                                 |


 The implemented logger class creates logger objects which are used in the following way:
- the file logger logs all messages equal or higher than `DEBUG` and writes them to a file named `script_name.log` in the `logs` directory in daily files.
- the console logger logs all messages equal or higher defined by the option `--verbose` or `-v`:
  - `-v`: logs all messages equal or higher than `WARNING`
  - `-vv`: logs all messages equal or higher than `INFO`
  - `-vvv`: logs all messages equal or higher than `DEBUG`.


## The `argparse` module

The CLI arguments are parsed using the `argparse` module. The `argparse` module is a standard library module in Python that provides a way to parse command-line arguments. In order to assist the user in finding out which arguments are available, the `argparse` module provides a help message that lists all the available arguments.

```bash
± rtk_pvtgeod.py -h
usage: rtk_pvtgeod.py [-h] [-V] [-v] --sbf_fn SBF_FN

argument_parser.py analysis of SBF data

options:
  -h, --help       show this help message and exit
  -V, --version    show program's version number and exit
  -v, --verbose    verbose level... repeat up to three times.
  --sbf_fn SBF_FN  input SBF filename
```

By importing the `argcomplete` module, the command line arguments can be completed automatically by pressing the tab key after including in the `~/.bashrc` file:

```bash
for file in  rtk_pvtgeod.py ppk_rnx2rtkp.py rtkppk_plot.py ebh_lines.py
do
    complete -o nospace -o default -o bashdefault -F _Python_argcomplete ${file}
done
```

The file `utils/argument_parser.py` contains the function `argument_parser_xyz()` which is used to parse the command line arguments for each Python script. The function `argument_parser_xyz()` is called in the main script and the arguments are passed to the main function.

---

Return to  [top level readme](../README.md)