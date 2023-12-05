# Auto_QQword
一个批量抽取QQ好友字符的小程序。
效果：
![image](https://github.com/PinkYuDeer/Auto_QQword/assets/83949453/ec6a0baa-d5a1-4e4e-b99a-8b6b5b60ca11)

-如果运行出现了乱码或者/033等说明缺少解析彩色控制台的转义文件，可以在[这里](https://github.com/adoxa/ansicon/releases)下载，运行对应版本的exe即可。

## 使用说明：
- 下载py文件或release里通过pyinstaller打包好的exe文件。
- 运行程序
- 通过引导。
- 开始自动抽取。
引导内容由两部分：1、录入QQ号；2、录入登录信息。

## 登录信息获取方式：
在任意设备上登录qq，然后查看ti.qq.com的cookies复制。
【例子：】作者使用的是[全平台抓包软件ProxyPIN](https://github.com/wanghongenpin/network_proxy_flutter)，步骤为：
打开ProxyPin-打开https代理-开始抓包-打开QQ-打开好友标识界面【注意：一定要打开好友标识界面，如图：】——
![image](https://github.com/PinkYuDeer/Auto_QQword/assets/83949453/93bd9037-2740-46b7-92d3-636c53528950)

返回ProxyPin-停止抓包-域名列表-ti.qq.com-点进一个GET后面链接中有friends_mutualmark的选项内——
【cookie：】-Request-Cookie-Select all-Copy Value-粘贴至程序内。
![image](https://github.com/PinkYuDeer/Auto_QQword/assets/83949453/20ce3f16-9c4e-4a62-9732-98b7c47bc696)
![image](https://github.com/PinkYuDeer/Auto_QQword/assets/83949453/023eab45-88a6-4bcc-a839-d6b55bc51e00)
【url：】-General-Request URL-Select all-CopyValue-粘贴至程序内。


## 其中，录入QQ号可以手动完成：
在第一次运行可以稍微输入几个，然后退出程序，进入生成的qq.ini文件中，手动在末尾添加。格式：
【有备注】qq号+空格+等于号+空格+备注。
【无备注】qq号+空格+等于号+空格。
快速复制所有好友的qq号和备注可以参考[这个教程](https://www.bilibili.com/read/cv10026240/)
