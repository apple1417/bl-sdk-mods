set -x

# Need the outer folder to be called 'Mods' like the actual folder
mkdir Mods

# Save dirs for later so all ignored ones are logged in one place
# Symlink everything though so imports still line up
lintDirs=()
for mod in */ ; do
    if [ "$mod" == "Mods/" ]; then
        continue
    fi

    ln -s "$PWD/$mod" "$PWD/Mods/${mod%/}"
    if [ -f $mod/.nolint ]; then
        echo Not linting \'${mod%/}\'
        continue
    fi
    lintDirs+=( $mod )
done

# These are files the sdk provides which we might import from
# Follow imports is off so using empty files works fine
sdkFiles=(
    "__init__.py"
    "ModManager.py"
    "OptionManager.py"
    "KeybindManager.py"
    "ModMenuManager.py"
    "SaveManager.py"
    "Util.py"
)
for file in ${sdkFiles[@]}; do
    touch "Mods/$file"
done

for mod in ${lintDirs[@]}; do
    echo Checking \'${mod%/}\'
    # Need to use absolute paths for it to recognise `from Mods import ___`
    find "$PWD/Mods/$mod" -name "*.py" -print0 | xargs -0 mypy
    flake8 "Mods/$mod"
done
