import hashlib
from zlib import crc32 as crc32_hash

def getChecksumFromFile(file: str):
    """
    Takes a filepath of type String and
    returns a String representation of the
    CRC32, MD5, SHA1, SHA256, SHA512
    hashes corresponding to the given file.
    """
    BUF_SIZE = 65536 #64kb
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    sha512 = hashlib.sha512()
    crc32 = 0
    
    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
            sha1.update(data)
            sha256.update(data)
            sha512.update(data)
            crc32 = crc32_hash(data, crc32) 
    
    crc32 = "%08X" % (crc32 & 0xFFFFFFFF)
    
    checksum  = "%-10s" % "\tCRC23:"  + str(crc32) + "\n"
    checksum += "%-10s" % "\tMD5:"    + str(md5.hexdigest()) + "\n"
    checksum += "%-10s" % "\tSHA1:"   + str(sha1.hexdigest()) + "\n"
    checksum += "%-10s" % "\tSHA256:" + str(sha256.hexdigest()) + "\n"
    checksum += "%-10s" % "\tSHA512:" + str(sha512.hexdigest()) + "\n"
    return checksum