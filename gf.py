

def gf_2_8_mul(a, b):

    p = 0

    for i in xrange(8):
        # check i-th bit of b (x^i term in polynomial)
        if b & (1<<i):
            p ^= a

        # store x^7 term
        carry = a & (1<<7)

        # multiply by x
        a = (a<<1)
        a &= 0xff

        if carry:
            # subtract R
            a ^= 0x1b   # 0x1b = x^8 + x^4 + x^3 + x + 1

    return p

def gf_mul_gen(a, b, R=0x11b):
    R_msb = R.bit_length()-1
    p = 0
    for i in xrange(R_msb):
        if b & (1<<i):
            p ^= a

        carry = a & (1<<(R_msb-1))

        a = (a<<1)

        if carry:
            a ^= R

    return p

def gf_mul(a, b):
    p = 0
    a_len = a.bit_length()
    b_len = b.bit_length()
    for i in xrange(max(a_len, b_len)):
        if b & (1<<i):
            p ^= a
        a = (a<<1)

    return p

# returns division dropping remainder
# if a / r
def gf_div_rem(a, r=0x11b):
    bit_len = a.bit_length()
    r_len = r.bit_length()
    q = 0
    for i in range(bit_len, r_len-2, -1):
        if a & (1<<i):
            q_shift = i - (r_len-1)
            q |= (1<<q_shift)
            a ^= (r<<q_shift)
    return q, a

def gf_div(a, r):
    q, remainder = gf_div_rem(a, r)
    return q

def gf_mod(a, r=0x11b):
    q, remainder = gf_div_rem(a, r)
    return remainder

def egcd_gf(a, b=0x11b):
    #print 'egcd_gf(0x%x, 0x%x)' % (a, b)
    if a == 0:
        return (b, 0, 1)
    else:
        mod = gf_mod(b,a)
        #print 'taking 0x%x %% 0x%x (=0x%x)' % (b, a, mod)
        g, y, x = egcd_gf(mod, a)
        div = gf_div(b,a)
        mul = gf_mul(div, y)
        sub = x ^ mul
        #print 'div = 0x%x, mul = 0x%x, sub = 0x%x, g = 0x%x, y = 0x%x' % (div, mul, sub, g, y)
        return (g, sub, y)


def modinv_gf(a, r=0x11b):
    g, x, y = egcd_gf(a, r)
    if g != 1:
        raise Exception('mod inverse does not exist')
    else:
        return gf_mod(x, r)


def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)


def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('mod inverse does not exist')
    else:
        return x % m


# (x^4 + x^3 + 1) * (x^6 + x^2)
#
a = 0x19
b = 0x44


import random
a = random.randint(0, 2**128)
b = random.randint(0, 2**128)

R = (1<<128)|0x87

x = gf_mul_gen(a, b, R)
print 'a=0x%x' % a
print 'b=0x%x' % b
print 'a*b=0x%x' % x

inv = modinv_gf(a, R)

print 'a^-1=0x%x' % inv

y = gf_mul_gen(a, inv, R)

print 'a*a^-1=0x%x' % y
