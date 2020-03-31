
import dice
import messages
import world
from mechanics import DnDRuleset as R

class Ability:

    """ Base class for special creature actions and abilities

    :param name              ability name
    :param dc                save DC
    :param save              ability score tied to this save
    :param to-hit            to hit bonus
    :param success           damage multiplier if successful save
    :param recharge          recharge value

    :type name               str
    :type dc                 int
    :type save               str
    :type to-hit             int
    :type success            float
    :type recharge           int """

    def __init__(self, name, dc=None, save=None, to_hit=None,
                 success=None, recharge=0, **kwargs):
        self.type = 'ability'
        self.name = name
        self.dc = dc
        self.save = save
        self.success = success
        self.to_hit = to_hit
        self.recharge = recharge
        self.available = True

    def __repr__(self):
        return "%s (DC: %i) " % (self.name, self.dc)

    def check_and_recharge(self):
        if not self.available:
            if dice.roll(1, 6, 0) >= self.recharge:
                self.available = True


class Restrain(Ability):

    def use(self, source, target):
        if R.roll_hit(source, target, self):
            target.set_restrain(True, self.dc, self.save)
        self.available = False


class Paralysis(Ability):

    def use(self, source, target):
        if not R.roll_save(target, self.save, self.dc):
            target.set_paralysis(True, self.dc, self.save)


class Grapple(Ability):

    def use(self, source, target):
        if not R.roll_save(target, self.save, self.dc):
            target.set_grapple(True, self.dc, self.save, source)


class Knockdown(Ability):

    def __init__(self, bonus_action=None, charge_distance=0, **kwargs):
        super().__init__(**kwargs)
        self.bonus_action = bonus_action
        self.charge_distance = charge_distance

    def use(self, source, target):
        if source.distance > self.charge_distance:
            if not R.roll_save(target, self.save, self.dc):
                target.set_prone(True)
                if self.bonus_action is not None:
                    self.bonus_action.use(source, target, always_hit=False)
                    source.distance = 0


class Poison(Ability):

    def __init__(self, damage, damage_type, **kwargs):
        super().__init__(**kwargs)
        self.damage = dice.parse_damage(damage)
        self.damage_type = damage_type

    def use(self, source, target):
        R.iterate_damage(source, target, self)

    def apply_condition(self, target):
        target.set_poison(state=True, dc=self.dc, save=self.save)


class AvoidDeath:

    """ Avoid death allows creatures to drop to N hitpoints instead
    of zero if it succeeds a save against the damage, e.g. Undead
    Fortitude

    :param name                 ability name
    :param penalty              penalty to saving throw
    :param save                 ability tied to save
    :param minimum_hp           amount of remaining hp if successful

    :type name                 str
    :type penalty              int
    :type save                 str
    :type minimum_hp           int """

    def __init__(self, name, save, minimum_hp, penalty=0):
        self.name = name
        self.penalty = penalty
        self.type = 'avoid_death'
        self.save = save
        self.minimum_hp = minimum_hp

    def use(self, creature, damage, damage_type, critical):
        if critical > 1 or damage_type == 'radiant':
            return creature.hp
        else:
            if R.roll_save(creature, self.save, damage+self.penalty):
                messages.IO.conditions.append('%s resists death with %s!' % (creature.name, self.name))
                return self.minimum_hp
        return creature.hp


class PackTactics:

    """ Pack tactics gives and advantage to hit rolls if
    adjacent squares contain allies  """

    type = 'on_start'

    @staticmethod
    def use(creature, allies, enemies=[]):

        ally_positions = (a.position for a in allies.get_alive()
                    if a.position != creature.position)
        if world.any_is_adjacent(creature.position, ally_positions):
            creature.set_advantage('hit', 1)
        else:
            creature.set_advantage('hit', 0)