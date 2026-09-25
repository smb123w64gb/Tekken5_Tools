import sys
import pycdlib
from io import BytesIO
from ModelMagic.fileRW import *
import decNLZ1
import package_fmt_pkg
iso = pycdlib.PyCdlib()
iso.open(sys.argv[1])

for child in iso.list_children(iso_path='/'):
    print(child.file_identifier())



TekkenCodeFile = '/TK5DATA3.BIN;1'
TekkenDataFile = '/TK5DATA1.BIN;1'

TekkenCodeArchive = BytesIO()
TekkenDataArchive = BytesIO()
iso.get_file_from_iso_fp(TekkenCodeArchive, iso_path=TekkenCodeFile)
iso.get_file_from_iso_fp(TekkenDataArchive, iso_path=TekkenDataFile)
#1 Get hooks to 2 files

CodeArchive = FRead(TekkenCodeArchive.getvalue())

archiveCode = package_fmt_pkg.PKG()
archiveCode.read(CodeArchive)
print(len(archiveCode.files))
cmpCode = archiveCode.files[5]
print(len(cmpCode))
decCode = decNLZ1.unpack_sc3game(cmpCode)
print(len(decCode))


iso.close()
