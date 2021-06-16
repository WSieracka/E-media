import random
from collections import deque
import png
from key import Key
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA


class RSA_algorithm:
    def __init__(self, keysize):
        self.orginalkeysize = keysize
        self.keysize = keysize // 8
        self.public_key, self.private_key = Key(self.orginalkeysize).getkey()
        self.lessmthann = keysize // 8 - 1

    def encrypt_ECB(self, data):
        length_org = len(data)
        data_ECB = []
        lastelement = []
        for i in range(0, len(data), self.lessmthann):
            chunk_to_encrypt = bytes(data[i: i + self.lessmthann])
            c = pow(int.from_bytes(chunk_to_encrypt, byteorder='big'), self.public_key[0],
                    self.public_key[1])
            hex_encrypted = c.to_bytes(self.keysize, byteorder='big')
            for i in range(self.lessmthann):
                data_ECB.append(hex_encrypted[i])
            lastelement.append(hex_encrypted[-1])
        # byte odpowiedzialny za koniec czytania
        data_ECB.append(lastelement.pop())
        return data_ECB, lastelement, length_org

    def encrypt_CBC(self, data):
        length_org = len(data)
        data_CBC = []
        lastelement = []
        # zeby każdy komunikat był unikatowy to w pierwszym bloku używamy wektor inicjujący- IV -liczba losowa
        self.liczbalosowa = random.getrandbits(self.orginalkeysize)
        initialization_vector = self.liczbalosowa
        for i in range(0, len(data), self.lessmthann):
            chunk_to_encrypt = bytes(data[i: i + self.lessmthann])
            iv_byte = initialization_vector.to_bytes(self.keysize, byteorder='big')
            iv = int.from_bytes(iv_byte[:len(chunk_to_encrypt)], byteorder='big')
            initialization_v = pow((int.from_bytes(chunk_to_encrypt, byteorder='big') ^ iv), self.public_key[0],
                                   self.public_key[1])
            initialization_vector = initialization_v
            hex_encrypted = initialization_v.to_bytes(self.keysize, byteorder='big')
            for i in range(self.lessmthann):
                data_CBC.append(hex_encrypted[i])
            lastelement.append(hex_encrypted[-1])
        # byte odpowiedzialny za koniec czytania
        data_CBC.append(lastelement.pop())
        return data_CBC, lastelement, length_org

    def decrypt_ECB(self, data, after_iend, length_org):
        data_ECB_dec = []
        # danych zaszyfrowanych
        ECB_encrypt = []
        # łączenie danych
        after_iend = deque(after_iend)
        for i in range(0, len(data), self.lessmthann):
            ECB_encrypt.extend(data[i:i + self.lessmthann])
            ECB_encrypt.append(after_iend.popleft())
        ECB_encrypt.extend(after_iend)
        for i in range(0, len(ECB_encrypt), self.keysize):
            decrypt_bytes = bytes(ECB_encrypt[i: i + self.keysize])
            decrypt_int = pow(int.from_bytes(decrypt_bytes, byteorder='big'), self.private_key[0], self.private_key[1])
            if len(data_ECB_dec) + self.lessmthann > length_org:
                decrypt_length = length_org - len(data_ECB_dec)
            else:
                decrypt_length = self.lessmthann
            bytes_decrypt = decrypt_int.to_bytes(decrypt_length, byteorder='big')

            for i in bytes_decrypt:
                data_ECB_dec.append(i)

        return data_ECB_dec

    def decrypt_CBC(self, data, after_iend, length_org):
        data_CBC_dec = []

        # danych zaszyfrowanych
        CBC_encrypt = []
        # łączenie danych
        after_iend = deque(after_iend)
        for i in range(0, len(data), self.lessmthann):
            CBC_encrypt.extend(data[i:i + self.lessmthann])
            CBC_encrypt.append(after_iend.popleft())
        CBC_encrypt.extend(after_iend)
        # zeby każdy komunikat był unikatowy to w pierwszym bloku używamy wektor inicjujący- IV -liczba losowa
        initialization_vector = self.liczbalosowa
        # initialization_vector = random.getrandbits(self.orginalkeysize)
        for i in range(0, len(CBC_encrypt), self.keysize):
            decrypt_bytes = bytes(CBC_encrypt[i: i + self.keysize])
            decrypt_int = pow(int.from_bytes(decrypt_bytes, byteorder='big'), self.private_key[0], self.private_key[1])
            if len(data_CBC_dec) + self.lessmthann > length_org:
                decrypt_length = length_org - len(data_CBC_dec)
            else:
                decrypt_length = self.lessmthann
            iv_byte = initialization_vector.to_bytes(self.keysize, byteorder='big')
            iv = int.from_bytes(iv_byte[:decrypt_length], byteorder='big')
            xor = iv ^ decrypt_int
            initialization_vector = int.from_bytes(decrypt_bytes, byteorder='big')
            decrypt_hex = xor.to_bytes(decrypt_length, byteorder='big')
            for i in decrypt_hex:
                data_CBC_dec.append(i)

        return data_CBC_dec

    # Dzielenie zaszyfrowanych danych na te, ktore znajduja sie w chunku IDAT oraz te ktore umieszczane sa za chunkiem IEND
    def splitData(self, encryptedData, length_org):
        encryptedData = deque(encryptedData)
        idatData = []
        dataAfterIend = []

        for i in range(length_org):
            idatData.append(encryptedData.popleft())
        for i in range(len(encryptedData)):
            dataAfterIend.append(encryptedData.popleft())
        return idatData, dataAfterIend

    def encrypted_file(self, encryptedData, bytesPerPixel, width, height, encryptedPngPath,
                       lastElementInEncryptedDataBlock, length_org):
        idatData, dataAfterIend = self.splitData(encryptedData, length_org)
        pngWriter = self.create_writer(width, height, bytesPerPixel)
        pixelWidth = width * bytesPerPixel
        rows = [idatData[i: i + pixelWidth] for i in range(0, len(idatData), pixelWidth)]

        file = open(encryptedPngPath, 'wb')
        pngWriter.write(file, rows)
        file.write(bytes(lastElementInEncryptedDataBlock))
        file.write(bytes(dataAfterIend))
        file.close()

    def descrypted_file(self, decryptedData, bytesPerPixel, width, height, decryptedPngPath):
        pngWriter = self.create_writer(width, height, bytesPerPixel)
        pixelWidth = width * bytesPerPixel
        rows = [decryptedData[i: i + pixelWidth] for i in range(0, len(decryptedData), pixelWidth)]
        file = open(decryptedPngPath, 'wb')
        pngWriter.write(file, rows)
        file.close()

    def create_writer(self, width, height, bytesPerPixel):
        global pngWriter
        if bytesPerPixel == 1:
            pngWriter = png.Writer(width, height, greyscale=True)
        elif bytesPerPixel == 2:
            pngWriter = png.Writer(width, height, greyscale=True, alpha=True)
        elif bytesPerPixel == 3:
            pngWriter = png.Writer(width, height, greyscale=False)
        elif bytesPerPixel == 4:
            pngWriter = png.Writer(width, height, greyscale=False, alpha=True)
        return pngWriter

    def Library_encrypt(self, data):
        lessmthann2 = self.orginalkeysize // 16 - 1
        cdata = []
        after_iend_data_embedded = []
        length_org = len(data)
        key = RSA.construct((self.public_key[1], self.public_key[0]))
        cipher = PKCS1_OAEP.new(key)

        for i in range(0, len(data), lessmthann2):
            chunk_to_encrypt_hex = bytes(data[i: i + lessmthann2])
            cipher_hex = cipher.encrypt(chunk_to_encrypt_hex)

            for i in range(lessmthann2):
                cdata.append(cipher_hex[i])
            after_iend_data_embedded.append(cipher_hex[-1])
        cdata.append(after_iend_data_embedded.pop())

        return cdata, after_iend_data_embedded, length_org
