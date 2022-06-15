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
- Aquamarine Snipers are based off of maliwan SMGs, instead of snipers, so have a completely wrong part list

The following parts all have some bonuses adjusted:
- Hawkeye Barrel
  - -10 preadd zoom turns into +10 grade
- Twister Barrel
  - +0.75 damage turns into +1
- Little Evie Barrel
  - +0.33 damage turns into +0.4
  - +4 mag size turns into +6
- Actualizer Barrel
  - +0.6 damage turns into +1.4
  - -0.2 mag size turns into +0.2
  - +0.35 reload turns into +1
- Tattler Barrel
  - +1 projectile count turns into +2
  - +10 weapon spread turns into +6
