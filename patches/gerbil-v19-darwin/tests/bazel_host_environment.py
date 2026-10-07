#!/usr/bin/env python3
"""Reuse Bazel host discovery for isolated source-build experiments."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
from types import SimpleNamespace


def build_environment():
    environment = dict(os.environ)
    for key in ("SDKROOT", "DEVELOPER_DIR", "CPATH", "C_INCLUDE_PATH",
                "CPLUS_INCLUDE_PATH", "LIBRARY_PATH", "LDFLAGS", "PKG_CONFIG_PATH"):
        environment.pop(key, None)
    gcc = os.environ.get("GERBIL_GNU_GCC") or shutil.which("gcc-16")
    gxx = os.environ.get("GERBIL_GNU_GXX") or shutil.which("g++-16")
    if not gcc or not gxx:
        raise RuntimeError("GNU GCC 16 and G++ 16 are required")
    environment["GERBIL_CC"] = gcc

    class Context:
        os = SimpleNamespace(environ=environment, name="darwin")

        def which(self, name):
            return shutil.which(name, path=environment.get("PATH"))

        def path(self, value):
            return SimpleNamespace(exists=Path(value).exists())

        def execute(self, argv, quiet=True):
            result = subprocess.run(argv, env=environment, capture_output=True,
                                    text=True, timeout=30)
            return SimpleNamespace(return_code=result.returncode,
                                   stdout=result.stdout, stderr=result.stderr)

    def fail(message):
        raise RuntimeError(message)

    repository = Path(__file__).resolve().parents[3]
    namespace = {"struct": SimpleNamespace, "fail": fail}
    source = repository / "gerbil/host_system.bzl"
    # This discovery module uses the Python-compatible subset of Starlark.
    exec(compile(source.read_text(), str(source), "exec"), namespace)
    host = namespace["resolve_host_environment"](
        Context(), ["openssl@3", "sqlite", "zlib"])
    environment.update(host.environment)
    environment.update(CC=gcc, CXX=gxx, GERBIL_GNU_GCC=gcc,
                       COMPILER_PATH="/usr/bin", GERBIL_BUILD_CORES="2")
    return environment


if __name__ == "__main__":
    environment = build_environment()
    for key in ("SDKROOT", "DEVELOPER_DIR", "CPATH", "LIBRARY_PATH",
                "LDFLAGS", "PKG_CONFIG_PATH", "AR", "CC", "CXX", "GERBIL_CC",
                "GERBIL_GNU_GCC", "COMPILER_PATH", "GERBIL_BUILD_CORES"):
        if key in environment:
            print(f"export {key}={shlex.quote(environment[key])}")
