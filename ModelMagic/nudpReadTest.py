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
            print(testblob.get_faces())

