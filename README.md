# lobotomob
A Python script that disables the AI of all mobs currently spawned in a Minecraft world, effectively making them brainless. Do note you'll probably want to also run `/gamerule doMobSpawning false` and utilise mods/plugins for disabling mob spawning via other methods.

This is done by applying the following NBT tags to all mob entities saved in the world:
 - `Invulnerable`
 - `NoAI`
 - `NoGravity`
 - `PersistenceRequired`
 - `Silent`
 - `Fire`

A button is also placed in the head slot of mobs that burn during daylight, unless there's already something occupying that slot.

This is mostly intended to preserve worlds and their mobs as they were when the game last saved (while also saving on server resources), acting as a time capsule when loaded up on an appropriately configured server.

Do note this currently only works for worlds in the most recent format.

## Usage
Python 3.9+ supported. Install the `quarry` package listed in `requirements.txt`.

```
usage: lobotomob.py [-h] world_folder

Disable mob AI and other shit on Minecraft worlds.

positional arguments:
  world_folder  Path to the Minecraft world folder.

optional arguments:
  -h, --help    show this help message and exit
```