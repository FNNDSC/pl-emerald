#!/bin/bash

COMMIT='7c8ac54213cecd4fbb15f700b14d73f7086cf11d'
REPO='https://github.com/kevin-keraudren/example-motion-correction'
URL="$REPO/archive/$COMMIT.tar.gz"
DIR_INSIDE_TARBALL="$(basename "$REPO")-$COMMIT"

tarball="$(mktemp --suffix '.tar.gz')"
output_dir="$1"

if [ -z "$output_dir" ]; then
  echo "usage: $0 example_data_dir/"
  exit 1
fi

if [ -e "$output_dir" ]; then
  echo "error: $output_dir exists"
  exit 1
fi

set -ex
wget -O "$tarball" "$URL"
tar xvf "$tarball" --directory=/tmp
mv -v "/tmp/$DIR_INSIDE_TARBALL" "$output_dir"
rm -v "$tarball"

find "$output_dir" -name '*.nii.gz' -type f | parallel gzip -d
