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
    def roll_hit(source, target, attack):
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

        advantage = source.advantage['hit']
        hitroll = dice.roll(1, 20, 0, advantage)
            
        """ Apply critical multiplier """
        multiplier = int(max(hitroll / 10, 1))

        """ Auto-crit if target is paralyzed """
        if target.is_paralyzed:
            hitroll = 20
            multiplier = 2


        critical_failure_effect = False

        """ Check if attack hits """
        if hitroll == 1:
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
        elif hitroll + bonus > target.ac + target.ac_bonus:
            hit = True
            msg = "attacks"
        else:
            hit = False
            msg = "misses"

        if advantage == 1:
            adv = ' (adv.)'
        elif advantage == -1:
            adv = ' (disadv.)'
        else:
            adv = ''

        messages.IO.log += "{source} {hit} {target}"\
                  " with {attackname}{adv}.".format(source=source.name,
                                               target=target.name,
                                               attackname=attack_name,
                                               hit=msg,
                                               adv=adv)

        if not hit:
            messages.IO.printlog()
            messages.IO.reset()

        """ Set critical failure effects """
        if critical_failure_effect:
            source.set_prone(True)
            source.take_damage(source, 4, 'bludgeoning', 1)

        return hit, multiplier, hitroll + bonus

    @staticmethod
    def roll_save(target, ability, dc) -> bool:
        """ Roll a save tied on ability against DC
        :type target       CreatureBaseClass
        :type ability      str
        :type dc           int """

        bonus = target.saves[ability]
        advantage = target.advantage[ability]

        """ Auto-fails """
        if target.is_paralyzed and ability in ("str", "dex"):
            return False

        return dice.roll(1, 20, bonus, advantage) >= int(dc)

    @staticmethod
    def iterate_damage(source, target, weapon, crit_multiplier=1):
        """ Iterate all damage types in weapon or ability and roll
        damages """
        for i in range(len(weapon.damage)):
            dmg = weapon.damage[i]
            dmg_type = weapon.damage_type[i]
            DnDRuleset.roll_damage(source, target, weapon, dmg, dmg_type, crit_multiplier)


    @staticmethod
    def roll_damage(source, target, weapon, dmg, dmg_type, crit_multiplier=1):

        """ Parse damage as times, sides and bonus """
        times, sides, bonus = dmg
        damage = dice.roll(times*crit_multiplier, sides, bonus)

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
        #damage = target.check_resistances(dmg_type, damage)

        """ Check vulnerabilities """
        #damage = target.check_vulnerabilities(dmg_type, damage)

        """ Store damage statistics """
        #source.damage_dealt += damage

        """ Subtract damage from target's HP pool """
        target.take_damage(source, damage, dmg_type, crit_multiplier)


