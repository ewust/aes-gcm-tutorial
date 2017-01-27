

from Crypto.Cipher import AES
from Crypto.Util.number import bytes_to_long, long_to_bytes


# a and b are little-endian 128-bit integers corresponding to
# polynomials in GF(2^128)
# We will multiply these polynomials and reduce them modulo
# R = 1 + x + x^2 + x^7 + x^128 (an irreducible polynomial)
#       0xE1000...0001
# Note this code is NOT constant time, and is intended for
# instruction purposes only
# Addition and subtraction of polynomials in GF(2^128)
# can be done by xor (^) of the numbers that represent them
#
# This is a bit ugly, because NIST specifies the parameters
# are bitwise little endian. We would have to reverse them
# at the bitlevel to write this function in a way that makes
# sense.
#
def gf_2_128_mul(a, b):

    # store the product in p
    p = 0

    # iterate over bits/terms in b
    for i in xrange(128):

        # check i-th bit of b (i-th term of polynomial b)
        if b & (1<<(127-i)):
            p ^= a          # adds polynomial a to p

        # store x^127 term of polynomial a
        carry = a & 1

        # multiply polynomial a by x^1
        a = (a>>1)

        if carry:
            # subtract R
            a ^= 0xE1000000000000000000000000000000
                            # This is R without the x^128 term
                            # which cancels with carry (which
                            # we just shifted off of a)
    return p


# pad to nearest 16 bytes
def pad(data):
    return data + '\x00'*(16 - (len(data) % 16))

def ghash(H, A, C):
    len_A = len(A)
    len_C = len(C)

    # pad
    A = pad(A)
    C = pad(C)

    H = bytes_to_long(H)
    x = 0x00

    A_blocks = (len_A+15)/16
    C_blocks = (len_C+15)/16


    # Add in AAD
    for i in xrange(A_blocks):
        x = gf_2_128_mul(x ^ bytes_to_long(A[16*i:16*(i+1)]), H)
        print 'Xa_%d = %s' % (i+1, hex(x))

    # Add in ciphertext
    for i in xrange(C_blocks):
        x = gf_2_128_mul(x ^ bytes_to_long(C[16*i:16*(i+1)]), H)
        print 'Xc_%d = %s' % (i+1+A_blocks, long_to_bytes(x,16).encode('hex'))

    len_bits = (len_A*8) << 64 | (len_C*8)
    print 'len bits: %s' % (long_to_bytes(len_bits,16).encode('hex'))
    x = gf_2_128_mul(x ^ len_bits, H)
    print 'X_$ = %s' % (long_to_bytes(x,16).encode('hex'))
    return long_to_bytes(x, 16)





def aes_gcm(key, iv, pt, auth_data):
    aes = AES.new(key, AES.MODE_ECB)
    H = aes.encrypt('\x00'*16)
    print 'H = %s' % H.encode('hex')

    # Initialize the counter to IV || 0^31 1
    # TODO: non-96 bit IV's get passed to GHASH
    y = (bytes_to_long(iv) << 32) | 0x01

    # We'll xor the auth tag by this at the end
    E_y0 = aes.encrypt(long_to_bytes(y, 16))
    print 'E(K, Y_0) = %s' % E_y0.encode('hex')

    C = ''
    for i in xrange((len(pt)+15)/16):
        block = pt[16*i:16*(i+1)]

        # Increment the counter
        y += 1

        # Encrypt this plaintext block
        ctext = bytes_to_long(aes.encrypt(long_to_bytes(y, 16))) ^ bytes_to_long(block)

        # Add it to the ciphertext
        C += long_to_bytes(ctext, len(block))

    print 'C = %s' % (C.encode('hex'))

    gh = ghash(H, auth_data, C)
    print 'GHASH(H, A, C) = %s' % gh.encode('hex')

    tag = long_to_bytes(bytes_to_long(gh) ^ bytes_to_long(E_y0), 16)
    print 'Tag = %s' % tag.encode('hex')




aes_gcm(key='\x00'*16,
        iv='\x00'*12,
        pt='00000000000000000000000000000000'.decode('hex'),
        auth_data='')

#AES.new(key, AES.MODE_ECB)
