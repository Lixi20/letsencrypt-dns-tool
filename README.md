# LetsEncryptDnsTool

Let's Encrypt DNS工具

## 获取AccessKey
### 阿里云

https://www.alibabacloud.com/help/zh/doc-detail/107708.htm

操作步骤：
1. 以主账号登录阿里云管理控制台。
2. 将鼠标置于页面右上方的账号图标，单击accesskeys。
3. 在安全提示页面，选择获取主账号还是子账号的Accesskey。

API参考：

https://help.aliyun.com/document_detail/29740.html

### 腾讯云

https://console.cloud.tencent.com/cam/capi

操作步骤：
1. 以主账号登录腾讯云管理控制台。
2. 将鼠标置于页面左边导航栏的API密钥管理并单击，如没有密钥，点击新建密钥。
3. 在API密钥管理页面，选择获取主账号还是子账号的SecretKey。

API参考：

https://cloud.tencent.com/document/api/1427/56180

## 运行

### 增加域名解析记录

```bash
CERTBOT_DOMAIN=foo.com CERTBOT_VALIDATION=123 python3 app.py --auth
```

验证域名解析：

    $ dig _acme-challenge.foo.com TXT

    ; <<>> DiG 9.18.4 <<>> _acme-challenge.foo.com TXT
    ;; global options: +cmd
    ;; Got answer:
    ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 43958
    ;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0

    ;; QUESTION SECTION:
    ;_acme-challenge.foo.com.	IN	TXT

    ;; ANSWER SECTION:
    _acme-challenge.foo.com.	489 IN	TXT	"123"

    ;; Query time: 10 msec
    ;; SERVER: 223.5.5.5#53(223.5.5.5) (UDP)
    ;; WHEN: Sat Jul 02 11:43:35 CST 2022
    ;; MSG SIZE  rcvd: 64


### 删除域名解析记录

```bash
CERTBOT_DOMAIN=foo.com CERTBOT_VALIDATION=123 python3 app.py --cleanup
```

## 手动续签

```bash
certbot certonly -d foo.com -d *.foo.com \
  --manual --preferred-challenges dns \
  --server https://acme-v02.api.letsencrypt.org/directory
```

```bash
certbot renew \
  --dry-run \
  --manual \
  --preferred-challenges=dns \
  --manual-auth-hook '/data/letsencrypt-dns-tool/app.py --auth' \
  --manual-cleanup-hook '/data/letsencrypt-dns-tool/app.py --cleanup'
```

`--dry-run` 参数用于反复续签测试，而不是真正续签

```bash
certbot certificates -d foo.com -d *.foo.com
```

## 自动续签

### 新增系统服务文件

```bash
cat << EOF > /etc/systemd/system/letsencrypt.service
[Unit]
Description=Let's Encrypt renewal

[Service]
Type=oneshot
ExecStart=/usr/local/bin/certbot renew --manual --preferred-challenges=dns --manual-auth-hook '/data/letsencrypt-dns-tool/app.py --auth' --manual-cleanup-hook '/data/letsencrypt-dns-tool/app.py --cleanup'
ExecStartPost=/bin/systemctl reload nginx.service  

[Install]
WantedBy=multi-user.target
EOF

cat << EOF > /etc/systemd/system/letsencrypt.timer
[Unit]
Description=Monthly renewal of Let's Encrypt's certificates

[Timer]
OnCalendar=daily  
Persistent=true

[Install]
WantedBy=timers.target
EOF
```

### 启动定时器

```bash
systemctl start letsencrypt.timer
```


### 设置开机启动

```bash
systemctl enable letsencrypt.service
systemctl enable letsencrypt.timer
```

### 查看定时器列表

```bash
systemctl list-timers letsencrypt.timer
```
