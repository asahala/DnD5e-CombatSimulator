# DnD5e-CombatSimulator
D&amp;D 5e Creature Combat Simulator

A (Python 3.6) script for simulating Dungeons & Dragons 5th edition encounters between creatures. No external libraries needed.

## Why does this exist?
This script is mainly created as a DM tool for simulating encounters between different types of creatures. Want to know how a level 8 Barbarian with a magical Greataxe +2 and his Dire Wolf companion can stand against a Mammoth? How about a Purple Worm vs. 30 zombies? Just run the script and see.

## How to use
Run ```simulate()``` function in ```main.py```. You can get a list of implemented creatures by calling function ```list_creatures()```. More documentation in ```main.py```

## Features
- Movement in two-dimensional world (flying/burrowing not yet implemented)
- Possibility to create battles between parties of arbitrary size
- Create approximations of player characters by combining already defined creature, ability and weapon objects (see *definitions.py*)
- Most of the crucial D&D mechanics defined

## Caveats
Creature behavior is very straightforward. Thus the results are not always comparable one-to-one to Pen & Paper encounters. 

## Known bugs
- If a creature has swallowed other creatures and dies, the swallowed creatures end up in the same coordinates.

## TODO
- Spell casting
- Flying and burrowing
- More creatures
- Perhaps a more interactive UI (TkInter etc.)
- Implement creature size on the map (now all take same amount of space)
