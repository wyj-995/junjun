import random
from time import localtime, sleep
from requests import get, post
from datetime import datetime, date, timedelta
from zhdate import ZhDate
import sys
import os

def get_color():
    # 获取随机颜色
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)

def get_access_token():
    # appId
    app_id = config["app_id"]
    # appSecret
    app_secret = config["app_secret"]
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
             .format(app_id, app_secret))
    try:
        access_token = get(post_url).json()['access_token']
    except KeyError:
        print("获取access_token失败，请检查app_id和app_secret是否正确")
        os.system("pause")
        sys.exit(1)
    # print(access_token)
    return access_token

def get_weather(region):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config["weather_key"]
    region_url = "https://geoapi.qweather.com/v2/city/lookup?location={}&key={}".format(region, key)
    response = get(region_url, headers=headers).json()
    if response["code"] == "404":
        print("推送消息失败，请检查地区名是否有误！")
        os.system("pause")
        sys.exit(1)
    elif response["code"] == "401":
        print("推送消息失败，请检查和风天气key是否正确！")
        os.system("pause")
        sys.exit(1)
    else:
        # 获取地区的location--id
        location_id = response["location"][0]["id"]
    weather_url = "https://devapi.qweather.com/v7/weather/now?location={}&key={}".format(location_id, key)
    response = get(weather_url, headers=headers).json()
    # 天气
    weather = response["now"]["text"]
    # 当前温度
    temp = response["now"]["temp"] + u"\N{DEGREE SIGN}" + "C"
    # 风向
    wind_dir = response["now"]["windDir"]
    return weather, temp, wind_dir

def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    # 判断是否为农历生日
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        try:
            # 获取农历生日的今年对应的月和日，如果今年生日已过，获取下一年的生日日期
            birthday_date = ZhDate(year, r_mouth, r_day).to_datetime().date()
            if birthday_date < today:
                birthday_date = ZhDate(year + 1, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在")
            os.system("pause")
            sys.exit(1)
    else:
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        birthday_date = date(year, birthday_month, birthday_day)
        # 如果今年生日已过，获取下一年的生日日期
        if birthday_date < today:
            birthday_date = date(year + 1, birthday_month, birthday_day)
    # 计算距离生日的天数
    birth_day = (birthday_date - today).days
    return birth_day

def get_ciba():
    url = "http://open.iciba.com/dsapi/"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    r = get(url, headers=headers)
    note_en = r.json()["content"]
    note_ch = r.json()["note"]
    return note_ch, note_en

def send_message(to_user, access_token, region_name, weather, temp, wind_dir, note_ch, note_en):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]
    # 获取在一起的日子的日期格式
    love_year = int(config["love_date"].split("-")[0])
    love_month = int(config["love_date"].split("-")[1])
    love_day = int(config["love_date"].split("-")[2])
    love_date = date(love_year, love_month, love_day)
    # 获取在一起的日期差
    love_days = str(today.__sub__(love_date)).split(" ")[0]
    # 获取所有生日数据
    birthdays = {}
    for k, v in config.items():
        if k[0:5] == "birth":
            birthdays[k] = v
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": "{} {}".format(today, week),
                "color": get_color()
            },
            "region": {
                "value": region_name,
                "color": get_color()
            },
            "weather": {
                "value": weather,
                "color": get_color()
            },
            "temp": {
                "value": temp,
                "color": get_color()
            },
            "wind_dir": {
                "value": wind_dir,
                "color": get_color()
            },
            "love_day": {
                "value": love_days,
                "color": get_color()
            },
            "note_en": {
                "value": note_en,
                "color": get_color()
            },
            "note_ch": {
                "value": note_ch,
                "color": get_color()
            }
        }
    }
    for key, value in birthdays.items():
        # 获取距离下次生日的时间
        birth_day = get_birthday(value["birthday"], year, today)
        if birth_day == 0:
            birthday_data = "今天{}生日哦，祝{}生日快乐！".format(value["name"], value["name"])
        else:
            birthday_data = "距离{}的生日还有{}天".format(value["name"], birth_day)
        # 将生日数据插入data
        data["data"][key] = {"value": birthday_data, "color": get_color()}
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    response = post(url, headers=headers, json=data).json()
    if response["errcode"] == 40037:
        print("推送消息失败，请检查模板id是否正确")
    elif response["errcode"] == 40036:
        print("推送消息失败，请检查模板id是否为空")
    elif response["errcode"] == 40003:
        print("推送消息失败，请检查微信号是否正确")
    elif response["errcode"] == 0:
        print("推送消息成功")
    else:
        print(response)

if __name__ == "__main__":
    while True:
        now = datetime.now()
        # 判断是否是周一、三、五且是早上9点
        if now.weekday() in [0, 2, 4] and now.hour == 9 and now.minute == 0 and now.second == 0:
            try:
                with open("config.txt", encoding="utf-8") as f:
                    config = eval(f.read())
            except FileNotFoundError:
                print("推送消息失败，请检查config.txt文件是否与程序位于同一路径")
                os.system("pause")
                sys.exit(1)
            except SyntaxError:
                print("推送消息失败，请检查配置文件格式是否正确")
                os.system("pause")
                sys.exit(1)

            # 获取accessToken
            accessToken = get_access_token()
            # 接收的用户
            users = config["user"]
            # 传入地区获取天气信息
            region = config["region"]
            weather, temp, wind_dir = get_weather(region)
            note_ch = config["note_ch"]
            note_en = config["note_en"]
            if note_ch == "" and note_en == "":
                # 获取词霸每日金句
                note_ch, note_en = get_ciba()
            # 公众号推送消息
            for user in users:
                send_message(user, accessToken, region, weather, temp, wind_dir, note_ch, note_en)
            # 每次任务执行完后等待60秒，避免在9点整的一分钟内多次执行任务（因为循环执行可能会有延迟）
            sleep(60)
        else:
            # 计算距离下一次执行任务的时间间隔（秒）
            next_execution_time = datetime(now.year, now.month, now.day, 9, 0, 0)
            if now.weekday() > 4:  # 如果当前是周六或周日，将下一次执行时间设置为下周一
                next_execution_time += timedelta(days=(7 - now.weekday()) + 1)
            elif now.hour > 9 or (now.hour == 9 and now.minute > 0):  # 如果当前时间已经过了9点，将下一次执行时间设置为明天
                next_execution_time += timedelta(days=1)
            elif now.hour == 9 and now.minute == 0 and now.second > 0:  # 如果当前时间是9点整但秒数大于0，等待到下一分钟
                next_execution_time += timedelta(minutes=1)
            time_to_wait = (next_execution_time - now).total_seconds()
            sleep(time_to_wait)