# -*- coding: utf-8 -*-

from HttpClient import HttpClient
import re, random, json, os, datetime, time, thread, logging

from replymsg import getreplymsg
from replyList import replylist


class WebQQ(HttpClient):
    ClientID = 53999199
    APPID = 0
    FriendList = {}
    MaxTryTime = 5
    PSessionID = ''
    Referer = 'http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2'
    SmartQQUrl = 'http://w.qq.com/'
    qqlist = replylist

    def __init__(self, vpath, qq=0):
        self.VPath = vpath  # QRCode保存路径
        logging.basicConfig(filename='qq.log', level=logging.DEBUG,
                            format='%(asctime)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='[%Y-%m-%d %H:%M:%S]')

        self.initUrl = "https://ui.ptlogin2.qq.com/cgi-bin/login?daid=164&target=self&style=16&mibao_css=m_webqq&appid=501004106&enable_qlogin=0&no_verifyimg=1&s_url=http%3A%2F%2Fw.qq.com%2Fproxy.html&f_url=loginerroralert&strong_login=1&login_state=10&t=20131024001"

        html = self.Get(self.initUrl, self.SmartQQUrl)
        qun = False
        zu = False
        robot = True
        self.APPID = 501004106
        MiBaoCss = "m_webqq"
        JsVer = 10149

        StarTime = self.date_to_millis(datetime.datetime.utcnow())

        T = 0
        while True:
            T = T + 1
            self.Download(
                'https://ssl.ptlogin2.qq.com/ptqrshow?appid={0}&e=0&l=M&s=5&d=72&v=4&t=0.5462884965818375'.format(
                    self.APPID), self.VPath)
            logging.info('[{0}] Get QRCode Picture Success.'.format(T))
            while True:
                html = self.Get(
                    'https://ssl.ptlogin2.qq.com/ptqrlogin?webqq_type=10&remember_uin=1&login2qq=1&aid={0}&u1=http%3A%2F%2Fw.qq.com%2Fproxy.html%3Flogin2qq%3D1%26webqq_type%3D10&ptredirect=0&ptlang=2052&daid=164&from_ui=1&pttype=1&dumy=&fp=loginerroralert&action=0-0-{1}&mibao_css={2}&t=undefined&g=1&js_type=0&js_ver={3}&login_sig=&pt_randsalt=0'.format(
                        self.APPID, self.date_to_millis(datetime.datetime.utcnow()) - StarTime, MiBaoCss, JsVer),
                    self.initUrl)
                logging.info(html)
                ret = html.split("'")
                if ret[1] == '65' or ret[1] == '0':  # 65: QRCode 失效, 0: 验证成功, 66: 未失效, 67: 验证中
                    break
                time.sleep(2)
            if ret[1] == '0' or T > self.MaxTryTime:
                break

        logging.debug(ret)
        if ret[1] != '0':
            return

        if os.path.exists(self.VPath):  # 删除QRCode文件
            os.remove(self.VPath)

        html = self.Get(ret[5])

        url = self.getReValue(html, r' src="(.+?)"', 'Get mibao_res Url Error.', 0)

        if url != '':
            html = self.Get(url.replace('&amp;', '&'))
            url = self.getReValue(html, r'location\.href="(.+?)"', 'Get Redirect Url Error', 1)
            html = self.Get(url)

        self.PTWebQQ = self.getCookie('ptwebqq')

        logging.info('PTWebQQ: {0}'.format(self.PTWebQQ))

        # self.Get('http://s.web2.qq.com/proxy.html?v=20130916001&callback=1&id=1')

        while 1:
            html = self.Get(
                'http://s.web2.qq.com/api/getvfwebqq?ptwebqq={0}&clientid={1}&psessionid=&t={2}'.format(self.PTWebQQ,
                                                                                                        self.ClientID,
                                                                                                        StarTime),
                self.Referer)
            logging.debug(html)
            ret = json.loads(html)

            if ret['retcode'] != 0:
                break

            self.VFWebQQ = ret['result']['vfwebqq']

            # self.Get('http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2', self.SmartQQUrl)

            html = self.Post('http://d1.web2.qq.com/channel/login2', {
                'r': '{{"ptwebqq":"{0}","clientid":{1},"psessionid":"","status":"online"}}'.format(self.PTWebQQ,
                                                                                                   self.ClientID)
            }, 'http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2')

            logging.debug(html)
            ret = json.loads(html)

            if ret['retcode'] != 0:
                break

            self.PSessionID = ret['result']['psessionid']

            logging.info('Login success')
            ############################################################################################################################

            msgId = int(random.uniform(1000, 3456)) * 10000 + 1

            E = 0
            while 1:
                html = self.Post('http://d1.web2.qq.com/channel/poll2', {
                    'r': '{{"ptwebqq":"{1}","clientid":{2},"psessionid":"{0}","key":""}}'.format(self.PSessionID,
                                                                                                 self.PTWebQQ,
                                                                                                 self.ClientID)
                }, self.Referer)

                # 超时时会返回空, 所以此处如果是空, 则继续发出请求, 不用往后走下去
                if html == '':
                    continue

                logging.info(html)

                try:
                    ret = json.loads(html)
                    E = 0
                except ValueError as e:
                    logging.debug(e)
                    E += 1
                except Exception as e:
                    logging.debug(e)
                    E += 1

                if E > 0 and E < 5:
                    time.sleep(2)
                    continue

                if E > 0:
                    logging.debug('try auto login ...')
                    break

                if ret['retcode'] == 100006:
                    break
                if ret['retcode'] == 116:  # 更新PTWebQQ值
                    self.PTWebQQ = ret['p']
                    continue
                if ret['retcode'] == 0 and ret.get('result'):
                    for msg in ret['result']:
                        msgType = msg['poll_type']
                        if msgType == 'message' and robot is True:  # QQ消息
                            txt = msg['value']['content'][1]
                            logging.debug(txt)
                            tuin = msg['value']['from_uin']
                            if not tuin in self.FriendList:  # 如果消息的发送者的真实QQ号码不在FriendList中,则自动去取得真实的QQ号码并保存到缓存中
                                try:
                                    info = json.loads(self.Get(
                                        'http://s.web2.qq.com/api/get_friend_uin2?tuin={0}&type=1&vfwebqq={1}'.format(
                                            tuin, self.VFWebQQ), self.Referer))
                                    logging.info(info)
                                    if info['retcode'] != 0:
                                        raise ValueError, info
                                    info = info['result']
                                    self.FriendList[tuin] = str(info['account'])
                                except Exception as e:
                                    logging.debug(e)
                                    continue
                            if not self.FriendList.get(tuin, 0) in self.qqlist:  # 如果消息的发送者与replyList不相同,则忽略本条消息不往下继续执行
                                continue
                            if txt[0:7] == '!on robot':
                                robot = True
                            if txt[0:8] == '!off robot':
                                robot = False
                            if txt[0:5] == '!exit':
                                exit(0)
                            if txt[0:7] == '!on qun':
                                qun = True
                            if txt[0:8] == '!off qun':
                                qun = False
                            if txt[0:6] == '!on zu':
                                zu = True
                            if txt[0:7] == 'off zu':
                                zu = False
                            if txt is not None:
                                thread.start_new_thread(self.runCommand, (tuin, txt, msgId))
                                msgId += 1

                        elif msgType == 'sess_message':  # QQ临时会话的消息
                            logging.debug(msg['value']['content'][1])
                        elif msgType == 'group_message' and qun is True:  # 群消息
                            txt = msg['value']['content'][1]
                            logging.debug("QQGroup Message:" + txt)
                        elif msgType == 'discu_message' and zu is True:  # 讨论组的消息
                            txt = msg['value']['content'][1]
                            logging.debug("Discu Message:" + txt)
                        elif msgType == 'kick_message':  # QQ号在另一个地方登陆,被挤下线
                            logging.error(msg['value']['reason'])
                            raise Exception, msg['value']['reason']  # 抛出异常,重新启动WebQQ,需重新扫描QRCode来完成登陆
                            break
                        elif msgType != 'input_notify':
                            logging.debug(msg)

    def runCommand(self, fuin, cmd, msgId):
        ret = ''
        try:
            ret = getreplymsg(cmd)
        except Exception, e:
            ret += e

        self.Post("http://d1.web2.qq.com/channel/send_buddy_msg2", {
            'r': '{{"to":{0},"content":"[\\"{4}\\",[\\"font\\",{{\\"name\\":\\"宋体\\",\\"size\\":10,\\"style\\":[0,0,0],\\"color\\":\\"000000\\"}}]]","face":570,"clientid":{2},"msg_id":{1},"psessionid":"{3}"}}'.format(
                fuin, msgId, self.ClientID, self.PSessionID, ret)
        }, self.Referer)

    def getReValue(self, html, rex, er, ex):
        v = re.search(rex, html)
        if v is None:  # 如果匹配失败
            logging.error(er)  # 记录错误
            if ex:  # 如果条件成立,则抛异常
                raise Exception, er
            return ''
        return v.group(1)  # 返回匹配到的内容

    def date_to_millis(self, d):
        return int(time.mktime(d.timetuple())) * 1000


if __name__ == "__main__":
    vpath = './v.png'
    qq = 0
    while True:
        try:
            WebQQ(vpath, qq)
        except Exception, e:
            print e
# vim: tabstop=2 softtabstop=2 shiftwidth=2 expandtab
