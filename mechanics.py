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
    def roll_hit(source, target, attack, always_hit=False):
        """ Genera hit roller
        :param source     source of attack (creature object)
        :param target     target of attack (creature object)
        :param attack     ability or weapon (weapon or ability object) """

        messages.IO.reset()

        bonus = attack.to_hit
        attack_name = attack.name

        """ Check advantage conditions """
        if target.gives_advantage_to_attacker:
            source.set_advantage('hit', 1)

        """ Rollening's """
        advantage = source.advantage['hit']
        hitroll = dice.roll(1, 20, 0, advantage)

        """ Override hitroll if always_hit is true"""
        if always_hit:
            hitroll = target.ac + target.ac_bonus + 10
            advantage = 0

        """ Apply critical multiplier """
        multiplier = int(max(hitroll / 10, 1))

        """ Auto-crit if target is paralyzed """
        if target.is_paralyzed:
            hitroll = 20
            multiplier = 2

        critical_failure_effect = False

        """ Check if attack hits """
        if hitroll == 1:
            source.misses += 1
            hit = False
            # TODO: CRITICAL FAILURES
            roll = dice.roll(times=1, sides=3, bonus=0)
            if roll == 1:
                msg = "falls prone due to critical FAILURE attacking"
                critical_failure_effect = True
            else:
                msg = "FAILS critically attacking"
        elif hitroll == 20:
            hit = True
            msg = "lands a CRITICAL hit on"
            source.hits += 1
        elif hitroll + bonus > target.ac + target.ac_bonus:
            hit = True
            msg = "attacks"
            source.hits += 1
        else:
            hit = False
            msg = "misses"
            source.misses += 1

        if advantage == 1:
            adv = ' (adv.)'
        elif advantage == -1:
            adv = ' (disadv.)'
        else:
            adv = ''

        messages.IO.log += "{source} {hit} {target}"\
                  " with {attackname}{adv}.".format(source=source.name,
                                               target=target.name,
                                               attackname=attack_name.title(),
                                               hit=msg,
                                               adv=adv)

        if not hit:
            messages.IO.printlog()
            messages.IO.reset()

        """ Set critical failure effects """
        if critical_failure_effect:
            source.set_prone(True)
            source.take_damage(source, {'bludgeoning': dice.roll(1, 6, 0)}, 1)

        return hit, multiplier, hitroll + bonus

    @staticmethod
    def roll_save(target, ability, dc):
        """ Roll a save tied on ability against DC
        :type target       CreatureBaseClass
        :type ability      str
        :type dc           int

        A boolean is returned and the value is also written
        to the creature for more complex situations """

        bonus = target.saves[ability]
        advantage = target.advantage[ability]

        result = dice.roll(1, 20, bonus, advantage) >= int(dc)

        """ Auto-fails """
        if target.is_paralyzed and ability in ("str", "dex"):
            result = False

        target.save_success = result
        return result

    @staticmethod
    def iterate_damage_(source, target, weapon, crit_multiplier=1,
                       success=None, save=None, dc=None):

        """ Iterate all damage types in weapon and roll damage"""
        total = []
        for i in range(len(weapon.damage)):
            dmg = weapon.damage[i]
            dmg_type = weapon.damage_type[i]
            total.append(DnDRuleset.roll_damage(source, target, weapon, dmg,
                            dmg_type, crit_multiplier, success, save, dc))
        return sum(total)

    @staticmethod
    def roll_damage_(source, target, weapon, dmg, dmg_type, crit_multiplier=1,
                    success=None, save=None, dc=None):

        """ Parse damage as times, sides and bonus """
        times, sides, bonus = dmg
        damage = dice.roll(times*crit_multiplier, sides, bonus)

        """ If attack allows save, multiply damage with success multiplier
        in case target did not fail its save """
        if success is not None:
            if target.save_success:
                damage = int(damage * success)
                target.reset_save()

        """ Subtract damage from target's HP pool """
        return target.take_damage(source, damage, dmg_type, crit_multiplier)

    @staticmethod
    def roll_damage(source, target, weapon, crit_multiplier=1,
                    success=None, save=None, dc=None):

        damage_types = {}
        for i in range(len(weapon.damage)):
            t, s, b = weapon.damage[i]
            damage = dice.roll(t * crit_multiplier, s, b)
            dmg_type = weapon.damage_type[i]
            """ If attack allows save, multiply damage with success multiplier
            in case target did not fail its save """
            if success is not None:
                if target.save_success:
                    damage = int(damage * success)
                    target.reset_save()
            damage_types[dmg_type] = damage

        """ Subtract damage from target's HP pool """
        #return target.take_damage(source, damage, dmg_type, crit_multiplier)
        return target.take_damage(source, damage_types, crit_multiplier)

