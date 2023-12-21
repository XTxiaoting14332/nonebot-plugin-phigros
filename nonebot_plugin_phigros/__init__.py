from nonebot import on_command
from nonebot import get_driver
from requests import Session
from nonebot.plugin import PluginMetadata
from nonebot.log import logger
from nonebot.adapters.qq import Event, event, Bot, Message, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from pathlib import Path
import sqlite3
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import socket
import uuid
from .config import Config



__plugin_meta__ = PluginMetadata(
    name="Phigros查分器（adapter-qq）",
    description="一个简单的基于PhigrosLibrary的Phigros查分插件，适用于Adapter-qq",
    usage="""使用/phi查看帮助
""",
)


data_dir = Path("data/phigros").absolute()
cache_dir = Path("data/phigros/cache").absolute()
data_dir.mkdir(parents=True, exist_ok=True)
cache_dir.mkdir(parents=True, exist_ok=True)
datapath = "data/phigros/"
db = sqlite3.connect("data/phigros/binded.db")
cursor = db.cursor()

config = Config.parse_obj(get_driver().config)
s = Session()


#初始化数据库
try:
    create_tb_cmd='''
    CREATE TABLE IF NOT EXISTS binded
    (id text,
    token text);
    '''
    cursor.execute(create_tb_cmd)
    logger.success("[Phigros]连接至数据库")
except:
    logger.error("[Phigros]数据库创建失败")


def insert_tb(id,token):
    insert_tb_cmd = f'insert into binded(id, token) values("{id}","{token}")'
    cursor.execute(insert_tb_cmd)
    db.commit()

def delete_by_id(id):
    delete_cmd = f'DELETE FROM binded where id = "{id}"'
    cursor.execute(delete_cmd)
    db.commit()

def select_token(id):
    select_tb_cmd = f'SELECT id, token FROM binded WHERE id = "{id}"'
    cursor.execute(select_tb_cmd)
    return cursor.fetchall()

#评级
def get_rank(score,fc):
    try:
        if score == 1000000:
            rank = "Phi"
        else:
            if fc == True:
                rank = "Full Combo"
            else:
                if score < 700000:
                    rank = "F"
                elif 700000 <= score <= 819999:
                    rank = "C"
                elif 820000 <= score <= 879999:
                    rank = "B"
                elif 880000 <= score <= 919999:
                    rank = "A"
                elif 920000 <= score <= 959999:
                    rank = "S"
                elif 960000 <= score <= 999999:
                    rank = "V"
    except:
        rank = "NaN"
    return rank


ip = config.phigros_api_host.replace("http://","")
ip = ip.replace("https://","")
port = int(config.phigros_api_port)
api = str(f"{config.phigros_api_host}:{config.phigros_api_port}")


def is_connection_successful(ip, port):
    try:
        sock = socket.create_connection((ip, port), timeout=2)
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False

if is_connection_successful(ip, port):
    logger.success("[Phigros]连接至Phigros API成功")
else:
    logger.error(f"[Phigros]无法连接至Phigros API")

def generate_text_image(text, filename) -> BytesIO:
    lines = text.splitlines()
    line_count = len(lines)
    logger.info("[Phigros]开始绘制图片")
    font_size = config.phigros_font_size
    font_path = config.phigros_font_path
    font = ImageFont.truetype(font_path, font_size)

    # 获取字体的行高
    left, top, width, line_height = font.getbbox("a")
    # 增加行距
    line_height += 3
    # 获取画布需要的高度
    height = line_height * line_count + 20
    # 获取画布需要的宽度
    width = int(max([font.getlength(line) for line in lines])) + 25
    # 字体颜色
    black_color = (0, 0, 0)

    # 生成画布
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 按行绘制文字
    c = 0
    for line in lines:
        draw.text((10, 6 + line_height * c), line, font=font, fill=black_color)
        c += 1

    img.save(filename, format="PNG")

    # 返回字节流
    byte_stream = BytesIO()
    img.save(byte_stream, format="PNG")
    logger.info(f"[Phigros]图片已保存至data/phigros/cache/{filename}")

    return byte_stream.getvalue()






def upload_to_image_host(filename):
    logger.info("[Phigros]正在上传至sm.ms图床")
    files = {'smfile': open("data/phigros/cache/"+filename, 'rb')}
    api_url = 'https://sm.ms/api/v2/upload'
    headers = {"Authorization": token}

    response = requests.post(api_url, files=files, headers=headers)
    json_data = response.json()
    try:
        if json_data["code"] == "success":
            url = json_data["data"]["url"]
            logger.info(f"[Phigros]上传成功，返回url：{url}")
            return json_data["data"]["url"]
        else:
            url = json_data["images"]
            logger.warning(f"[Phigros]检测到已存在相同的图片，返回上次保存的url：{url}")
            return json_data["images"]
    except KeyError:
        logger.error("[Phigros]未配置sm.ms的token，图片发送失败！")

token = config.phigros_smms_token
if len(token) == 0:
    logger.error("[Phigros]sm.ms图床token未配置！将无法发送图片！")
else:
    logger.info("[Phigros]读取到sm.ms的token")



s = Session()

phi = on_command('phi help',aliases={'phi'})
unbind = on_command('phi unbind',aliases={'phi 解绑'})
bind = on_command('phi bind', aliases={'phi 绑定'})
info = on_command('phi info', aliases={'phi 用户信息'})
b19 = on_command('phi b19',aliases={''})

@phi.handle()
async def phi_handle(event: Event,bot: Bot):
    msg = "\n/phi bind 你的token\t--绑定Phigros帐号\n/phi unbind\t--解除绑定\n/phi info\t--个人概览\n/phi b19\t--获取b19成绩"
    await phi.finish(msg)


@bind.handle()
async def _handle(matcher: Matcher, token: Message = CommandArg()):
    if token.extract_plain_text() and token.extract_plain_text()[0]!='_':
        matcher.set_arg('token', token)


@bind.got('token', prompt='请at机器人后发送你的token')
async def _(event: Event, bot: Bot,token: str = ArgPlainText('token')):
    if token[0]!='_':
        id = event.get_user_id()
        if not select_token(id):
            insert_tb(id,token)
            await bind.finish("绑定成功，请及时撤回你的token")
        else:
            await bind.finish("你已经绑定过了！")

    else:
        await bind.reject_arg('token',prompt='不能使用“_”作为前缀')


@unbind.handle()
async def unbind_handle(event: Event,bot: Bot):
    id = event.get_user_id()
    if not select_token(id):
        await unbind.finish('你还没有绑定你的phigros账号！')
    else:
        delete_by_id(id)
        await unbind.finish('已解除绑定')



@info.handle()
async def info_handle(event: Event, bot: Bot):
    id = event.get_user_id()
    result = select_token(id)
    if not result:
        await info.finish('你还没有绑定你的phigros账号！请先使用/phi bind命令绑定')
    else:
        try:
            id, token = result[0]
            result = s.get(f"{api}/saveUrl/%s" % token)
            json = result.json()
            saveUrl = json["saveUrl"]
            rks = json["RKS"]
            ktf = json["课题分"]
            EZ = json["EZ"]
            HD = json["HD"]
            IN = json["IN"]
            AT = json["AT"]
            playerid = s.get(f"{api}/playerId/%s" % token)
            msg = f"\n玩家概览\n玩家id：{playerid.text}\n课题分：{ktf}\nRanking Score：{rks}\n歌曲游玩进度[Cleared, Full Combo, Phi]\nEZ{EZ}\nHD{HD}\nIN{IN}\nAT{AT}"
            await info.finish(msg)
        except requests.exceptions.JSONDecodeError:
            msg = "查无此人，请检查你的token是否正确"
            await info.finish(msg)


@b19.handle()
async def b19_handle(event: Event,bot: Bot):
    id = event.get_user_id()
    result = select_token(id)
    if not result:
        await info.finish('你还没有绑定你的phigros账号！请先使用/phi bind命令绑定')
    else:
        try:
            id, token = result[0]
            result = s.get(f"{api}/saveUrl/%s" % token)
            json = result.json()
            saveUrl = json["saveUrl"]
            playerid = s.get(f"{api}/playerId/%s" % token)
            b19_get = s.get(f"{api}/b19/%s" % saveUrl)
            b19_json = b19_get.json()
            #各种项目
            songid = [entry["songId"] for entry in b19_json]
            level = [entry["level"] for entry in b19_json]
            score = [entry["score"] for entry in b19_json]
            acc = [entry["acc"] for entry in b19_json]
            rank = [entry["定数"] for entry in b19_json]
            s_rks = [entry["单曲rks"] for entry in b19_json]
            fc = [entry["fc"] for entry in b19_json]

            #屎山
            #曲目
            s1 = songid[0]
            s2 = songid[1]
            s3 = songid[2]
            s4 = songid[3]
            s5 = songid[4]
            s6 = songid[5]
            s7 = songid[6]
            s8 = songid[7]
            s9 = songid[8]
            s10 = songid[9]
            s11= songid[10]
            s12 = songid[11]
            s13 = songid[12]
            s14 = songid[13]
            s15 = songid[14]
            s16 = songid[15]
            s17 = songid[16]
            s18 = songid[17]
            s19 = songid[18]
            s20 = songid[19]

            #等级
            l1 = level[0]
            l2 = level[1]
            l3 = level[2]
            l4 = level[3]
            l5 = level[4]
            l6 = level[5]
            l7 = level[6]
            l8 = level[7]
            l9 = level[8]
            l10 = level[9]
            l11= level[10]
            l12 = level[11]
            l13 = level[12]
            l14 = level[13]
            l15 = level[14]
            l16 = level[15]
            l17 = level[16]
            l18 = level[17]
            l19 = level[18]
            l20 = level[19]

            #分数
            sc1 = int(score[0])
            sc2 = int(score[1])
            sc3 = int(score[2])
            sc4 = int(score[3])
            sc5 = int(score[4])
            sc6 = int(score[5])
            sc7 = int(score[6])
            sc8 = int(score[7])
            sc9 = int(score[8])
            sc10 = int(score[9])
            sc11= int(score[10])
            sc12 = int(score[11])
            sc13 = int(score[12])
            sc14 = int(score[13])
            sc15 = int(score[14])
            sc16 = int(score[15])
            sc17 = int(score[16])
            sc18 = int(score[17])
            sc19 = int(score[18])
            sc20 = int(score[19])

            #acc
            acc1 = acc[0]
            acc2 = acc[1]
            acc3 = acc[2]
            acc4 = acc[3]
            acc5 = acc[4]
            acc6 = acc[5]
            acc7 = acc[6]
            acc8 = acc[7]
            acc9 = acc[8]
            acc10 = acc[9]
            acc11= acc[10]
            acc12 = acc[11]
            acc13 = acc[12]
            acc14 = acc[13]
            acc15 = acc[14]
            acc16 = acc[15]
            acc17 = acc[16]
            acc18 = acc[17]
            acc19 = acc[18]
            acc20 = acc[19]

            #定数
            rank1 = rank[0]
            rank2 = rank[1]
            rank3 = rank[2]
            rank4 = rank[3]
            rank5 = rank[4]
            rank6 = rank[5]
            rank7 = rank[6]
            rank8 = rank[7]
            rank9 = rank[8]
            rank10 = rank[9]
            rank11= rank[10]
            rank12 = rank[11]
            rank13 = rank[12]
            rank14 = rank[13]
            rank15 = rank[14]
            rank16 = rank[15]
            rank17 = rank[16]
            rank18 = rank[17]
            rank19 = rank[18]
            rank20 = rank[19]

            #单曲rks
            s_rks1 = s_rks[0]
            s_rks2 = s_rks[1]
            s_rks3 = s_rks[2]
            s_rks4 = s_rks[3]
            s_rks5 = s_rks[4]
            s_rks6 = s_rks[5]
            s_rks7 = s_rks[6]
            s_rks8 = s_rks[7]
            s_rks9 = s_rks[8]
            s_rks10 = s_rks[9]
            s_rks11= s_rks[10]
            s_rks12 = s_rks[11]
            s_rks13 = s_rks[12]
            s_rks14 = s_rks[13]
            s_rks15 = s_rks[14]
            s_rks16 = s_rks[15]
            s_rks17 = s_rks[16]
            s_rks18 = s_rks[17]
            s_rks19 = s_rks[18]
            s_rks20 = s_rks[19]


            #FC
            fc1 = fc[0]
            fc2 = fc[1]
            fc3 = fc[2]
            fc4 = fc[3]
            fc5 = fc[4]
            fc6 = fc[5]
            fc7 = fc[6]
            fc8 = fc[7]
            fc9 = fc[8]
            fc10 = fc[9]
            fc11= fc[10]
            fc12 = fc[11]
            fc13 = fc[12]
            fc14 = fc[13]
            fc15 = fc[14]
            fc16 = fc[15]
            fc17 = fc[16]
            fc18 = fc[17]
            fc19 = fc[18]
            fc20 = fc[19]

            #返回评级
            r1 = get_rank(sc1, fc1)
            r2 = get_rank(sc2, fc2)
            r3 = get_rank(sc3, fc3)
            r4 = get_rank(sc4, fc4)
            r5 = get_rank(sc5, fc5)
            r6 = get_rank(sc6, fc6)
            r7 = get_rank(sc7, fc7)
            r8 = get_rank(sc8, fc8)
            r9 = get_rank(sc9, fc9)
            r10 = get_rank(sc10, fc10)
            r11 = get_rank(sc11, fc11)
            r12 = get_rank(sc12, fc12)
            r13 = get_rank(sc13, fc13)
            r14 = get_rank(sc14, fc14)
            r15 = get_rank(sc15, fc15)
            r16 = get_rank(sc16, fc16)
            r17 = get_rank(sc17, fc17)
            r18 = get_rank(sc18, fc18)
            r19 = get_rank(sc19, fc19)
            r20 = get_rank(sc20, fc20)



            msg = f"\n{playerid.text}的Best19：\n[BestPhi]\n{s1}[{r1}]\n难度：{l1}\n定数：{rank1}\n分数：{sc1}\nACC：{acc1}\n单曲rks：{s_rks1}\n\n{s2}[{r2}]\n难度：{l2}\n定数：{rank2}\n分数：{sc2}\nACC：{acc2}\n单曲rks：{s_rks2}\n\n{s3}[{r3}]\n难度：{l3}\n定数：{rank3}\n分数：{sc3}\nACC：{acc3}\n单曲rks：{s_rks3}\n\n{s4}[{r4}]\n难度：{l4}\n定数：{rank4}\n分数：{sc4}\nACC：{acc4}\n单曲rks：{s_rks4}\n\n{s5}[{r5}]\n难度：{l5}\n定数：{rank5}\n分数：{sc5}\nACC：{acc5}\n单曲rks：{s_rks5}\n\n{s6}[{r6}]\n难度：{l6}\n定数：{rank6}\n分数：{sc6}\nACC：{acc6}\n单曲rks：{s_rks6}\n\n{s7}[{r7}]\n难度：{l7}\n定数：{rank7}\n分数：{sc7}\nACC：{acc7}\n单曲rks：{s_rks7}\n\n{s8}[{r8}]\n难度：{l8}\n定数：{rank8}\n分数：{sc8}\nACC：{acc8}\n单曲rks：{s_rks8}\n\n{s9}[{r9}]\n难度：{l9}\n定数：{rank9}\n分数：{sc9}\nACC：{acc9}\n单曲rks：{s_rks9}\n\n{s10}[{r10}]\n难度：{l10}\n定数：{rank10}\n分数：{sc10}\nACC：{acc10}\n单曲rks：{s_rks10}\n\n{s11}[{r11}]\n难度：{l11}\n定数：{rank11}\n分数：{sc11}\nACC：{acc11}\n单曲rks：{s_rks11}\n\n{s12}[{r12}]\n难度：{l12}\n定数：{rank12}\n分数：{sc12}\nACC：{acc12}\n单曲rks：{s_rks12}\n\n{s13}[{r13}]\n难度：{l13}\n定数：{rank13}\n分数：{sc13}\nACC：{acc13}\n单曲rks：{s_rks13}\n\n{s14}[{r14}]\n难度：{l14}\n定数：{rank14}\n分数：{sc14}\nACC：{acc14}\n单曲rks：{s_rks14}\n\n{s15}[{r15}]\n难度：{l15}\n定数：{rank15}\n分数：{sc15}\nACC：{acc15}\n单曲rks：{s_rks15}\n\n{s16}[{r16}]\n难度：{l16}\n定数：{rank16}\n分数：{sc16}\nACC：{acc16}\n单曲rks：{s_rks16}\n\n{s17}[{r17}]\n难度：{l17}\n定数：{rank17}\n分数：{sc17}\nACC：{acc17}\n单曲rks：{s_rks17}\n\n{s18}[{r18}]\n难度：{l18}\n定数：{rank18}\n分数：{sc18}\nACC：{acc18}\n单曲rks：{s_rks18}\n\n{s19}[{r19}]\n难度：{l19}\n定数：{rank19}\n分数：{sc19}\nACC：{acc19}\n单曲rks：{s_rks19}\n\n{s20}[{r20}]\n难度：{l20}\n定数：{rank20}\n分数：{sc20}\nACC：{acc20}\n单曲rks：{s_rks20}\n"
            filename = str(uuid.uuid4()) + ".png"
            image_data = generate_text_image(msg, "data/phigros/cache/"+filename)
            direct_link = upload_to_image_host(filename)
            await b19.finish(MessageSegment.image(direct_link))
        except requests.exceptions.JSONDecodeError:
            msg = "出错了，请重试"
            await b19.finish(msg)

