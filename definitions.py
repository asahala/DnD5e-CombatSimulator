import copy
import behavior
from abilities import *
from creature import BaseCreature
from weapons import Weapon, MultiWeapon

""" asahala 2020
https://github.com/asahala/DnD5e-CombatSimulator/
"""

""" ================================================================ """
""" ==================== GENERAL TYPE DEFS ========================= """
""" ================================================================ """

""" Damage types; use these instead of plain strings to avoid typos """
bludgeoning = 'bludgeoning'
piercing = 'piercing'
slashing = 'slashing'
bludgeoning_magic = 'magical bludgeoning'
piercing_magic = 'magical piercing'
slashing_magic = 'magical slashing'
piercing_silver = 'silvered piercing'
slashing_silver = 'silvered slashing'
radiant = 'radiant'
necrotic = 'necrotic'
cold = 'cold'
poison = 'poison'
acid = 'acid'
psychic = 'psychic'
fire = 'fire'
force = 'force'
thunder = 'thunder'
lightning = 'lightning'

""" Creature types """
aberration = 'aberration'
beast = 'beast'
celestial = 'celestial'
construct = 'construct'
dragon = 'dragon'
elemental = 'elemental'
fey = 'fey'
fiend = 'fiend'
giant = 'giant'
humanoid = 'humanoid'
monstrosity = 'monstrosity'
ooze = 'ooze'
plant = 'plant'
undead = 'undead'

""" Creature sizes """
tiny = 1
small = 2
medium = 3
large = 4
huge = 5
gargantuan = 6
colossal = 7

""" Condition types """
grapple = 'grapple'
restrain = 'restrain'
paralysis = 'paralysis'
charm = 'charm'
prone = 'prone'
fear = 'fear'

""" ================================================================ """
""" ========================== WEAPONS ============================= """
""" ================================================================ """
""" Note that you should use copy.deepcopy(weapon) for ranged weapons
    to prevent them using same ammo pool!
"""

greatclub = Weapon(name='greatclub', damage=["3d8+6"],
                   damage_type=[bludgeoning], reach=15, to_hit=9)

crocodile_bite = Weapon(name='bite',
                        damage=["1d10+2"],
                        damage_type=[piercing],
                        reach=5,
                        to_hit=4,
                        special=[Grapple(name='bite', dc=15, save='str')])

dire_wolf_bite = Weapon(name='bite',
                        damage=["2d6+3"],
                        damage_type=[piercing],
                        reach=5,
                        to_hit=5,
                        special=[Knockdown(name="bite",
                                           dc=13,
                                           save='str')])

ghast_bite = Weapon(name='bite',
                    damage=["2d8+2"],
                    damage_type=[piercing],
                    reach=5,
                    to_hit=3)

ghast_claw = Weapon(name='claws',
                    damage=["2d6+3"],
                    damage_type=[slashing],
                    reach=5,
                    to_hit=5,
                    special=[Paralysis(name='claws', dc=10, save='con')])

ghoul_bite = Weapon(name='bite',
                    damage=["2d6+2"],
                    damage_type=[piercing],
                    reach=5,
                    to_hit=2)

ghoul_claw = Weapon(name='claws',
                    damage=["2d4+2"],
                    damage_type=[slashing],
                    reach=5,
                    to_hit=4,
                    special=[Paralysis(name='claws', dc=10, save='con')])

giant_crocodile_bite = MultiWeapon(name='bite',
                                    damage=["3d10+5"],
                                    damage_type=[piercing],
                                    reach=5,
                                    to_hit=8,
                                    uses_per_turn=1,
                                    special=[Grapple(name='bite', dc=6, save='str')])

giant_crocodile_tail = MultiWeapon(name='tail',
                                    damage=["2d8+5"],
                                    damage_type=[bludgeoning],
                                    reach=10,
                                    to_hit=8,
                                    uses_per_turn=1,
                                    special=[Knockdown(name="tail",
                                         dc=20,
                                         save='str')])


giant_spider_bite = Weapon(name='bite', damage=["1d8+3"],
                           damage_type=[piercing],
                           reach=5,
                           to_hit=5,
                           special=[Poison(name='bite',
                                           dc=11,
                                           save='con',
                                           damage=['2d8'],
                                           success=0.5,
                                           duration=None,
                                           damage_type=[poison])])

lion_bite = Weapon(name='bite',
                   damage=["1d8+3"],
                   damage_type=[piercing],
                   reach=5,
                   to_hit=5)

lion_claw = Weapon(name='claw',
                   damage=["1d6+3"],
                   damage_type=[slashing],
                   reach=5,
                   to_hit=5)

lion_pounce = Weapon(name='pounce',
                     damage=["1d6+3"],
                     damage_type=[slashing],
                     reach=5,
                     min_distance=20,
                     to_hit=5,
                     special=[Knockdown(name="pounce", dc=13, save='str',
                                        charge_distance=20,
                                        bonus_action=lion_bite)])

extra_2d8 = Weapon(name='extra gore damage',
                   damage=["2d8"],
                   damage_type=[piercing],
                   reach=0,
                   min_distance=0,
                   to_hit=0)

mammoth_trample = Weapon(name='trample',
                         damage=["4d10+7"],
                         damage_type=[bludgeoning],
                         reach=5,
                         to_hit=10)

mammoth_gore = Weapon(name='gore',
                      damage=["4d8+7"],
                      damage_type=[piercing],
                      reach=10,
                      to_hit=10,
                      special=[Knockdown(name="trampling charge", dc=18, save='str',
                                         charge_distance=20,
                                         bonus_action=mammoth_trample)])

mummy_fist = MultiWeapon(name='rotting fist',
                         damage=["2d6+3", "3d6"],
                         damage_type=[bludgeoning, necrotic],
                         reach=5, to_hit=5,
                         uses_per_turn=1,
                         special=[MummyRot(name="Mummy Rot",
                                           save='con',
                                           dc=12,
                                           damage=['1d1+9'],
                                           duration=1,
                                           damage_type=[necrotic])])

minotaur_axe = Weapon(name='greataxe',
                      damage=["2d12+4"],
                      damage_type=[slashing],
                      reach=5, to_hit=6)

minotaur_gore = Weapon(name='gore',
                       damage=["2d8+3"],
                       damage_type=[piercing],
                       reach=5,
                       min_distance=5,
                       to_hit=6,
                       special=[Knockback(name="gore knockback", dc=14, save='str',
                                          charge_distance=10,
                                          knockback_distance=10,
                                          bonus_action=extra_2d8)])

shortbow = Weapon(name='shortbow',
                damage=["1d6+2"],
                damage_type=[piercing],
                ranged=True,
                ammo=20,
                reach=80,
                to_hit=4)

troll_bite = MultiWeapon(name='bite',
                         damage=["1d6+4"],
                         damage_type=[piercing],
                         reach=5, to_hit=7,
                         uses_per_turn=1)

troll_claws = MultiWeapon(name='claws',
                          damage=["2d6+4"],
                          damage_type=[slashing],
                          reach=5, to_hit=11,
                          uses_per_turn=2)

wight_longsword = MultiWeapon(name='longsword',
                              damage=["1d10+2"],
                              damage_type=[slashing],
                              reach=5, to_hit=4)

wight_life_drain = MultiWeapon(name='life drain',
                               damage=["1d6+2"],
                               damage_type=[necrotic],
                               reach=5, to_hit=5,
                               uses_per_turn=1,
                               special=[DamageMaxHP(name='life drain',
                                                    dc=13,
                                                    save='con')])

wyvern_bite = MultiWeapon(name='bite',
                          damage=["2d6+4"],
                          damage_type=[piercing],
                          reach=10, to_hit=7,
                          uses_per_turn=1)

wyvern_claws = MultiWeapon(name='claws',
                           damage=["2d8+4"],
                           damage_type=[slashing],
                           reach=5, to_hit=7,
                           uses_per_turn=1)

wyvern_stinger = MultiWeapon(name='stinger',
                             damage=["2d6+4"],
                             damage_type=[piercing],
                             reach=10, to_hit=11,
                             uses_per_turn=1,
                             special=[Poison(name='poison stinger',
                                             dc=11,
                                             save='con',
                                             damage=['7d6'],
                                             damage_type=[poison],
                                             success=0.5,
                                             duration=None)])

""" ================================================================ """
""" ========================== CREATURES =========================== """
""" ================================================================ """

class Creatures:

    black_bear = BaseCreature(name='black bear', cr=0.5, ac=11, hp=19, speed=40,
                          size=medium,
                          category=beast,
                          attacks=2,
                          ai=behavior.Standard,
                          scores={'str': 15, 'dex': 10, 'con': 14,
                                  'int': 2, 'wis': 12, 'cha': 7},
                          melee_attacks={'basic':
                                             [MultiWeapon(name='bite',
                                                          damage=["1d6+2"],
                                                          damage_type=[piercing],
                                                          reach=5,
                                                          to_hit=3,
                                                          uses_per_turn=1),
                                              MultiWeapon(name='claws',
                                                          damage=["2d4+2"],
                                                          damage_type=[slashing],
                                                          reach=5,
                                                          to_hit=3,
                                                          uses_per_turn=1)]})

    brown_bear = BaseCreature(name='brown bear', cr=1, ac=11, hp=34, speed=40,
                              size=large,
                              category=beast,
                              attacks=2,
                              ai=behavior.Standard,
                              scores={'str': 19, 'dex': 10, 'con': 16,
                                      'int': 2, 'wis': 13, 'cha': 7},
                              melee_attacks={'basic':
                                                 [MultiWeapon(name='bite',
                                                              damage=["1d8+4"],
                                                              damage_type=[piercing],
                                                              reach=5,
                                                              to_hit=5,
                                                              uses_per_turn=1),
                                                  MultiWeapon(name='claws',
                                                              damage=["2d6+4"],
                                                              damage_type=[slashing],
                                                              reach=5,
                                                              to_hit=5,
                                                              uses_per_turn=1)]})

    bugbear = BaseCreature(name='bugbear', cr=1, ac=16, hp=27, speed=30,
                       size=medium,
                       category=humanoid,
                       ai=behavior.Standard,
                       # Surprise attack undefined
                       # Brute hardcoded into weapon 
                       scores={'str': 15, 'dex': 14, 'con': 13,
                               'int': 8, 'wis': 11, 'cha': 9},
                       melee_attacks={'basic': [
                           Weapon(name='morningstar', damage=["2d8+2"],
                                  damage_type=[piercing], reach=5,
                                  to_hit=4)]},
                       ranged_attacks={'basic': [
                           Weapon(name='javelin', damage=["1d6+2"],
                                  damage_type=[piercing], reach=30,
                                  ranged=True,
                                  ammo=5,
                                  to_hit=4)]})

    crocodile = BaseCreature(name='crocodile', cr=0.5, ac=12, hp=19, speed=20,
                             size=large,
                             category=beast,
                             ai=behavior.Standard,
                             scores={'str': 15, 'dex': 10, 'con': 13,
                                     'int': 2, 'wis': 10, 'cha': 5},
                             melee_attacks={'basic': [crocodile_bite]})

    dire_wolf = BaseCreature(name='dire wolf', cr=1, ac=14, hp=37, speed=50,
                             size=large,
                             ai=behavior.SocialAnimal,
                             category=beast,
                             scores={'str': 17, 'dex': 15, 'con': 15,
                                     'int': 3, 'wis': 12, 'cha': 7},
                             melee_attacks={'special': [dire_wolf_bite]},
                             passives=[PackTactics])

    giant_crocodile = BaseCreature(name='giant crocodile', cr=5, ac=14, hp=85, speed=30,
                             size=huge,
                             category=beast,
                             ai=behavior.Standard,
                             attacks=2,
                             scores={'str': 21, 'dex': 9, 'con': 17,
                                     'int': 2, 'wis': 10, 'cha': 7},
                             melee_attacks={'basic': [giant_crocodile_bite,
                                                      giant_crocodile_tail] })


    giant_spider = BaseCreature(name='giant spider', cr=1, ac=14, hp=26, speed=30,
                                size=large,
                                category=beast,
                                ai=behavior.Standard,
                                scores={'str': 14, 'dex': 16, 'con': 12,
                                        'int': 2, 'wis': 11, 'cha': 4},
                                melee_attacks={'basic': [giant_spider_bite]})

    ghast = BaseCreature(name='ghast', cr=2, ac=13, hp=36, speed=30,
                         size=medium,
                         category=undead,
                         ai=behavior.Standard,
                         scores={'str': 16, 'dex': 17, 'con': 10,
                                 'int': 11, 'wis': 10, 'cha': 8},
                         immunities=[poison, paralysis, charm],
                         resistances=[necrotic],
                         melee_attacks={'basic': [ghast_bite],
                                        'special': [ghast_claw]},
                         passives=[Stench(name='ghast stench',
                                          type_='on_start',
                                          save='con',
                                          dc=10)])

    ghoul = BaseCreature(name='ghoul', cr=1, ac=12, hp=22, speed=30,
                         size=medium,
                         category=undead,
                         ai=behavior.Standard,
                         scores={'str': 13, 'dex': 15, 'con': 10,
                                 'int': 7, 'wis': 10, 'cha': 6},
                         immunities=[poison, paralysis, charm, fear],
                         melee_attacks={'basic': [ghoul_bite],
                                        'special': [ghoul_claw]})

    goblin = BaseCreature(name='goblin', cr=0.25, ac=15, hp=7, speed=30,
                       size=small,
                       category=humanoid,
                       ai=behavior.Standard,
                       scores={'str': 8, 'dex': 14, 'con': 10,
                               'int': 10, 'wis': 8, 'cha': 8},
                       melee_attacks={'basic': [
                           Weapon(name='scimitar', damage=["1d6+2"],
                                  damage_type=[slashing], reach=5,
                                  to_hit=4)]},
                       ranged_attacks={'basic': [copy.deepcopy(shortbow)]})
    
    kobold = BaseCreature(name='kobold', cr=0.125, ac=12, hp=5, speed=30,
                       size=small,
                       category=humanoid,
                       ai=behavior.Standard,
                       scores={'str': 7, 'dex': 15, 'con': 9,
                               'int': 8, 'wis': 7, 'cha': 8},
                       passives=[PackTactics],
                       melee_attacks={'basic': [
                           Weapon(name='dagger', damage=["1d4+2"],
                                  damage_type=[piercing], reach=5,
                                  to_hit=4)]},
                       ranged_attacks={'basic': [
                           Weapon(name='sling', damage=["1d4+2"],
                                  damage_type=[bludgeoning], reach=30,
                                  ranged=True,
                                  ammo=20,
                                  to_hit=4)]})

    lion = BaseCreature(name='lion', cr=1, ac=12, hp=26, speed=50,
                        size=large,
                        category=beast,
                        ai=behavior.SocialAnimal,
                        scores={'str': 17, 'dex': 15, 'con': 13,
                                'int': 3, 'wis': 12, 'cha': 8},
                        melee_attacks={'basic': [lion_bite, lion_claw],
                                       'special': [lion_pounce]},
                        passives=[PackTactics])

    mammoth = BaseCreature(name='mammoth', cr=6, ac=13, hp=126, speed=40,
                           size=huge,
                           category=beast,
                           ai=behavior.Standard,
                           scores={'str': 24, 'dex': 9, 'con': 21,
                                   'int': 3, 'wis': 11, 'cha': 6},
                           melee_attacks={'basic': [mammoth_gore]})

    minotaur = BaseCreature(name='minotaur', cr=3, ac=14, hp=76, speed=40,
                            size=medium,
                            category=beast,
                            ai=behavior.Standard,
                            scores={'str': 18, 'dex': 11, 'con': 16,
                                    'int': 6, 'wis': 16, 'cha': 9},
                            melee_attacks={'basic': [minotaur_axe],
                                           'special': [minotaur_gore]})

    mummy = BaseCreature(name='mummy', cr=3, ac=11, hp=58, speed=20,
                         size=medium,
                         category=undead,
                         ai=behavior.Standard,
                         attacks=1,
                         vulnerabilities=[fire],
                         resistances=[bludgeoning, piercing, slashing],
                         immunities=[necrotic, poison, charm, paralysis, fear],
                         scores={'str': 16, 'dex': 8, 'con': 15,
                                 'int': 6, 'wis': 10, 'cha': 12},
                         melee_attacks={'basic': [mummy_fist]},
                         passives=[DreadfulGlare(name="Dreadful Glare",
                                                 save="wis",
                                                 dc=11,
                                                 type_='at_end',
                                                 duration=1)])

    orc = BaseCreature(name='orc', cr=0.5, ac=13, hp=15, speed=30,
                       size=medium,
                       category=humanoid,
                       ai=behavior.Standard,
                       scores={'str': 16, 'dex': 12, 'con': 16,
                               'int': 7, 'wis': 11, 'cha': 10},
                       melee_attacks={'basic': [
                           Weapon(name='greataxe', damage=["1d12+2"],
                                  damage_type=[slashing], reach=5,
                                  to_hit=5)]},
                       ranged_attacks={'basic': [
                           Weapon(name='javelin', damage=["1d6+3"],
                                  damage_type=[piercing], reach=30,
                                  ranged=True,
                                  ammo=5,
                                  to_hit=5)]})

    orc_war_chieftain = BaseCreature(name='orc war chieftain', cr=4, ac=16, hp=93, speed=30,
                                     size=medium,
                                     category=humanoid,
                                     ai=behavior.Standard,
                                     attacks=2,
                                     scores={'str': 18, 'dex': 12, 'con': 18,
                                             'int': 11, 'wis': 11, 'cha': 16},
                                     melee_attacks={'basic': [
                                         Weapon(name='greataxe', damage=["2d10+4"],
                                                     damage_type=[slashing], reach=5,
                                                     to_hit=6)]},
                                     ranged_attacks={'basic': [
                                         Weapon(name='javelin', damage=["2d7+4"],
                                                     damage_type=[piercing], reach=40,
                                                     ranged=True,
                                                     ammo=5,
                                                     to_hit=6)]})

    orog = BaseCreature(name='orog', cr=2, ac=18, hp=42, speed=30,
                        size=medium,
                        category=humanoid,
                        ai=behavior.Standard,
                        attacks=2,
                        scores={'str': 18, 'dex': 12, 'con': 18,
                                'int': 12, 'wis': 11, 'cha': 12},
                        melee_attacks={'basic': [
                            Weapon(name='greataxe', damage=["1d12+2"],
                                        damage_type=[slashing], reach=5,
                                        to_hit=6)]},
                        ranged_attacks={'basic': [
                            Weapon(name='javelin', damage=["1d6+3"],
                                        damage_type=[piercing], reach=30,
                                        ranged=True,
                                        ammo=5,
                                        to_hit=5)]})

    owlbear = BaseCreature(name='owlbear', cr=3, ac=13, hp=59, speed=40,
                           size=medium,
                           category=beast,
                           ai=behavior.Standard,
                           attacks=2,
                           scores={'str': 20, 'dex': 12, 'con': 17,
                                   'int': 3, 'wis': 12, 'cha': 7},
                           melee_attacks={'basic': [
                               MultiWeapon(name='beak', damage=["1d10+5"],
                                           damage_type=[piercing], reach=5,
                                           to_hit=7, uses_per_turn=1),
                               MultiWeapon(name='claws', damage=["2d8+5"],
                                           damage_type=[slashing], reach=5,
                                           to_hit=7, uses_per_turn=1)
                           ]})

    polar_bear = BaseCreature(name='brown bear', cr=2, ac=12, hp=42, speed=40,
                              size=large,
                              category=beast,
                              attacks=2,
                              ai=behavior.Standard,
                              scores={'str': 20, 'dex': 10, 'con': 16,
                                      'int': 2, 'wis': 13, 'cha': 7},
                              melee_attacks={'basic':
                                                 [MultiWeapon(name='bite',
                                                              damage=["1d8+5"],
                                                              damage_type=[piercing],
                                                              reach=5,
                                                              to_hit=7,
                                                              uses_per_turn=1),
                                                  MultiWeapon(name='claws',
                                                              damage=["2d6+6"],
                                                              damage_type=[slashing],
                                                              reach=5,
                                                              to_hit=7,
                                                              uses_per_turn=1)]})


    purple_worm = BaseCreature(name='purple worm', cr=15, ac=18, hp=247, speed=50,
                               size=gargantuan,
                               category=monstrosity,
                               ai=behavior.Standard,
                               attacks=2,
                               stomach=Stomach(name="purple worm stomach",
                                               damage_type=[acid],
                                               damage=['6d6'],
                                               breakout_dmg=30,
                                               breakout_dc=21),
                               scores={'str': 28, 'dex': 7, 'con': 22,
                                       'int': 1, 'wis': 8, 'cha': 4},
                               saves={'con': 11, 'wis': 4},
                               melee_attacks={'basic': [
                                   MultiWeapon(name='bite', damage=["3d8+9"],
                                               damage_type=[piercing], reach=10,
                                               to_hit=9, uses_per_turn=1,
                                               special=[Swallow(name="swallow",
                                                                save="dex",
                                                                dc=19)]),
                                   MultiWeapon(name='tail stinger', damage=["3d6+9"],
                                               damage_type=[piercing], reach=10,
                                               to_hit=9, uses_per_turn=1,
                                               special=[Poison(name='poison stinger',
                                                               dc=19,
                                                               save='con',
                                                               damage=['12d6'],
                                                               damage_type=[poison],
                                                               success=0.5,
                                                               duration=None)])
                               ]})

    skeleton = BaseCreature(name='skeleton', cr=0.25, ac=13, hp=13, speed=30,
                            size=medium,
                            category=undead,
                            ai=behavior.Standard,
                            scores={'str': 10, 'dex': 14, 'con': 15,
                                    'int': 6, 'wis': 8, 'cha': 5},
                            immunities=[poison, paralysis, fear],
                            vulnerabilities=[bludgeoning],
                            melee_attacks={'basic':
                                               [Weapon(name='shortsword',
                                                       damage=["1d6+2"],
                                                       damage_type=[slashing],
                                                       reach=5,
                                                       to_hit=4)]},
                            ranged_attacks={'basic': [copy.deepcopy(shortbow)]})

    stone_giant = BaseCreature(name='stone giant', cr=7, ac=17, hp=126, speed=40,
                               size=large,
                               category=giant,
                               ai=behavior.Standard,
                               scores={'str': 23, 'dex': 15, 'con': 20,
                                       'int': 10, 'wis': 12, 'cha': 9},
                               saves={'str': 10},
                               attacks=2,
                               melee_attacks={'basic': [greatclub]},
                               actions=[])

    tarrasque = BaseCreature(name='tarrasque', cr=30, ac=25, hp=676, speed=40,
                             size=gargantuan,
                             category=monstrosity,
                             ai=behavior.Standard,
                             attacks=5,
                             # TODO: magic resistance
                             # TODO: legendary resistance
                             immunities=[fire, poison, bludgeoning, piercing,
                                         slashing, charm, paralysis, poison, fear],
                             stomach=Stomach(name="tarrasque stomach",
                                             damage_type=[acid],
                                             damage=['16d6'],
                                             breakout_dmg=60,
                                             breakout_dc=20),
                             scores={'str': 30, 'dex': 11, 'con': 30,
                                     'int': 3, 'wis': 11, 'cha': 11},
                             saves={'int': 5, 'wis': 9, 'cha': 9},
                             passives=[FrightfulPresence(name='Frightful Presence',
                                                         range=120,
                                                         duration=10,
                                                         dc=17,
                                                         save="wis")],
                             melee_attacks={'basic': [
                                 MultiWeapon(name='bite', damage=["4d12+10"],
                                             damage_type=[piercing], reach=10,
                                             to_hit=19, uses_per_turn=1,
                                             special=[Swallow(name="swallow",
                                                              save="str",
                                                              dc=20)]),
                                 MultiWeapon(name='claws', damage=["4d8+10"],
                                             damage_type=[slashing], reach=15,
                                             to_hit=19, uses_per_turn=2),
                                 MultiWeapon(name='horns', damage=["4d10+10"],
                                             damage_type=[piercing], reach=10,
                                             to_hit=19, uses_per_turn=1),
                                 MultiWeapon(name='tail', damage=["4d6+10"],
                                             damage_type=[bludgeoning], reach=20,
                                             to_hit=19, uses_per_turn=1,
                                             specials=[Knockdown(name="tail",
                                             dc=20,
                                             save='str')])
                             ]})

    troll = BaseCreature(name='troll', cr=5, ac=15, hp=84, speed=30,
                         size=large,
                         category=giant,
                         ai=behavior.Standard,
                         attacks=3,
                         dies_at=-1,
                         scores={'str': 18, 'dex': 13, 'con': 20,
                                 'int': 7, 'wis': 9, 'cha': 7},
                         melee_attacks={'basic': [troll_bite, troll_claws, troll_claws],
                                        },
                         passives=[AvoidDeath(name="Kill it with fire!",
                                              save='con',
                                              vulnerabilities=[acid, fire],
                                              minimum_hp=0,
                                              min_crit_to_kill=1000,
                                              penalty=-1000),
                                   Regeneration(name="Regeneration",
                                                amount=10,
                                                type_="initial")])

    wight = BaseCreature(name='wight', cr=3, ac=14, hp=45, speed=30,
                         size=medium,
                         category=undead,
                         ai=behavior.Standard,
                         attacks=2,
                         scores={'str': 15, 'dex': 14, 'con': 16,
                                 'int': 10, 'wis': 13, 'cha': 15},
                         immunities=[poison, paralysis, fear, charm],
                         resistances=[necrotic, bludgeoning, piercing, slashing],
                         melee_attacks={'basic':
                                            [wight_longsword,
                                             wight_longsword,
                                             wight_life_drain]},
                         ranged_attacks={'basic':
                                             [MultiWeapon(name='longbow',
                                                          damage=["1d8+2"],
                                                          damage_type=[piercing],
                                                          ranged=True,
                                                          ammo=20,
                                                          reach=150,
                                                          to_hit=11)]})

    wraith = BaseCreature(name='wraith', cr=5, ac=13, hp=67, speed=60,
                          size=medium,
                          category=undead,
                          ai=behavior.Standard,
                          attacks=1,
                          scores={'str': 6, 'dex': 16, 'con': 16,
                                  'int': 12, 'wis': 14, 'cha': 15},
                          immunities=[poison, necrotic, prone, paralysis, grapple,
                                      restrain, fear],
                          resistances=[acid, cold, fire, lightning, thunder,
                                       bludgeoning, piercing, slashing],
                          melee_attacks={'basic':
                                             [Weapon(name='life drain',
                                                     damage=["4d8+3"],
                                                     damage_type=[necrotic],
                                                     reach=5, to_hit=6,
                                                     special=[DamageMaxHP(name='life drain',
                                                                          dc=14,
                                                                          save='con')]
                                                     )]})

    wyvern = BaseCreature(name='wyvern', cr=6, ac=13, hp=110, speed=80,
                          size=large,
                          category=dragon,
                          ai=behavior.Standard,
                          attacks=2,
                          scores={'str': 19, 'dex': 10, 'con': 16,
                                  'int': 5, 'wis': 12, 'cha': 6},
                          melee_attacks={'basic':
                                             [wyvern_bite,
                                              wyvern_claws,
                                              wyvern_stinger]}
                          )

    zombie = BaseCreature(name='zombie', cr=0.25, ac=8, hp=22, speed=20,
                          ai=behavior.Standard,
                          size=medium,
                          category=undead,
                          scores={'str': 13, 'dex': 6, 'con': 16,
                                  'int': 3, 'wis': 6, 'cha': 5},
                          saves={'wis': 0},
                          immunities=[poison, paralysis, fear],
                          melee_attacks={'basic':
                                             [Weapon(name='slam',
                                                     damage=["1d6+1"],
                                                     damage_type=[bludgeoning],
                                                     reach=5,
                                                     to_hit=3)]
                                         },
                          passives=[AvoidDeath(name="Undead Fortitude",
                                               save='con',
                                               vulnerabilities=[radiant],
                                               minimum_hp=1)])

""" ================================================================ """
""" ================== PLAYER CHARACTERS =========================== """
""" ================================================================ """

""" Player weapons """
ognon_kirves = Weapon(name='greataxe +2',
                    damage=["1d10+1", "1d6+3"],
                    damage_type=[slashing_magic, fire],
                    reach=5,
                    to_hit=8)


class PlayerCharacters:

    ogno = BaseCreature(name='Ogno Pisam', cr=4, ac=18, hp=120, speed=40,
                        size=medium,
                        ai=behavior.Standard,
                        category=humanoid,
                        attacks=2,
                        resistances=[piercing, slashing, bludgeoning],
                        scores={'str': 18, 'dex': 16, 'con': 16,
                                'int': 12, 'wis': 14, 'cha': 10},
                        saves={'str': 8, 'dex': 3, 'con': 7,
                               'int': 1, 'wis': 1, 'cha': 0},
                        melee_attacks={'basic': [ognon_kirves]})
