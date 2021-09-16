#!/usr/bin/python3.9
import argparse
from quarry.types import nbt
from quarry.types.buffer import Buffer
import os
import glob
import time
import zlib

def valid_dir(parser, arg):
    if not os.path.isdir(arg):
        parser.error(f'The directory {arg} does not exist.')
    os.chdir(arg)
    if not os.path.isfile('level.dat'):
        parser.error(f'The directory does not appear to be a valid Minecraft world.')
    if not os.path.isdir('entities/'):
        parser.error(f'No entities folder found. Try updating the world to the latest Minecraft version and try again.')
    os.chdir('entities/')
    return glob.glob('*.mca')

parser = argparse.ArgumentParser(description='Disable mob AI and other shit on Minecraft worlds.')
parser.add_argument('world_folder', type=lambda x: valid_dir(parser, x), help='Path to the Minecraft world folder.')

args = parser.parse_args()

class EntityRegion(nbt.RegionFile):
    """
    Function `save_chunk` is modified from https://github.com/barneygale/quarry/blob/master/quarry/types/nbt.py 
    ------
    Copyright (C) 2020 Barnaby Gale

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to
    deal in the Software without restriction, including without limitation the
    rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
    sell copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies of the Software and its documentation and acknowledgment shall be
    given in the documentation and software packages that this Software was
    used.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
    IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
    """
    def save_chunk(self, chunk, chunk_x, chunk_z):
        """
        Saves the given chunk, which should be a ``TagRoot``, to the region
        file.
        """

        # Compress chunk
        chunk = zlib.compress(chunk.to_bytes())
        chunk = Buffer.pack('IB', len(chunk), 2) + chunk
        chunk_length = 1 + (len(chunk) - 1) // 4096

        # Load extents
        extents = [(0, 2)]
        self.fd.seek(0)
        buff = Buffer(self.fd.read(4096))
        for idx in range(1024):
            z, x = divmod(idx, 32)
            entry = buff.unpack('I')
            offset, length = entry >> 8, entry & 0xFF
            if offset > 0 and not (x == chunk_x and z == chunk_z):
                extents.append((offset, length))
        extents.sort()
        extents.append((extents[-1][0] + extents[-1][1] + chunk_length, 0))

        # Compute new extent
        for idx in range(len(extents) - 1):
            start = extents[idx][0] + extents[idx][1]
            end = extents[idx+1][0]
            if (end - start) >= chunk_length:
                chunk_offset = start
                extents.insert(idx+1, (chunk_offset, chunk_length))
                break

        # Write extent header
        self.fd.seek(4 * (32 * chunk_z + chunk_x))
        self.fd.write(Buffer.pack(
            'I', (chunk_offset << 8) | (chunk_length & 0xFF)))

        # Write timestamp header
        self.fd.seek(4096 + 4 * (32 * chunk_z + chunk_x))
        self.fd.write(Buffer.pack('I', int(time.time())))

        # Write chunk
        self.fd.seek(4096 * chunk_offset)
        self.fd.write(chunk)

        # Truncate file
        self.fd.seek(4096 * extents[-1][0])
        self.fd.truncate()

tags = nbt.TagCompound({
    'Invulnerable': nbt.TagInt(1),
    'NoAI': nbt.TagInt(1),
    'NoGravity': nbt.TagInt(1),
    'PersistenceRequired': nbt.TagInt(1)
})

entity_blacklist = [
    'minecraft:area_effect_cloud',
    'minecraft:armor_stand',
    'minecraft:arrow',
    'minecraft:boat',
    'minecraft:chest_minecart',
    'minecraft:command_block_minecart',
    'minecraft:dragon_fireball',
    'minecraft:egg',
    'minecraft:end_crystal',
    'minecraft:ender_pearl',
    'minecraft:evoker_fangs',
    'minecraft:experience_bottle',
    'minecraft:experience_orb',
    'minecraft:eye_of_ender',
    'minecraft:falling_block',
    'minecraft:fireball',
    'minecraft:firework_rocket',
    'minecraft:fox',
    'minecraft:furnace_minecart',
    'minecraft:glow_item_frame',
    'minecraft:hopper_minecart',
    'minecraft:item',
    'minecraft:item_frame',
    'minecraft:leash_knot',
    'minecraft:lightning_bolt',
    'minecraft:llama_spit',
    'minecraft:marker',
    'minecraft:minecart',
    'minecraft:painting',
    'minecraft:potion',
    'minecraft:small_fireball',
    'minecraft:snowball',
    'minecraft:spawner_minecart',
    'minecraft:spectral_arrow',
    'minecraft:tnt',
    'minecraft:tnt_minecart',
    'minecraft:trident',
    'minecraft:wither_skull'
]

files = args.world_folder
total_files = len(files)
print(f'Found {total_files} region files.')

entity_count = 0
file_count = 0
chunk_count = 0
for file in files:
    file_count += 1
    print(f'Opening region file {file_count}/{total_files}: {file}')
    region = EntityRegion(file)
    for chunk_x in range(0, 32):
        for chunk_z in range(0, 32):
            try:
                chunk = region.load_chunk(chunk_x, chunk_z)
            except:
                continue
            chunk_count += 1
            compound = chunk.value[''].value
            entities = compound['Entities'].value
            for entity in entities:
                entity.update(tags)
                entity_count += 1
            region.save_chunk(chunk, chunk_x, chunk_z)
    region.close()

print(f'Done! Updated {entity_count} entities over {chunk_count} chunks.')
