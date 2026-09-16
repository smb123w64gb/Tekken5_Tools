from model_nudp import *
import sys

f = open(sys.argv[1],'rb')
f2 = open(sys.argv[2],'rb')
fin = FRead(f)
nud = NUDP()
nud.read(fin)

fin2 = FRead(f2)
nud2 = NUDP()
nud2.read(fin2)


print(nud.header.magic)
fo = open(sys.argv[3],'wb')
fout = FWrite(fo)
nud.MeshGroups[-1] = nud2.MeshGroups[-2]

nud.write(fout)
fo.close()

