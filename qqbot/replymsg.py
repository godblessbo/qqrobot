# coding=utf-8
import urllib2


def getreplymsg(ret):
    # models 是应答模型 ‘收到的关键词’：‘回复的内容’
    userfunc = ''
    # fileread = open('./functionList.txt', '')
    # while 1:
    #     line = fileread.readline()
    #     if not line:
    #         break
    #     userfunc += line
    # models = eval(userfunc)
    models = {
        'hi': 'hi,什么事',
        'hello': 'hi',
        '在不': '大飞不在，有事吗',
        'admin': '!exit\n!on robot !off robot\n!on qun !off qun\n!on zu !off zu\n',
    }
    tail = '\n(本消息来自机器人--小飞)'
    for p in models:
        if p in ret:
            return models[p] + tail
        else:
            ret = ret.encode('utf-8')
            msg = urllib2.urlopen(
                'http://api.qingyunke.com/api.php?key=free&appid=0&msg=%s' % str(ret)).read()
            msg = eval(msg)
            return msg['content'] + tail
