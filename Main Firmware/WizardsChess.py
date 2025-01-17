import ChessboardGraph
import PhysicalBoard
import UserInteractor
from ComputerVision import ComputerVision
from ComputerVision2 import ComputerVision as CV
import ChessAI


class WizardsChess:
    def __init__(self):
        print("initializing")
        self.chess_ai = ChessAI.ChessAI()
        self.user_interactor = UserInteractor.UserInteractor()
        self.physical_board = PhysicalBoard.PhysicalBoard()
        self.is_game_finished = False
        self.path_generator = ChessboardGraph.PathGenerator()

    def start(self):
        self.is_game_finished = False
        player_mode = self.user_interactor.get_game_mode()
        # player_mode = True
        level = self.user_interactor.choose_ai_level()
        self.chess_ai.engine.configure({"Skill Level": level + 1})
        if player_mode:
            self.play_human_vs_ai()
        else:
            self.play_ai_vs_ai()

    def play_ai_vs_ai(self):
        ai_1_move = None
        ai_2_move = None
        is_ai_1_turn = True
        while not (self.is_game_finished):
            if is_ai_1_turn:
                (ai_1_move, is_capture) = self.chess_ai.play_move_auto()
                self.user_interactor.display("AI1 Played", str(ai_1_move))
                print("ai 1 ", ai_1_move)
                self.perform_move_on_board(str(ai_1_move), is_capture)
                # print(self.chess_ai.get_board())
            else:
                (ai_2_move, is_capture) = self.chess_ai.play_move_auto()
                print("ai 2 ", ai_2_move)
                self.user_interactor.display("AI2 Played", str(ai_2_move))
                self.perform_move_on_board(str(ai_2_move), is_capture)
            is_ai_1_turn = not is_ai_1_turn
            self.is_game_finished = self.chess_ai.is_game_over()

    def play_human_vs_ai(self):
        ai_move = None
        player_move = None
        # is_player_turn = self.user_interactor.get_player_starts()
        is_player_turn = False
        while not (self.is_game_finished):
            if is_player_turn:
                # capture before
                CV.save_pre_movement_image()
                is_move_performed = False
                while not (is_move_performed):

                    # we can add move suggestion here, prompt user with question, if yes, call chessAI.getMoveSuggestion and display it
                    reset = self.user_interactor.wait_for_player_confirmation()
                    if reset:
                        return
                    # input("press when played")
                    else:
                        player_move = CV.get_next_move_empty(
                            list(
                                map(
                                    lambda x: str(x),
                                    list(self.chess_ai.get_board().legal_moves),
                                )
                            ),
                            str(self.chess_ai.get_board()),
                        )
                        # player_move = CV.get_next_move(
                        #    list(map(
                        #        lambda x: str(x),
                        #        list(self.chess_ai.get_board().legal_moves),
                        #    ))
                        # )
                        # player_move = ComputerVision.get_player_move_from_camera(self.chess_ai.get_board())
                        if player_move == "":
                            self.user_interactor.display_no_move()
                        else:
                            (is_move_performed, is_capture) = self.chess_ai.play_move(
                                player_move
                            )
                            print(player_move, is_move_performed)
                            if not (is_move_performed):
                                self.user_interactor.display_try_again()
                            else:
                                self.user_interactor.display(
                                    "You played", str(player_move)
                                )
            else:
                (ai_move, is_capture) = self.chess_ai.play_move_auto()
                self.user_interactor.display("AI Played", str(ai_move))
                self.perform_move_on_board(str(ai_move), is_capture)
            is_player_turn = not is_player_turn
            self.is_game_finished = self.chess_ai.is_game_over()

        # check if draw

        # else see who won
        if is_player_turn:  # last move was done by AI
            self.user_interactor.display("AI won!", "")
            print("AI won")
        else:
            self.user_interactor.display("You won!", "")
            print("Player won")

    def perform_move_on_board(self, move, is_capture, verbose=False):
        if __debug__:
            input("confirm when move performed on board")
            return
        if is_capture:  # eliminate captured
            # Go to end position of piece (corresponding to start position of piece to eliminate)
            path = self.path_generator.get_path_to_cell(move[2:])
            if verbose:
                print("going to", move[2:], " to gutter")
            self.physical_board.move_motors(path, active_magnet=False)
            path = self.path_generator.get_path_from_cell_to_gutter(move[2:])

            self.physical_board.move_motors(path, active_magnet=True)
            print(move[2:], "in gutter")

        # Go to start position of the move, magnet off
        path = self.path_generator.get_path_to_cell(move[:2])
        if verbose:
            print("going to", move[:2])
        self.physical_board.move_motors(path, active_magnet=False)
        # Perform the move, magnet ON
        path = self.path_generator.get_path_move(move)
        if verbose:
            print("taking to", move[2:])
        self.physical_board.move_motors(path, active_magnet=True)

    def reset(self):
        self.physical_board.reset_motors()
        self.chess_ai.reset()
        self.is_game_finished = False
        self.path_generator.reset()


if __name__ == "__main__":
    instance = WizardsChess()
    while True:
        instance.start()
        instance.reset()
