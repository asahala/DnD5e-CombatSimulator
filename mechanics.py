#!/usr/bin/python
# -*- coding: utf-8 -*-

import dice
import math
import re
import messages


class Movement:

    def __init__(self, x=0, y=0):
        pass

class DnDRuleset:

    @staticmethod
    def parse_damage_type(damage_type):
        """ Parse damage types such as poison(DC:con:0.5:11) that
         contain, type, saving throw, damage multiplier if
         successful and DC  """
        dmg_type = re.sub("\(.+$", "", damage_type)
        return re.sub('.*\((.+)\).*', r'\1', damage_type).split(':') + [dmg_type]

    @staticmethod
    def roll_hit(source, target, attack):
        """ Genera hit roller
        :param source     source of attack (creature object)
        :param target     target of attack (creature object)
        :param attack     ability or weapon (weapon or ability object) """

        messages.IO.reset()

        bonus = attack.to_hit
        attack_name = attack.name

        """ Check advantage conditions """
        advantage = source.advantage['hit']
        hitroll = dice.roll(1, 20, 0, advantage)
            
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

        messages.IO.log += "{source} {hit} {target}"\
                  " with {attackname}.".format(source=source.name,
                                               #sourceteam=source.party,
                                               target=target.name,
                                               #targetteam=target.party,
                                               attackname=attack_name,
                                               hit=msg)

        if not hit:
            messages.IO.printlog()
            messages.IO.reset()

        return hit, multiplier, hitroll + bonus

    @staticmethod
    def roll_save(target, ability, dc):
        """ Return True if save is successful"""
        bonus = target.saves[ability]
        advantage = target.advantage[ability]
        return dice.roll(1, 20, bonus, advantage) >= int(dc)

    @staticmethod
    def iterate_damage(source, target, weapon, crit_multiplier=1):
        """ Iterate all damage types in weapon or ability and roll
        damages """
        for i in range(len(weapon.damage)):
            dmg = weapon.damage[i]
            dmg_type = weapon.damage_type[i]
            DnDRuleset.roll_damage(source, target, weapon, dmg, dmg_type, crit_multiplier)
        messages.IO.printlog()

    @staticmethod
    def roll_damage(source, target, weapon, dmg, dmg_type, crit_multiplier=1):

        """ Parse damage as times, sides and bonus """
        times, sides, bonus = dmg
        damage = dice.roll(times*crit_multiplier, sides, bonus)

        """ Check if there's save against the damage """

        if weapon.type == 'ability':
            if weapon.save is not None:
                """ Scale damage with a given factor if successful save """
                if DnDRuleset.roll_save(target, weapon.save, weapon.dc):
                   damage = math.floor(float(weapon.success) * damage)
                else:
                    """ Special conditions for damage types """
                    weapon.apply_condition(target)

        """ Check if target has resistance or immunity to 
        the given damage type """
        damage = target.check_resistances(dmg_type, damage)

        """ Store damage statistics """
        source.damage_dealt += damage

        """ Subtract damage from target's HP pool """
        target.hp -= damage

        messages.IO.total_damage.setdefault(dmg_type, 0)
        messages.IO.total_damage[dmg_type] += damage
        messages.IO.hp = target.hp
        messages.IO.target_name = target.name


