import dice
from mechanics import DnDRuleset as R
from messages import IO

class Weapon(object):

    def __init__(self, name, damage, damage_type,
                 reach, to_hit, number_of_targets=1):
        self.name = name
        self.damage_print = damage
        self.damage = dice.parse_damage(damage)
        self.damage_type = damage_type
        self.reach = reach
        self.to_hit = to_hit
        self.number_of_targets = number_of_targets

    def __repr__(self):
        dmg = []
        for i in range(0, len(self.damage)):
            dmg.append(self.damage_print[i] \
                       + " (%s)" % self.damage_type[i] \
                       + " %i ft. reach" % self.reach)
        return "{name}: {dmg}".format(name=self.name.capitalize(),
                                      dmg=", ".join(dmg))

    def use(self, source, target):
        hit, crit_multiplier, hitroll, message \
            = R.roll_hit(source, target, self.to_hit, self.name)

        """ Iterate all different damage types in weapon if hit """
        total_damage = []
        if hit:
            for i in range(len(self.damage)):
                dmg = self.damage[i]
                dmg_type = self.damage_type[i]
                """ Store total damage """
                total_damage.append(
                    R.roll_damage(source ,target, dmg, dmg_type, crit_multiplier))


            if target.hp <= -target.max_hp:
                source.kills += 1
                msg = ". Target turns into bloody pulp!"
            elif target.hp <= 0:
                source.kills += 1
                msg = ". Target dies!"
            else:
                msg = "."

            message += ": does " + " and ".join(total_damage) \
                       + " damage" + msg + " (%i HP remaining)." % target.hp

        IO.printmsg(message, 2, indent=True, print_turn=True)