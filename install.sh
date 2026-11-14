#!/bin/sh
# Install the Idle RPG layout the way Herdr expects: copy its layout, theme and
# mod files into the Herdr config home. Re-run to update an existing install.
#
#   ./install.sh
set -eu

name=idle-rpg
# The layout used to live in a folder of that name, passed as an argument;
# it is still accepted, and anything else is a mistake.
usage() { echo "usage: ./install.sh (installs the $name layout)" >&2; exit 2; }
[ $# -le 1 ] || usage
case "${1:-$name}" in
  "$name") ;;
  *) usage ;;
esac
src="$(CDPATH='' cd -P -- "$(dirname -- "$0")" && pwd)"
home="${HERDR_APP_HOME:-$HOME/.config/herdr-app}"

[ -d "$src/layouts" ] || { echo "no layouts folder beside install.sh: $src" >&2; exit 1; }
[ -d "$home" ] || { echo "Herdr config home not found: $home (open the app once first)" >&2; exit 1; }

# Before copying anything: the repo is laid out like a Herdr home, so a home
# that is the repo, or whose layouts, themes or mods folder leads back into
# it, would have the repo's own files removed below. Refuse it whole.
for dir in layouts themes mods; do
  [ -d "$home/$dir" ] || continue
  case "$(CDPATH='' cd -P -- "$home/$dir" && pwd)/" in
    "$src"/*) echo "$home/$dir leads into this repo ($src): nothing to install" >&2; exit 1 ;;
  esac
done

for dir in layouts themes; do
  for f in "$src/$dir"/*; do
    [ -f "$f" ] || continue
    mkdir -p "$home/$dir"
    rm -f "$home/$dir/$(basename "$f")"   # replaces a symlink rather than writing through it
    cp "$f" "$home/$dir/"
  done
done

for mod in "$src"/mods/*/; do
  [ -d "$mod" ] || continue
  dest="$home/mods/$(basename "$mod")"
  if [ -L "$dest" ]; then rm "$dest"; fi
  mkdir -p "$dest"
  # A home whose mods folder leads back into this repo would have the mod
  # removed from under itself below: nothing to install, and nothing to lose.
  if [ "$(CDPATH='' cd -P -- "$dest" && pwd)" = "$(CDPATH='' cd -P -- "$mod" && pwd)" ]; then
    echo "$dest is this repo's own copy of the mod: nothing to install" >&2
    exit 1
  fi
  # Replace each file and folder the mod ships rather than copy over it, so a
  # picture an earlier install left in art/ (moved or dropped since) does not
  # linger, and a symlink is replaced rather than written through (rm removes
  # the link itself, never what it points to). Only those names inside the
  # mod's own folder are removed; anything else there is left alone.
  for entry in "$mod"*; do
    [ -e "$entry" ] || [ -L "$entry" ] || continue
    rm -rf "$dest/$(basename "$entry")"
  done
  cp -R "$mod". "$dest"/
done

echo "Installed $name into $home"
echo "Show it with: herdr-app do layout.switch --name $name"
