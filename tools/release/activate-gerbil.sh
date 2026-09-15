#!/usr/bin/env bash

if [[ -n "${BASH_VERSION:-}" ]]; then
  gerbil_activate_source="${BASH_SOURCE[0]}"
  gerbil_activate_sourced=$([[ "$gerbil_activate_source" != "$0" ]] && printf true || printf false)
elif [[ -n "${ZSH_VERSION:-}" ]]; then
  gerbil_activate_source="${(%):-%N}"
  gerbil_activate_sourced=$([[ ":$ZSH_EVAL_CONTEXT:" == *:file:* ]] && printf true || printf false)
else
  printf 'activate requires bash or zsh\n' >&2
  return 64 2>/dev/null || exit 64
fi

if [[ "$gerbil_activate_sourced" != true ]]; then
  printf 'source this file to activate the released Gerbil toolchain\n' >&2
  exit 64
fi

GERBIL_PREFIX="$(cd "$(dirname "$gerbil_activate_source")" && pwd)"
GERBIL_HOME="$GERBIL_PREFIX/current"
gerbil_runtime_options="~~=$GERBIL_HOME,~~bin=$GERBIL_HOME/bin,~~lib=$GERBIL_HOME/lib"

export GERBIL_PREFIX GERBIL_HOME
export GAMBOPT="${GAMBOPT:+$GAMBOPT,}$gerbil_runtime_options"
export PATH="$GERBIL_PREFIX/bin:$PATH"

unset gerbil_activate_source gerbil_activate_sourced gerbil_runtime_options
