# 象胥

一个为 ArcRaider 而生的实时语音翻译软件，支持捕获 Windows 系统声音进行流式识别与翻译。  

PS：`象胥`是中国古代对翻译人员或外交使节的称呼，主要用于周代及以后的典籍中。XiangXu

## 功能

- 流式语音识别与翻译（接入 阿里云百炼 gummy-realtime-v1）
- 捕获系统声音（含游戏音频）
- 浅色主题 GUI，左侧导航：识别与翻译 / 对话建议 / 设置
- 设置持久化（API Key 等）
- 历史记录一键清空
- 调试模式（.env 中 `Debug_Mode=True`）

## 环境

- Python 3.11
- Conda 环境：XiangXu

## 使用

1. `git clone`本项目到你的电脑上
2. 双击`run.bat`

```
如果你没有一个配置好的代理，你可以选择访问我的云盘
云盘地址：http://www.nqr-lty.com:5244/服务器高速盘
下载后解压运行 run.bat即可
```

- 启动后并点击开始即可开始传译，请尽情探索吧

```
（实则是不想写了）
如果你不是B站过来的，你可以去我的B站主页上找找视频
https://account.bilibili.com/account/home?spm_id_from=333.337.0.0
```

## 如何获取API-KEY

- 只支持阿里云百炼平台的API-KEY

1. 自己获取
2. 去看我的B站视频

## 开发者配置

```bash
conda activate XiangXu
pip install -r requirements.txt
```

或使用 environment.yml 创建环境：

```bash
conda env create -f environment.yml
conda activate XiangXu
```

### 配置

1. 复制 `.env.example` 为 `.env`
2. 设置 `Debug_Mode=True` 开启调试
3. 在应用设置页输入 DashScope API Key 并保存（或写入 config.json）

### 运行

```bash
conda activate XiangXu
python main.py
```

## 如果你想支持我

1. 请附上你的邮箱！！！
2. 请附上一句话。
3. 如果可以，你可以附上一个想要我去开发的内容，我会在后续尽量实现。
4. 非常感谢你的支持，但是我只是一个职业本科的大一的学生，项目一般由我个人维护，会尽量保证更新速度
5. 最后欢迎扫码进群唠嗑

![QQ群码](images/QQ群码.jpg "QQ群码")
![支付宝收款码](images/支付宝收款码.jpg "支付宝收款码")