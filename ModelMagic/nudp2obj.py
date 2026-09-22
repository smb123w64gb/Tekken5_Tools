from model_nudp import *
from vifMaker import VIFerator
import sys


f = open(sys.argv[1],'rb')
o = open(sys.argv[1] + '.obj','w')
o.write('# Nudp2obj alpha 0.\n')
fin = FRead(f)
nud = NUDP()
nud.read(fin)
curFace = 1
for idx,x in enumerate(nud.MeshGroups):
    for idy,y in enumerate(x.subMeshs):
        for idz,z in enumerate(y.vifDMA):
            o.write(str("0 M%03i_S%03i_V%03i\n"))
            testblob = VIFerator()
            testVif = FRead(z.data)
            testblob.read_vif(testVif)
            for xvert in testblob.verts:
                o.write("v")
                for xelm in xvert.pos:
                    o.write(" %01.06f" % xelm)
                o.write("\n")
            curStrips = testblob.get_faces()
            for xstrip in curStrips:
                o.write("f")
                for xelm in xstrip:
                    o.write(" %i" % (xelm+curFace))
                o.write("\n")
            testMax = max(max(curStrips))+1
            curFace += testMax

