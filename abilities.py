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

    def __init__(self, name, type_='ability', dc=None, save=None, to_hit=None,
                 success=None, recharge=0, **kwargs):
        self.type = type_
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

    def use(self, source, target, total_damage=0, crit_multipiler=1):
        if R.roll_hit(source, target, self):
            target.set_restrain(True, self.dc, self.save)
        self.available = False


class Paralysis(Ability):

    def use(self, source, target, total_damage=0, crit_multipiler=1):
        if not R.roll_save(target, self.save, self.dc):
            target.set_paralysis(True, self.dc, self.save)


class Grapple(Ability):

    def use(self, source, target, total_damage=0, crit_multipiler=1):
        if not R.roll_save(target, self.save, self.dc):
            target.set_grapple(True, self.dc, self.save, source)


class Knockdown(Ability):

    def __init__(self, bonus_action=None, charge_distance=0, **kwargs):
        super().__init__(**kwargs)
        self.bonus_action = bonus_action
        self.charge_distance = charge_distance

    def use(self, source, target, total_damage=0, crit_multipiler=1):
        if source.distance >= self.charge_distance:
            if not R.roll_save(target, self.save, self.dc):
                target.set_prone(True)
                if self.bonus_action is not None:
                    self.bonus_action.use(source, target, always_hit=False)
        source.distance = 0


class Swallow(Ability):

    def use(self, source, target, total_damage=0, crit_multipiler=1):
        if not R.roll_save(target, self.save, self.dc) \
                and source.size - target.size >= 2:
            target.set_swallowed(state=True, source=source)
            source.focused_enemy = None


class Knockback(Ability):

    def __init__(self, bonus_action=None,
                 charge_distance=0,
                 knockback_distance=0,
                 **kwargs):
        super().__init__(**kwargs)
        self.bonus_action = bonus_action
        self.charge_distance = charge_distance
        self.knockback_distance = knockback_distance

    def use(self, source, target, total_damage=0, crit_multipiler=1):
        if source.distance >= self.charge_distance:
            if self.bonus_action is not None:
                self.bonus_action.use(source, target, always_hit=True)
            if not R.roll_save(target, self.save, self.dc):
                target.set_prone(True)
                knockback_path = world.get_opposite(target.position,
                                                    source.position,
                                                    self.knockback_distance)
                world.force_move(source, target, knockback_path, self.name)
        source.distance = 0


class Poison(Ability):

    # TODO: Make this properly
    # Saving throw has to be checked in two different places
    # and thus it's now saved to target creature class as well as
    # returned.

    def __init__(self, damage, damage_type, duration=None, **kwargs):
        super().__init__(**kwargs)
        self.damage = dice.parse_damage(damage)
        self.damage_type = damage_type
        self.duration = duration

    def use(self, source, target, total_damage=0, crit_multipiler=1):

        messages.IO.reset()
        messages.IO.log += "{source} on-hit effect on {target}.".format(source=source.name, target=target.name)

        save_success = R.roll_save(target, self.save, self.dc)

        if self.damage is not None:
            R.roll_damage(source, target, self, crit_multipiler,
                             self.success, self.save, self.dc)

        if not save_success and self.duration is not None:
            self.apply_condition(target)

    def apply_condition(self, target):
        target.set_poison(state=True, dc=self.dc,
                          save=self.save, duration=self.duration)


class MummyRot(Poison):

    # TODO: Define properly

    def use(self, source, target, total_damage=0, crit_multipiler=1):
        save_success = R.roll_save(target, self.save, self.dc)

        if save_success:
            pass
        else:
            multi = 1
            if self.damage_type in target.immunities \
                    or self.name in target.immunities:
                pass
            elif self.damage_type in target.resistances:
                multi = 0.5
            else:
                target.take_max_hp_damage(source, 10*multi, self.name)
                target.prevent_heal = True
                target.immunities.append(self.name)
                source.damage_dealt += 10*multi


class DamageMaxHP(Ability):

    def use(self, source, target, total_damage, crit_multipiler=1):
        if not R.roll_save(target, self.save, self.dc):
            target.take_max_hp_damage(source, total_damage, self.name)

""" ================================================================ """
""" ======================= SPECIAL FEATURES ======================= """
""" ================================================================ """

class Stomach:

    """ Stomach for creatures that can swallow other creatures """

    def __init__(self, name, damage, damage_type, breakout_dmg, breakout_dc):
        self.name = name
        self.contents = []
        self.damage = dice.parse_damage(damage)
        self.damage_type = damage_type
        self.breakout_dmg = breakout_dmg
        self.breakout_dc = breakout_dc
        self.damage_count = 0

    def regurgitate(self):
        for target in self.contents:
            target.set_swallowed(state=False)
        self.contents = []

    def check_status(self, source):
        if self.damage_count >= self.breakout_dmg:
            self.regurgitate()
            self.damage_count = 0
        else:
            for target in self.contents:
                messages.IO.reset()
                messages.IO.log += "{source} digests {target}.".format(
                    source=source.name, target=target.name)
                R.roll_damage(source, target, self)


""" ================================================================ """
""" ======================= PASSIvE ABILITIES ====================== """
""" ================================================================ """

class FrightfulPresence(Ability):

    def __init__(self, duration, range, **kwargs):
        super().__init__(**kwargs)
        self.duration = duration
        self.range = range
        self.type = 'on_start'

    def use(self, creature, allies, enemies=[]):
        for e in (e for e in enemies.get_alive()
                  if world.get_dist(creature.position, e.position) <= int(self.range / 5)
                  and self.name not in e.immunities):
            if R.roll_save(e, self.save, self.dc):
                e.immunities.append(self.name)
            else:
                e.set_fear(state=True, dc=self.dc, save=self.save, duration=self.duration, by=creature)


class DreadfulGlare(Ability):
    """ This is really an action but here it is defined as a passive
     ability that targets random enemy at the start of each turn """

    def use(self, creature, allies, enemies=[]):
        for e in (e for e in enemies.get_alive()
                  if world.get_dist(creature.position, e.position) <= 8
                  and self.name not in e.immunities):
            if R.roll_save(e, self.save, self.dc):
                e.immunities.append(self.name)
                break
            else:
                e.set_fear(state=True, dc=self.dc, save=self.save, duration=2, by=creature)
                if R.roll_save(e, self.save, self.dc+5):
                    e.set_paralysis(state=True, dc=self.dc+5, save=self.save, duration=2)
                break


class Stench(Ability):
    """ Undead stench that poisons nearby enemies. Targets gain
     immunity to this ability on successful save """

    def use(self, creature, allies, enemies=[]):
        """ Check if enemies are nearby """
        for enemy in (e for e in enemies.get_alive()):
            if world.is_adjacent(enemy.position, creature.position):
                """ Roll save and set immunity if success"""
                if R.roll_save(enemy, self.save, self.dc):
                    enemy.immunities.append(self.name)
                else:
                    """ Else apply poison """
                    if self.name not in enemy.immunities \
                            or not enemy.is_poisoned \
                            or 'poison' not in enemy.immunities:
                        enemy.set_poison(state=True, dc=self.dc,
                                         save=self.save, duration=1)


class Regeneration(Ability):

    def __init__(self, amount, **kwargs):
        super().__init__(**kwargs)
        self.amount = amount

    def use(self, creature, allies=[], enemies=[]):
        creature.heal(amount=self.amount, spellname=self.name)


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


class AvoidDeath:
    """ Avoid death allows creatures to drop to N hitpoints instead
    of zero if it succeeds a save against the damage, e.g. Undead
    Fortitude. This can be also used to prevent certain monsters from
    dying unless specific damage type is used, e.g. trolls require
    fire or acid (if no saves or crits, just give impossible negative
    penalty and crit multiplier, see troll in definitions.

    :param name                 ability name
    :param penalty              penalty to saving throw
    :param save                 ability tied to save
    :param minimum_hp           amount of remaining hp if successful
    :param vulnerabilities      damage types that ignore this passive
    :param min_crit_to_kill     minimum crit multiplier that ignores this
                                passive

    :type name                 str
    :type penalty              int
    :type save                 str
    :type minimum_hp           int
    :type vulnerabilities      list(str, str ...)
    :type min_crit_to_kill     int """

    def __init__(self, name, save, minimum_hp, penalty=0,
                 vulnerabilities=[], min_crit_to_kill=1):
        self.name = name
        self.penalty = penalty
        self.type = 'avoid_death'
        self.save = save
        self.minimum_hp = minimum_hp
        self.min_crit = min_crit_to_kill
        self.vulnerabilities = vulnerabilities

    def use(self, creature, damage, damage_type, critical):
        if critical > self.min_crit or damage_type in self.vulnerabilities:
            return creature.hp
        else:
            if R.roll_save(creature, self.save, damage + self.penalty):
                messages.IO.conditions.append('%s resists death with %s!' % (creature.name, self.name))
                return self.minimum_hp
        return creature.hp
