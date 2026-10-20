#!/bin/sh
set -eu
exec "${GERBIL_GNU_GCC:-$(command -v gcc-16)}" -ftrack-macro-expansion=0 "$@"
