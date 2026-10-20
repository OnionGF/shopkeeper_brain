Aolynk CB304n Cable 网桥

用户手册

Copyright © 2014 杭州华三通信技术有限公司及其许可者 版权所有，保留一切权利。

未经本公司书面许可，任何单位和个人不得擅自摘抄、复制本书内容的部分或全部，并不得以任何形式传播。

H3C、 、H3CS、H3CIE、H3CNE、Aolynk、 Aolynk 、H<sup>3</sup>Care、 Yeare IRF、NetPilot、Netflow、SecEngine、SecPath、SecCenter、SecBlade、Comware、ITCMM、HUASAN、华三均为杭州华三通信技术有限公司的商标。对于本手册中出现的其它公司的商标、产品标识及商品名称，由各自权利人拥有。

由于产品版本升级或其他原因，本手册内容有可能变更。H3C 保留在没有任何通知或者提示的情况下对本手册的内容进行修改的权利。本手册仅作为使用指导，H3C 尽全力在本手册中提供准确的信息，但是 H3C 并不确保手册内容完全没有错误，本手册中的所有陈述、信息和建议也不构成任何明示或暗示的担保。

## 前 言

《Aolynk CB304n Cable 网桥 用户手册》将会详细地指导您如何通过 Web 设置页面对设备进行本地管理。

前言部分包含如下内容:

<u>读者对象</u>

<u>本书约定</u>

<u>资料获取方式</u>

<u>技术支持</u>

<u>资料意见反馈</u>

## 读者对象

本手册主要适用于如下工程师:

网络规划人员

• 现场技术支持与维护人员

负责网络配置和维护的网络管理员

## 本书约定

## 1. 命令行格式约定

| 格 式 | 意 义 |
| --- | --- |
| 粗体 | 命令行关键字（命令中保持不变、必须照输的部分）采用加粗字体表示。 |
| 斜体 | 命令行参数（命令中必须由实际值进行替代的部分）采用斜体表示。 |
| [ ] | 表示用"[ ]"括起来的部分在命令配置时是可选的。 |
| { x \| y \| ... } | 表示从多个选项中仅选取一个。 |
| [ x \| y \| ... ] | 表示从多个选项中选取一个或者不选。 |
| { x \| y \| ... } * | 表示从多个选项中至少选取一个。 |
| [ x \| y \| ... ] * | 表示从多个选项中选取一个、多个或者不选。 |
| &amp;&lt;1-n> | 表示符号&amp;前面的参数可以重复输入1～n次。 |
| # | 由"#"号开始的行表示为注释行。 |

## 2. 图形界面格式约定

| 格 式 | 意 义 |
| --- | --- |
| &lt; > | 带尖括号"&lt; >"表示按钮名，如"单击&lt;确定>按钮"。 |
| [ ] | 带方括号"[ ]"表示窗口名、菜单名和数据表，如"弹出[新建用户]窗口"。 |
| / | 多级菜单用"/"隔开。如[文件/新建/文件夹]多级菜单表示[文件]菜单下的[新建]子菜单下的[文件夹]菜单项。 |

## 3. 各类标志

本书还采用各种醒目标志来表示在操作过程中应该特别注意的地方，这些标志的意义如下:

<table><tr><td><img src="data:image/jpeg;base64,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"/> 注意</td><td>提醒操作中应注意的事项,不当的操作可能会导致数据丢失或者设备损坏。</td></tr><tr><td>[0598] 提示</td><td>为确保设备配置成功或者正常工作而需要特别关注的操作或信息。</td></tr><tr><td><img src="data:image/jpeg;base64,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"/> 说明</td><td>对操作内容的描述进行必要的补充和说明。</td></tr></table>

## 资料获取方式

您可以通过H3C网站（<u>www.h3c.com.cn</u>）获取最新的产品资料:

H3C 网站与产品资料相关的主要栏目介绍如下:

<u>[服务支持/文档中心]</u>:可以获取硬件安装类、软件升级类、配置类或维护类等产品资料。

<u>[产品技术]</u>:可以获取产品介绍和技术介绍的文档，包括产品相关介绍、技术介绍、技术白皮书等。

<u>[解决方案]</u>:可以获取解决方案类资料。

<u>[服务支持/软件下载]</u>:可以获取与软件版本配套的资料。

## 技术支持

用户支持邮箱:service@h3c.com

技术支持热线电话:400-810-0504（手机、固话均可拨打）

网址:<u>http://www.h3c.com.cn</u>

## 资料意见反馈

如果您在使用过程中发现产品资料的任何问题，可以通过以下方式反馈:

E-mail:info@h3c.com

感谢您的反馈，让我们做得更好！

## 目 录

- 1 您想了解什么？.... 1-1
- 2 产品概述.... 2-1
- 2.1 产品简介.... 2-1
- 2.2 产品特点.... 2-1
- 3 登录设备Web页面.... 3-1
- 3.1 建立网络连接.... 3-1
- 3.1.1 有线方式.... 3-1
- 3.1.2 无线方式.... 3-2
- 3.1.3 取消代理服务器.... 3-3
- 3.2 登录设备Web页面.... 3-4
- 3.3 熟悉Web设置页面.... 3-5
- 3.3.1 Web设置页面概述.... 3-5
- 3.3.2 退出.... 3-6
- 4 设备常用功能管理.... 4-1
- 4.1 网络.... 4-1
- 4.1.1 LAN侧地址配置.... 4-1
- 4.1.2 无线配置.... 4-2
- 4.2 安全.... 4-5
- 4.2.1 广域网访问控制.... 4-5
- 4.2.2 防火墙.... 4-5
- 4.2.3 Mac过滤.... 4-6
- 4.2.4 IP过滤.... 4-7
- 4.3 应用.... 4-7
- 4.3.1 DDNS配置.... 4-7
- 4.3.2 高级NAT配置.... 4-8
- 4.3.3 upnp配置.... 4-10
- 4.3.4 IGMP配置.... 4-10
- 4.4 管理.... 4-11
- 4.4.1 用户管理.... 4-11
- 4.4.2 设备管理.... 4-12
- 4.5 状态.... 4-13
- 4.5.1 设备信息.... 4-13
- 4.5.2 网络侧信息.... 4-14

- 4.5.3 用户侧信息……4-14
- 4.6 帮助……4-15
- 5 附录-故障排除……5-1
- 6 附录-产品术语……6-1

## 您想了解什么？

| 如果您想 | 您可以查看 |
| --- | --- |
| 初识设备的大致形态、熟悉设备面板上的接口、指示灯及设备的主要特点 | "产品概述" |
| 通过有线或无线的方式建立网络连接，登陆设备Web页面 | "登录设备Web页面" |
| 通过Web设置页面来对设备进行配置和管理，包括:网络、安全、应用、管理和帮助 | "设备常用功能管理" |
| 定位或排除使用设备过程中遇到的问题 | "附录 - 故障排除" |
| 了解产品相关的技术术语及其解释 | "附录 - 产品术语" |

## 2 产品概述

本章节主要包含以下内容:

<u>产品简介</u>

<u>产品特点</u>

## 2.1 产品简介

Aolynk CB304n是 H3C推出的一款面向家庭用户的 EPCN无线终端设备。产品采用全新一代芯片，并且向前兼容，配合新一代 Aolynk CC700E 系列、CC754 系列、CC710 系列以及 CC721E 网络集中器，融合了 Cable 网络和无线路由器的功能，在提供有线客户端接入的同时允许支持802.11b/g/n 无线客户端接入，组网更灵活，使用更方便，同时不影响原有的 CATV 信号。

Aolynk CB304n 提供 4 个百兆全双工以太网接口，可用于连接计算机、数字机顶盒、IP 电话机等多种终端。同时内置 IEEE 802.11b/g/n 无线模块，最高支持 300Mbps 的传输速率，用于连接笔记本、平板电脑、智能手机等无线终端设备，是家庭用户及小企业构建无线网络的理想设备。

## 2.2 产品特点

提供 4 个 10/100M 自适应以太网接口，用于连接计算机、机顶盒、IP 电话等设备。

具有无线接入点功能。工作在 2.4GHz 频段，支持 802.11n 标准，最高传送速率达到 300M，能够兼容目前的 802.11b 和 802.11g 网络。

内置分离滤波器。

占用 65MHz 以下的低频带通信，对现有的 CATV 信号无任何影响。

## 3 登录设备Web页面

本章节主要包含以下内容:

<u>建立网络连接</u>

<u>登录设备Web页面</u>

<u>熟悉Web设置页面</u>

完成硬件安装后（安装过程可参见《Aolynk CB 系列 Cable 网桥 快速入门》），在登录设备的 Web设置页面前，您需要确保管理计算机和网络满足一些基本要求。

## 3.1 建立网络连接

您可以通过有线方式或无线方式连接到 CB304n。以下描述均在 CB304n 缺省配置的基础上进行。

## 3.1.1 有线方式

1. 客户端计算机要求

• 确认计算机已安装并启用了以太网网卡。

• 确认计算机已和 CB304n 的 LAN 口相连（有线方式）。

2. 设置客户端计算机的IP地址

建议您将计算机设置成缺省的“自动获得 IP 地址”和“自动获得 DNS 服务器地址”，由 CB304n自动分配 IP 地址。

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img1.jpg)

## 说明

如果您想给计算机指定静态 IP 地址，则需要将计算机的 IP 地址与 CB304n 的 IP 地址设置在同一子网中（CB304n 缺省 IP 地址为:192.168.1.1，子网掩码为 255.255.255.0）。

## 3. 确认管理计算机和设备之间的网络是否连通

操作步骤如下:

通过快捷键&lt;Win+R&gt;，弹出“运行”对话框

运行

打开(O):

输入“ping 192.168.1.1（设备的IP地址，此处是缺省IP地址）”，单击<确定>按钮。如果在弹出的对话框中显示了从设备侧返回的回应，则表示网络连通；否则请检查网络连接

Windows将根据您所输入的名称，为您打开相应的程序文件夹、文档或Internet资源。

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img2.jpg)

ping 192.168.1.1

使用管理权限创建此任务。

确定

取消

浏览(B)...

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img3.jpg)

## 3.1.2 无线方式

1. 客户端计算机要求

• 确认计算机已安装了无线网卡，并处于开启状态。

• 将计算机放置于 CB304n 的无线网络范围内。

2. 设置客户端计算机的IP地址

建议您将计算机设置成缺省的“自动获得 IP 地址”和“自动获得 DNS 服务器地址”，由 CB304n自动分配 IP 地址。

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img4.jpg)

## 说明

如果您想给计算机指定静态 IP 地址，则需要将计算机的无线网卡的 IP 地址与 CB304n 的 IP 地址设置在同一子网中（CB304n 缺省 IP 地址为:192.168.1.1，子网掩码为 255.255.255.0）。

## 3. 设置无线客户端

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img5.jpg)

## 说明

本手册以 Windows7 的无线网络设置功能为例进行介绍。

单击屏幕左下角<开始>按钮，进入[开始]菜单，选择[控制面板]，点击“网络和 Internet”，打开“网络和共享中心”

• 单击“更改适配器设置”，显示无线网络连接界面

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img6.jpg)

本地连接2

在“无线网络连接” 列表里找到需连接的无线网络，缺省情况下，CB304n提供一个名为

“ROUTE\_XXXXXX”的无线网络，XXXXXX为设备背面铭牌上MAC地址的后六位，且不加密，单击<连接(C)>按钮，即可连接成功

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img7.jpg)

## 3.1.3 取消代理服务器

如果当前管理计算机使用代理服务器访问因特网，则必须取消代理服务，操作步骤如下:

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img8.jpg)

## 3.2 登录设备Web页面

运行Web浏览器，在地址栏中输入“http://192.168.1.1”，回车后跳转到Web登录页面，如 <u>图 3-1</u>所示，输入用户名、密码（缺省均为admin，区分大小写），单击<登录>按钮或直接回车即可进入Web设置页面。

图3-1 登录设备 Web 设置页面

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img9.jpg)

登录

admin

取消

## 3.3 熟悉Web设置页面

设备提供非常简便的 Web 设置页面，您可以通过该设置页面快速地完成所需功能的配置。

## 3.3.1 Web设置页面概述

成功登录后，出现Web设置页面。设备提供的Web页面主要分为两部分，如 <u>图 3-2</u> 所示。

页面上方是一级导航栏。通过单击链接，可以进入相应的配置、管理页面。

页面左侧是二级导航栏及配置管理区域。右侧显示的内容根据导航栏选中的功能而定，详细信息请参见下面具体业务配置。

图3-2 Web 设置页面

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img10.jpg)

为了安全起见，建议您首次登录后修改缺省的登录密码，并保管好密码信息，修改登录密码操作请参见 <u>4.4.1 用户管理</u>。

## 3.3.2 退出

如 <u>图 3-3</u> 所示，单击导航栏右上角的<退出>按钮，确认后即可退出Web设置页面。

图3-3 退出 Web 设置页面

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img11.jpg)

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img12.jpg)

请勿通过直接关闭浏览器来退出 Web 设置页面，因为这样操作用户并不能真正退出设备的 Web 设置页面。

## 设备常用功能管理

## 4.1 网络

## 4.1.1 LAN侧地址配置

## 页面向导:网络→LAN 侧地址配置→IPV4 配置本页面为您提供如下主要功能:

配置 LAN 侧的 IPv4 地址信息，包括网关 IP 地址、起始/终止 IP地址和 DNS 服务器等。

配置完成后，单击<保存/应用>按钮，配置将被保存并生效。

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img13.jpg)

页面中关键项的含义如下表所示。

表4-1 页面关键项描述

| 页面关键项 | 描述 |
| --- | --- |
| IP地址/子网掩码 | 配置网关的IP地址和子网掩码 |
| 禁用/启用环流控制 | 启用环流控制，即表示局域网侧开启STP（Spanning Tree Protocol，生成树协议）功能 |
| 禁用/启用DHCP服务 | •开启网关的DHCP服务器功能，网关将自动为连接到网关的设备分配IP地址 |
| 器 | •禁用网关的DHCP服务器功能，网关将不能为连接到网关的设备分配IP地址 |
| 起始/终止IP地址 | 启用DHCP服务器功能后，网关可指定设备的起始和终止IP地址 |
| 延续时间 | DHCP服务器分配的租约时间 |
| DNS服务器 | •自动:连接到网关的设备可以自动连接到局域网内的DNS服务器•手动:手动设置连接到网关的设备需连接的局域网内的DNS服务器地址 |
| 首选/备用DNS服务器 | 配置首选和备用的DNS服务器 |
| 预留IP地址 | 通过&lt;添加>或&lt;删除>按钮，您可以添加或删除一个规则:一个MAC地址对应一个IP地址 |

## 4.1.2 无线配置

## 页面向导:网络→无线配置→无线配置

本页面为您提供如下主要功能:

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img14.jpg)

页面中关键项的含义如下表所示。

表4-2 页面关键项描述

| 页面关键项 | 描述 |
| --- | --- |
| 启用无线 | 启用或禁用无线网络，缺省为开启状态 |
| 隐藏热点 | 启用或禁用隐藏热点，启用后终端将无法通过扫描来获得设备的SSID |
| 客户端分离 | 启用或禁用客户端分离，启用后可以使无线网络中的不同客户端之间相互隔离，不能通信 |
| SSID | 设置无线网络名，SSID用来区分不同的无线网络 |
| BSSID | 无线网络设备的MAC地址 |
| 访问数量限制 | 设置同时访问无线网络的用户数量 |

## 页面向导:网络→无线配置→无线配置→安全

本页面为您提供如下主要功能:

配置无线 LAN 口的安全特性。包括设置认证方式、数据加密方式、无线网络认证密钥和密钥长度等。

配置完成后，单击<保存/应用>按钮，配置将被保存并生效。

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img15.jpg)

页面中关键项的含义如下表所示。

表4-3 页面关键项描述

| 页面关键项 | 描述 |
| --- | --- |
| 选择SSID | 选择需要配置的无线网络 |
| 网络认证方式 | 可以选择开放、共享、WPA-PSK、WPA2-PSK、Mixed WPA2/WPA-PSK等认证方式 |
| WEP加密 | 可以选择禁用或者启用 |

页面向导:网络→无线配置→无线配置→安全（以网络认证方式为 Mixed WPA2/WPA-PSK 举例）本页面为您提供如下主要功能:

将网络认证方式设置为 Mixed WPA2/WPA-PSK，将显示右图所示页面。

配置完成后，单击<保存/应用>按钮，配置将被保存并生效。

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img16.jpg)

页面中关键项的含义如下表所示。

表4-4 页面关键项描述

| 页面关键项 | 描述 |
| --- | --- |
| 网络认证方式 | 设置无线认证方式，选择Mixed WPA2/WPA-PSK |
| WPA预共享密钥 | 设置WPA预共享密钥 |
| 显示文本 | 勾选该选项，WPA预共享密钥将以明文显示 |
| WPA更新会话密钥间隔 | 设置WPA更新会话密钥间隔时间，缺省为3600s |
| WPA加密 | 设置WPA加密方式，可以选择TKIP、AES或TKIP+AES等加密方式 |

## 页面向导:网络→无线配置→无线高级配置

本页面为您提供如下主要功能:

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img17.jpg)

页面中关键项的含义如下表所示。

表4-5 页面关键项描述

| 页面关键项 | 描述 |
| --- | --- |
| 频段 | 无线使用的频段 |
| 信道选择 | 无线信息，有1-13选择，也可以选择Auto |
| 802.11n/EWC | 启用或禁用802.11n功能•选择"自动"，开启802.11n模式，此时可以设置802.11n模式的速率；•选择"禁用"，关闭802.11n模式，此时可以设置54g<sup>TM</sup>模式和前导类型 |
| 带宽 | 无线网络工作的带宽 |
| 控制边带 | 默认为降低控制边带 |
| 802.11n速率 | 设置802.11n工作的速率 |
| 仅支持802.11n客户端 | 是否启用仅支持802.11n客户端 |
| 54g<sup>TM</sup>速率 | 缺省为54Mbps |
| 54g<sup>TM</sup>模式选择 | 设置54g<sup>TM</sup>模式，默认为54g Auto |
| 前导类型 | 设置前导类型，默认为long |
| 发送功率 | 缺省为100% |

## 4.2 安全

## 4.2.1 广域网访问控制

## 页面向导:安全→广域网访问控制→广域网访问控制本页面为您提供如下主要功能:

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img18.jpg)

## 4.2.2 防火墙

## 1. 防火墙等级

## 页面向导:安全→防火墙→防火墙等级

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img19.jpg)

## 2. 攻击保护设置

页面向导:安全→防火墙→攻击保护设置

本页面为您提供如下主要功能:

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img20.jpg)

## 4.2.3 Mac过滤

## 页面向导:安全→Mac 过滤→Mac 过滤

本页面为您提供如下主要功能:

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img21.jpg)

页面中关键项的含义如下表所示。

表4-6 页面关键项描述

| 页面关键项 | 描述 |
| --- | --- |
| MAC地址过滤 | 禁用和开启MAC地址过滤功能，缺省处于禁用状态 |
| 过滤模式 | 可以配置过滤模式为白名单和黑名单:•启用黑名单后，除加入黑名单的MAC地址不可以通过，其余均可通过•启用白名单后，除加入白名单的MAC地址可以通过，其余均不可通过 |

## 4.2.4 IP过滤

## 页面向导:安全→IP 过滤→IP 过滤本页面为您提供如下主要功能:

配置过滤器名，并配置协议、源 IP 地址、源子网掩码、目的IP 地址和目的子网掩码等过滤器规则。

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img22.jpg)

页面中关键项的含义如下表所示。

表4-7 页面关键项描述

| 页面关键项 | 描述 |
| --- | --- |
| IP地址过滤 | 开启或禁用IP地址过滤功能，缺省处于开启状态 |
| 流出IP过滤器配置 | 配置流出IP过滤器来阻止某些IP通信 |

## 4.3 应用

## 4.3.1 DDNS配置

## 页面向导:应用→DDNS 配置→DDNS 配置

本页面为您提供如下主要功能:

配置动态 DNS 服务，可以将一个动态的IP地址化名为任意多域中的一个静态主机名。

单击<添加>按钮，在“添加动态 DNS”页面，选择 D-DNS提供方，并通过配置域名、接口、用户名和密码等信息，添加一个动态 DNS 地址。

配置完成后，单击<保存/应用>按钮，配置将被保存并生效。

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img23.jpg)

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img24.jpg)

## 4.3.2 高级NAT配置

## 1. ALG配置

页面向导:应用→高级 **NAT** 配置→**ALG** 配置

本页面为您提供如下主要功能:

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img25.jpg)

## 2. DMZ主机配置

页面向导:应用→高级 **NAT** 配置→**DMZ** 主机配置

本页面为您提供如下主要功能:

配置主机在 DMZ 下的主机可以无限制访问互联网，解决计算机不能够正常运行互联网应用程序等问题。不过这会使主机面临安全风险，请谨慎使用。

配置完成后，单击<保存/应用>按钮，配置将被保存并生效。

## NAT--DMZ主机

路由器将所有来自广域网中不属于虚拟服务列表中配置的应用的Ip报文发给DMZ主机

☑启用DMZ主机

输入电脑IP地址，然后点击"应用"按钮激活DMZ主机

清空IP地址输入框，然后点击"应用"按钮解除DMZ主机

DMZ主机IP地址:

192.168.1.18

保存/应用

## 3. 虚拟服务器配置

## 页面向导:应用→高级 NAT 配置→虚拟服务器配置

## 本页面为您提供如下主要功能:

配置虚拟服务器，允许将 WAN侧输入流(根据协议和端口识别)直接转发到 LAN 侧拥有私有地址的内部服务器。仅当外部端口需要转化为LAN侧服务器不同的端口时，内部端口才需设置。最多可配置 32 个条目。

配置完成后，单击<保存/应用>按钮，配置将被保存并生效。

## NAT--虚拟服务器设置

虚拟服务器允许将WAN侧输入流(根据协议和端口识别)直接转发到LAN侧拥有私有地址的内部服务器仅当外部端口需要转化为LAN侧服务器不同的端口时,内部端口才需设置。

最多可配置32个条目

添加

## NAT--虚拟服务器设置

选择服务名并输入服务器的IP地址，然后点击"保存/应用”，为这项服务将IP包转发到指定的服务器。

注:通常内部结束端口不能直接修改。其值等于外部结束端口-外部开始端口+内部开始端口。端口值取值范围1-65535

选择WAN连接: 2\_INTERNET\_R\_VID\_201/eth0.201.3

服务器名称:

自定义服务器:

<table><tr><td colspan="5">可剩余配置条目:32</td></tr><tr><td>外部开始端口</td><td>外部结束端口</td><td>协议</td><td>内部开始端口</td><td>内部结束端口</td></tr><tr><td></td><td></td><td>TCP▼</td><td></td><td></td></tr><tr><td></td><td></td><td>TCP▼</td><td></td><td></td></tr><tr><td></td><td></td><td>TCP▼</td><td></td><td></td></tr><tr><td></td><td></td><td>TCP▼</td><td></td><td></td></tr><tr><td></td><td></td><td>TCP▼</td><td></td><td></td></tr><tr><td></td><td></td><td>TCP▼</td><td></td><td></td></tr><tr><td></td><td></td><td>TCP▼</td><td></td><td></td></tr><tr><td></td><td></td><td>TCP▼</td><td></td><td></td></tr><tr><td></td><td></td><td>TCP▼</td><td></td><td></td></tr><tr><td></td><td></td><td>TCP▼</td><td></td><td></td></tr><tr><td></td><td></td><td>TCP▼</td><td></td><td></td></tr></table>

保存应用

页面中关键项的含义如下表所示。

表4-8 页面关键项描述

| 页面关键项 | 描述 |
| --- | --- |
| 服务器名 | 选择一项服务，例如SMTP、POP、HTTP、FTP Server等，被选择服务对应的端口号将被显示在下表框 |
| 自定义服务器 | 输入一个新的服务名建立指定的用户服务类型 |
| 服务器IP地址 | 分配一个指定的地址到虚拟服务器 |
| 外部开始/结束端口 | 当选择了一种服务，端口号自动显示，也可以根据需要更改 |
| 协议 | 为服务选择正确的协议 |
| 内部开始/结束端口 | 当选择了一种服务，端口号自动显示，也可以根据需要更改。其中内部结束端口不能手动修改 |

## 4.3.3 upnp配置

页面向导:应用→**upnp** 配置→**upnp** 配置

本页面为您提供如下主要功能:

通过配置可以禁止一部分 LAN UPnP配置侧 IP 使用 upnp 功能。

配置完成后，单击<添加>按钮，配置将被保存并生效。

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img26.jpg)

## 4.3.4 IGMP配置

1. IGMP SNOOPING

页面向导:应用→**IGMP** 配置→**IGMP SNOOPING**

本页面为您提供如下主要功能:

启用或禁止 IGMP Snooping功能，使得用户可以通过路由器观看 IPTV 节目。

配置完成后，单击<保存/应用>按钮，配置将被保存并生效。

## IGMP Snooping 配置

这个页面允许你启用或者禁用IGMP Snooping功能。

☑启用IGMP Snooping

标准模式

C阻塞模式

保存/应用

页面中关键项的含义如下表所示。

表4-9 页面关键项描述

| 页面关键项 | 描述 |
| --- | --- |
| 标准模式 | 在标准模式下，如果没有组播转发条目，数据流将会洪泛 |
| 阻塞模式 | 在阻塞模式下，如果没有组播转发条目，数据流将会丢弃 |

## 2. IGMP 代理

## 页面向导:应用→IGMP 配置→IGMP 代理

本页面为您提供如下主要功能:

配置 IGMP 代理功能，使得用户可以通过路由器观看 IPTV节目。

IGMP服务器设定

启用服务器功能可以允许使用者在局端网络使用因特网服务器的多媒体服务

配置完成后，单击<保存/应用>按钮，配置将被保存并生效。 IGMP配置

这个页面允许你针对特定WAN连接启用IGMP代理

| 因特网连接 | IGMP 服务器启用 |
| --- | --- |
| 1_INTERNET_R_VID_ | ☑ |

保存/应用

## 4.4 管理

## 4.4.1 用户管理

页面向导:管理→用户管理→用户管理

本页面为您提供如下主要功能:

• 通过此页面，可以修改用户的密码。

## 访问控制 --密码

配置完成后，单击<保存/应用>按钮，配置将被保存并生效。

本页面只允许修改密码。

注意:如果修改成功，需要重新登录。

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img27.jpg)

注意:密码只能在16个字符以内，且不能包含空格。

原用户名:

确认密码:

## 4.4.2 设备管理

## 1. 设备重启

页面向导:管理→设备管理→设备重启

本页面为您提供如下主要功能:

<table><tr><td>状态</td><td>网络</td><td>安全</td><td>应用</td><td>管理</td><td>帮助</td><td></td><td></td></tr><tr><td colspan="8">点击如下按钮重启路由器。</td></tr><tr><td colspan="8">重启</td></tr></table>

## 2. 恢复出厂设置

页面向导:管理→设备管理→恢复出厂设置

本页面为您提供如下主要功能:

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img28.jpg)

恢复出厂设置

## 3. 更新备份配置

页面向导:管理→设备管理→更新备份配置

本页面为您提供如下主要功能:

单击<更新配置>按钮，将使用配置文件更新设备的配置。

单击<备份配置>按钮，将备份设备的配置文件。

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img29.jpg)

## 4.5 状态

## 4.5.1 设备信息

## 1. 设备基本信息

页面向导:状态→设备信息→设备基本信息本页面为您提供如下主要功能:

查看设备的基本信息，包括:设备型号、设备标志号、硬件版本、软件版本、bootloader版本、生产序列号、系统运行时间、软件编译时间和系统资源使用情况等。

| 设备型号: | CB304n |
| --- | --- |
| 设备标志号: | BC9680-BC9680F7D6B8 |
| 硬件版本: | VER.A |
| 软件版本: | V100R001 |
| bootloader版本: | V2.2 |
| 生产序列号: | 201402000001 |
| 系统运行时间: | 0天:0小时:53分:54秒 |
| 软件编译时间: | 2014-07-21 09:47:25 |
| 系统资源使用情况: | 总内存大小61592 KB;空闲内存大小 31700 KB;内存空闲率 51% |

页面中关键项的含义如下表所示。

表4-10 页面关键项描述

<table><tbody><tr><td>页面关键项</td><td>描述</td></tr><tr><td>设备型号</td><td>显示当前设备的型号</td></tr><tr><td>设备标志号</td><td>显示当前设备的设备标志号</td></tr><tr><td>硬件版本</td><td>显示当前设备的硬件版本</td></tr><tr><td>软件版本</td><td>显示设备当前运行软件的版本号<img src="data:image/jpeg;base64,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"/> 说明页面中的软件版本信息仅作参考,请以设备加载软件版本后的最终显示为准</td></tr><tr><td>bootloader版本</td><td>显示设备的bootloader程序版本号</td></tr><tr><td>生产序列号</td><td>显示设备的生产序列号</td></tr><tr><td>系统运行时间</td><td>显示设备自启动后持续运行的时间</td></tr><tr><td>软件编译时间</td><td>显示设备当前运行软件的编译时间</td></tr><tr><td>系统资源使用情况</td><td>显示设备系统资源使用信息,便于您判断设备运行是否正常</td></tr></tbody></table>

## 4.5.2 网络侧信息

## 1. IPV4 连接信息

页面向导:状态→网络侧信息→**IPV4** 连接信息

本页面为您提供如下主要功能:

通过此页面可以查看网络侧已配置的 IPv4 的连接信息。

WAN 连接信息

• 单击“刷新”按钮，将刷新 WAN连接信息。

| 接口名 | 接口描述 | 类型 | VlanMuxId | IGMP | NAT | 防火墙 | 状态 | DNS地址 | IPv4地址 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eth0_3 | 1_INTERNET_R_VID_ | IPoE | 禁用 | 启用 | 启用 | 启用 | Connecting |  |  |

网络信息

| 默认网关 |  |
| --- | --- |
| 子网掩码 |  |
| 首选DNS服务器 |  |
| 备用DNS服务器 |  |

刷新

## 4.5.3 用户侧信息

## 1. WLAN接口信息

页面向导:状态→用户侧信息→**WLAN** 接口信息

本页面为您提供如下主要功能:

<table><tr><td rowspan="3">通过此页面可以查看用户侧已配置的WLAN接口的连接信息</td><td colspan="4">WLAN接口信息</td></tr><tr><td>SSID名称</td><td>无线网络连接状态</td><td>当前信道</td><td>SSID加密认证方式</td></tr><tr><td>ROUTE_F7D6B8</td><td>启用</td><td>5</td><td>开放</td></tr></table>

## 2. 以太网接口信息

页面向导:状态→用户侧信息→以太网接口信息

本页面为您提供如下主要功能:

<table><tr><td rowspan="14">通过此页面可以查看以太网接口的连接信息</td><td colspan="4">网关信息</td></tr><tr><td colspan="2">MAC 地址</td><td colspan="2">bc:96:80:f7:d6:78</td></tr><tr><td colspan="4">内网设备信息</td></tr><tr><td>IP 地址</td><td>剩余租借期</td><td>MAC 地址</td><td>设备类型</td></tr><tr><td>192.168.11.100</td><td>80046s</td><td>d4:97:0b:88:bb:7d</td><td>计算机</td></tr><tr><td>192.168.11.101</td><td>80658s</td><td>c4:6a:b7:51:9c:9f</td><td>计算机</td></tr><tr><td>192.168.11.106</td><td>84923s</td><td>88:32:9b:e9:29:ab</td><td>计算机</td></tr><tr><td>192.168.11.103</td><td>86307s</td><td>bc:3b:af:0c:71:4b</td><td>计算机</td></tr><tr><td>192.168.11.104</td><td>85216s</td><td>60:c5:47:61:07:6c</td><td>计算机</td></tr><tr><td>192.168.11.107</td><td>85499s</td><td>6c:c2:6b:48:3a:e3</td><td>计算机</td></tr><tr><td>192.168.11.108</td><td>86154s</td><td>6c:8b:2f:7f:3b:f9</td><td>计算机</td></tr><tr><td>192.168.11.110</td><td>86161s</td><td>60:fa:cd:07:a6:46</td><td>摄像头</td></tr><tr><td>192.168.11.111</td><td>86186s</td><td>bc:c6:db:d0:65:56</td><td>摄像头</td></tr><tr><td>192.168.11.127</td><td>0s</td><td>74:46:a0:aa:78:25</td><td>计算机</td></tr></table>

## 4.6 帮助

单击一级导航<帮助>页签，可以查看设备的帮助信息。如 <u>图 4-1</u> 所示。

图4-1 设备帮助信息

<table><tr><td>帮助</td><td>状态</td><td>网络</td><td>安全</td><td>应用</td><td>管理</td><td>帮助</td><td></td><td></td></tr><tr><td colspan="9">状态帮助</td></tr><tr><td colspan="9">设备信息帮助</td></tr><tr><td colspan="9">设备基本信息</td></tr><tr><td colspan="9">设备基本信息页面显示设备型号,设备标识号,硬件版本,软件版本,bootloader版本,生产序列号,系统运行时间,软件编译时间,系统资源使用情况</td></tr></table>

## 附录 – 故障排除

本手册仅介绍简单的设备故障处理方法，如仍不能排除，可通过 <u>表 5-2</u> 获取售后服务。

表5-1 故障排除

<table><tr><td>常见问题</td><td>故障排除</td></tr><tr><td>插上电源后,所有指示灯不亮</td><td>请首先确认设备的电源适配器与电源插座连接正常,且设备电源开关已打开(即开关按钮已按下)。确认后如指示灯仍不亮,则可能电源适配器或设备已损坏。请联系当地运营商进行维修,切勿私自拆开设备</td></tr><tr><td>设备的Cable指示灯始终不亮</td><td>Cable指示灯若始终不亮表示Cable链路没有建立成功。请确认设备Cable口的同轴电缆是否插牢,同轴电缆另一端与入户接口是否连接正确。确认后如指示灯依然不亮,请与运营商联系,以确定是否为远端机房的EoC业务问题或运营商网络链路故障所致</td></tr><tr><td>搜索不到设备发出的无线信号或信号很弱</td><td>(1)确认计算机的无线网卡是否正常运作(2)确认是否关闭了本产品的SSID广播功能(3)如无线网卡距离设备太远,请靠近再扫描一次(4)确认附近是否有无线电话、微波炉或其他无线干扰源(5)确认设备的无线端口是否已激活。如不能确定,请恢复出厂值后重新扫描<img src="data:image/jpeg;base64,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"/>说明使用设备时应尽量远离无线电话和微波炉等产品,以消除频率干扰。而封闭空间、金属障碍物或混凝土墙壁等也会显著降低AP的覆盖范围</td></tr><tr><td>从无线网卡上可以发现无线信号但却无法建立无线连接</td><td>(1)请确认计算机的无线网卡驱动程序是否已正确安装,在其它的无线环境中是否能正常使用。如果您的无线网卡曾经在其它环境中设置并使用过,请检查是否原先预设的profile参数有影响,可尝试将原有的无线设置清除后再重新连接本设备<img src="data:image/jpeg;base64,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"/>说明关于计算机无线网卡的安装、设置和使用,可咨询您的无线网卡生产厂商或设备提供商(2)请确认无线网卡已搜索到并选择了正确的设备以建立连接(3)请检查无线网卡参数的设置是否与设备相一致,如:SSID名称,加密与否,加密类型和密钥<img src="data:image/jpeg;base64,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"/>说明设备标贴上有该设备的缺省的无线网络名称、默认加密方式和密钥(4)如您曾进行MAC/IP地址过滤设置,请确认“MAC/IP过滤”未屏蔽您的无线网卡</td></tr><tr><td>不能正常上网</td><td>先检查设备是否正常工作,再检查网线是否正常,确保其与设备之间的连接是可靠的如果设备工作正常,可能是您的计算机或者应用网络出现了问题。如果设备工作不正常,请根据具体的指示灯状态进行排查,或联系运营商解决</td></tr><tr><td>无法校验密码</td><td>设备同步、连接一切正常，但有时仍会出现无法校验密码的情况(1) 注意帐号和密码要区分大小写，并注意帐号是否包含域名(2) 虚拟拨号软件出现问题，或与您的操作系统里的某些软件有冲突。建议您最好重装拨号软件，或更换另外的软件尝试(3) 网卡驱动程序出现问题(4) 欠费，请及时交费</td></tr></table>

表5-2 获取售后服务

| 故障类型 | 描述 | 如何获取售后服务 |
| --- | --- | --- |
| 硬件类故障 | 比如:出现设备不能正常通电、未插网线但以太网端口指示灯却常亮等问题 | 请联系当地授权服务中心予以确认后更换（各地区的H3C授权服务中心的联系方式可在H3C官方网站找到） |
| 软件类问题 | 比如:出现设备功能不可用、异常等问题或配置咨询 | 请联系H3C技术支持服务热线:400-810-0504获取帮助 |

![暂无图片描述](http://minio.milvus.orb.local:9000/knowledge-base-v1/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册/Aolynk CB304n Cable网桥 用户手册-5W100-整本手册_img30.jpg)

## 附录 – 产品术语

表6-1 术语表

| 术语缩写 | 英文全称 | 中文名称 | 含义 |
| --- | --- | --- | --- |
| 100Base-TX | 100Base-TX | 100Base-TX | 100Mbit/s基带以太网规范，使用两对5类双绞线连接，可提供最大100Mbit/s的传输速率 |
| 10Base-T | 10Base-T | 10Base-T | 10Mbit/s基带以太网规范，使用两对双绞线（3/4/5类双绞线）连接，其中一对用于发送数据，另一对用于接收数据，提供最大10Mbit/s传输速率 |
| AP | Access Point | 接入点 | 作为无线网络中重要的环节无线接入点、无线网关也就是无线AP（Access Point），它的作用类似于我们常用的有线网络中的集线器 |
| DDNS | Dynamic Domain Name Service | 动态域名服务 | 动态域名服务（Dynamic Domain Name Service），能实现固定域名到动态IP地址之间的解析 |
| DHCP | Dynamic Host Configuration Protocol | 动态主机配置协议 | 动态主机配置协议（Dynamic Host Configuration Protocol）为网络中的主机动态分配IP地址、子网掩码、网关等信息 |
| DHCP Server | Dynamic Host Configuration Protocol Server | DHCP 服务器 | 动态主机配置协议服务器（Dynamic Host Configuration Protocol Server）是一台运行了DHCP动态主机配置协议的设备，主要用于给DHCP客户端分配IP地址 |
| DMZ | D zoenmeilitarized | 隔离区 | 为了解决安装防火墙后外部网络不能访问内部网络服务器缓的冲问区题。，通而过设这立样的一一个个DM非Z安区全域系，统能与更安加全有系效统地之保间护的了内部网络，因为对攻击者来说，又多了一道关卡 |
| DNS | D Seormviacien Name | 域名服务 | 域名服务（Domain Name Service）将域名解析成IP地址。DNS信息按等级分布在整个因特网上的DNS服务器间，当我们访问一个网址时，DNS服务器查看发出请求的域名并搜寻它所对应的IP地址。如果该DNS服务器无法找到这个IP地址，就将请求传送给上级DNS服务器，继续搜寻IP地址。例如，www.yahoo.com 这个域名所对应的IP地址为 216.115.108.243 |
| DoS | D Seernviaicle of | 拒绝服务 | 拒绝服务（Denial of Service）是一种利用合法的方式请求占用过多的服务资源，从而使其他用户无法得到服务响应的网络攻击行为 |
| DSL | D Suigbitsaclriber Line | 数字用户线路 | 数字用户线（Digital Subscriber Line）这种技术使得数字数据和仿真语音信号都可以在现有的电话线路上进行传输。目前比较受家庭用户青睐的是ADSL接入方式 |
| Firewall | Firewall | 防火墙 | 防火墙（Firewall）技术保护您的计算机或局域网免受来自外网的恶意攻击或访问 |
| FTP | F Pirloeto Tcraonl sfer | 文件传输协议 | 文上件的传计输算协机议之（间F如ile何 T传ra输ns文fe件r P的ro协to议col）是一种描述网络 |
| HTTP | Hypertext Transfer Protocol | 超文本传送协议 | 超文本传送协议（Hypertext Transfer Protocol）是一种主要用于传输网页的标准协议 |
| Hub | Hub | 集线器 | 共享式网络连接设备，工作在物理层，主要用于扩展局域网规模 |
| ISP | I Pnrtoevrnideetr Service | 因商特网服务提供 | 因因特特网网服接务入提服供务商的（提I供nt商ernet Service Provider），提供 |
| LAN | L Noectwalo Arkrea | 局域网 | 局庭域网网络（，L中o小ca型l A企re业a的 Ne内tw部or网k）络一等般指内部网，例如家 |
| MAC address | M Coendtiraol A acdcdersesss | 介址质访问控制地 | 介质访问控制地址（Media Access Control address），M对A十C六地进址制是数由字厂所商构指成定。给例设如备:的0永0-久0F物-E理2-地80址-6，5-2它5由。每6一个网络设备都拥有一个全球唯一的MAC地址 |
| NAT | Network Address Translation | 网络地址转换 | 网络地址转换（Network Address Translation），可以把局域网内的多台计算机通过NAT转换后共享一个或多个公网IP地址，接入Internet，这种方式同时也可以屏蔽局域网用户，起到网络安全的作用。通常共享上网的宽带设备都使用这个技术 |
| Ping | P Garocpkeet Internet | 因特网包探测器 | Ping 命令是用来测试本机与网络上的其它计算机能否进行通信的诊断工具。Ping命令将报文发送给指定的计算机，如果该计算机收到报文则会返回响应报文 |
| PPP | P Proointot-ctool-Point | 点对点协议 | 点信对协点议协议（Point-to-Point Protocol）是一种链路层通 |
| PPPoE | P EtPhPer onveetr | 点载对协点议以太网承 | 点对点以太网承载协议（PPP over Ethernet）在以太网上承载PPP协议封装的报文，它是目前使用较多的业务形式 |
| RJ-45 | RJ-45 | RJ-45 | 用于连接以太网交换机、集线器、设备等设备的标准插头。直连网线和交叉网线通常使用这种接头 |
| Route | Route | 路由 | 基于数据的目的地址和当前的网络条件，通过有效的路由选择能够到达目的网络或地址的出接口或网关，进行数据转发。具有路由功能的设备称作设备（router） |
| TCP | Transfer Control Protocol | 传输控制协议 | 传输控制协议（Transfer Control Protocol）是一种面向连接的、可靠的传输层协议。 |
| TCP/IP | Transmission C Proonttorcool l/Interne t Protocol | 传网输际控协制议协议/ | 传输控制协议/网际协议（Transmission Control Protocol/Internet Protocol），网络通信的基本通信协议簇。TCP/IP定义了一组协议，不仅仅是TCP和IP |
| Telnet | Telnet | Telnet | 一种用来访问远程主机的基于字符的交互程序。Telnet允许用户远程登录并对设备进行管理 |
| UDP | U Prsoetroc Doaltagram | 用户数据报协议 | 向用非户连数接据的报传协输议层（协Us议er Datagram Protocol）是一种面 |
| VLAN | V Ariretuaa Nl e Ltowcoarlk | 虚拟局域网 | 虚物拟理局地域划网分是成一一种个通个过网将段局从域而网实内现的虚设拟备工逻作辑组地的而技不术是 |
| VID | VLAN ID | VLAN标识符 | - |
| WAN | W Neidtweo Arkrea | 广域网 | 广的域数网据（通W信i网de络 A，rea如 N因et特wo网rk）是覆盖地理范围相对较广 |
| WLAN | W Ariereale Nsestw Loocrkal | 无线局域网 | 无线局域网是一种利用射频（Radio Frequency）技术进行数据传输的系统，用来弥补有线局域网络的不足，以达到网络延伸的目的 |