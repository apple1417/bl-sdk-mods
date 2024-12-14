# File Parser Tests
These tests run on the file parser module, in a regular Python intepreter.

To run:
```sh
pip install pytest
pytest command_extensions/file_parser_tests
```

Generally, tests consist of a `.testin` and `.json` pair. The `.testin` file is the raw mod file to
be parsed. The `.json` contains the commands to be enabled, as a list of strings under the
`commands` key, and the expected results under the `output` key (using a list of lists instead of
a list of tuples).

## On a Linux Host
Since this uses your system python, a Linux host cannot import the Windows `file_parser.pyd` the mod
ships with/builds by default. You'll need to build a native Linux module instead:

```sh
cmake -G Ninja -B .out/ce-linux -DCE_FILE_PARSER_NATIVE_LINUX=1 -DCMAKE_BUILD_TYPE=Release command_extensions
cmake --build .out/ce-linux --target install
```
