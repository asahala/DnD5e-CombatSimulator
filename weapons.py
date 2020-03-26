import dice
from mechanics import DnDRuleset as R
from messages import IO

"""
Weapon class

    name
    damage
    damage_type
    reach
    to_hit
    number_of_targets
    on_it_special           OBJ

"""

class Weapon(object):

    def __init__(self, name, damage, damage_type,
                 reach, to_hit, ammo=0, ranged=False, number_of_targets=1,
                 special=[]):

        self.type = 'weapon'
        self.ammo = ammo
        self.ranged = ranged
        self.name = name
        self.damage_print = damage
        self.damage = dice.parse_damage(damage)
        self.damage_type = damage_type
        self.reach = reach
        self.to_hit = to_hit
        self.number_of_targets = number_of_targets
        self.special = special

    def __repr__(self):
        dmg = []
        for i in range(0, len(self.damage)):
            dmg.append(self.damage_print[i] \
                       + " (%s)" % self.damage_type[i] \
                       + " %i ft. reach" % self.reach)
        return "{name}: {dmg}".format(name=self.name.capitalize(),
                                      dmg=", ".join(dmg))

    def apply_condition(self):
        pass

    def use(self, source, target, always_hit=False):

        """ Roll d20 to hit """
        hit, crit_multiplier, hitroll = R.roll_hit(source, target, self)

        """ Iterate all different damage types in weapon if successful """
        if hit or always_hit:
            R.iterate_damage(source, target, self, crit_multiplier)

            """ Apply weapon's special abilities on target"""
            if self.special:
                for on_hit_effect in self.special:
                    on_hit_effect.use(source, target)