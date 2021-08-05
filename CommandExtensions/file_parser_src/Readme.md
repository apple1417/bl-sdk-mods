## File Parser
This folder holds the code used to parse through files looking for commands. This is done in a
native module to increase parsing speed. BLCMM files may look like xml, but they use some weird
custom escape logic which is very slow to handle from inside python.

Uses [pugixml](https://pugixml.org/) and [pybind11](https://pybind11.readthedocs.io/).

### Building
1. Get a python install of the same version used to build the sdk.    
   This is currently 3.7.9 32bit (for windows).
2. `pip install -r requirements.txt`
3. `python setup.py build`
4. (Optional) Install and run `pybind11-stubgen` on the generated `.pyd`. The actual stub file is
   manually written, but this might help find automatically added things you weren't expecting.
