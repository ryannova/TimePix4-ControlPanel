from unittest import result
import numpy as np
import unittest
from PyQt5.QtWidgets import QFrame
from numpy.lib.function_base import rot90

from references.tp4 import FRAME_SIZE

HEADER_SIZE = 4
FRAME_SIZE = 56*16*4*8
PACKET_SIZE = HEADER_SIZE + FRAME_SIZE
IMAGE_SIZE = (446, 512)

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)

class imageCoordinateOrigin():
    bottom_left = 1
    bottom_right = 2
    top_left = 3
    top_right = 4

class timepix4PixelMatrix():
    # The TOP and Bottom pixel matrix in timepix4 
    # The matrix is set in the following format
    # (EOC edge address, Super Pixel Group, Super Pixel, Pixel)
    top_matrix = np.zeros((223, 16, 4, 8))
    bottom_matrix = np.zeros((223, 16, 4, 8))

# Rotates a pixel matrix by 180 degrees.(Used for Top Matrix)
def cooridate_rot180(x:int, y:int, matrix_shape:tuple = (448,256)):
    return matrix_shape[0] - x - 1, matrix_shape[1] - y - 1

# Converts image coordinates to pixel matrix coordinates
def image_to_matrix_coordinates(x:int, y:int, origin=imageCoordinateOrigin.bottom_left):
    
    # Determine if in Top or Bottom Matrix
    TopMatrix = 1 if y >= 256 else 0
    # Rotate the Top Matrix after removing index for Bottom Matrix
    if TopMatrix:
        x, y = cooridate_rot180(x, y-256)
    
    # Find EOC edge address
    EOC_edge_address = x // 2

    # Find Super Pixel Group
    SPGroup = y // 16

    # Find Super Pixel
    SPixel = (y // 4) % 4

    # Find Pixel
    Pixel = (y % 4) + ((x % 2) * 4)

    return TopMatrix, EOC_edge_address, SPGroup, SPixel, Pixel


class TestUtilFunctions(unittest.TestCase):
    def test_coordinate_rot180(self):
        matrix_shape = (15,10)
        test_matrix = np.reshape(np.arange(15*10, dtype=int), matrix_shape)
        result_matrix = np.zeros(matrix_shape, dtype=int)
        for x in range(matrix_shape[0]):
            for y in range(matrix_shape[1]):
                coord = cooridate_rot180(x, y, matrix_shape=matrix_shape)
                result_matrix[coord[0], coord[1]] = test_matrix[x,y]
        self.assertTrue(np.equal(np.rot90(np.rot90(test_matrix)), result_matrix).all())
    
    def test_image_to_matrix_coordinates(self):
        matrix_shape = (448,512)
        BottomMatrix = np.zeros((448, 256), dtype=tuple)
        TopMatrix = np.zeros((448, 256), dtype=tuple)
        EOC = 0
        FirstCol = True
        for x in range(448):
            SPGroup = 0
            SPixel = 0
            Pixel = 0 if FirstCol else 4
            for y in range(256):
                BottomMatrix[x,y] = (0, EOC, SPGroup, SPixel, Pixel)
                TopMatrix[x,y] = (1, EOC, SPGroup, SPixel, Pixel)
                if FirstCol:
                    Pixel += 1
                    SPixel += Pixel // 4
                    SPGroup += SPixel // 4
                    Pixel = Pixel % 4
                    SPixel = SPixel % 4
                else:
                    Pixel += 1
                    SPixel += Pixel // 8
                    SPGroup += SPixel // 4
                    Pixel = 4 if Pixel >= 8 else Pixel
                    SPixel = SPixel % 4
            FirstCol = not FirstCol
            EOC += 1 if FirstCol else 0
        
        TopMatrix = np.rot90(np.rot90(TopMatrix))

        Matrix = np.concatenate((BottomMatrix, TopMatrix), axis=1)

        test_matrix = np.zeros(matrix_shape, dtype=tuple)
        for x in range(matrix_shape[0]):
            for y in range(matrix_shape[1]):
                test_matrix[x, y] = image_to_matrix_coordinates(x, y)
        self.assertTrue(np.equal(test_matrix, Matrix).all())


def main():
    pass

if __name__ == "__main__":
    unittest.main(verbosity=2)