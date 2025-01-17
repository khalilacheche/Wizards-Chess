import cv2 as cv
import numpy as np
import imutils
import os
import math
from sklearn.cluster import KMeans
import requests


class ComputerVision:
    def centroid_histogram(clt):
        # grab the number of different clusters and create a histogram
        # based on the number of pixels assigned to each cluster
        numLabels = np.arange(0, len(np.unique(clt.labels_)) + 1)
        (hist, _) = np.histogram(clt.labels_, bins=numLabels)
        # normalize the histogram, such that it sums to one
        hist = hist.astype("float")
        hist /= hist.sum()
        # return the histogram
        return hist

    def crop_img(img):
        cropXBegin = 125
        cropXEnd = 110
        cropYTop = 25
        cropYBottom = 50
        img_cropped = imutils.rotate_bound(img, -1.5)
        img_cropped = img_cropped[
            cropYTop : img.shape[0] - cropYBottom,
            cropXBegin : img.shape[1] - cropXEnd,
            :,
        ]
        img_cropped = cv.rotate(img_cropped, cv.ROTATE_90_COUNTERCLOCKWISE)
        return img_cropped

    def classify_square(square):
        # The idea here is to classify the pixels as either part of the background or of the foreground
        # We use K-Means clustering to create both these "classes"
        flat_square = square.reshape((square.shape[0] * square.shape[1], 3))
        clt = KMeans(n_clusters=2)
        clt.fit(flat_square)
        # We will then have the centroids, which correspond to the colors of the foreground and the background
        # After that, we calculate the percentage of background and foreground pixels in the square
        hist = ComputerVision.centroid_histogram(clt)
        # We consider the square to be mostly black and the square as "full" when there's enough "foreground" pixels
        # (we consider the lower of the two percentages to belong to the foreground pixels, and if that value is high enough, i.e above 7.5% of the square)
        # We then also consider how far both colors are (foreground and background, if they are too close, we consider the square as "not full")
        return (
            min(hist) >= 0.075
            and len(hist) > 1
            and (
                ComputerVision.color_distance(
                    clt.cluster_centers_[0].astype("uint8").tolist(),
                    clt.cluster_centers_[1].astype("uint8").tolist(),
                )
                > 50
            )
        )

    def color_distance(color1, color2):
        # color is array of int in format BGR
        return math.sqrt(
            (color1[0] - color2[0]) ** 2
            + (color1[1] - color2[1]) ** 2
            + (color1[2] - color2[2]) ** 2
        )

    def get_uci_from_coordinates(coordinates):
        y = coordinates[0]
        x = 7 - coordinates[1]
        uci = chr(x + ord("a")) + str(y + 1)
        return uci

    def save_pre_movement_image():
        ComputerVision.capture("last.jpg")

    def capture(filename):
        url = "http://192.168.4.1/capture"
        req = requests.get(url)
        with open(filename, "wb") as f:
            f.write(req.content)

    def get_changed_squares():
        ComputerVision.capture("current.jpg")
        board = ComputerVision.crop_img(cv.imread("current.jpg"))
        background = ComputerVision.crop_img(cv.imread("last.jpg"))
        return ComputerVision.get_diff(board, background)

    def get_changed_squares_empty(last_board):
        ComputerVision.capture("current.jpg")
        board = ComputerVision.crop_img(cv.imread("current.jpg"))
        background = ComputerVision.crop_img(cv.imread("empty.jpg"))
        current_board = ComputerVision.get_diff_empty(board, background)
        # last board coordinates: bottom left a1
        last_board = ComputerVision.convert_board_to_array(last_board)
        print(current_board)
        print(last_board)
        res = []
        for x in range(8):
            for y in range(8):
                if last_board[x][y] != current_board[x][y]:
                    res.append(ComputerVision.get_uci_from_coordinates((x, y)))
        return res

    def convert_board_to_array(board):
        res = [
            [(c if c == "." else "x") for c in line.replace(" ", "")]
            for line in board.split("\n")
        ]
        res.reverse()
        for l in res:
            l.reverse()
        return res

    def get_next_move_empty(legal_moves, last_board):
        changed_squares = ComputerVision.get_changed_squares_empty(last_board)
        print(changed_squares)
        move = ""
        # we could have a problem when player wants to make an illegal move
        if len(changed_squares) == 1:
            # check for legal moves and return it if there's exactly one that corresponds to the move we have but a problem might be that the person makes an illegal move and by chance the piece that detected the difference cna be moved in another way
            possible_moves = [a for a in legal_moves if (changed_squares[0] in a)]
            if len(possible_moves) == 1:
                move = possible_moves[0]
        if len(changed_squares) == 2 or len(changed_squares) == 3:
            move_combinations = ComputerVision.get_move_combinations(changed_squares)
            possible_moves = [a for a in move_combinations if (a in legal_moves)]
            print(possible_moves)
            if len(possible_moves) == 1:
                move = possible_moves[0]
        if len(changed_squares) == 4:
            # should be an ideal case of detecting a castling move (=> verify if the moves correspond to a castling, if this is the case, return it)
            print()

        return move

    def get_next_move(legal_moves):
        changed_squares = ComputerVision.get_changed_squares()
        move = ""
        print("changed squares", changed_squares)
        print("legal moves", legal_moves)
        # we could have a problem when player wants to make an illegal move
        if len(changed_squares) == 1:
            # check for legal moves and return it if there's exactly one that corresponds to the move we have but a problem might be that the person makes an illegal move and by chance the piece that detected the difference cna be moved in another way
            possible_moves = [a for a in legal_moves if (changed_squares[0] in a)]
            if len(possible_moves) == 1:
                move = possible_moves[0]
        if len(changed_squares) == 2 or len(changed_squares) == 3:
            move_combinations = ComputerVision.get_move_combinations(changed_squares)
            possible_moves = [a for a in move_combinations if (a in legal_moves)]
            print(possible_moves)
            if len(possible_moves) == 1:
                move = possible_moves[0]
        if len(changed_squares) == 4:
            # should be an ideal case of detecting a castling move (=> verify if the moves correspond to a castling, if this is the case, return it)
            print()

        return move

    def get_diff_empty(current_board_img, last_board_img):
        subtracted = cv.absdiff(current_board_img, last_board_img)
        square_shape = (subtracted.shape[0] // 8, subtracted.shape[1] // 8)
        res = [["." for i in range(8)] for j in range(8)]
        if __debug__:
            blank = np.zeros(subtracted.shape, dtype=np.uint8)
            blank.fill(255)
        for x in range(8):
            for y in range(8):
                square = subtracted[
                    x * square_shape[0] : square_shape[0] * (x + 1),
                    y * square_shape[1] : (y + 1) * square_shape[1],
                    :,
                ]
                square_changed = ComputerVision.classify_square(square)
                if __debug__ and square_changed:
                    cv.putText(
                        img=blank,
                        text="X",
                        org=(
                            int(y * square_shape[1] + square_shape[1] * 0.5),
                            int(x * square_shape[0] + square_shape[0] * 0.5),
                        ),
                        fontFace=cv.FONT_HERSHEY_TRIPLEX,
                        fontScale=0.25,
                        color=(255, 0, 0),
                        thickness=1,
                    )
                res[x][y] = "x" if square_changed else "."
        if __debug__:
            left_display = blank
            right_display = subtracted
            merged = np.hstack((left_display, right_display))
            if len(res) == 2:
                print(res)
            cv.imshow("sub", merged)
            cv.waitKey(0)
            cv.destroyAllWindows()
        return res

    def get_diff(current_board_img, last_board_img):
        subtracted = cv.absdiff(current_board_img, last_board_img)
        square_shape = (subtracted.shape[0] // 8, subtracted.shape[1] // 8)
        if __debug__:
            blank = np.zeros(subtracted.shape, dtype=np.uint8)
            blank.fill(255)
        res = []
        for x in range(8):
            for y in range(8):
                square = subtracted[
                    x * square_shape[0] : square_shape[0] * (x + 1),
                    y * square_shape[1] : (y + 1) * square_shape[1],
                    :,
                ]
                square_changed = ComputerVision.classify_square(square)
                if square_changed:
                    if __debug__:
                        cv.putText(
                            img=blank,
                            text="X",
                            org=(
                                int(y * square_shape[1] + square_shape[1] * 0.5),
                                int(x * square_shape[0] + square_shape[0] * 0.5),
                            ),
                            fontFace=cv.FONT_HERSHEY_TRIPLEX,
                            fontScale=0.25,
                            color=(255, 0, 0),
                            thickness=1,
                        )
                    res.append(ComputerVision.get_uci_from_coordinates((x, y)))
        if __debug__:
            left_display = blank
            right_display = subtracted
            merged = np.hstack((left_display, right_display))
            if len(res) == 2:
                print(res)
            cv.imshow("sub", merged)
            cv.waitKey(0)
            cv.destroyAllWindows()
        return res

    def get_move_combinations(list_squares):
        return [x + y for x in list_squares for y in list_squares if x != y]
