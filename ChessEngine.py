"""
    This class responsible for store all information about chess state and all valid move at the current state
"""

from asyncio.windows_events import NULL

class GameStart():
    def __init__(self):
        """ The Board is size 8x8 with each elenment contain 2 character.
            The First character represent for color of pieces which is black or white 
            The Second character represent for type of pieces which can be rook, knight, bishop, queen, king or pawn
            "--" stand for space """
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]
        self.moveFunc = {'p' : self.GetPawnMoves,
                         'R' : self.GetRookMoves,
                         'N' : self.GetKnightMoves,
                         'B' : self.GetBishopMoves,
                         'Q' : self.GetQueenMoves,
                         'K' : self.GetKingMoves}

        self.whiteToMove = True
        self.moveLog = []
        self.WhiteKingLocation = (7, 4)
        self.BlackKingLocation = (0, 4)
        self.checkMate = False
        self.staleMate = False
        self.inCheck = False
        self.pins = []
        self.checks = []

        self.enpassantPossible = () #location of enpassant square
        self.enpassantPossibleLog = []

        self.currentCastlingRights = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.wqs, 
                                                    self.currentCastlingRights.bks, self.currentCastlingRights.bqs)]

    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)
        self.whiteToMove = not self.whiteToMove #swap player
        # update king location
        if move.pieceMoved == 'wK':
            self.WhiteKingLocation = (move.endRow, move.endCol)
        if move.pieceMoved == 'bK':
            self.BlackKingLocation = (move.endRow, move.endCol)
        # make pawn promotion
        if move.isPawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + 'Q'

        # enpassant handler
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = ((move.endRow + move.startRow) // 2, move.startCol) 
        else:
            self.enpassantPossible = ()

        # make enpassant move
        if move.isEnpassant:
            self.enpassantPossibleLog.append(self.enpassantPossible)
            move.pieceCaptured = self.board[move.startRow][move.endCol]
            self.board[move.startRow][move.endCol] = '--'

        # make castle move
        if move.isCastle:
            if move.endCol - move.startCol == 2:    #king side castle
                self.board[move.endRow][move.endCol-1] = self.board[move.endRow][move.endCol+1] #place rook next to king
                self.board[move.endRow][move.endCol+1] = '--'   #remove old rook
            else:   #Queen side casle
                self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-2]
                self.board[move.endRow][move.endCol-2] = '--'   #same as above
        
        #update castling rights
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.wqs, 
                                                    self.currentCastlingRights.bks, self.currentCastlingRights.bqs))
        
    '''
    undo last move
    '''
    def undoMove(self):
        if (len(self.moveLog) != 0):
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove
            #update king location
            if move.pieceMoved == 'wK':
                self.WhiteKingLocation = (move.startRow, move.startCol)
            if move.pieceMoved == 'bK':
                self.BlackKingLocation = (move.startRow, move.startCol)

            #undo enpassant move
            if move.isEnpassant:
                self.board[move.endRow][move.endCol] = '--'     #this square should be empty not enemy pawn
                self.board[move.startRow][move.endCol] = move.pieceCaptured #this is the right square
                self.enpassantPossible = self.enpassantPossibleLog.pop() #allow enpassant next move 
            #undo 2 square pawn advance should make enpassant possible = () again
            if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
                self.enpassantPossible = ()

            #undo castle move
            if move.isCastle:
                #undo move
                if move.endCol - move.startCol == 2:    #king side castle
                    self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-1] #place back the rook
                    self.board[move.endRow][move.endCol-1] = '--'   #remove old rook
                else:   #Queen side castle
                    self.board[move.endRow][move.endCol-2] = self.board[move.endRow][move.endCol+1]
                    self.board[move.endRow][move.endCol+1] = '--'
            #update current and track log of castle rights
            self.castleRightsLog.pop()
            castleRights = self.castleRightsLog[-1]
            self.currentCastlingRights.wks = castleRights.wks
            self.currentCastlingRights.wqs = castleRights.wqs
            self.currentCastlingRights.bks = castleRights.bks
            self.currentCastlingRights.bqs = castleRights.bqs    
                

    # '''naive algorithm '''

    # def GetValidMove(self):
    #     # 1/ Generate all valid move
    #     moves = self.GetAllPossibleMove()
    #     # 2/ make a move in valid move
    #     for i in range(len(moves) - 1, -1, -1):
    #         self.makeMove(moves[i])
    #         # 3/ generate all opponent move to see if they attack ally king
    #         # 4/ remove all the move that opponent can attack your king
    #         self.whiteToMove = not self.whiteToMove
    #         if self.IsCheck():
    #             moves.remove(moves[i]) #5/ this move is not valid cuz they're attacking your king
    #         self.whiteToMove = not self.whiteToMove
    #         self.undoMove()
    #     if len(moves) == 0: #neither check mate and stale mate
    #         if self.IsCheck():
    #             self.checkMate = True
    #         else:
    #             self.staleMate = True
    #     else:
    #         self.checkMate = self.staleMate = False
    #     return moves
    
    # def IsCheck(self):
    #     if self.whiteToMove:
    #         return self.SquareIsAttacked(self.WhiteKingLocation[0], self.WhiteKingLocation[1])
    #     else:
    #         return self.SquareIsAttacked(self.BlackKingLocation[0], self.BlackKingLocation[1])

    def updateCastleRights(self, move):
        if move.pieceMoved == 'wK':
            self.currentCastlingRights.wks = False
            self.currentCastlingRights.wqs = False
        if move.pieceMoved == 'bK':
            self.currentCastlingRights.bks = False
            self.currentCastlingRights.bqs = False
        if move.pieceMoved == 'wR':
            if move.startCol == 7:
                self.currentCastlingRights.wks = False
            if move.startCol == 0:
                self.currentCastlingRights.wqs = False
        if move.pieceMoved == 'bR':
            if move.startCol == 7:
                self.currentCastlingRights.bks = False
            if move.startCol == 0:
                self.currentCastlingRights.bqs = False

    def SquareIsAttacked(self, r, c):
        self.whiteToMove = not self.whiteToMove #switch to opp move so we can get opponent's move
        oppMoves = self.GetAllPossibleMove()    
        self.whiteToMove = not self.whiteToMove #switch back to current player's turn
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:   #this square(r, c) is under attack
                return True
        return False

    '''advance algorithm'''
    def GetValidMove(self):
        moves = []
        self.inCheck, self.pins, self.checks = self.CheckForPinsAndCheck()
        if self.whiteToMove:
            kingRow = self.WhiteKingLocation[0]
            kingCol = self.WhiteKingLocation[1]
        else:
            kingRow = self.BlackKingLocation[0]
            kingCol = self.BlackKingLocation[1]

        if self.inCheck:
            if len(self.checks) == 1:
                moves = self.GetAllPossibleMove()
                #to block a check, you must move your piece into square beetween enemy and king
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol]
                validSquares = []
                #if the piece is checking is knight, you must capture this knight or move your king
                if pieceChecking[1] == 'N':
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8):
                        validSquare = (kingRow + check[2] * i, kingCol + check[3] * i) #check[2] and check[3] are check direction
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol:   #once it reach piece checking, stop continue checking  
                            break
                #get rid of all the move that not blocking the check or move king
                for i in range(len(moves) -1, -1, -1):
                    if moves[i].pieceMoved[1] != 'K':
                        if not (moves[i].endRow, moves[i].endCol) in validSquares:
                            moves.remove(moves[i])
            else:   #in case double check only king move is valid
                self.GetKingMoves(kingRow, kingCol, moves)
        else:
            moves = self.GetAllPossibleMove()
            self.GetCastleMoves(kingRow, kingCol, moves)
        
        if len(moves) == 0: #doesn't have any valid move so end up to game over
            if self.inCheck:
                self.checkMate = True
                self.staleMate = False
            else:
                self.checkMate = False
                self.staleMate = True
        return moves

    def CheckForPinsAndCheck(self):
        pins = []   # store the location of pieces is pinned and direction pin from
        checks = [] #store the type of the piece is checking
        inCheck = False
        if self.whiteToMove:
            allyColor = 'w'
            enemyColor = 'b'
            startRow = self.WhiteKingLocation[0]
            startCol = self.WhiteKingLocation[1]
        else:
            allyColor = 'b'
            enemyColor = 'w'
            startRow = self.BlackKingLocation[0]
            startCol = self.BlackKingLocation[1]

        #check outward from king for pins and check, keep track on pins
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range (len(directions)):
            d = directions[j]
            possiblePins = ()   #mark for piece that possible a pin piece
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePins == ():
                            possiblePins = (endRow, endCol, d[0], d[1])
                        else:
                            break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        # there are 5 possiblities we might face again
                        # 1/ orthogonally away from king and it's a rook
                        # 2/ diagonally away from king and it's a bishop
                        # 3/ 1 square away diagonally from king and it's a pawn
                        # 4/ any direction from king and it's a quuen
                        # 5/ any direction 1 square away from king and it's a another king
                        if (0 <= j <= 3 and type == 'R') or \
                            (4 <= j <= 7 and type == 'B') or \
                            (i == 1 and type == 'p' and ((enemyColor == 'w' and 6 <= j <= 7) or (enemyColor == 'b' and 4 <= j <= 5))) or \
                            (type == 'Q') or (i == 1 and type == 'K'):
                            if possiblePins == ():  #there were no blocking piece
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else:   #piece is blocking will be pinned
                                pins.append(possiblePins)
                                break
                        else: #none of enemy is checking
                            break
                else:
                    break
        
        #check for kngiht check
        KnightMoves = ((2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2))
        for m in KnightMoves:
            endRow = startRow + m[0]
            endCol = startRow + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N':
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
        
        return inCheck, pins, checks


    def GetAllPossibleMove(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunc[piece](r, c, moves) #call the approiate move function base on piece type
        return moves
    
    '''
    Get all the pawns moves for the located row and col and these move to moves 
    '''
    def GetPawnMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.whiteToMove:
            moveAmount = -1
            startRow = 6
            enemyColor = 'b'
        else:
            moveAmount = 1
            startRow = 1
            enemyColor = 'w'

        if self.board[r + moveAmount][c] == '--':
            if not piecePinned or pinDirection == (moveAmount, 0):
                moves.append(Move((r, c), (r + moveAmount, c), self.board))
                if r == startRow and self.board[r + moveAmount*2][c] == '--':
                    moves.append(Move((r, c), (r + moveAmount*2, c), self.board))
        #pawn capture
        if c-1 >= 0:
            if not piecePinned or pinDirection == (moveAmount, -1):
                if self.board[r + moveAmount][c-1][0] == enemyColor:
                    moves.append(Move((r, c), (r + moveAmount, c-1), self.board))
                if (r+moveAmount, c-1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r + moveAmount, c-1), self.board, enpassant = True))

        if c+1 <= 7:
            if not piecePinned or pinDirection == (moveAmount, 1):
                if self.board[r + moveAmount][c+1][0] == enemyColor:
                    moves.append(Move((r, c), (r + moveAmount, c+1), self.board))
                if (r+moveAmount, c+1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r + moveAmount, c+1), self.board, enpassant = True))
   
    '''
    Get all the Rooks moves for the located row and col and these move to moves 
    '''
    def GetRookMoves(self, r, c, moves):
        direction = ((-1, 0), (1, 0), (0, 1), (0, -1))
        enemyColor = 'b' if self.whiteToMove else 'w'
        piecePinned = False
        pinDirection = ()

        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])      
                if self.board[r][c] != 'Q':
                    self.pins.remove(self.pins[i])
                break

        for dir in direction:
            for i in range(1, 8):
                endRow = r + dir[0] * i
                endCol = c + dir[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == dir or pinDirection == (-dir[0], -dir[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == '--':
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else: # meet ally piece
                            break
                else: #out of board
                    break

    '''
    Get all the Kinghts moves for the located row and col and these move to moves 
    '''
    def GetKnightMoves(self, r, c, moves):
        direction = ((2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2))
        piecePinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break

        allyColor = 'w' if self.whiteToMove else 'b'
        for dir in direction:
            endRow = r + dir[0]
            endCol = c + dir[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8: #onboard
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyColor:
                        moves.append(Move((r, c), (endRow, endCol), self.board))

    '''
    Get all the Bishops moves for the located row and col and these move to moves 
    '''
    def GetBishopMoves(self, r, c, moves):
        enemyColor = 'b' if self.whiteToMove else 'w'
        piecePinned = False
        pinDirection = ()

        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])      
                self.pins.remove(self.pins[i])
                break

        direction = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        for dir in direction:
            for i in range(1, 8):
                endRow = r + dir[0] * i
                endCol = c + dir[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == dir or pinDirection == (-dir[0], -dir[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == '--':
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else: # meet ally piece
                            break
                else: #out of board
                    break
    '''
    Get all the Queen moves for the located row and col and these move to moves 
    '''
    def GetQueenMoves(self, r, c, moves):
        self.GetBishopMoves(r, c, moves)
        self.GetRookMoves(r, c, moves)
    
    '''
    Get all the King moves for the located row and col and these move to moves 
    '''
    def GetKingMoves(self, r, c, moves):
        direction = ((-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, 1), (0, -1))
        allyColor = 'w' if self.whiteToMove else 'b'
        for dir in direction:
            endRow = r + dir[0]
            endCol = c + dir[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8: #onboard
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                    #temporary put king in next move to see if they are in check so those move is not valid
                    if allyColor == 'w':
                        self.WhiteKingLocation = (endRow, endCol)
                    else:
                        self.BlackKingLocation = (endRow, endCol)
                    
                    inCheck, pins, checks = self.CheckForPinsAndCheck()
                    if not inCheck:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    #place king back to original location
                    if allyColor == 'w':
                        self.WhiteKingLocation = (r, c)
                    else:
                        self.BlackKingLocation = (r, c)     
    
    def GetCastleMoves(self, r, c, moves):
        # if self.inCheck:
        #     return    #we not use cuz we know we call castle when it not in check before
        if (self.whiteToMove and self.currentCastlingRights.wks) or (not self.whiteToMove and self.currentCastlingRights.bks):
            self.GetKingSideCastle(r, c, moves)
        if (self.whiteToMove and self.currentCastlingRights.wqs) or (not self.whiteToMove and self.currentCastlingRights.bqs):
            self.GetQueenSideCastle(r, c, moves)

    def GetKingSideCastle(self, r, c, moves):
        if self.board[r][c+1] == '--' and self.board[r][c+2] == '--':
            if not self.SquareIsAttacked(r, c+1) and not self.SquareIsAttacked(r, c+2):
                moves.append(Move((r, c), (r, c+2), self.board, castle=True))

    def GetQueenSideCastle(self, r, c, moves):
        if self.board[r][c-1] == '--' and self.board[r][c-2] == '--' and self.board[r][c-3] == '--':
            if not self.SquareIsAttacked(r, c-1) and not self.SquareIsAttacked(r, c-2):
                moves.append(Move((r, c), (r, c-2), self.board, castle=True))

class CastleRights():
    def __init__(self, wks, wqs, bks, bqs):
        self.wks = wks
        self.wqs = wqs
        self.bks = bks
        self.bqs = bqs
    def __str__(self):
        return str(self.wks) + ", " + str(self.wqs) + ", " + str(self.bks) + ", " + str(self.bqs)

class Move():

    ranksToRows = {"1" : 7, "2" : 6, "3" : 5, "4" : 4, 
                  "5" : 3, "6" : 2, "7" : 1, "8" : 0}
    rowsToRanks = {v : k for k, v in ranksToRows.items()}
    filesToCols = {"h" : 7, "g" : 6, "f" : 5, "e" : 4, 
                  "d" : 3, "c" : 2, "b" : 1, "a" : 0}
    colsToFiles = {v : k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, enpassant = False, castle = False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        #pawn promotion
        self.isPawnPromotion = (self.pieceMoved == 'wp' and self.endRow == 0) or (self.pieceMoved == 'bp' and self.endRow == 7)

        #pawn espassant
        self.isEnpassant = enpassant

        #castle move
        self.isCastle = castle

        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def GetChessNotation(self):
        #we can change that later
        return self.GetRankFile(self.startRow, self.startCol) + self.GetRankFile(self.endRow, self.endCol)

    def GetRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    def __str__(self): #call for debuging
        return str(self.moveID)