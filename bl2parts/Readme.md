### bl2.parts data dumper
Creates data dumps used for [bl2.parts](https://bl2.parts).

Requires a PyYaml install in the `bl2parts/yaml` folder.

To generate:
1. Run `pyexec bl2parts/gen.py` in each game.
2. Run `merge.py` *outside* of the game, in a normal python intepreter.
3. If any collision messages are spat out to console, update `merge.py`, either with new name
   overrides, or logic to merge more data.
