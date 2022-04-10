"""This is the main file. This file handling user input and displaying the current game state object"""

from ctypes.wintypes import HICON
import ChessEngine
import pygame as p

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

""" Initialize a global dictionaty images. And this is called only one"""
def LoadImages():
    pieces = ['wR', 'wN', 'wB', 'wQ', 'wK', 'wp', 'bR', 'bN', 'bB', 'bQ', 'bK', 'bp']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + '.png'), (SQ_SIZE, SQ_SIZE))

"""The main driver for our code. This will handle user input and updating graphics"""
def main():
    p.init()
    screen = p.display.set_mode((HEIGHT, WIDTH))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameStart()
    LoadImages()
    running = True
    validMove = gs.GetValidMove()
    moveMade = False #flag when move is made
    animate = False # flag when to animate move
    sqSelected = () #none of square is selected, keep tracking of the last click of the user(tuple (row, col))
    playerClicks = [] #keep tracking of player clicks (two tuple [(6, 4), (4, 4)])
    gameOver = False
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver:
                    location = p.mouse.get_pos() #(x, y) location of mouse
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    if sqSelected == (row, col): #if square is already choose
                        sqSelected = () #deselect it
                        playerClicks = []
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected)
                    if len(playerClicks) == 2:
                        move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board) 
                        print(move.GetChessNotation()) #use for debug
                        for i in range(len(validMove)):
                            if move == validMove[i]:
                                gs.makeMove(validMove[i])   #this move is not the same as validMove[i] so if we use move we can get some trouble with espassant or castlling move
                                moveMade = True
                                animate = True
                                sqSelected = () #reset user click
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]
            #key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    if not gameOver:
                        gs.undoMove()
                        moveMade = True
                        animate = False
                if e.key == p.K_r:
                    gs = ChessEngine.GameStart()
                    validMove = gs.GetValidMove()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False

            if moveMade:
                if animate:
                    AnimateMove(gs.moveLog[-1], screen, gs.board, clock)
                validMove = gs.GetValidMove()
                moveMade = False
                animate = False

        drawGameState(screen, gs, validMove, sqSelected) 

        if gs.checkMate:
            gameOver = True
            if gs.whiteToMove:
                DrawText(screen, 'Black win by checkmate')
            else:
                DrawText(screen, 'White win by checkmate')
        elif gs.staleMate:
            gameOver = True
            DrawText(screen, 'Stalemate')
           
        clock.tick(MAX_FPS)
        p.display.flip()

def DrawHightLightSquare(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'):
            #hight light selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100) #transperancy value -> 0 transparent; 255 opaque
            s.fill(p.Color('blue'))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            s.fill(p.Color('yellow')) #color of square that piece can move to
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE)) 


def drawGameState(screen, gs, validMoves, sqSelected):
    DrawBoard(screen)   #draw square on the board
    #can draw hight light suare or move suggestion(later)
    DrawHightLightSquare(screen, gs, validMoves, sqSelected)
    DrawPieces(screen, gs.board) # draw pieces on top of those square

"""
Draw the square on the board
"""
def DrawBoard(screen):
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            p.draw.rect(screen, color, p.Rect(SQ_SIZE*c, SQ_SIZE*r, SQ_SIZE, SQ_SIZE))


"""
Draw the pieces on the board in the current gamestate.board
"""
def DrawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(SQ_SIZE*c, SQ_SIZE*r, SQ_SIZE, SQ_SIZE))

def DrawText(screen, text):
    font = p.font.SysFont('Helvitca', 32, True, False)
    textObject = font.render(text, 0, p.Color('Blue'))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 - textObject.get_width()/2, HEIGHT/2 - textObject.get_height()/2)
    screen.blit(textObject, textLocation)

'''
Draw animate move
'''
def AnimateMove(move, screen, board, clock):
    global colors
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framePerSquare = 10 #frames to move one square
    frameCount = (abs(dR) + abs(dC))*framePerSquare
    for frame in range(frameCount+1):
        r, c = (move.startRow + dR*frame/frameCount, move.startCol + dC*frame/frameCount)
        DrawBoard(screen)
        DrawPieces(screen, board)
        #erease the piece from ending square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        #draw capture piece onto rectangle
        if move.pieceCaptured != '--':
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        #draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()