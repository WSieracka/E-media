from PNG import PNG
from rsa import RSA_algorithm

import cv2
import numpy as np
from matplotlib import pyplot as plt


def main():
    name = input("Podaj nazwę obrazu png: ")
    nazwa = '{name}.png'.format(name=name)

    image_file = nazwa
    image = PNG(image_file)

    print(image.chunk_ihdr)
    j = 0
    for i in image.critical_ancillary:
        print(image.critical_ancillary[j])
        j+=1
    print(image.chunk_iend)
    image.anonymization()

    img_org = cv2.imread(nazwa)
    cv2.imshow('Obrazek', img_org)
    img = cv2.imread(nazwa, 0)
    fourier = np.fft.fft2(img)
    fshift = np.fft.fftshift(fourier)
    magnitude_spectrum = 20 * np.log(np.abs(fshift))
    fourier_phase = np.asarray(np.angle(fshift))
    f_ishift = np.fft.ifftshift(fshift)
    img_back = np.fft.ifft2(f_ishift)
    img_back = np.abs(img_back)
    plt.subplot(221), plt.imshow(img, cmap='gray')
    plt.title('Black and white Image'), plt.xticks([]), plt.yticks([])
    plt.subplot(222), plt.imshow(magnitude_spectrum, cmap='gray')
    plt.title('Magnitude Spectrum'), plt.xticks([]), plt.yticks([])
    plt.subplot(223), plt.imshow(fourier_phase, cmap='gray')
    plt.title('FFT Phase'), plt.xticks([]), plt.yticks([])
    plt.subplot(224), plt.imshow(img_back, cmap='gray')
    plt.title('Inverted FFT'), plt.xticks([]), plt.yticks([])
    plt.show()
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    image.process_idat_data()
    encrypted_file_path = "encrypted_ECB.png"
    decrypted_file_path = "decrypted_ECB.png"
    encrypted_file_path2 = "encrypted_CBC.png"
    decrypted_file_path2 = "decrypted_CBC.png"
    encrypted_file_path3 = "encrypted_library.png"

    # klasa = RSA_algorithm(1024)
    # cipher, after_iend_data_embedded, length_org = klasa.encrypt_ECB(image.idat_decoded)
    # klasa.encrypted_file(cipher, image.pixel_bytes, image.chunk_ihdr.width, image.chunk_ihdr.height,
    #                      encrypted_file_path,
    #                      after_iend_data_embedded, length_org)
    # new_png = PNG(encrypted_file_path)
    # new_png.process_idat_data()
    # decrypted_data = klasa.decrypt_ECB(new_png.idat_decoded, new_png.extra_data, length_org)
    # klasa.descrypted_file(decrypted_data, new_png.pixel_bytes, new_png.chunk_ihdr.width,
    #                       new_png.chunk_ihdr.height, decrypted_file_path)
    # cipher2, after_iend_data_embedded2, length_org2 = klasa.encrypt_CBC(image.idat_decoded)
    # klasa.encrypted_file(cipher2, image.pixel_bytes, image.chunk_ihdr.width, image.chunk_ihdr.height,
    #                      encrypted_file_path2,
    #                      after_iend_data_embedded2, length_org2)
    #
    # new_png2 = PNG(encrypted_file_path2)
    # new_png2.process_idat_data()
    # decrypted_data2 = klasa.decrypt_CBC(new_png2.idat_decoded, new_png2.extra_data, length_org2)
    # klasa.descrypted_file(decrypted_data2, new_png2.pixel_bytes, new_png2.chunk_ihdr.width,
    #                       new_png2.chunk_ihdr.height, decrypted_file_path2)
    #
    # cipher3, after_iend_data_embedded3, length_org3 = klasa.Library_encrypt(image.idat_decoded)
    # klasa.encrypted_file(cipher3, image.pixel_bytes, image.chunk_ihdr.width, image.chunk_ihdr.height,
    #                      encrypted_file_path3,
    #                      after_iend_data_embedded3, length_org3)


main()
