import itchat
from itchat.content import *
import os
import json
import time
import random

# constants
THINK_RANGE = 3

#===== Global variables
players = []
gameState = 'idle'
questions = None
questionTurn = 0
isTextReplyActive = False

#====== Result Calculator
def calcResult():
    global players

    player1Result = calcPlayer(players[0])
    player2Result = calcPlayer(players[1])
    print('player1Result', player1Result)
    print('player2Result', player2Result)

    return (player1Result, player2Result)

def printPlayerResult(playerType, player, r):
    return u"%s 的类型为：%s，得分情况： E%d, I%d, N%d, S%d, F%d, T%d, J%d, P%d" % \
        (player['nickName'], playerType, r['E'], r['I'], r['N'], r['S'], r['F'], r['T'], r['J'], r['P'])

def calcType(playerResult):
    playerType = ''
    # EI
    if (playerResult['E'] > playerResult['I']):
        playerType += 'E'
    else:
        playerType += 'I'
    # NS
    if (playerResult['N'] > playerResult['S']):
        playerType += 'N'
    else:
        playerType += 'S'
    # FT
    if (playerResult['F'] > playerResult['T']):
        playerType += 'F'
    else:
        playerType += 'T'
    # JP
    if (playerResult['J'] > playerResult['P']):
        playerType += 'J'
    else:
        playerType += 'P'
    
    return playerType

def calcPlayer(player):
    result = {'E': 0, 'I': 0, 'N': 0, 'S': 0, 'F': 0, 'T': 0, 'J': 0, 'P': 0}
    for choice in player['choices']:
        if 'E' == choice['value']:
            result['E'] += 1
        if 'I' == choice['value']:
            result['I'] += 1
        if 'N' == choice['value']:
            result['N'] += 1
        if 'S' == choice['value']:
            result['N'] += 1
        if 'F' == choice['value']:
            result['F'] += 1
        if 'T' == choice['value']:
            result['T'] += 1
        if 'J' == choice['value']:
            result['J'] += 1
        if 'P' == choice['value']:
            result['P'] += 1
    return result

def loadTypeDescription(playerType):
    path = os.path.join(os.getcwd(), 'types', '%s.txt' % playerType)
    print('start to load %s' % path)
    with open(path, 'r') as fp:
        text = fp.read()
        return text

#====================== Player functions
def createPlayer(id, nickName):
    return {
        'id': id,
        'nickName': nickName,
        'choices': [],
        'selected': False
    }

def getPlayer(id):
    global players

    for player in players:
        if (player['id'] == id):
            return player
    return None

def resetPlayerSelectState():
    global players

    for player in players:
        player['selected'] = False

def isBothPlayersSelected():
    global players

    return players[0]['selected'] and players[1]['selected']

#==================== Question functions
def loadQuestions():
    global questions

    cwd = os.getcwd()
    with open(os.path.join(cwd, 'q.json')) as fp:
        questions = json.load(fp)

def getQuestionFormat(q):
    global questionTurn

    a = q['choices'][0]
    b = q['choices'][1]
    return "%d. %s\n  A. %s\n  B. %s" % (questionTurn+1, q['text'], a['value'], b['value'])

def getChoiceKey(q, choice):
    if choice == 'a' or choice == 'A':
        return q['choices'][0]['key']
    if choice == 'b' or choice == 'B':
        return q['choices'][1]['key']

    return None

#==================== Game handlers
def idleHandler(msg):
    global gameState, questions

    if msg.text == 'MBTI':
        msg.user.send(u'开始加载题库...')
        loadQuestions()
        think()
        msg.user.send(u'MBTI 类型测试题库（%d题）已加载完毕~' % len(questions))
        think()
        msg.user.send(u'请双方回复数字 1 确认身份。')
        gameState = 'ready'

def readyHandler(msg):
    global gameState, players

    if msg.text == '1':
        if not getPlayer(msg.ActualUserName):
            player = createPlayer(msg.ActualUserName, msg.ActualNickName)
            players.append(player)
            msg.user.send(u'@%s\u2005 身份已确认' % msg.ActualNickName)
            if len(players) == 2:
                think()
                gameStart(msg)
        else:
            msg.user.send(u'请不要重复确认')

def gameStart(msg):
    global gameState, questions, questionTurn

    msg.user.send(u'人数确认完毕, 双方准备答题')
    think()
    gameState = 'play'

    questionTurn = 0
    q = questions[questionTurn]
    msg.user.send(getQuestionFormat(q))

def endHandler(msg):
    global players, gameState, questions, questionTurn, isTextReplyActive

    msg.user.send('测试结束，正在计算特征类型得分结果...')
    player1Result, player2Result = calcResult()
    player1Type = calcType(player1Result)
    player2Type = calcType(player2Result)
    player1Result = printPlayerResult(player1Type, players[0], player1Result)
    player2Result = printPlayerResult(player2Type, players[1], player2Result)
    think()
    msg.user.send(u'%s\n\n%s' % (player1Result, player2Result))

    # get type description
    think()
    msg.user.send(u'正在获取类型详细数据...')
    playerTypeDesc = loadTypeDescription(player1Type)
    think()
    msg.user.send(playerTypeDesc)
    playerTypeDesc = loadTypeDescription(player2Type)
    think()
    msg.user.send(playerTypeDesc)

    # reset global variables
    players = []
    gameState = 'idle'
    questions = None
    questionTurn = 0
    isTextReplyActive = False

def gameOver():
     global questions, questionTurn

     return questionTurn >= len(questions) - 1

def playHandler(msg):
    global questions, questionTurn, players
    print('player1.selected', players[0]['selected'])
    print('player2.selected', players[1]['selected'])

    player = getPlayer(msg.ActualUserName)

    if isChoice(msg.text) and not player['selected']:
        currQ = questions[questionTurn]
        choiceKey = getChoiceKey(currQ, msg.text.strip())
        player['choices'].append({'turn': questionTurn, 'value': choiceKey})
        player['selected'] = True

        if isBothPlayersSelected(): 
            if gameOver():
                endHandler(msg)
            else:
                resetPlayerSelectState()
                questionTurn += 1
                if questionTurn >= len(questions):
                    questionTurn = len(questions) - 1
                nextQ = questions[questionTurn]
                msg.user.send(getQuestionFormat(nextQ))

def isChoice(text):
    if not text:
        return False
    else:
        trimed = text.strip()
        return trimed == 'a' or \
            trimed == 'A' or \
            trimed == 'b' or \
            trimed == 'B'

#==================== Bot message handlers
@itchat.msg_register(TEXT, isGroupChat=True)
def text_reply(msg):
    global players, gameState, isTextReplyActive

    print('current game state', gameState)
    # print('msg', json.dumps(msg))
    tryToActiveTextReply(msg)

    if not isTextReplyActive:
        return

    if gameState == 'idle':
        idleHandler(msg)
    if gameState == 'ready':
        readyHandler(msg)
    if gameState == 'play':
        playHandler(msg)

def tryToActiveTextReply(msg):
    global isTextReplyActive

    if msg.User and msg.User.Self and msg.User.Self.NickName:
        activeCommand = '@%s help' % msg.User.Self.NickName

        if activeCommand == msg.Content:
            isTextReplyActive = True
            msg.user.send(u'我已被激活，回复 MBTI 开始测试~')

def think():
    time.sleep(random.randrange(THINK_RANGE) + 1)

if __name__ == "__main__":
    itchat.auto_login(enableCmdQR=2)
    itchat.run(True)