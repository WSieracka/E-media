import secrets
import math
import random
import miller_rabin

class Key:
    def __init__(self, keysize):
        self.p = 0
        self.q = 0
        self.n = 0
        self.e = 0
        self.phi = 0
        self.d = 0
        self.keysize = keysize
        self.qsize = self.keysize // 2
        self.psize = self.keysize // 2


    # funkcja zwracająca p i q
    def pqnumber(self, b):
        while True:
            a = int(2 ** b)
            number = secrets.randbelow(a)
            #number=os.urandom(self.pqsize)
            if miller_rabin.miller_rabin(number,200):
                return number

    def enumber(self):
        self.phi = (self.p - 1) * (self.q - 1)
        while True:
            self.e = secrets.randbelow(2 ** self.keysize)
            #a = os.urandom(self.keysize)
            #self.e = int.from_bytes(a, byteorder='big', signed=True)
            # gcd-największy wspólny dzielnik dwóch liczb to największa dodatnia liczba całkowita, która doskonale
            # dzieli dwie podane liczby względnie pierwsze
            if math.gcd(self.e, self.phi) == 1 and self.e < self.phi:
                break

    def InverseMod(self, e1, phi1):
        # a oraz m muszą być względnie pierwsze
        if math.gcd(e1, phi1) != 1:
            return None
        u1, u2, u3 = 1, 0, e1
        v1, v2, v3 = 0, 1, phi1
        while v3 != 0:
            q = u3 // v3
            v1, v2, v3, u1, u2, u3 = (u1 - q * v1), (u2 - q * v2), (u3 - q * v3), v1, v2, v3
        return u1 % phi1


    def getkey(self):
        while self.p == 0 and self.q == 0:
            while self.p == self.q:
                self.p = self.pqnumber(self.psize)
                self.q = self.pqnumber(self.psize)
        self.n = self.p * self.q
        self.enumber()
        self.d = self.InverseMod(self.e, self.phi)
        kpublic = (self.e, self.n)
        kprivate = (self.d, self.n)
        return kpublic, kprivate





