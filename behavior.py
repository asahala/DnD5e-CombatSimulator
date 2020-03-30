
class Standard:

    """ Standard AI / behavior for creatures """

    def __init__(self, creature):
        self.me = creature

    def do_stuff(self, allies, enemies):
        self.me.choose_target(enemies)
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
        for a in allies.members:
            if a.focused_enemy is not None:
                choice = a.focused_enemy
        self.me.choose_target(enemies, choice)
        self.me.choose_weapon(enemies)
        at_range = self.me.move()
        if at_range:
            self.me.attack()