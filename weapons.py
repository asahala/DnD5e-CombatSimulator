import dice
import messages
from mechanics import DnDRuleset as R

class Weapon(object):

    def __init__(self, name, damage, damage_type,
                 reach, to_hit, uses_per_turn=-1,
                 min_distance=0, ammo=0, ranged=False,
                 number_of_targets=1,
                 special=[], **kwargs):

        self.type = 'weapon'
        self.multiattack = False
        self.ammo = ammo
        self.min_distance = min_distance
        self.ranged = ranged
        self.name = name
        self.damage_print = damage
        self.damage = dice.parse_damage(damage)
        self.damage_type = damage_type
        self.reach = reach
        self.to_hit = to_hit
        self.number_of_targets = number_of_targets
        self.special = special
        self.max_uses_per_turn = uses_per_turn
        self.uses_per_turn = uses_per_turn

    def __repr__(self):
        dmg = []
        for i in range(0, len(self.damage)):
            dmg.append(self.damage_print[i] \
                       + " | (%s)" % self.damage_type[i] \
                       + " | %i ft. reach" % self.reach \
                       + " | %i ammo" % max(self.ammo, 0))
        return "{name}: {dmg}".format(name=self.name.capitalize(),
                                      dmg=", ".join(dmg))

    def use(self, source, target, always_hit=False):

        """ Roll d20 to hit """
        hit, crit_multiplier, hitroll = R.roll_hit(source, target, self, always_hit)

        """ Iterate all different damage types in weapon if successful """
        if hit:
            #total_damage = R.iterate_damage(source, target, self, crit_multiplier)
            total_damage = R.roll_damage(source, target, self, crit_multiplier)

            """ Apply weapon's special abilities on target unless the target is
            already dead """
            if self.special and not target.is_dead:
                for on_hit_effect in self.special:
                    on_hit_effect.use(source, target, total_damage, crit_multiplier)

class MultiWeapon(Weapon):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiattack = True
