# -*- coding: utf8 -*-
import base64
import json
import re

import requests
from lxml import etree

QQ = []
myself_qq = 0


# 初始化 cookie
def init_cookie(file_name):
    cookies = {}
    try:
        with open('cookie.ini') as file:
            lines = file.readlines()
            for line in lines:
                # 解析每一行，获取名称、值和默认值
                name, value = init_cookie_line(line)
                if name is not None:
                    cookies[name] = value
        return cookies
    except FileNotFoundError:
        cookies = input('请输入cookie：')
        return process_cookies(file_name, cookies)


# 解析每行cookie数据
def init_cookie_line(line):
    parts = line.strip().split(' ')
    if not parts[0].startswith('-'):
        name = parts[0]
        if parts[1] == 'null' and len(parts) > 2 and parts[2] != 'null':
            value = parts[2]
        else:
            value = parts[1]
        return name, value
    else:
        return None, None


# 读取旧的 cookie 文件
def read_cookie(file_name):
    cookies = {}
    try:
        with open(file_name, 'r') as file:
            lines = file.readlines()
            for line in lines:
                # 解析每一行，获取名称、值和默认值
                name, value, default, delete = parse_cookie_line(line)
                cookies[name] = {'value': value, 'default': default, 'delete': delete}
    except FileNotFoundError:
        pass
    return cookies


# 解析每行cookie数据
def parse_cookie_line(line):
    parts = line.strip().split(' ')
    if parts[0].startswith('-'):
        name = parts[0][1:]
        delete = True
    else:
        name = parts[0]
        delete = False
    value = parts[1] if len(parts) > 1 and parts[1] != 'null' else None
    default = parts[2] if len(parts) > 2 and parts[2] != 'null' else None
    return name, value, default, delete


# 处理 cookie 数据
def process_cookies(file_name, cookies):
    processed_cookies = {}
    write_cookies = {}

    # 将新的 cookie 数据"domainId=338; pvid=9714795492"转换为字典
    new_cookies = {}
    for cookie in cookies.split('; '):
        parts = cookie.split('=')
        if len(parts) == 2:
            new_cookies[parts[0]] = parts[1]

    # 读取旧的 cookie 数据
    old_cookies = read_cookie(file_name)

    # 遍历新的 cookie 数据，如果旧的 cookie 中有默认值，则将新的 cookie 的默认值设为旧的 cookie 的默认值
    for name, value in new_cookies.items():
        processed_cookies[name] = value
        if name in old_cookies and old_cookies[name]['default'] is not None:
            write_cookies[name] = {'value': value, 'default': old_cookies[name]['default'], 'delete': False}
        else:
            write_cookies[name] = {'value': value, 'default': None, 'delete': False}

    # 遍历旧的 cookie 数据，如果旧的 cookie 数据不在新的 cookie 数据中，则将旧的 cookie 数据的默认值设为新的 cookie 数据的默认值 或 删除旧的 cookie 数据
    for name, values in old_cookies.items():
        if name not in processed_cookies:
            if values['default'] is not None:
                processed_cookies[name] = values['default']
                write_cookies[name] = {'value': None, 'default': values['default'], 'delete': False}
            else:
                write_cookies[name] = {'value': values['value'], 'default': None, 'delete': True}

    # 排序，首先按照是否删除排序为删除在后，未删除在前；其次按照有默认值在前，没有默认值在后；最后按照name的首字母排序
    write_cookies = sorted(write_cookies.items(), key=lambda x: (not x[1]['delete'], not x[1]['default'], x[0]))

    # 将处理后的 cookie 数据写入文件, 一行一个 cookie，格式为：name value default 或 -name value default
    # 其中 -name value default 表示曾经出现过的 cookie，其中value在default不为空时可能为null，default为空时则格式为：name value
    with open(file_name, 'w') as file:
        for name, values in write_cookies:
            if values['default'] is not None:
                if values['delete']:
                    file.write('-' + name + ' ' + values['value'] + ' ' + values['default'] + '\n')
                else:
                    file.write(name + ' ' + str(values['value']) + ' ' + str(values['default']) + '\n')
            else:
                if values['delete']:
                    file.write('-' + name + ' ' + values['value'] + '\n')
                else:
                    file.write(name + ' ' + str(values['value']) + '\n')

    return processed_cookies


def read_QQ():
    try:
        with open('qq.ini', encoding='utf-8') as f:
            for line in f:
                data = line.strip().split(' ')
                if len(data) == 1:
                    QQ.append([data[0], ''])  # 如果没有备注，则将备注设为空字符串
                else:
                    if data[1] == '__我':
                        global myself_qq
                        myself_qq = int(data[0])
                    else:
                        QQ.append([data[0], ' '.join(data[1:])])
    except FileNotFoundError:
        add_QQ()


def add_QQ():
    print('检测到第一次使用，请输入自己的QQ号')
    global myself_qq
    myself_qq = input('请输入自己的QQ号：')
    print('请手动输入批量抽卡的QQ号和备注（QQ号和备注用空格分隔，输入空行结束）')
    count = 0
    with open('qq.ini', 'w', encoding='utf-8') as f:
        f.write(myself_qq + ' ' + '__我' + '\n')
        while True:
            count += 1
            qq_data = input(f"{count}: ").split(' ')
            if qq_data[0] == '':  # 检查是否输入空行
                print('添加成功，总共添加', count - 1, '个账号')
                break
            qq = qq_data[0]
            if len(qq_data) > 1:
                note = ' '.join(qq_data[1:])
            else:
                note = ''
            QQ.append([qq, note])
            f.write(qq + ' ' + note + '\n')


def count_card(cookies, qq):
    user_agent = 'Mozilla/5.0 (Linux; Android 8.0.0; FLA-AL20 Build/HUAWEIFLA-AL20; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/66.0.3359.126 MQQBrowser/6.2 TBS/045130 Mobile Safari/537.36 V1_AND_SQ_8.2.8_1346_YYB_D QQ/8.2.8.4440 NetType/4G WebP/0.3.0 Pixel/1080 StatusBarHeight/73 SimpleUISwitch/0 QQTheme/1000'
    host = 'ti.qq.com'
    url_get = 'https://ti.qq.com/hybrid-h5/interactive_logo/word'
    params = {
        'target_uin': qq[0],
        '_wv': '67108867',
        '_nav_txtclr': '000000',
        '_wvSb': '0'
    }
    headers = {
        'User-Agent': user_agent,
        'host': host
    }
    r = requests.get(url_get, params=params, headers=headers, cookies=cookies)
    html = etree.HTML(r.text)
    div_elements = html.xpath('//*[@id="app"]/div[1]/div[2]/div[3]/div[2]/div')
    number_of_card = len(div_elements) - 1
    if number_of_card == 0:
        print("已拥有字符：" + str(number_of_card) + "个")
        return
    else:
        print("已拥有字符：" + str(number_of_card) + "个", end='/')

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
            print("完全点亮：" + str(count) + "张")
        else:
            print("完全点亮：" + str(count) + "张/无法判断：" + str(unknown) + "张")


def get_card(cookies):
    user_agent = 'Mozilla/5.0 (Linux; Android 8.0.0; FLA-AL20 Build/HUAWEIFLA-AL20; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/66.0.3359.126 MQQBrowser/6.2 TBS/045130 Mobile Safari/537.36 V1_AND_SQ_8.2.8_1346_YYB_D QQ/8.2.8.4440 NetType/4G WebP/0.3.0 Pixel/1080 StatusBarHeight/73 SimpleUISwitch/0 QQTheme/1000'
    host = 'ti.qq.com'
    card_get = 0
    card_null = 0
    qq_pass = 0
    qq_done = 0
    for qq in QQ:
        qq_done += 1
        print('\n', qq_done, '/', len(QQ), end=' ')
        if qq[1] == '':
            print("：" + qq[0], end=' - ')
        else:
            print("：" + qq[0] + ' ' + qq[1], end=' - ')
        url_get = 'https://ti.qq.com/hybrid-h5/interactive_logo/two'
        params = {
            'target_uin': qq[0],
            '_wv': '67108867',
            '_nav_txtclr': '000000',
            '_wvSb': '0'
        }
        headers = {
            'User-Agent': user_agent,
            'host': host
        }
        r = requests.get(url_get, params=params, headers=headers, cookies=cookies)
        html = etree.HTML(r.text)
        result = html.xpath('//*[@id="app"]/div[1]/div[3]/div[1]/span/span/text()')
        if len(result) != 0:
            process = html.xpath('//*[@id="app"]/div[1]/div[4]/div[2]/div[2]/div[2]/span/text()')
            print('目前字符进度' + process[0], end='- ')
            print(result[0].strip() + '个好友互动标识', end='：')
            for count in range(int(result[0])):
                c_name = html.xpath('//*[@id="app"]/div[1]/div[3]/div[' + str(count + 2) + ']/div[2]/text()')
                c_days = html.xpath(
                    '//*[@id="app"]/div[1]/div[3]/div[' + str(count + 2) + ']/div[3]/span[1]/text()')
                if len(c_days) != 0:
                    print(c_name[0].strip(), c_days[0], '天')
                else:
                    print(c_name[0])
        else:
            process = html.xpath('//*[@id="app"]/div[1]/div[3]/div[2]/div[2]/div[2]/span/text()')
            print('目前字符进度' + process[0])
        url_post = 'https://ti.qq.com/proxy/domain/oidb.tim.qq.com/v3/oidbinterface/oidb_0xdd0_0'
        params = {
            'sdkappid': '39998',
            'actype': '2',
            'bkn': '125442749'
        }
        headers = {
            'User-Agent': user_agent,
            'host': host,
            'Content-Type': 'application/json'
        }
        is_pass = True
        while True:
            data = {
                'uin': myself_qq,
                'frd_uin': int(qq[0])
            }
            r = requests.post(url_post, headers=headers, params=params, data=json.dumps(data), cookies=cookies)
            r = json.loads(r.text)
            if r['ActionStatus'] == 'OK':
                if r['card_url'] == '':
                    print('没抽中', end=' - ')
                    card_null += 1
                    is_pass = False
                else:
                    print('\n抽到卡片', end='：')
                    print(base64.b64decode(r['card_id']).decode(), end=' - ')
                    print(base64.b64decode(r['card_word']).decode(), end=' - ')
                    print(base64.b64decode(r['card_url']).decode())
                    print("卡片描述：", base64.b64decode(r['rpt_wording'][0]).decode())
                    card_get += 1
                    is_pass = False
            elif r['ActionStatus'] == 'FAIL':
                if r['ErrorCode'] == 10005:
                    if is_pass:
                        qq_pass += 1
                    print('今日次数已用完')
                    count_card(cookies, qq)
                    break
                elif r['ErrorCode'] == 10006:
                    print(' 警告 该QQ号不是你的好友')
                    qq_pass += 1
                    break
                elif r['ErrorCode'] == 151:
                    print(' 警告 登录过期')
                    return 151
                elif r['ErrorCode'] == 304:
                    print(' 警告 请检查你的myself_qq，该数据应为int类型数字')
                    return 304
                print(' ErrorInfo: ', r['ErrorInfo'], ' ErrorCode: ', r['ErrorCode'])
            else:
                print(r)
    print('\n总/抽中/null：', (card_get + card_null), '/', card_get, '/', card_null, '张字符，总/跳过',
          len(QQ), '/', qq_pass, '个QQ号')
    return 0


if __name__ == '__main__':
    read_QQ()
    status = get_card(init_cookie("cookie.ini"))
    while status != 0:
        if status == 151:
            status = get_card(process_cookies("cookie.ini", input('请输入cookie：')))
        if status == 304:
            break

input('按回车键退出')
