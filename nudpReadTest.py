from model_nudp import *
import sys

f = open(sys.argv[1],'rb')
fin = FRead(f)
nud = NUDP()
nud.read(fin)
print(nud.header.magic)
fo = open(sys.argv[1]+".rewrote.nud",'wb')
fout = FWrite(fo)
nud.write(fout)
fo.close()

