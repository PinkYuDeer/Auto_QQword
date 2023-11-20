# Auto_QQword
一个批量抽取QQ好友字符的小程序。
效果：
![image](https://github.com/PinkYuDeer/Auto_QQword/assets/83949453/0656d04a-668f-4b3b-9068-68bd7b0ee49b)

## 使用说明：
- 下载py文件或release里通过pyinstaller打包好的exe文件。
- 运行程序
- 通过引导。
- 开始自动抽取。
引导内容由两部分：1、录入QQ号；2、录入登录信息cookies。

## 登录信息cookies获取方式：
在任意设备上登录qq，然后查看ti.qq.com的cookies复制。
【例子：】作者使用的是[全平台抓包软件ProxyPIN](https://github.com/wanghongenpin/network_proxy_flutter)，步骤为：
打开ProxyPin-打开https代理-开始抓包-打开QQ-打开字符页面-返回ProxyPin-
停止抓包-域名列表-ti.qq.com-随便一个点进去-Request-Cookie-Select all-Copy Value-粘贴至程序内。
![image](https://github.com/PinkYuDeer/Auto_QQword/assets/83949453/20ce3f16-9c4e-4a62-9732-98b7c47bc696)
![image](https://github.com/PinkYuDeer/Auto_QQword/assets/83949453/023eab45-88a6-4bcc-a839-d6b55bc51e00)


## 其中，录入QQ号可以手动完成：
同级目录下创建qq.ini，内容为：1、自己的QQ号2、需要抽卡的QQ号们；
每行一个qq号格式：（qq号+空格+备注）
【！！注意！！】必须要有一个备注为“__我”（下划线下划线我）的QQ号作为myself_qq。
