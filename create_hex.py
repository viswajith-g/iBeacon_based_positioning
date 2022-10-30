#!/usr/bin/env python3

import shutil

import fs
import intelhex


# This is set by the circuitpython impl for the microbit.
# Look at build-microbit_v2/common.ld to find this value.
FILESYSTEM_OFFSET_IN_FLASH = 0x75000

# FILESYSTEM_FILE_EMPTY = "microbit_circuitpython_emptyfilesystem.img"
FILESYSTEM_FILE_EMPTY = "emptyfile36k.img"
FILESYSTEM_FILE_POPULATED = "microbit_circuitpython_filesystem.img"

CODE_PY = "code.py"

FILESYSTEM_FILE_HEX = "microbit_circuitpython_filesystem.hex"
CIRCUITPYTHON_FIRMWARE_HEX = "firmware.combined.hex"
OUT_FIRMWARE_HEX = "microbit.firmware.hex"

######
## Add code.py to the filesystem
######

# Start with an empty FAT filesystem.
shutil.copyfile(FILESYSTEM_FILE_EMPTY, FILESYSTEM_FILE_POPULATED)

# Open the filesystem so we can read and write to it.
my_fs = fs.open_fs("fat://" + FILESYSTEM_FILE_POPULATED)

# Write the contents of CODE_PY file to our filesystem.
with open(CODE_PY, "rb") as f:
    c = f.read()
    my_fs.writebytes("/code.py", c)

# Finished editing our filesystem.
my_fs.close()

######
## Create .hex file to flash to microbit
######

h = intelhex.IntelHex()

# Load the binary filesystem image starting at the correct address in flash.
h.loadbin(FILESYSTEM_FILE_POPULATED, FILESYSTEM_OFFSET_IN_FLASH)

# Write the filesystem in Intel Hex format.
h.tofile(FILESYSTEM_FILE_HEX, format="hex")

# Open the main circuit python firmware hex file.
circuitpy_firmware_hex = intelhex.IntelHex(CIRCUITPYTHON_FIRMWARE_HEX)
# Open the filesystem hex file.
filesystem_hex = intelhex.IntelHex(FILESYSTEM_FILE_HEX)
# Combine the filesystem into the main firmware.
circuitpy_firmware_hex.merge(filesystem_hex)
# Write to a new hex file that we can load to the microbit.
circuitpy_firmware_hex.tofile(OUT_FIRMWARE_HEX, format="hex")
