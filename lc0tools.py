import chess.engine
import chess
import time

def leela(args):
    lc0 = chess.engine.SimpleEngine.popen_uci(args)
    return(lc0)

def get_board(moves):
    board = chess.Board()
    if type(moves)==str:
        board.set_fen(moves)
        return(board)
    for m in moves:
        m = m.lower()
        #print(m)
        board.push_uci(m)
    return(board)

def play(args, nodes, moves = []):
    print('Playing game with arguments:', args)
    lc0 = leela(args)
    board = get_board(moves)
    #print("BOARD!!!!!!!!!!!!!!!!!!!!!!!!!")
    #print(board)
    print('starting search, nodes= ',str(nodes) )
    start = time.time()
    lc0.play(board, chess.engine.Limit(nodes=nodes))
    print('search completed in time: ', time.time() - start)
    lc0.quit()
    return(None)
