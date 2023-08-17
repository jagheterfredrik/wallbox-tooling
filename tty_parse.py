import sys

STATE_PREAMBLE = 0
STATE_FUNCTION = 1
STATE_PARSING = 2
STATE_LEN = 3

DIR_REQ = len(b'< ')
DIR_RESP = len(b'> \t')


state = STATE_PREAMBLE
dir = DIR_REQ
outstr = ''

reg = {}
ri=0
def get_int(f):
    line = f.readline()
    # print(line, line[dir:dir+4])
    global ri
    # print('read line %d'%ri)
    ri+=1
    return int(line[dir:dir+4], 16)

def main():
    with open(sys.argv[1], 'rb') as f:
        while True:
            global state, outstr, dir, reg, ri
            if state == STATE_PREAMBLE:
                line = f.readline()
                ri+=1
                if line.startswith(b'< 0x0a ([LF])'):
                    outstr += 'Request : '
                    dir = DIR_REQ
                    state += 1
                elif line.startswith(b'> \t0x0a ([LF])'):
                    outstr += 'Response: '
                    dir = DIR_RESP
                    state += 1
            elif state == STATE_FUNCTION:
                func = get_int(f)
                # print(func)
                if func == 3:
                    if dir == DIR_REQ:
                        addr_hi, addr_lo = get_int(f), get_int(f)
                        num_hi, num_lo = get_int(f), get_int(f)
                        err_hi, err_lo = get_int(f), get_int(f)
                        addr = addr_hi*256 + addr_lo
                        num = num_hi*256 + num_lo
                        # print('Read request 0x%X cnt %d'%(addr, num))
                    else:
                        cnt = get_int(f)
                        for i in range(cnt//2):
                            val_hi, val_lo = get_int(f), get_int(f)
                            val = val_hi*256 + val_lo
                            if not i in reg or reg[i] != val:
                                # if i not in (0x11, 0x12):
                                print('Read resp reg 0x%X = 0x%X'%(i, val))
                                reg[i] = val
                if func == 6 and dir == DIR_REQ:
                    addr_hi, addr_lo = get_int(f), get_int(f)
                    val_hi, val_lo = get_int(f), get_int(f)
                    err_hi, err_lo = get_int(f), get_int(f)
                    addr = addr_hi*256 + addr_lo
                    val = val_hi*256 + val_lo
                    # if not addr in reg or reg[addr] != val:
                    print('Write 0x%X = 0x%X' % (addr, val))
                    reg[addr] = val
                else:
                    # print(f'Unknown func {func}')
                    pass
                state = STATE_PREAMBLE

if __name__ == "__main__":
    main()