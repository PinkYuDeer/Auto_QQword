import base64
import configparser
import json
import os
import re
import threading
import time

import requests
from lxml import etree


class MyThread(threading.Thread):
    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.my_result = None

    def run(self):
        self.my_result = self.func(*self.args)

    def result(self):
        self.join()  # 等待线程执行完毕
        return self.my_result


class QQ:
    myself_QQ = 0
    QQ_list = {}

    def __init__(self):
        try:
            config = configparser.RawConfigParser()
            config.read('qq.ini', encoding='utf-8')
            self.myself_QQ = config['myself']['account']
            for account, name in config['QQ_list'].items():
                self.QQ_list[account] = name if name else ''
        except FileNotFoundError:
            self.first_run()
        except KeyError:
            self.first_run()

    def first_run(self):
        count = 0
        self.myself_QQ = input('\n检测到第一次使用，请输入自己的QQ号：')
        print('请手动输入批量抽卡的QQ号和备注（QQ号和备注用空格分隔，输入空行结束）')
        while True:
            qq_data = input(f"{count + 1}: ").split(' ')
            if qq_data[0] == '':
                print('添加成功，总共添加' + str(count - 1) + '个账号')
                break
                # 检查输入合法性
            if not qq_data[0].isdigit():
                print('QQ号必须为纯数字')
                continue
            if qq_data[0] in self.QQ_list:
                print('QQ号已存在')
                continue
            if len(qq_data) > 2:
                print('备注不能有空格，请检查格式为：QQ号+空格+不含空格的备注')
                continue
            elif len(qq_data) > 1:
                if qq_data[1] == '__我':
                    print('备注不能为__我')
                    continue
                if qq_data[1] in self.QQ_list.values():
                    print('备注已存在')
                    if input('是否允许重复备注？（y/n）') == 'n':
                        continue
            self.QQ_list[qq_data[0]] = qq_data[1] if len(qq_data) > 1 else ''
            count += 1
        self.save()

    def save(self):
        fr_config = configparser.RawConfigParser()
        fr_config['myself'] = {'account': self.myself_QQ}
        fr_config['QQ_list'] = {}
        for fr_account, fr_name in self.QQ_list.items():
            fr_config['QQ_list'][fr_account] = fr_name if fr_name else ''
        with open('qq.ini', 'w', encoding='utf-8') as f:
            fr_config.write(f)


class Setting:
    setting = {}
    cookies = {}

    def __init__(self):
        try:
            config = configparser.RawConfigParser()
            config.read('setting.ini', encoding='utf-8')
            self.setting = config['setting']
            self.cookies = config['cookies']
        except FileNotFoundError:
            self.first_run()
        except KeyError:
            self.first_run()

    # 第一次运行
    def first_run(self):
        print('检测到第一次使用，请设置抽卡参数')
        self.input_setting(2)
        # 检查初始参数
        if 'QQ_locale_id' not in self.setting:
            self.setting['QQ_locale_id'] = '2052'
        if 'domainId' not in self.setting:
            self.setting['domainId'] = '338'
        if 'pgv_pvi' not in self.cookies:
            self.cookies['pgv_pvi'] = '112969728'
        if 'pgv_si' not in self.cookies:
            self.cookies['pgv_si'] = 's6262475776'
        fs_config = configparser.RawConfigParser()
        fs_config['setting'] = self.setting
        fs_config['cookies'] = self.cookies
        with open('setting.ini', 'w', encoding='utf-8') as f:
            fs_config.write(f)

    # 输入设置
    def input_setting(self, input_mode):
        if input_mode > 0:
            cookies_str = input('请输入cookies：')
            url = input('请输入url：')
            # url如：https://ti.qq.com/interactive_new/cgi-bin/friends_mutualmark/aggregate/home/get?frd_uin=747405109&version=8.9.93&bkn=1708188483
            # 解析version和bkn
            params = re.findall(r'\?(.*?)$', url)[0].split('&')
            for param in params:
                param = param.split('=')
                if param[0] == 'version':
                    self.setting['version'] = param[1]
                elif param[0] == 'bkn':
                    self.setting['bkn'] = param[1]
            for cookie in cookies_str.split('; '):
                cookie = cookie.split('=')
                if len(cookie) == 2:
                    self.cookies[cookie[0]] = cookie[1]
        if input_mode > 1 or input_mode == 0:
            self.setting['mode'] = input('请输入详细程度【1：抽卡】，【2：抽卡+统计好友关系】，【3：抽卡+预测卡池+统计好友关系】：')
        self.save()

    # 保存设置
    def save(self):
        fs_config = configparser.RawConfigParser()
        fs_config['setting'] = self.setting
        fs_config['cookies'] = self.cookies
        with open('setting.ini', 'w', encoding='utf-8') as f:
            fs_config.write(f)

    # 重置cookies
    def recover_cookies(self):
        self.input_setting(1)
        # 排序cookies
        cookies = {}
        for key in sorted(self.cookies):
            cookies[key] = self.cookies[key]
        self.cookies = cookies
        self.save()


class Words:
    words = {}

    def __init__(self):
        try:
            with open('data/words.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    data = line.strip().split(' ')
                    self.words[data[0]] = {
                        'word': data[1],
                        'description': data[2],
                        'url': data[3],
                        'first_time': data[4],
                        'last_time': data[5],
                        'count': data[6],
                        'first_qq': data[7],
                        'last_qq': data[8],
                        'qq_count': data[9]
                    }
        except FileNotFoundError:
            if not os.path.exists('data'):
                os.makedirs('data')
            with open('data/words.txt', 'w', encoding='utf-8'):
                pass

    def save(self):
        # 将已抽卡信息写入文件，按照id排序
        # 文件中每行的格式为：卡片id 卡片描述 卡片文字 卡片图片url 最早抽中时间 最近抽中时间 抽中次数 最早抽中QQ 最近抽中QQ 抽中QQ总数
        with open('data/words.txt', 'w', encoding='utf-8') as f:
            for word in sorted(self.words.items(), key=lambda x: x[0]):
                f.write(word[0] + ' ' + word[1]['word'] + ' ' + word[1]['description'] + ' ' + word[1]['url'] + ' ' +
                        word[1]['first_time'] + ' ' + word[1]['last_time'] + ' ' + word[1]['count'] + ' ' +
                        word[1]['first_qq'] + ' ' + word[1]['last_qq'] + ' ' + word[1]['qq_count'] + '\n')

    def add_word(self, word, account):
        if word[0] not in self.words:
            self.words[word[0]] = {
                'word': word[1],
                'description': word[2].replace(' ', '-'),
                'url': word[3],
                'first_time': time.strftime("%Y/%m/%d-%H:%M:%S", time.localtime()),
                'last_time': time.strftime("%Y/%m/%d-%H:%M:%S", time.localtime()),
                'count': '1',
                'first_qq': account,
                'last_qq': account,
                'qq_count': '1'
            }
        else:
            self.words[word[0]]['last_time'] = time.strftime("%Y/%m/%d-%H:%M:%S", time.localtime())
            self.words[word[0]]['count'] = str(int(self.words[word[0]]['count']) + 1)
            self.words[word[0]]['description'] = word[2].replace(' ', '-')
            self.words[word[0]]['last_qq'] = account
            self.words[word[0]]['qq_count'] = str(int(self.words[word[0]]['qq_count']) + 1)


class MyRequest:
    user_agent = 'Mozilla/5.0 (Linux; Android 8.0.0; FLA-AL20 Build/HUAWEIFLA-AL20; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/66.0.3359.126 MQQBrowser/6.2 TBS/045130 Mobile Safari/537.36 V1_AND_SQ_8.2.8_1346_YYB_D QQ/8.2.8.4440 NetType/4G WebP/0.3.0 Pixel/1080 StatusBarHeight/73 SimpleUISwitch/0 QQTheme/1000'
    host = 'ti.qq.com'
    setting = None
    cookies = {}
    data = []

    def __init__(self, setting, cookies):
        self.setting = setting
        self.cookies = cookies

    def count_relation(self, account):
        url = 'https://ti.qq.com/interactive_new/cgi-bin/friends_mutualmark/aggregate/home/get'
        params = {
            'frd_uin': account,
            'version': self.setting['version'],
            'bkn': self.setting['bkn']
        }
        headers = {
            'User-Agent': self.user_agent,
            'host': self.host,
            'Accept': 'application/json; charset=utf-8'
        }
        response = None
        try:
            response = requests.get(url, params=params, headers=headers, cookies=self.cookies)
            if response.status_code == 200:
                if json.loads(response.text)['msg'][0:22] == 'ptlogin-ex verify fail':
                    return 151
                return json.loads(response.text)['data']
            else:
                print('\033[1;31m获取好友关系失败，错误码：' + str(response.status_code) + '\033[0m')
        except requests.exceptions.RequestException as e:
            print('\033[1;31m获取好友关系失败，错误信息：' + str(e) + '\033[0m')
        except KeyError:
            print('\033[1;31m获取好友关系失败，错误信息：' + str(response.text) + '\033[0m')
        return response

    def count_words(self, account):
        url = 'https://ti.qq.com/hybrid-h5/interactive_logo/word'
        params = {
            'target_uin': account,
            '_wv': '67108867',
            '_nav_txtclr': '000000',
            '_wvSb': '0'
        }
        headers = {
            'User-Agent': self.user_agent,
            'host': self.host
        }
        try:
            response = requests.get(url, params=params, headers=headers, cookies=self.cookies)
            if response.status_code == 200:
                html = etree.HTML(response.text)
                return html
            else:
                print('\033[1;31m获取卡片信息失败，错误码：' + str(response.status_code) + '\033[0m')
        except requests.exceptions.RequestException as e:
            print('\033[1;31m获取卡片信息失败，错误信息：' + str(e) + '\033[0m')
        return None

    def refresh_chance(self, account):
        url = 'https://ti.qq.com/hybrid-h5/interactive_logo/two'
        params = {
            'target_uin': account,
            '_wv': '67108867',
            '_nav_txtclr': '000000',
            '_wvSb': '0'
        }
        headers = {
            'User-Agent': self.user_agent,
            'host': self.host
        }
        try:
            response = requests.get(url, params=params, headers=headers, cookies=self.cookies)
            if response.status_code == 200:
                return 200
            else:
                print('\033[1;31m刷新卡池失败，错误码：' + str(response.status_code) + '\033[0m')
        except requests.exceptions.RequestException as e:
            print('\033[1;31m刷新卡池失败，错误信息：' + str(e) + '\033[0m')
        return None

    def get_word(self, account: int, myself_QQ: int):
        url = 'https://ti.qq.com/proxy/domain/oidb.tim.qq.com/v3/oidbinterface/oidb_0xdd0_0'
        params = {
            'sdkappid': '39998',
            'actype': '2',
            'bkn': self.setting['bkn']
        }
        headers = {
            'User-Agent': self.user_agent,
            'host': self.host,
            'content-type': 'application/json'
        }
        data = {
            'uin': myself_QQ,
            'frd_uin': account,
        }
        try:
            response = requests.post(url, params=params, headers=headers, cookies=self.cookies, data=json.dumps(data))
            if response.status_code == 200:
                get_word_data = json.loads(response.text)
                return get_word_data
            else:
                print('\033[1;31m获取卡片失败，错误码：' + str(response.status_code) + '\033[0m')
        except requests.exceptions.RequestException as e:
            print('\033[1;31m获取卡片失败，错误信息：' + str(e) + '\033[0m')

    def get_word_status(self, account: int):
        url = 'https://ti.qq.com/proxy/domain/oidb.tim.qq.com/v3/oidbinterface/oidb_0xdd3_0'
        params = {
            'sdkappid': '39998',
            'actype': '2',
            'bkn': self.setting['bkn']
        }
        headers = {
            'User-Agent': self.user_agent,
            'host': self.host,
            'content-type': 'application/json'
        }
        data = {
            "rpt_uint64_frd_uin": account,
            "uint32_check_recentchat_timespan": 7,
            "uint32_req_pic_type": 1,
            "uint32_start_idx": 0,
            "uint32_req_count": 149
        }
        try:
            response = requests.post(url, params=params, headers=headers, cookies=self.cookies, data=json.dumps(data))
            if response.status_code == 200:
                get_word_status_data = json.loads(response.text)
                return get_word_status_data
            else:
                print('\033[1;31m获取卡池状态失败，错误码：' + str(response.status_code) + '\033[0m')
        except requests.exceptions.RequestException as e:
            print('\033[1;31m获取卡池状态失败，错误信息：' + str(e) + '\033[0m')


class MainProcess:
    def __init__(self):
        self.qq = QQ()
        self.setting = Setting()
        self.words = Words()
        self.my_request = MyRequest(self.setting.setting, self.setting.cookies)

        self.mode = int(self.setting.setting['mode'])

        self.start_time = time.time()
        self.process = 0
        self.total = len(self.qq.QQ_list)

        self.word_get_success_count = 0
        self.word_get_null_count = 0
        self.passed_account_count = 0
        self.all_account_passed = True
        self.account_count = []

        self.need_again_QQ_list = {}
        self.need_again = False
        self.again = 0

    @staticmethod
    def print_relation_data(data):
        if data == "None":
            print("\033[31m" + '获取好友关系失败' + "\033[0m\033[40m")
            return
        # 判断是否存在data['light_up_num']
        light_up_num = data['light_up_num'] if 'light_up_num' in data else 0
        try:
            if data['category_list'][3]['mutual_mark_state_list'][0]['status']['is_lightup']:
                light_up_num -= 1
        except IndexError:
            pass
        try:
            word_process = data['category_list'][3]['mutual_mark_state_list'][0]['info']['graded'][0]['desc']
            if word_process != '':
                print('\33[35m字符进度：' + word_process + '\033[0m\033[40m', end=' - ')
        except IndexError:
            print('\33[35m暂无字符进度\033[0m\033[40m', end=' - ')
            word_process = '暂无字符进度'
        rarity_light_up_num = data['rarity_light_up_num']
        if data['category_list'][2]['name'] == '幸运字符':
            Qualified_num = 0
            if data['category_list'][2]['light_up_num'] == 1:
                light_up_num -= 1
        else:
            Qualified_num = data['category_list'][2]['total_num']
        print(' 点亮标识个数：' + str(light_up_num) + '个', end='')
        if int(rarity_light_up_num) > 0:
            print('，点亮稀有标识：' + str(rarity_light_up_num) + '个', end='')
        if int(Qualified_num) > 0:
            print('，限定标识：' + str(Qualified_num) + '个', end='')
        print(":")
        mark = {}
        line_item = 0
        for category in data['category_list']:
            for mutual_mark_state in category['mutual_mark_state_list']:
                mark[mutual_mark_state['info']['intro']] = mutual_mark_state['status']['lightup_days']
                if int(mutual_mark_state['status']['lightup_days']) > 0:
                    # 如果mutual_mark_state['info']['intro']以数字开头，则输出mutual_mark_state
                    if mutual_mark_state['info']['intro'][0].isdigit():
                        level = mutual_mark_state['status']['level']
                        for i in mutual_mark_state['info']['graded']:
                            if i['level'] == level:
                                print("\033[35m新奇物种：" + i['name'] + "\033[0m\033[40m" + '|\033[32m' +
                                      mutual_mark_state['status']['lightup_days'] + '天\033[0m\033[40m', end='')
                                line_item += 1
                                if line_item == 4:
                                    print("\033[36m" + ";" + "\033[0m\033[40m")
                                    line_item = 0
                                else:
                                    print(' - ', end='')
                                break
                    else:
                        print("\033[36m" + mutual_mark_state['info']['intro'] + "\033[0m\033[40m" + '|\033[32m' +
                              mutual_mark_state['status']['lightup_days'] + '天\033[0m\033[40m', end='')
                        line_item += 1
                        if line_item == 4:
                            print("\033[36m" + ";" + "\033[0m\033[40m")
                            line_item = 0
                        else:
                            if category['mutual_mark_state_list'].index(mutual_mark_state) != len(
                                    category['mutual_mark_state_list']) - 1:
                                print(' - ', end='')
                            else:
                                print()
        return word_process, light_up_num

    def print_get_word_data(self, data, p_account):
        get = 0
        null = 0
        if data['ActionStatus'] == 'OK':
            if data['card_url'] == '':
                print("\033[37m" + '没抽中' + "\033[0m\033[40m", end=' - ')
                null += 1
                return get, null, True, 201, None
            else:
                word = [base64.b64decode(data['card_id']).decode(), base64.b64decode(data['card_word']).decode(),
                        base64.b64decode(data['rpt_wording'][0]).decode(), base64.b64decode(data['card_url']).decode()]
                print("\033[33m" + '\n抽到卡片' + "\033[0m\033[40m", end='：')
                print("\033[33m" + word[0] + "\033[0m\033[40m", end=' - ')
                print("\033[33m" + word[1] + "\033[0m\033[40m", end=' - ')
                print(word[3])
                print("\033[33m" + "卡片描述：" + str(word[2]) + "\033[0m\033[40m")
                get += 1
                self.words.add_word(word, p_account)
                return get, null, True, 200, word
        elif data['ActionStatus'] == 'FAIL':
            if data['ErrorCode'] == 10005:
                # 绿色字体输出
                print("\033[32m" + '今日次数已用完' + "\033[0m\033[40m")
                return get, null, False, 202, None
            elif data['ErrorCode'] == 10006:
                print("\033[31m" + '该QQ号不是你的好友' + "\033[0m\033[40m")
                return get, null, False, 203, None
            elif data['ErrorCode'] == 151:
                print("\033[31m" + '登录过期' + "\033[0m\033[40m")
                return get, null, False, 151, None
            elif data['ErrorCode'] == 304:
                print("\033[31m" + '请检查你自己的qq号是否有误' + "\033[0m\033[40m")
                return get, null, False, 304, None
            print(' ErrorInfo: ', data['ErrorInfo'], ' ErrorCode: ', data['ErrorCode'])
        else:
            print(data)
            return get, null, False, 404, None

    @staticmethod
    def print_get_word_status_data(data):
        if data['ActionStatus'] == 'OK':
            specialword_frdInfo = data['rpt_msg_get_specialwordlist_rsp'][0]['msg_specialword_frdInfo']

            can_get_word_count_max = specialword_frdInfo['msg_cur_specialword_cardInfo']['msg_specialword_attr']['msg_max_special_word_card_get_info'][
                'uint32_can_get_card_count']
            can_get_word_count_min = specialword_frdInfo['msg_cur_specialword_cardInfo']['msg_specialword_attr']['msg_min_special_word_card_get_info'][
                'uint32_can_get_card_count']
            print("\033[36m" + '剩余卡池：' + str(can_get_word_count_min) + '-' + str(can_get_word_count_max) + "\033[0m\033[40m", end=' - ')
        else:
            if data['ErrorCode'] == 204:
                print("读卡错误")
            else:
                print(data)

    @staticmethod
    def print_count_words_data(html):
        div_elements = html.xpath('//*[@id="app"]/div[1]/div[2]/div[3]/div[2]/div')
        if len(div_elements) > 3:
            number_of_word = len(div_elements) - 1
        else:
            number_of_word = len(div_elements)
        if number_of_word == 0:
            print("\033[35m已拥有字符：" + str(number_of_word) + "个 \033[0m\033[40m")
            return number_of_word, 0, 0
        else:
            print("\033[35m已拥有字符：" + str(number_of_word) + "个 \033[0m\033[40m", end='/')

            count = 0
            unknown = 0

            for div_element in div_elements:
                # 提取span中的文本内容
                span_texts = div_element.xpath('.//div[@class="cell-title"]/span/text()')

                if not span_texts:
                    span_texts = div_element.xpath('.//div[@class="cell-title select"]/span/text()')

                # 检查是否存在span文本
                if span_texts:
                    span_text = span_texts[0].strip()

                    # 提取url地址
                    url = div_element.xpath('.//div[@class="image-wrapper"]/div/@style')[0]
                    url_number = 0

                    # 匹配URL中的数字，考虑数字在@前或者.前的情况
                    match = re.search(r'[-_.](\d+)@|-(\d+)\.', url)

                    if match:
                        if match.group(1):
                            url_number = int(match.group(1)) - 1
                        elif match.group(2):
                            url_number = int(match.group(2))
                    else:
                        unknown += 1
                        continue

                    # 检查条件：span中的字母数量与url地址中的数字是否相等
                    if len(re.findall(r'[a-zA-Z]', span_text)) <= url_number:
                        count += 1
            if unknown == 0:
                print("\033[35m 完全点亮：" + str(count) + "张\033[0m\033[40m")
            else:
                print("\033[35m 完全点亮：" + str(count) + "张\033[0m\033[40m / \033[35m付费字符无法判断：" + str(unknown) + "张\33[0m\033[40m")
        return number_of_word, count, unknown

    @staticmethod
    def read_old_data(file_name):
        old_data = {}
        acIL = []
        summary = {}
        with open(file_name, 'r', encoding='utf-8') as f:
            state = -1
            for line in f:
                if line[0:2] == '模式':
                    # 这一行是"模式： 1"
                    state = 0
                    old_data['mode'] = line[4]
                    continue
                elif line[0:4] == 'QQ号 ':
                    state = 1
                    continue
                elif line[0:2] == '总抽':
                    state = 2
                    continue
                elif state == 1:
                    data = line.strip().split(' ')
                    acI = {
                        'account': data[0],
                        'name': data[1],
                        'word_get_total': int(data[2]),
                        'word_get_success': int(data[3]),
                        'word_get_null': int(data[4]),
                        'light_up': int(data[5]),
                        'word_have': int(data[6]),
                        'word_process': data[7],
                        'word_light_up': int(data[8]),
                        'word_unknown': int(data[9]),
                        'words': []
                    }
                    for i in range(10, len(data)):
                        data[i] = data[i].replace(' ', '')
                        if data[i] != '':
                            acI['words'].append([data[i]])
                    acIL.append(acI)
                elif state == 2:
                    data = line.strip().split(' ')
                    summary['word_get_total'] = int(data[0])
                    summary['word_get_success'] = int(data[1])
                    summary['word_get_null'] = int(data[2])
                    summary['account_count'] = int(data[3])
                    summary['passed_account_count'] = int(data[4])
            print('读取到' + str(len(acIL)) + '个账号的抽卡数据')
            old_data['account_count'] = acIL
            old_data['summary'] = summary
        return old_data

    def save_data(self):
        print('正在保存抽卡结果...')
        self.words.save()
        print('新抽字符已更新在data/words.txt中')
        file_name = 'data/' + time.strftime("%Y-%m-%d %H-%M-%S", time.localtime()) + '.txt'
        summary = {
            'word_get_total': self.word_get_success_count + self.word_get_null_count,
            'word_get_success': self.word_get_success_count,
            'word_get_null': self.word_get_null_count,
            'account_count': len(self.qq.QQ_list),
            'passed_account_count': self.passed_account_count
        }
        # data / 读取文件列表
        file_list = os.listdir('data')
        # 判断文件列表中是否存在同天的文件，忽略时分秒
        for file in file_list:
            if file[0:10] == file_name[5:15]:
                print('检测到同天的抽卡结果文件:' + file, end='，')
                # 读取该文件中的内容，然后删除该文件，将新老数据合并后写入新文件
                old_data = self.read_old_data('data/' + file)
                try:
                    old_data_mode = int(old_data['mode'])
                    if old_data_mode != self.mode:
                        print('检测到运行模式不同，已保留旧文件。')
                        continue
                    else:
                        os.remove('data/' + file)
                        print('正在合并抽卡结果...')
                    for acI in old_data['account_count']:
                        for ac in self.account_count:
                            if ac['account'] == acI['account']:
                                ac['word_get_total'] += acI['word_get_total']
                                ac['word_get_success'] += acI['word_get_success']
                                ac['word_get_null'] += acI['word_get_null']
                                ac['light_up'] = acI['light_up']
                                ac['word_have'] = acI['word_have']
                                ac['word_light_up'] = acI['word_light_up']
                                ac['word_unknown'] = acI['word_unknown']
                                for word in acI['words']:
                                    if word not in ac['words']:
                                        ac['words'].append(word)
                            else:
                                self.account_count.append(acI)
                    summary['word_get_total'] += old_data['summary']['word_get_total']
                    summary['word_get_success'] += old_data['summary']['word_get_success']
                    summary['word_get_null'] += old_data['summary']['word_get_null']
                    summary['account_count'] += old_data['summary']['account_count']
                    summary['passed_account_count'] += old_data['summary']['passed_account_count']
                except KeyError:
                    print('文件' + file + '损坏，已尽可能提取有用数据。')
                continue

        with open(file_name, 'w', encoding='utf-8') as f:
            f.write('主号码：' + self.qq.myself_QQ + '\n')
            f.write('模式：' + self.setting.setting['mode'] + '\n')
            f.write('抽卡结果：\n')
            if int(self.setting.setting['mode']) == 1:
                f.write('QQ号 备注 总抽数 抽中数 未抽中数 卡片id\n')
            elif int(self.setting.setting['mode']) == 2:
                f.write('QQ号 备注 总抽数 抽中数 未抽中数 点亮好友关系数 字符进度 卡片id\n')
            elif int(self.setting.setting['mode']) >= 3:
                f.write('QQ号 备注 总抽数 抽中数 未抽中数 点亮好友关系数 已拥有字符数 字符进度 已拥有完全点亮数 无法判断数 卡片id\n')  # 若备注为空，则备注为N/A
            for ac in self.account_count:
                ac['name'] = 'N/A' if ac['name'] == '' else ac['name']
                f.write(ac['account'] + ' ' + ac['name'] + ' ' + str(ac['word_get_total']) + ' ' +
                        str(ac['word_get_success']) + ' ' + str(ac['word_get_null']) + ' ')
                if self.mode >= 2:
                    f.write(str(ac['light_up']) + ' ')
                if self.mode >= 3:
                    f.write(str(ac['word_have']) + ' ')
                if self.mode >= 2:
                    f.write(str(ac['word_process']) + ' ')
                if self.mode >= 3:
                    f.write(str(ac['word_light_up']) + ' ' + str(ac['word_unknown']) + ' ')
                for word in ac['words']:
                    f.write(word[0] + ' ')
                f.seek(f.tell() - 1, 0)
                f.write('\n')
            f.write('\n总抽 抽中 null 总人 跳过\n')
            f.write(str(summary['word_get_total']) + ' ' + str(summary['word_get_success']) + ' ' +
                    str(summary['word_get_null']) + ' ' + str(summary['account_count']) + ' ' +
                    str(summary['passed_account_count']))
        print('抽卡结果保存在' + file_name)

    def progress_bar(self):
        progress = self.process / self.total
        progress_bar_length = 30
        done_length = int(progress * progress_bar_length)
        remaining_length = progress_bar_length - done_length

        percentage = progress * 100
        time_elapsed = time.time() - self.start_time if self.process > 0 else 0
        time_per_unit = time_elapsed / self.process if self.process > 0 else 0
        estimated_time_remaining = time_per_unit * (self.total - self.process)

        progress_bar_str = '█' * done_length + '_' * remaining_length
        if time_elapsed == 0:
            status_str = f"[{progress_bar_str}] ({percentage:.2f}%)  */秒|剩余*秒 {self.process}/{self.total}"
        else:
            status_str = (f"[{progress_bar_str}] ({percentage:.2f}%)  {self.process / time_elapsed:.2f}/秒|"
                          f"剩余{estimated_time_remaining:.2f}秒 {self.process}/{self.total}")
        # 将status_str红字输出
        if self.mode == -1:
            print("\r")
        print("\033[31m" + status_str + "\033[0m\033[40m", end='')
        if self.mode != -1:
            print()

    def get_word_in_list(self, my_list):
        print('开始抽卡...')
        self.need_again = False
        self.need_again_QQ_list = {}
        for account, name in my_list.items():
            print("\033[0;30;47m " + account + ' ' + name + " \033[0m\033[40m", end=' - ')
            if self.again == 0:
                account_count_info = {
                    'account': account,
                    'name': name,
                }
            else:
                for ac in self.account_count:
                    if ac['account'] == account:
                        account_count_info = ac
                        self.account_count.remove(ac)
                        break

            # 获取好友关系 2
            count_relation = MyThread(self.my_request.count_relation, args=(account,))

            # 抽卡 1
            refresh_chance = MyThread(self.my_request.refresh_chance, args=(account,))
            get_word = MyThread(self.my_request.get_word, args=(account, self.qq.myself_QQ))

            # 获取卡池状态 3
            get_word_status = MyThread(self.my_request.get_word_status, args=(account,))

            # 统计字符数量 2
            count_words = MyThread(self.my_request.count_words, args=(account,))

            # 开始线程
            refresh_chance.start()
            if self.mode >= 2 and self.again == 0:
                count_relation.start()
            get_word.start()
            if self.mode >= 3:
                get_word_status.start()

            # 获取线程返回值
            if self.mode >= 2 and self.again == 0:
                relation_data = count_relation.result()
                while relation_data == 151:
                    print("\033[31m" + '登录过期，正在尝试重新登录' + "\033[0m")
                    self.setting.recover_cookies()
                    self.my_request = MyRequest(self.setting.setting, self.setting.cookies)
                    count_relation = MyThread(self.my_request.get_word, args=(account, self.qq.myself_QQ))
                    count_relation.start()
                    relation_data = count_relation.result()
                account_count_info['word_process'], account_count_info['light_up'] = self.print_relation_data(relation_data)
                print("-------------------------------------------")
            is_passed = True
            get_No = 0
            word_gets = []
            account_get = 0
            account_null = 0
            while True:
                get_No += 1
                if get_No == 1:
                    account_get = 0
                    account_null = 0
                if get_No == 2 or self.again > 0:
                    refresh_chance.join()
                if self.mode >= 3:
                    self.print_get_word_status_data(get_word_status.result())
                p_get, p_null, p_success, status_code, p_word = self.print_get_word_data(get_word.result(), account)
                if status_code == 151:
                    self.setting.recover_cookies()
                    self.my_request = MyRequest(self.setting.setting, self.setting.cookies)
                    get_word = MyThread(self.my_request.get_word, args=(account, self.qq.myself_QQ))
                    get_word.start()
                    if self.mode >= 3 and self.again == 0:
                        get_word_status = MyThread(self.my_request.get_word_status, args=(account,))
                        get_word_status.start()
                    continue
                elif status_code == 201:
                    if get_No == 2:
                        self.need_again_QQ_list[account] = name
                        self.need_again = True
                    if self.again > 0:
                        for ac in self.account_count:
                            if ac['account'] == account and ac['word_get_total'] < 3:
                                self.need_again_QQ_list[account] = name
                                self.need_again = True
                                break

                self.word_get_success_count += p_get
                self.word_get_null_count += p_null
                account_get += p_get
                account_null += p_null
                if p_word is not None:
                    word_gets.append(p_word[0])
                if p_success:
                    get_word = MyThread(self.my_request.get_word, args=(account, self.qq.myself_QQ))
                    get_word.start()
                    if self.mode >= 3:
                        get_word_status = MyThread(self.my_request.get_word_status, args=(account,))
                        get_word_status.start()
                    is_passed = False
                    self.all_account_passed = False
                else:
                    account_count_info['word_get_success'] = account_get
                    account_count_info['word_get_null'] = account_null
                    account_count_info['word_get_total'] = account_get + account_null
                    account_count_info['words'] = word_gets
                    if is_passed:
                        self.passed_account_count += 1
                    break

            # 统计字符数量
            if self.mode >= 2 and self.again == 0:
                print("-------------------------------------------")
                count_words.start()
                account_count_info['word_have'], account_count_info['word_light_up'], account_count_info['word_unknown'] = self.print_count_words_data(
                    count_words.result())

            self.account_count.append(account_count_info)
            self.process += 1
            self.progress_bar()
            print("\33[0m=================================================================================================================")

    def print_summary(self):
        header = f"{'总抽':^6} {'抽中':^6} {'null':^8} {'总人':^6} {'跳过':^6}"
        values = f"{self.word_get_success_count + self.word_get_null_count:^7} " \
                 f"{self.word_get_success_count:^7} " \
                 f"{self.word_get_null_count:^9} " \
                 f"{len(self.qq.QQ_list):^7} " \
                 f"{self.passed_account_count:^7}"

        print(f"\n\33[40m{header}")
        print(values)


if __name__ == '__main__':
    my_process = MainProcess()
    my_process.get_word_in_list(my_process.qq.QQ_list)
    while my_process.need_again:
        my_process.again += 1
        my_process.get_word_in_list(my_process.need_again_QQ_list)
        if my_process.again == 5:
            break

    my_process.print_summary()

    if not my_process.all_account_passed:
        my_process.save_data()
        
    input('按任意键退出')
