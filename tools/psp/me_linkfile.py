#!/usr/bin/env python3
"""Media Engine cache isolation for the game's PRX.

The ME (the PSP's second CPU) runs the audio engine. Each CPU has its own data cache, and the ME writes back its WHOLE cache after
every job: a 64-byte cache line that holds audio state (written by the ME) next to game data (written by the main CPU meanwhile) would
be written back with the ME's stale copy of the game data, silently undoing the main CPU's writes.

This tool takes the PSPSDK's linkfile.prx and puts the .data and .bss of the objects whose code runs on the ME at the start of the
.data / .bss output sections, between 64-byte boundaries, so none of their cache lines is shared with anything else. The idea comes from
z2442's oot-PSP (tools/psp_me_render_ld.py, which does the same for its ME renderer).

  me_linkfile.py make  <sdk linkfile.prx> <out linkfile>    write the linker script
  me_linkfile.py check <elf>                                 verify the linked image (fails the build if the isolation is broken)
"""
import subprocess
import sys

# Objects whose data the ME writes (the audio engine, the mixer and the audio output buffers). Patterns are matched against the object
# paths given to the linker (build/<ver>_psp/src/...).
ME_OBJECTS = [
    "*src/audio/*.o",
    "*src/sh/audio/*.o",
    "*src/pc/mixer.o",
    "*src/pc/audio/audio_psp.o",
]

DATA_ANCHOR = "    *(.data .data.* .gnu.linkonce.d.*)\n"
BSS_ANCHOR = "   *(.bss .bss.* .gnu.linkonce.b.*)\n"


def block(kind, sections):
    lines = ["    . = ALIGN(64);\n", "    __psp_me_%s_start = .;\n" % kind]
    for pattern in ME_OBJECTS:
        lines.append("    %s(%s)\n" % (pattern, sections))
    lines += ["    . = ALIGN(64);\n", "    __psp_me_%s_end = .;\n" % kind]
    return "".join(lines)


def make(src, dst):
    with open(src) as f:
        text = f.read()
    if text.count(DATA_ANCHOR) != 1 or text.count(BSS_ANCHOR) != 1:
        sys.exit("me_linkfile.py: unexpected linkfile.prx layout (%s)" % src)
    text = text.replace(DATA_ANCHOR, block("data", ".data .data.*") + DATA_ANCHOR)
    text = text.replace(BSS_ANCHOR, block("bss", ".bss .bss.* COMMON") + BSS_ANCHOR)
    with open(dst, "w") as f:
        f.write(text)


def check(elf):
    out = subprocess.run(["psp-nm", elf], capture_output=True, text=True, check=True).stdout
    syms = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3:
            syms[parts[2]] = int(parts[0], 16)
    errors = []
    for kind in ("data", "bss"):
        start, end = syms.get("__psp_me_%s_start" % kind), syms.get("__psp_me_%s_end" % kind)
        if start is None or end is None:
            errors.append("missing __psp_me_%s_start/end" % kind)
        elif start % 64 or end % 64 or end <= start:
            errors.append("ME %s region not 64-byte isolated (%#x..%#x)" % (kind, start, end))
    if errors:
        sys.exit("me_linkfile.py check %s: %s" % (elf, "; ".join(errors)))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "make":
        make(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3 and sys.argv[1] == "check":
        check(sys.argv[2])
    else:
        sys.exit(__doc__)
