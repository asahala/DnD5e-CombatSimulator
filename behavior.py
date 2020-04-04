
class Standard:

    """ Standard AI / behavior for creatures """

    def __init__(self, creature):
        self.me = creature

    def do_stuff(self, allies, enemies):
        self.me.choose_target(enemies)
        if self.me.focused_enemy is not None:
            self.me.choose_weapon(enemies)
            at_range = self.me.move()
            if at_range:
                self.me.attack()


class SocialAnimal:

    """ Social Animals such as wolves, lions etc. Will focus on same
    target and try to keep in a pack """

    def __init__(self, creature):
        self.me = creature

    def do_stuff(self, allies, enemies):
        choice = None
        for a in allies.get_alive():
            if a.focused_enemy is not None and not a.focused_enemy.is_dead:
                choice = a.focused_enemy
        self.me.choose_target(enemies, choice)
        if self.me.focused_enemy is not None:
            self.me.choose_weapon(enemies)
            at_range = self.me.move()
            if at_range:
                self.me.attack()