# bl2.parts data dumper
Creates data dumps used for [bl2.parts](https://bl2.parts).

Requires a PyYaml install in the `bl2parts/yaml` folder.

To generate:
1. In each game:
   1. Get to the main menu, online with hotfixes
   2. Enter the game once then immediately SQ
   3. Run `pyexec bl2parts/gen.py`
   These steps are required for some items (see below) to get properly defined.
2. Run `merge.py` *outside* of the game, in a normal python intepreter.
3. If any collision messages are spat out to console, update `merge.py`, either with new name
   overrides, or logic to merge more data.


### Broken items when offline
1. Aquamarine Snipers are based off of maliwan SMGs, instead of snipers, so have a completely wrong part list
2. The Hawkeye barrel has a -10 preadd zoom fov bonus turn into a +10 grade
3. The Twister barrel has a +0.75 damage bonus turn into a +1
4. The Little Evie barrel has a +0.33 damage bonus turn into a +0.4, and a +4 mag size bonus turn into a +6
