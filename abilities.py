
import dice
from messages import IO

class Ability:

    """ Base class for special creature actions and abilities """

    def __init__(self, name, dc, save, to_hit, recharge=0, **kwargs):
        self.name = name
        self.dc = dc
        self.save = save
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

    def use(self, creature, enemy):
        if creature.roll_hit(self.to_hit, enemy.ac):
            enemy.set_restrain(True, self.dc, self.save)
        self.available = False


class Gore(Ability):

    def __init__(self, damage, damage_type, **kwargs):
        super().__init__(**kwargs)
        self.damage = dice.parse_damage(damage)
        self.damage_type = damage_type

    def use(self, creature, enemy):
        if creature.roll_hit(self.to_hit, enemy.ac):
            #self.apply_damage(self.damage, self.damage_type, enemy)
            enemy.set_prone(True)


class PackTactics:

    """ Pack tactics gives and advantage to hit rolls if
    creatures of similar type are nearby """

    @staticmethod
    def use(creature, allies, enemies):
        if len([c.type for c in allies.members
                if c.type == creature.type]) > 1:
            pass

    
    