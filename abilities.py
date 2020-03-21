
import dice
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
        super().__init__(**kwargs)

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


class Knockdown(Ability):

    def use(self, source, target):
        if not R.roll_save(target, self.save, self.dc):
            target.set_prone(True)


class Poison(Ability):

    def __init__(self, damage, damage_type, **kwargs):
        super().__init__(**kwargs)
        self.damage = dice.parse_damage(damage)
        self.damage_type = damage_type

    def use(self, source, target):
        R.iterate_damage(source, target, self)

    def apply_condition(self, target):
        target.set_poison(state=True, dc=self.dc, save=self.save)


class Gore(Ability):

    def __init__(self, damage, damage_type, **kwargs):
        super().__init__(**kwargs)
        self.damage = dice.parse_damage(damage)
        self.damage_type = damage_type

    def use(self, source, target):
        if source.roll_hit(self.to_hit, target.ac):
            #self.apply_damage(self.damage, self.damage_type, enemy)
            target.set_prone(True)


class PackTactics:

    """ Pack tactics gives and advantage to hit rolls if
    creatures of similar type are alive and nearby """

    @staticmethod
    def use(creature, allies, enemies=[]):
        if len([c.type for c in allies.members
                if c.type == creature.type and not c.is_dead]) > 1:
            creature.set_advantage('hit', 1)

    
    