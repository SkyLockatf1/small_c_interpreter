def ABOUT():
    pass
def HELP(cmd:str):
    pass
def APPEND():
    pass
def LIST(args = "", buffer = []):
    if(len(buffer) == 0):
        print("buffer is empty")
    else:
        args = list(map(args.split("-"),int))
        if args[0] < 1 or args[1] > len(buffer): pass #報錯

        if len(args) == 1:
            print("["+args[0]+"]: "+buffer[args[0]])
        elif len(args) == 2:
            for i in range(args[0], args[1]):
                print("["+i+"]: "+buffer[i])
        else:
            pass #error


def INSERT(arg:str):
    pass
def DELETE(args:list[str]):
    if(len(args) == 0):
        pass
    elif(len(args) == 1):
        pass
    else:
        pass
    pass