def ABOUT():
    pass
def HELP(cmd:str):
    pass
def APPEND():
    pass

def LIST(args = [], buffer = []):
    if(len(buffer) == 0):
        print("buffer is empty")
        return
    else:
        if len(args) == 0:
            for i in range(len(buffer)):
                print("["+str(i+1)+"]: "+buffer[i])
                return
        elif len(args) == 1:
            if args[0] < 1 or args[0] > len(buffer):
                raise RuntimeError(f"Runtime error: Index {args[0]} out of bounds.")
            print("["+str(args[0])+"]: "+buffer[args[0]])

        elif len(args) == 2:
            if args[0] < 1 or args[1] > len(buffer): raise RuntimeError(f"Runtime error: Index out of bounds. Valid range is 1 to {len(buffer)}")
            for i in range(args[0], args[1]):
                print("["+str(i)+"]: "+buffer[i])
        else:
            raise RuntimeError(f"Runtime error: Too many arguments for LIST. Expected 0, 1, or 2, got {len(args)}")


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

LIST("123,123",["hello","world","test","example"])