import numpy as np
import math
import io
import re
import zlib
from lxml import etree
from PIL import Image


length_bytes = 4
type_bytes = 4
crc_bytes = 4


class PNG:
    def __init__(self, file):
        self.name = file
        self.file = open(self.name, "rb")
        self.idat_data = []
        self.critical_ancillary = []
        self.extra_chunks = []
        self.plt_index = -1
        self.pixel_bytes = 0
        self.idat_decoded = []
        self.extra_data = bytes()
        if self.file.readable():
            if b'\x89PNG\r\n\x1a\n' == self.file.read(8):
                self.magic_number = b'\x89PNG\r\n\x1a\n'
            else:
                print("It's not png")
        chunk_type = "name"
        while chunk_type != "IEND":
            chunk_length_byte = self.file.read(length_bytes)
            data_length = int.from_bytes(chunk_length_byte, byteorder="big", signed=False)
            chunk_type = self.file.read(type_bytes).decode('utf-8')
            data = self.file.read(data_length)
            crc = self.file.read(crc_bytes)
            if chunk_type == "IHDR":
                self.chunk_ihdr = IHDR(chunk_length_byte, chunk_type, data, crc)
            elif chunk_type == "IDAT":
                self.idat_data.append(IDAT(chunk_length_byte, chunk_type, data, crc))
            elif chunk_type == "PLTE":
                self.critical_ancillary.append(PLTE(chunk_length_byte, chunk_type, data, crc))
                self.plt_index = len(self.critical_ancillary)
            elif chunk_type == "tEXt":
                self.critical_ancillary.append(tEXt(chunk_length_byte, chunk_type, data, crc))
            elif chunk_type == "iTXt":
                self.critical_ancillary.append(iTXt(chunk_length_byte, chunk_type, data, crc))
            elif chunk_type == "cHRM":
                self.critical_ancillary.append(cHRM(chunk_length_byte, chunk_type, data, crc))
            elif chunk_type == "sRGB":
                self.critical_ancillary.append(sRGB(chunk_length_byte, chunk_type, data, crc))
            elif chunk_type == "sPLT":
                self.critical_ancillary.append(sPLT(chunk_length_byte, chunk_type, data, crc))
            elif chunk_type == "pHYs":
                self.critical_ancillary.append(pHYs(chunk_length_byte, chunk_type, data, crc))
            elif chunk_type == "tIME":
                self.critical_ancillary.append(tIME(chunk_length_byte, chunk_type, data, crc))
            elif chunk_type == "IEND":
                self.chunk_iend = IEND(chunk_length_byte, chunk_type, data, crc)
            else:
                self.extra_chunks.append(Chunk(chunk_length_byte, chunk_type, data, crc))

        while True:
            bytes_read = self.file.read(2)
            if not bytes_read:
                break
            self.extra_data += bytes_read
        self.file.close()

    def anonymization(self):
        anonymization_file = open("anonymization.png", 'wb')
        data = self.magic_number
        data += self.chunk_ihdr.length
        data += self.chunk_ihdr.chunk_type.encode('utf-8')
        data += self.chunk_ihdr.data
        data += self.chunk_ihdr.crc
        if self.plt_index != -1:
            data += self.critical_ancillary[self.plt_index - 1].length
            data += self.critical_ancillary[self.plt_index - 1].chunk_type.encode('utf-8')
            data += self.critical_ancillary[self.plt_index - 1].data
            data += self.critical_ancillary[self.plt_index - 1].crc
        for i in range(len(self.idat_data)):
            data += self.idat_data[i].length
            data += self.idat_data[i].chunk_type.encode('utf-8')
            data += self.idat_data[i].data
            data += self.idat_data[i].crc
        data += self.chunk_iend.length
        data += self.chunk_iend.chunk_type.encode('utf-8')
        data += self.chunk_iend.data
        data += self.chunk_iend.crc
        anonymization_file.write(data)
        anonymization_file.close()

    def getDecompressedIdat(self):
        IDAT_data = b''.join(chunk.data for chunk in self.idat_data)
        return zlib.decompress(IDAT_data)

    # Dekodowanie chunku zostalo zaczerpniete z https://pyokagan.name/blog/2019-10-14-png/
    def process_idat_data(self):


        colorTypeToBytesPerPixel = {
            0: 1,
            2: 3,
            3: 1,
            4: 2,
            6: 4
        }

        IDAT_data = self.getDecompressedIdat()

        self.pixel_bytes = colorTypeToBytesPerPixel.get(self.chunk_ihdr.color_type)

        width = self.chunk_ihdr.width
        height = self.chunk_ihdr.height
        expected_IDAT_data_len = height * (1 + width * self.pixel_bytes)

        assert expected_IDAT_data_len == len(IDAT_data), "Decoding went wrong"
        stride = width * self.pixel_bytes

        def paeth_predictor(a, b, c):
            p = a + b - c
            pa = abs(p - a)
            pb = abs(p - b)
            pc = abs(p - c)
            if pa <= pb and pa <= pc:
                Pr = a
            elif pb <= pc:
                Pr = b
            else:
                Pr = c
            return Pr

        def recon_a(r, c):
            return self.idat_decoded[r * stride + c - self.pixel_bytes] if c >= self.pixel_bytes else 0

        def recon_b(r, c):
            return self.idat_decoded[(r - 1) * stride + c] if r > 0 else 0

        def recon_c(r, c):
            return self.idat_decoded[
                (r - 1) * stride + c - self.pixel_bytes] if r > 0 and c >= self.pixel_bytes else 0

        i = 0
        for r in range(height):
            filter_type = IDAT_data[i]
            i += 1
            for c in range(stride):
                single_filter_type = IDAT_data[i]
                i += 1
                if filter_type == 0:
                    recon_x = single_filter_type
                elif filter_type == 1:
                    recon_x = single_filter_type + recon_a(r, c)
                elif filter_type == 2:
                    recon_x = single_filter_type + recon_b(r, c)
                elif filter_type == 3:
                    recon_x = single_filter_type + (recon_a(r, c) + recon_b(r, c)) // 2
                elif filter_type == 4:
                    recon_x = single_filter_type + paeth_predictor(recon_a(r, c), recon_b(r, c), recon_c(r, c))
                else:
                    raise Exception('Wrong filter: ' + str(filter_type))
                self.idat_decoded.append(recon_x & 0xff)


class Chunk:
    def __init__(self, length, chunk_type, data, crc):
        self.length = length
        self.chunk_type = chunk_type
        self.data = data
        self.crc = crc

    def __str__(self):
        return "Chunk length: {0}\nChunk type: {1}\nChunk data: {2}\nChunk crc: {3}\n".format(self.length,
                                                                                              self.chunk_type,
                                                                                              self.data, self.crc)


class IHDR(Chunk):
    def __init__(self, length, chunk_type, data, crc):
        super().__init__(length, chunk_type, data, crc)
        self.width = int.from_bytes(self.data[0:4], byteorder="big", signed=False)
        self.height = int.from_bytes(self.data[4:8], byteorder="big", signed=False)
        self.bit_depth = self.data[8]
        self.color_type = self.data[9]
        self.compression_method = self.data[10]
        self.filter_method = self.data[11]
        self.interlace_method = self.data[12]

    def __str__(self):
        return "\n" + super().__str__() + "Width: {0}\nHeight: {1}\nBit Depth: {2}\nColor type: {3}\nCompression method: {4}\nFilter method: {5}\nInterlace method: {6}\n".format(
            self.width, self.height, self.bit_depth, self.color_type, self.compression_method, self.filter_method,
            self.interlace_method)


class PLTE(Chunk):
    def __init__(self, length, chunk_type, data, crc):
        super().__init__(length, chunk_type, data, crc)
        self.colors = []
        i = 0
        while i < int(int.from_bytes(self.length[0:4], byteorder="big", signed=False)):
            R = self.data[i]
            G = self.data[i + 1]
            B = self.data[i + 2]
            self.colors.append([R, G, B])
            i += 3

    def __str__(self):
        i = 0
        plte_info = ""
        while i < int(int.from_bytes(self.length[0:4], byteorder="big", signed=False) / 3):
            if not (i % 8):
                plte_info += "\n"
            plte_info += str(self.colors[i])
            i += 1
        size = math.ceil(math.sqrt(int(int.from_bytes(self.length[0:4], byteorder="big", signed=False) / 3)))
        size_visible = 50
        data = np.zeros((size_visible * size, size_visible * size, 3), dtype=np.uint8)
        x = 0
        y = 0
        for i in range(int(int.from_bytes(self.length[0:4], byteorder="big", signed=False) / 3)):
            if x == size:
                x = 0
                y += 1
            data[y * size_visible:y * size_visible + size_visible, x * size_visible:x * size_visible + size_visible] = \
                self.colors[i]
            x += 1
        img = Image.fromarray(data, 'RGB')
        img.save('PLTE.png')
        img.show()
        return "\n" + super().__str__() + str(
            plte_info) + "\n"


class IDAT(Chunk):
    def __init__(self, length, chunk_type, data, crc):
        super().__init__(length, chunk_type, data, crc)

    def __str__(self):
        return super().__str__()


class IEND(Chunk):
    def __init__(self, length, chunk_type, data, crc):
        super().__init__(length, chunk_type, data, crc)

    def __str__(self):
        return "\n" + super().__str__() + "\n"


class tIME(Chunk):
    def __init__(self, length, chunk_type, data, crc):
        super().__init__(length, chunk_type, data, crc)
        self.year = int.from_bytes(self.data[0:2], byteorder="big", signed=False)
        self.month = self.data[2]
        self.day = self.data[3]
        self.hour = self.data[4]
        self.minute = self.data[5]
        self.second = self.data[6]

    def __str__(self):
        return "\n" + super().__str__() + "Year: {0}\nMonth: {1}\nDay: {2}\nHour: {3}\nMinute: {4}\nSecond: {5}\n".format(
            self.year, self.month, self.day, self.hour, self.minute,
            self.second)


class iTXt(Chunk):
    def __init__(self, length, chunk_type, data, crc):
        super().__init__(length, chunk_type, data, crc)
        chunk_data = self.data
        data_start = chunk_data.index(b'\x00')
        self.keyword = chunk_data[:data_start].decode('utf-8')
        self.compression_flag = chunk_data[data_start + 1]
        self.itxt_compression_method = chunk_data[data_start + 2]
        chunk_data = chunk_data[data_start + 3:]
        data_start = chunk_data.index(b'\x00')
        self.language_tag = chunk_data[:data_start].decode('utf-8')
        chunk_data = chunk_data[data_start + 1:]
        data_start = chunk_data.index(b'\x00')
        self.translated_keyword = chunk_data[:data_start].decode('utf-8')
        self.text = chunk_data[data_start + 1:].decode('utf-8')
        if re.search("XML", self.keyword):
            with io.open("tmp.xml", "w", encoding="utf-8") as tmp:
                tmp.write(self.text)
                tmp.close()
            tree = etree.parse("tmp.xml")
            self.text = etree.tostring(tree, encoding="unicode", pretty_print=True)

    def __str__(self):
        return "\n" + super().__str__() + "Keyword: {0}\nCompression flag: {1}\nCompression method: {2}\nLanguage tag: {3}\nTranslated keyword: {4}\nText: {5}\n".format(
            self.keyword, self.compression_flag, self.itxt_compression_method, self.language_tag,
            self.translated_keyword,
            self.text)


class tEXt(Chunk):
    def __init__(self, length, chunk_type, data, crc):
        super().__init__(length, chunk_type, data, crc)
        all_data = self.data
        index = all_data.index(b'\x00')
        self.keyword = all_data[:index].decode('utf-8')
        self.text_string = all_data[index + 1:].decode('utf-8')

    def __str__(self):
        return "\n" + super().__str__() + "Keyword: {0}\nText string: {1}\n".format(
            self.keyword,
            self.text_string)


class cHRM(Chunk):
    def __init__(self, length, chunk_type, data, crc):
        super().__init__(length, chunk_type, data, crc)
        self.white_x = int.from_bytes(self.data[0:4], byteorder="big", signed=False)
        self.white_y = int.from_bytes(self.data[4:8], byteorder="big", signed=False)
        self.red_x = int.from_bytes(self.data[8:12], byteorder="big", signed=False)
        self.red_y = int.from_bytes(self.data[12:16], byteorder="big", signed=False)
        self.green_x = int.from_bytes(self.data[16:20], byteorder="big", signed=False)
        self.green_y = int.from_bytes(self.data[20:24], byteorder="big", signed=False)
        self.blue_x = int.from_bytes(self.data[24:28], byteorder="big", signed=False)
        self.blue_y = int.from_bytes(self.data[28:32], byteorder="big", signed=False)

    def __str__(self):
        return "\n" + super().__str__() + "White point x: {0}\nWhite point y: {1}\nRed x: {2}\nRed y: {3}\nGreen x: {4}\nGreen y: {5}\nBlue x: {6}\nBlue y: {7}\n".format(
            self.white_x, self.white_y, self.red_x, self.red_y, self.green_x, self.green_y, self.blue_x,
            self.blue_y)


class sRGB(Chunk):
    def __init__(self, length, chunk_type, data, crc):
        super().__init__(length, chunk_type, data, crc)
        self.rendering_intent = self.data.decode('utf-8')

    def __str__(self):
        return "\n" + super().__str__() + "Rendering data: {0}\n".format(
            self.rendering_intent) + "\n"


class pHYs(Chunk):
    def __init__(self, length, chunk_type, data, crc):
        super().__init__(length, chunk_type, data, crc)
        self.pixel_per_unit_x = int.from_bytes(self.data[0:4], byteorder="big", signed=False)
        self.pixel_per_unit_y = int.from_bytes(self.data[4:8], byteorder="big", signed=False)
        self.unit_specifier = self.data[8]

    def __str__(self):
        return "\n" + super().__str__() + "Pixel per unit, X axis: {0}\nPixel per unit, Y axis: {1}\nUnit specifier: {2}\n".format(
            self.pixel_per_unit_x, self.pixel_per_unit_y,
            self.unit_specifier) + "\n"


class sPLT(Chunk):
    def __init__(self, length, chunk_type, data, crc):
        super().__init__(length, chunk_type, data, crc)
        chunk_data = self.data
        start_data = chunk_data.index(b'\x00')
        self.plt = chunk_data[:start_data].decode('utf-8')
        chunk_data = chunk_data[start_data + 1:]
        self.depth = int.from_bytes(chunk_data[0:1], byteorder="big", signed=False)
        self.green = []
        self.red = []
        self.blue = []
        self.alpha = []
        self.freq = []
        f = 0
        if self.depth == 16:
            while f < len(chunk_data) / 10:
                self.green.append(int.from_bytes(chunk_data[10 * f + 1:10 * f + 3], byteorder="big", signed=False))
                self.red.append(int.from_bytes(chunk_data[10 * f + 3:10 * f + 5], byteorder="big", signed=False))
                self.blue.append(int.from_bytes(chunk_data[10 * f + 5:10 * f + 7], byteorder="big", signed=False))
                self.alpha.append(int.from_bytes(chunk_data[10 * f + 7:10 * f + 9], byteorder="big", signed=False))
                self.freq.append(int.from_bytes(chunk_data[10 * f + 9:10 * f + 11], byteorder="big", signed=False))
                f += 1
        else:
            while f < len(chunk_data) / 6:
                self.green.append(int.from_bytes(chunk_data[6 * f + 1:6 * f + 2], byteorder="big", signed=False))
                self.red.append(int.from_bytes(chunk_data[6 * f + 2:6 * f + 3], byteorder="big", signed=False))
                self.blue.append(int.from_bytes(chunk_data[6 * f + 3:6 * f + 4], byteorder="big", signed=False))
                self.alpha.append(int.from_bytes(chunk_data[6 * f + 4:6 * f + 5], byteorder="big", signed=False))
                self.freq.append(int.from_bytes(chunk_data[6 * f + 5:6 * f + 7], byteorder="big", signed=False))
                f += 1

    def __str__(self):
        return "\n" + "Palette name: {0}\nSample_depth: {1}\nGreen: {2}\nRed: {3}\nBlue: {4}\nAplha: {5}\nFrequency: {6}\n".format(
            self.plt, self.depth, self.green, self.red, self.blue, self.alpha,
            self.freq) + "\n"
