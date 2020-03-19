#!/usr/bin/python
# -*- coding: utf-8 -*-

import dice
import math
import re

class DnDRuleset:

    @staticmethod
    def parse_damage_type(damage_type):
        """ Parse damage types such as poison(DC:con:0.5:11) that
         contain, type, saving throw, damage multiplier if
         successful and DC  """
        dmg_type = re.sub("\(.+$", "", damage_type)
        return re.sub('.*\((.+)\).*', r'\1', damage_type).split(':') + [dmg_type]

    @staticmethod
    def roll_hit(source, target, bonus, attack_name):
        """ Check advantage conditions """
        if source.has_advantage_against(target):
            hitroll = dice.roll_advantage(1, 20, 0)
        elif source.has_disadvantage:
            hitroll = dice.roll_disadvantage(1, 20, 0)
        else:
            hitroll = dice.roll(1, 20, 0)
            
        """ Apply critical multiplier """
        multiplier = int(max(hitroll / 10, 1))

        """ Check if attack hits """
        if hitroll == 1:
            hit = False
            msg = "fails critically attacking"
        elif hitroll == 20:
            hit = True
            msg = "lands a CRITICAL hit on"
        elif hitroll + bonus > target.ac + target.ac_bonus:
            hit = True
            msg = "attacks"
        else:
            hit = False
            msg = "misses"

        message = "{source} ({sourceteam}) {hit} {target} ({targetteam})"\
                  " with {attackname}"\
                    .format(source=source.name, sourceteam=source.party,
                    target=target.name, targetteam=target.party,
                    attackname=attack_name, hit=msg)

        return hit, multiplier, hitroll + bonus, message

    @staticmethod
    def roll_save(creature, ability, dc):
        """ Return True if save is successful"""
        bonus = creature.get_modifier(ability)
        return dice.roll(1, 20, bonus) >= int(dc)

    @staticmethod
    def roll_damage(source, target, dmg, dmg_type, crit_multiplier):

        """ Parse damage as times, sides and bonus """
        times, sides, bonus = dmg
        damage = dice.roll(times*crit_multiplier, sides, bonus)

        """ Check if there's save against the damage """
        if 'DC' in dmg_type:
            _, ability, multiplier, dc, dmg_type =\
                Ruleset.parse_damage_type(dmg_type)
            """ Saving throw, scale damage if success """
            if Ruleset.roll_save(target, ability, dc):
                damage = math.floor(float(multiplier) * damage)
            else:
                """ Special conditions for damage types """
                if dmg_type.startswith('poison'):
                    target.set_poison(True)

        """ Check if target has resistance or immunity to 
        the given damage type """
        damage = target.check_resistances(dmg_type, damage)

        """ Store damage statistics """
        source.damage_dealt += damage

        """ Subtract damage from target's HP pool """
        target.hp -= damage

        return "%i %s" % (damage, dmg_type)