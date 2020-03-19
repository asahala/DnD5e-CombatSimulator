
VERBOSE_LEVEL = 2
INDENT = " " * 4

class IO:
    
    turn = 0

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

        """ Add punctuation """
        if message[-1].isalpha():
            message += "."

        """ Set if turn number is shown in action log """
        if print_turn:
            turn = "Turn %i: " % IO.turn
        else:
            turn = ""

        if VERBOSE_LEVEL >= level:
            print(tab + turn + message)