from os import path
from pydantic import BaseModel

class Config(BaseModel):
    #PhigrosLibrary的api地址，默认为http://127.0.0.1
    phigros_api_host: str = "http://127.0.0.1"

    #PhigrosLibrary的api端口，默认为9090
    phigros_api_port: int = 9090

    # 字体文件路径
    phigros_font_path: str = str(
        path.join(path.dirname(path.abspath(__file__)), "simyou.ttf")
    )
    # 字体大小
    phigros_font_size: int = 18

    #sm.ms图床的Token
    phigros_smms_token: str = ""

    #适配器是否为adapter-qq,默认为False
    phigros_adapter_qq: bool = False

