#!/bin/sh
# Install a visualizer the way Herdr expects: copy its layout, theme and mod
# files into the Herdr config home. Re-run to update an existing install.
#
#   ./install.sh [name]        default: raid-party
set -eu

name="${1:-raid-party}"
case "$name" in
  '' | */* | .*) echo "not a visualizer name: $name" >&2; exit 2 ;;
esac
root="$(CDPATH='' cd -P -- "$(dirname -- "$0")" && pwd)"
src="$root/$name"
home="${HERDR_APP_HOME:-$HOME/.config/herdr-app}"

[ -d "$src/layouts" ] || { echo "no visualizer named '$name' in $root" >&2; exit 1; }
[ -d "$home" ] || { echo "Herdr config home not found: $home (open the app once first)" >&2; exit 1; }

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
  cp -R "$mod". "$dest"/
done

echo "Installed $name into $home"
echo "Show it with: herdr-app do layout.switch --name $name"
