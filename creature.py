#!/usr/bin/python
# -*- coding: utf-8 -*-

import operator
import time
from typing import Dict

import dice
import math
import random
import world
import messages
from mechanics import DnDRuleset as R

TOTALTIME = 0



class BaseCreature(object):

    """
    Mandatory parameters
    :param name               creature name
    :param size               creature size
    :param category           creature subcategory, e.g. giant or undead
    :param cr                 challenge rating
    :param ac                 armor class
    :param hc                 hitpoints
    :param speed              ground speed
    :param scores             ability scores
    :param melee_attacks      melee attacks

    Obligatory parameters
    :param ranged_attacks     ranged attacks
    :param attacks            number of attack actions
    :param dies_at            creature dies if hitpoints fall under this
    :param speed_fly          flying speed
    :param ai                 creature behavior class
    :param saves              customized saving throws
    :param resistances        damage type resistances
    :param immunities         damage and condition immunities
    :param vulnerabilities    damage type vulnerabilities

    Complex type descriptions
    :type scores              dict {'str': int, ... 'cha': int...}
    :type saves               dict {'str': int, ... 'cha': int...}
    :type ai                  any object from behavior module
    :type melee_attacks       dict {'basic': [Weapon object, ...], ...}
    :type ranged_attacks      as above. Allowed keys are 'basic' and
                              'special'. Creatures prefer latter.
    :type passives            list(Ability, ...) """

    def __init__(self, name: str, size: int, category: str,
                 cr: float, ac: int, hp: int, speed: int,
                 scores: dict, melee_attacks: dict, ai: object(),
                 attacks=1,
                 dies_at=0,
                 ranged_attacks={},
                 actions=[],
                 speed_fly=0,
                 saves=None,
                 passives=[],
                 resistances=[],
                 immunities=[],
                 vulnerabilities=[],
                 stomach=None):

        self.name = name.upper()  # Enumerated name, e.g. ´wolf 3´
        self.type = name  # Creature base-type, e.g. ´wolf´
        self.category = category
        self.size = size
        self.cr = cr
        self.ac = ac
        self.max_hp = hp
        self.hp = hp
        self.max_speed = {'ground': speed, 'fly': speed_fly}
        self.speed = {'ground': speed, 'fly': speed_fly}
        self.original_scores = scores
        self.scores = scores
        self.melee_attacks = melee_attacks
        self.ranged_attacks = ranged_attacks
        self.actions = actions
        self.dies_at = dies_at
        self.passives = passives
        self.resistances = resistances
        self.immunities = immunities
        self.vulnerabilities = vulnerabilities
        self.attacks = attacks
        self.ai = ai(self)

        self.ac_bonus = 0
        self.to_hit_bonus = 0
        self.initiative = 0
        self.focused_enemy = None  # Focused enemy (object)
        self.party = None  # Belongs to this party

        """ Combat statistics """
        self.damage_dealt = 0
        self.kills = 0
        self.deaths = 0
        self.suicides = 0
        self.hits = 0
        self.misses = 0
        self.turns_alive = 0

        """ Conditions: ´by´ = source of grapple, ´duration´ = poison
        duration in rounds, -1 is permanent """
        self.grappled = dict(state=False, dc=0, save="str", by=None)
        self.poisoned = dict(state=False, dc=0, save="con", duration=-1)
        self.paralyzed = dict(state=False, dc=0, save="con", duration=-1)
        self.restrained = dict(state=False, dc=0, save="str")
        self.frightened = dict(state=False, dc=0, save="str", duration=-1, by=None)
        self.swallowed = dict(state=False, by=None)
        self.prone = False
        self.prevent_heal = False

        """ Set advantage or disadvantage to hit, ability checks or 
        saves tied to certain ability scores """
        self.advantage = dict(hit=0, ability=0, str=0, dex=0,
                              con=0, int=0, wis=0, cha=0)

        """ Set saving throws. Override if listed in MM """
        self.saves = saves
        self.update_saves()

        """ Creature position in cartesian X, Y, Z Coordinates """
        self.position = (0, 0, 0)

        """ Movement tracker used for charge abilities """
        self.distance = 0

        """ Store which weapon is being used """
        self.active_weapon = None

        """ Turn specific flags and saving roll states """
        self.first_attack = True
        self.save_success = False

        """ Container for swallowed creatures """
        self.stomach = stomach

    def __repr__(self):
        CR = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}
        indentation = " " * (20 - len(self.name))
        # scores = ' | '.join(["%s %i" % (k.upper(), v) for k, v in self.scores.items()])
        # attacks = "\n{x}".format(x=20*" ").join([x.__repr__() for x in self.attacks])
        return "%s%sAC %i | HP %i | Init %i | CR %s | Speed %i" \
               % (self.name,
                  indentation,
                  self.ac,
                  self.hp,
                  self.initiative,
                  CR.get(self.cr, str(self.cr)),
                  self.speed['ground'])

    def __gt__(self, other):
        """ Compare creature strength """
        if self.speed['ground'] == other.speed['ground'] * 2 \
                and self.ranged_attacks and not other.ranged_attacs \
                and abs(self.cr - other.cr) <= 2:
            return True
        elif self.cr == other.cr * 3:
            return True
        else:
            return self.cr > other.cr

        # a = max(self.get_modifier('str') / other.ac, 0.05)
        # b = max(other.get_modifier('str') / self.ac, 0.05)

    def update_saves(self):
        """ Replace ability score based saving throws with fixed
         values given in Monster Manual"""
        if self.saves is None:
            self.saves = {k: self.get_modifier(v)
                          for k, v in self.scores.items()}
        else:
            for k, v in self.scores.items():
                v2 = self.saves.get(k, 0)
                self.saves[k] = max(self.get_modifier(v), v2)

    # ==================================================================
    # Creature conditions
    # ==================================================================

    @property
    def is_dead(self):
        """ Creature is dead if its HP is 0 or it has any negative
        ability scores """
        # if min([i for i in self.scores.values()]) <= 0:
        #    return True
        return self.hp <= self.dies_at

    @property
    def is_restrained(self):
        return self.restrained["state"]

    @property
    def is_proned(self):
        return self.prone

    @property
    def is_incapacitated(self):
        """ Conditions that prevent all actions except end turn
        saves """
        if self.paralyzed['state']:
            return True
        if self.hp < 0:
            return True
        return False

    @property
    def is_poisoned(self):
        return self.poisoned

    @property
    def is_paralyzed(self):
        return self.paralyzed["state"]

    @property
    def is_swallowed(self):
        return self.swallowed["state"]

    @property
    def is_frightened(self):
        return self.frightened["state"]

    @property
    def has_disadvantage(self):
        return any([self.is_proned,
                    self.is_restrained,
                    self.is_poisoned])

    @property
    def gives_advantage_to_attacker(self):
        return any([self.is_proned,
                    self.is_restrained,
                    self.is_paralyzed])

    def ___has_advantage_against(self, other):
        """ Return True if enemy is given advantage on hit rolls against
        the creature """
        return any([other.is_proned,
                    other.is_restrained,
                    other.is_poisoned])

    # ==================================================================
    # Creature condition setters
    # ==================================================================

    def set_swallowed(self, state, source=None):
        if state:
            world.Map.remove(self)
            self.position = source.position
            source.stomach.contents.append(self)
            messages.IO.printmsg("-> %s is swallowed by %s. " % (self.name, source.name), 2, True, False)
            self.speed['fly'] = 0
            self.speed['ground'] = 0
        else:
            messages.IO.printmsg("%s is regurgitated. " % self.name, 2, True, True)
            self.speed = self.max_speed.copy()
            self.set_prone(state=True)
        self.swallowed = {'state': state, 'by': source}

    def set_grapple(self, state, dc=0, save='str', source=None):
        if 'grapple' not in self.immunities:
            if state:
                messages.IO.printmsg("-> %s is grappled. " % self.name, 2, True, False)
                self.set_advantage('hit', -1)
                self.set_advantage('dex', -1)
                self.speed['fly'] = 0
                self.speed['ground'] = 0
            else:
                messages.IO.printmsg("%s frees from grapple. " % self.name, 2, True, True)
                self.set_advantage('hit', 0)
                self.set_advantage('dex', 0)
                self.speed = self.max_speed.copy()
            self.grappled = {'state': state, 'dc': dc, 'save': save, 'by': source}

    def set_restrain(self, state, dc=0, save='str'):
        if 'restrain' not in self.immunities:
            if state:
                messages.IO.printmsg("-> %s is restrained. " % self.name, 2, True, False)
                self.set_advantage('hit', -1)
                self.set_advantage('dex', -1)
                self.speed['ground'] = 0
                self.speed['fly'] = 0
            else:
                messages.IO.printmsg("%s frees from restrain. " % self.name, 2, True, False)
                self.set_advantage('hit', 0)
                self.set_advantage('dex', 0)
                self.speed = self.max_speed.copy()
            self.restrained["state"] = state
            self.restrained["dc"] = dc
            self.restrained["save"] = save

    def set_fear(self, state, by, dc=0, save='wis', duration=-1):
        if "fear" not in self.immunities:
            if state:
                self.set_advantage('hit', -1)
                self.set_advantage('dex', -1)
                self.set_advantage('str', -1)
                self.set_advantage('con', -1)
                self.set_advantage('int', -1)
                self.set_advantage('wis', -1)
                self.set_advantage('cha', -1)
                messages.IO.printmsg("-> %s is frightened. " % self.name, 2, True, False)
            else:
                messages.IO.printmsg("%s is no longer frightened. " % self.name, 2, True, True)
                self.set_advantage('hit', 0)
                self.set_advantage('dex', 0)
                self.set_advantage('str', 0)
                self.set_advantage('con', 0)
                self.set_advantage('int', 0)
                self.set_advantage('wis', 0)
                self.set_advantage('cha', 0)
            self.frightened["state"] = state
            self.frightened["dc"] = dc
            self.frightened["save"] = save
            self.frightened["duration"] = duration
            self.frightened["by"] = by

    def set_paralysis(self, state, dc=0, save='str', duration=-1):
        if "paralysis" not in self.immunities:
            if state:
                messages.IO.printmsg("-> %s is paralyzed. " % self.name, 2, True, False)
                self.speed['ground'] = 0
                self.speed['fly'] = 0
            else:
                messages.IO.printmsg("%s recovers from paralysis. " % self.name, 2, True, True)
                self.speed = self.max_speed.copy()
            self.paralyzed["state"] = state
            self.paralyzed["dc"] = dc
            self.paralyzed["save"] = save
            self.paralyzed["duration"] = duration

    def set_prone(self, state):
        if 'prone' not in self.immunities:
            if state:
                messages.IO.printmsg("-> %s falls prone. " % self.name, 2, True, False)
                self.set_advantage('hit', -1)
            else:
                messages.IO.printmsg("%s stands up. " % self.name, 2, True, True)
                self.set_advantage('hit', 0)
            self.prone = state

    def set_poison(self, state, dc=0, save='con', duration=-1):
        if 'poison' not in self.immunities:
            if state:
                messages.IO.printmsg("-> %s is poisoned. " % self.name, 2, True, False)
                self.set_advantage('hit', -1)
            else:
                self.set_advantage('hit', 0)
                messages.IO.printmsg("%s recovers from poison. " % self.name, 2, True, True)
            self.poisoned["state"] = state
            self.poisoned["dc"] = dc
            self.poisoned["save"] = save
            self.poisoned["duration"] = duration

    def set_advantage(self, category, state):
        """ Give advantage or disadvantage to a certain category
        :param category    hit, save, ability
        :param state       -1, 0, 1 """

        if state == -1:
            self.advantage[category] = \
                max(self.advantage[category] + state, state)
        elif state == 1:
            self.advantage[category] = \
                min(self.advantage[category] + state, state)
        else:
            self.advantage[category] = 0

    def get_modifier(self, ability):
        if isinstance(ability, int):
            return math.floor((ability - 10) / 2)
        return math.floor((self.scores[ability] - 10) / 2)

    def reset_save(self):
        """ Reset temporaray save flag, this is just to make poisoned
        attacks work properly. This should be simplified in the future """
        self.save_success = False

    def begin_turn(self):
        """ At the beginning of each turn, perform a list of
        actions such as standing up, recharging abilities etc.
        Return True if creature did not use its action """
        self.distance = 0                    # reset traveled distance
        self.speed = self.max_speed.copy()   # reset movement speed
        self.first_attack = True             # reset first attack flag

        if self.is_poisoned:
            self.poisoned['duration'] -= 1
        if self.is_poisoned['duration'] == 0:
            self.set_poison(state=False, dc=0, save='con', duration=-1)

        """ If swallowed creatures, do damage and check conditions """
        if self.stomach is not None:
            if self.stomach.contents:
                self.stomach.check_status(self)

        """ Recharge abilities """
        if self.actions:
            for action in self.actions:
                action.check_and_recharge()

        """ Stand up if prone """
        if self.is_proned:
            self.set_prone(state=False)
            self.speed['fly'] = math.floor(self.speed['fly'] / 2)
            self.speed['ground'] = math.floor(self.speed['ground'] / 2)

        if self.is_swallowed:
            self.position = self.swallowed['by'].position
            self.speed['fly'] = 0
            self.speed['ground'] = 0

        """ Free from grapple if grappler has died """
        if self.grappled["state"]:
            self.speed['fly'] = 0
            self.speed['ground'] = 0
            if self.grappled["by"].is_dead:
                self.set_grapple(state=False, dc=0, save='str', source=None)
            else:
                dc = self.grappled["dc"]
                ability = self.grappled["save"]
                if R.roll_save(self, ability, dc):
                    self.set_grapple(state=False, dc=0, save=None)
                    return False

        if self.paralyzed["state"]:
            self.speed['fly'] = 0
            self.speed['ground'] = 0

        if self.restrained["state"]:
            self.speed['fly'] = 0
            self.speed['ground'] = 0
            dc = self.restrained["dc"]
            ability = self.restrained['save']
            if R.roll_save(self, ability, dc):
                self.set_restrain(state=False, dc=0, save=None)
                return False
        return True

    def end_turn(self):
        """ Reroll save against paralysis  """
        if self.is_paralyzed:
            dc = self.paralyzed["dc"]
            ability = self.paralyzed['save']
            if R.roll_save(self, ability, dc) or self.paralyzed['duration'] == 0:
                self.set_paralysis(state=False, dc=0, save=None, duration=-1)

        if self.is_frightened:
            dc = self.frightened["dc"]
            ability = self.frightened['save']
            if R.roll_save(self, ability, dc) or self.frightened['duration'] == 0:
                self.set_fear(state=False, dc=0, save=None, duration=-1, by=None)

        """ Decrease paralysis duration counter """
        self.paralyzed['duration'] -= 1
        self.frightened['duration'] -= 1

        """ Set first attack flag in case creature can make attacks
        of opportunity """
        self.first_attack = True

    def heal(self, amount, spellname):
        if not self.prevent_heal:
            self.hp += amount
            if self.hp > self.max_hp:
                self.hp = self.max_hp
            messages.IO.printmsg("%s heals %i hitpoints from %s." \
                                 % (self.name, amount, spellname), 2, True, True)

    def take_max_hp_damage(self, source, amount, spellname):
        self.max_hp -= amount
        messages.IO.printmsg("-> %s loses %i max hitpoints from %s." \
                             % (self.name, amount, spellname), 2, True, False)

    def take_damage_(self, source, damage, dmg_type, crit_multiplier):

        """ Check if creature has vulnerability, resistance or immunity
            to the given damage type """
        damage = self.check_resistances(dmg_type, damage)
        damage = self.check_vulnerabilities(dmg_type, damage)

        """ Store damage statistics """
        source.damage_dealt += damage

        self.hp -= damage

        """ Check if creature can drop to 1 HP instead of 0 """
        if self.hp <= 0 and self.passives:
            for passive in self.passives:
                if passive.type == 'avoid_death':
                    self.hp = passive.use(self, damage, dmg_type, crit_multiplier)

        #messages.IO.total_damage.setdefault(dmg_type, 0)
        #messages.IO.total_damage[dmg_type] += damage
        #messages.IO.hp = self.hp
        #messages.IO.target_name = self.name
        #messages.IO.printlog()

        messages.IO.printmsg(source.name + ' does ' + str(damage) + " " + dmg_type + " to " + self.name, 2, True, True)

        if self.is_dead:
            self.deaths += 1
            if source != self:
                source.kills += 1
            else:
                self.suicides += 1
            messages.IO.printmsg("-> %s is dead. " % self.name, 2, True, False)
            world.Map.remove(self)
            world.Map.statics[self.position] = ' † '

        if self.is_swallowed:
            self.swallowed['by'].stomach.damage_count += damage

        """ Return damage in case it's needed for special on-hit effects """
        return damage

    def take_damage(self, source, damage_types, crit_multiplier):

        """ Check if creature has vulnerability, resistance or immunity
            to the given damage type """

        for dmg_type, damage in damage_types.items():
            damage = self.check_resistances(dmg_type, damage)
            damage = self.check_vulnerabilities(dmg_type, damage)

            """ Store damage statistics """
            source.damage_dealt += damage

            self.hp -= damage

            """ Check if creature can drop to 1 HP instead of 0 """
            if self.hp <= 0 and self.passives:
                for passive in self.passives:
                    if passive.type == 'avoid_death':
                        self.hp = passive.use(self, damage, dmg_type, crit_multiplier)

            messages.IO.total_damage.setdefault(dmg_type, 0)
            messages.IO.total_damage[dmg_type] += damage
        messages.IO.hp = self.hp
        messages.IO.target_name = self.name
        messages.IO.printlog()

        if self.is_dead:
            self.deaths += 1
            if source != self:
                source.kills += 1
            else:
                self.suicides += 1
            messages.IO.printmsg("-> %s is dead. " % self.name, 2, True, False)
            world.Map.remove(self)
            world.Map.statics[self.position] = ' † '

        if self.is_swallowed:
            self.swallowed['by'].stomach.damage_count += damage

        """ Return damage in case it's needed for special on-hit effects """
        return damage_types

    def roll_initiative(self):
        """ Roll initiative for the creature, add decimals based
        on dexterity score and challenge rating to resolve equal rolls """
        dex = self.scores['dex'] / 100
        cr = self.cr / 1000
        dex_mod = self.get_modifier('dex')
        self.initiative = dice.roll(1, 20, dex_mod) + dex + cr

    def check_resistances(self, damage_type, damage):
        """ Strip save DC info from damage_type """
        if damage_type in self.resistances:
            damage = math.floor(damage / 2)
        if damage_type in self.immunities:
            damage = 0
        return damage

    def check_vulnerabilities(self, damage_type, damage):
        """ Strip save DC info from damage_type """
        if damage_type in self.vulnerabilities:
            return damage * 2
        return damage

    def take_ability_score_damage(self, ability_score, damage):
        self.scores[ability_score] -= damage
        ## TODO: Adjust AC, damage and hit

    def set_focus____444_(self, enemies):
        """ Set focus to some enemy and keep it unless the target dies """


        if self.focused_enemy is None:
            self.focused_enemy = enemies.get_weakest()
        elif self.focused_enemy.is_dead:
            self.focused_enemy = enemies.get_weakest()



    def check_passives(self, allies, enemies, type_=None):
        """ Check passive skills """
        if self.passives:
            for passive in self.passives:
                if passive.type == type_:
                    passive.use(self, allies, enemies)

    def attack(self):
        """ Set focus on enemy and attack it """

        self.active_weapon.use(self, self.focused_enemy)
        self.active_weapon.ammo -= 1
        self.first_attack = False
        if self.active_weapon.multiattack:
            self.active_weapon.uses_per_turn -= 1
        '''
        if self.melee_attacks or self.ranged_attacks:
            attacks = self.select_weapon(enemies)
            if isinstance(attacks, Weapon):
                attacks = [attacks]
            for attack in attacks:
                """ Always set new focus in case the enemy dies """
                self.set_focus(enemies)
                if self.focused_enemy is not None:
                    """ Do not attack or move if there are no enemies left """
                    at_range = self.move(self.focused_enemy, attack)
                    if at_range:
                        attack.use(self, self.focused_enemy)
                        attack.ammo -= 1'''

    def move(self):

        """ If creature has ran, it cannot perform further actions"""

        A = self.position
        B = self.focused_enemy.position
        distance = world.get_dist(A, B)

        enemy = self.focused_enemy
        weapon = self.active_weapon

        if self.is_swallowed:
            return True

        if distance > weapon.reach:
            """ If not at reach, close distance """
            path = world.get_path(A, B)
            if distance > self.speed['ground'] + weapon.reach:
                """ Run if can't get to range by moving regularly. 
                Return False as action points spent on moving  """
                points, new_pos = world.close_distance(self, path, weapon.reach, run=True)
                return False
            else:
                points, new_pos = world.close_distance(self, path, weapon.reach)
        elif distance < weapon.reach and weapon.ranged:
            """ If using ranged weapon, keep distance """
            path = world.get_opposite(A, B, self.speed['ground'])
            points, new_pos = world.keep_distance(self, enemy, path, weapon.reach)

        if self.speed['ground'] < 0:
            return False

        return world.get_dist(self.position, B) <= weapon.reach

    def choose_target(self, enemies, choice=None):
        """ Set focus to some enemy and keep it unless the target dies;
        lower intelligence results to simpler decisions """
        if choice is None:
            if self.scores['int'] <= 4:
                choice = enemies.get_closest(self.position)
            else:
                choice = enemies.get_weakest()

        if self.is_swallowed:
            self.focused_enemy = self.swallowed['by']
        elif self.focused_enemy is None:
            self.focused_enemy = choice
        elif self.focused_enemy.is_dead:
            self.focused_enemy = choice

    def choose_weapon(self, enemies, weapons=None):
        # TODO optimize for big encounters, just check surroundings
        # TODO rewrite this method
        """ Check if enemies are too close, pick melee weapon if so """

        distance_to_target = world.get_dist(self.position,
                                            self.focused_enemy.position)

        def has_ammo(weapons):
            if weapons is None:
                return None

            w = [attack for attack in weapons if attack.ammo > 0]
            if not w:
                return None
            return w

        def has_min_range(weapons):
            if weapons is None:
                return None

            w = [attack for attack in weapons if attack.min_distance <= distance_to_target]
            if not w:
                return None
            return w

        """ Pick melee weapon if enemy too close """
        enemy_positions = (e.position for e in enemies.get_alive())
        if world.any_is_adjacent(self.position, enemy_positions):
            weapons = has_min_range(self.melee_attacks.get('special',
                            self.melee_attacks.get('basic', None)))

        """ General weapon selector; prioritize ranged -> melee and
        special -> basic """
        if self.ranged_attacks and weapons is None and not self.is_swallowed:
            weapons = has_ammo(self.ranged_attacks.get('special',
                                self.ranged_attacks.get('basic', None)))

        if weapons is None and self.melee_attacks:
            weapons = has_min_range(self.melee_attacks.get('special', None))
            if weapons is None:
                weapons = has_min_range(self.melee_attacks.get('basic', None))

        if weapons is None or not weapons:
            weapons = self.melee_attacks

        """ Reset multiattacks and limited at the start of the combat round"""
        if self.first_attack:
            for weapon in weapons:
                weapon.uses_per_turn = weapon.max_uses_per_turn

        self.active_weapon = random.choice([w for w in weapons if w.uses_per_turn != 0])

    def act(self, allies, enemies):
        """ Routine for actions that utilizes given behavior class """
        world.Map.remove(self)
        self.check_passives(allies, enemies, type_="initial")
        if not self.is_dead and not self.is_incapacitated:
            self.turns_alive += 1
            if self.begin_turn():
                self.check_passives(allies, enemies, type_="on_start")
                for i in range(self.attacks):
                    if enemies.is_alive:
                        self.ai.do_stuff(allies, enemies)

        self.check_passives(allies, enemies, type_="at_end")
        self.end_turn()
        world.Map.update(self)


class Party:

    def __init__(self, name):
        self.name = name
        self.members = []

    def __repr__(self):
        return messages.IO.center_and_pad(self.name) + '\n' \
               + '\n'.join([c.__repr__() for c in self.members]) + '\n'

    def __add__(self, other):
        return self.members + other.members

    @property
    def hp(self):
        """ Party's total hitpoints """
        return [c.hp for c in self.members]

    @property
    def is_alive(self):
        """ Return True if any party member is alive """
        return False in [c.is_dead for c in self.members]

    @staticmethod
    def remove_dead(party):
        return [c for c in party if not c.is_dead and not c.is_swallowed]

    def get_alive(self):
        return (c for c in self.members if not c.is_dead)

    def add(self, creature):
        """ Add party members and roll initiatives, the party is
         ordered by initiative """
        creature.roll_initiative()
        creature.party = self.name

        """ Add number after creature name if the party has already 
        similar creature types """
        count = len([c.type for c in self.members if c.type == creature.type])
        if count >= 1:
            creature.name = "%s %i" % (creature.name, count + 1)

        self.members.append(creature)
        self.sort_by('initiative')

    def get_weakest(self):
        """ Pick weakest creature (HP-wise)
        :rtype BaseCreature or None """
        weakest = sorted(self.remove_dead(self.members),
                         key=operator.attrgetter('hp'),
                         reverse=False)[0]
        if weakest:
            return weakest
        return None

    def get_closest(self, B):
        """ Pick closest enemy to position ´B´
        :rtype BaseCreature or None """
        try:
            closest = min([(world.get_dist(x.position, B), x)
                           for x in self.remove_dead(self.members)],
                          key=operator.itemgetter(0))[-1]
        except ValueError:
            return None

        if closest:
            return closest
        return None

    def get_teams(self, other, creature):
        """ :type other Party
            :type creature BaseCreature
            :rtype (Party, Party) """
        if creature in self.members:
            return self, other
        else:
            return other, self

    def combine_and_sort_by(self, other, value="name", strongest_first=True):
        """ Reorder party by given creature variable """
        all_creatures = self.members + other.members
        return sorted(all_creatures,
                      key=operator.attrgetter(value),
                      reverse=strongest_first)

    def sort_by(self, value="name", strongest_first=True):
        """ Reorder party by given creature variable """
        self.members.sort(key=operator.attrgetter(value),
                          reverse=strongest_first)

    def set_formation(self, position):
        """ Sets party in formation near given coordinates """
        x, y, z = position
        i = 1
        for creature in self.members:
            j = dice.roll(1, 2, -1)
            if i % 2 == 0:
                k = -i
            else:
                k = i
            creature.position = (x + k, y + j, z)
            world.Map.update(creature)
            i += 1