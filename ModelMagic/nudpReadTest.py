from model_nudp import *
from vifMaker import VIFerator
import sys


f = open(sys.argv[1],'rb')
fin = FRead(f)
nud = NUDP()
nud.read(fin)
for idx,x in enumerate(nud.MeshGroups):
    for idy,y in enumerate(x.subMeshs):
        for idz,z in enumerate(y.vifDMA):
            testblob = VIFerator()
            testVif = FRead(z.data)
            testblob.read_vif(testVif)
            for xx in testblob.triStrips:
                base = int((xx.base - 1)/5)
                print("%3i,%2i,%i V%02i B%02i T%02i"%(idx,idy,idz,len(testblob.verts),base,xx.stripCount))

