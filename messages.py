
VERBOSE_LEVEL = 2
INDENT = " " * 2

class IO:
    
    turn = 0
    hp = 0
    target_name = ""
    total_damage = {}
    log = ""

    def reset():
        IO.log = ""
        IO.total_damage = {}
        IO.hp = 0
        IO.target_name = ""

    def printlog():
        d = " + ".join(["%i %s" % (v, k) for k, v in IO.total_damage.items()])
        damages = [i for i in IO.total_damage.values()]
        total = sum(damages)
        if d:
            if len(damages) == 1:
                total = ""
            else:
                total = " (total %i) " % total
            taken = " %s%s damage taken, %i HP remaining." % (d, total, IO.hp)
        else:
            taken = ""

        if IO.log:
            IO.printmsg(IO.log + taken, 2, True, True)

        if IO.hp <= 0 and IO.target_name:
            death = "-> %s is dead!" % IO.target_name
            IO.printmsg(death, 2, True, False)

    @staticmethod
    def center_and_pad(string, padding=":"):
        times = int( (72 - len(string) + 2) / 2 )
        return "{padding} {string} {padding}".format(padding=padding*times,
                                                     string=string)

    @staticmethod
    def printmsg(message, level, indent=False, print_turn=False):
        if indent:
            tab = INDENT
        else:
            tab = ""

        """ Set if turn number is shown in action log """
        if print_turn:
            turn = "Turn %s: " % IO.turn
        else:
            if indent:
                turn = " "*len("Turn %s: " % IO.turn)
            else:
                turn = ""

        if VERBOSE_LEVEL >= level:
            print(tab + turn + message)