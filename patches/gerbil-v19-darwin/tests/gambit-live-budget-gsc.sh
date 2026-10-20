#!/bin/sh
set -eu
export HOME="${D881_GSC_HOME:?}"
exec "${D881_GSC_REAL:?}" "-:~~=${D881_TOOLCHAIN_HOME:?}" "$@"
