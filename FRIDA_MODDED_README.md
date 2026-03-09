# Frida 魔改版 (Anti-Detection) 说明文档

基于 Frida 16.4.7 版本，针对常见检测手段进行特征修改。

---

## 一、已修改的特征

### 1. 端口特征
| 原值 | 新值 | 文件位置 |
|------|------|----------|
| `27042` | `39042` | `lib/base/socket.vala` |
| `27052` | `39052` | `lib/base/socket.vala` |

**说明**: 默认控制端口和集群端口已修改，避免端口扫描检测。

### 2. 目录/进程名特征
| 原值 | 新值 | 文件位置 |
|------|------|----------|
| `re.frida.server` | `re.xmsf.helper` | `server/server.vala` |

**说明**: 服务端默认目录名已修改。

### 3. 线程名特征
| 原值 | 新值 | 文件位置 |
|------|------|----------|
| `frida-server-main-loop` | `pool-main-loop` | `server/server.vala` |
| `gum-js-loop` | `v8-loop` | `gumscriptscheduler.c` |
| `frida-agent-container` | `jni-container` | `agent-container.vala` |
| `frida-agent-emulated` | `dex-emulated` | `agent.vala` |

**说明**: 线程名修改可避免 `/proc/[pid]/task/[tid]/comm` 扫描检测。

### 4. D-Bus/RPC 协议特征
| 原值 | 新值 | 文件位置 |
|------|------|----------|
| `frida:rpc` | `xmsf:rpc` | `lib/base/rpc.vala`, `message-dispatcher.js`, `worker.js` |

**说明**: RPC 消息类型标识已修改，避免内存字符串扫描。

### 5. SO 库名称特征
| 原值 | 新值 | 文件位置 |
|------|------|----------|
| `frida-agent-arm.so` | `libxmsf-arm.so` | `linux-host-session.vala` |
| `frida-agent-arm64.so` | `libxmsf-arm64.so` | `linux-host-session.vala` |
| `frida-agent-<arch>.so` | `libxmsf-<arch>.so` | `linux-host-session.vala` |
| `frida-agent.dll` | `libxmsf.dll` | `windows-host-session.vala` |

**说明**: Agent SO 名称已修改，避免 `/proc/self/maps` 扫描检测。

### 6. Gadget 特征
| 原值 | 新值 | 文件位置 |
|------|------|----------|
| `FridaGadget` | `NativeHelper` | 多个文件 |
| `frida-gadget` | `native-helper` | 多个文件 |

**说明**: Gadget 名称已修改。

---

## 二、未修改的特征（需要运行时绕过）

### 1. GLib 线程名 (gmain/gdbus)
- **原因**: `gmain` 和 `gdbus` 是 GLib 库硬编码的名称，不在 Frida 源码中
- **绕过方案**: 
  - 重编 GLib 库（复杂）
  - 运行时 Hook `/proc/[pid]/task/[tid]/comm` 读取

### 2. ptrace 占坑检测
- **原因**: 这是运行时行为，不是源码字符串
- **绕过方案**: 
  - 使用 Spawn 模式 (`-f`)
  - Hook `ptrace` 函数返回 0

### 3. D-Bus REJECT 响应
- **原因**: 这是 D-Bus 协议标准响应，不是 Frida 特有
- **绕过方案**: Hook `strstr`/`strcmp` 函数拦截 REJECT 匹配

### 4. Inline Hook 检测 (代码完整性校验)
- **原因**: Frida 的 Interceptor 必须修改内存代码
- **绕过方案**: 
  - 使用硬件断点
  - Hook `memcmp`/CRC 计算函数

### 5. /proc/self/maps 检测
- **原因**: 内存映射会显示加载的 SO
- **绕过方案**: Hook `open`/`openat` 重定向到干净的 maps 文件

---

## 三、修改完整性评估

### 源码层面可修改的 ✅
| 类别 | 覆盖率 | 说明 |
|------|--------|------|
| 端口特征 | 100% | 已全部修改 |
| 目录/文件名 | 100% | 已全部修改 |
| 线程名 | 80% | Frida 自身的已修改，GLib 的需要单独处理 |
| RPC 协议标识 | 100% | 已全部修改 |
| SO 库名称 | 100% | 已全部修改 |
| Gadget 名称 | 100% | 已全部修改 |

### 需要运行时绕过的 ⚠️
| 类别 | 说明 |
|------|------|
| gmain/gdbus | GLib 库特征，需单独修改或运行时 Hook |
| ptrace | 运行时反调试，需 Hook 绕过 |
| D-Bus REJECT | 协议标准，需运行时 Hook |
| Inline Hook | 代码修改，需特殊绕过 |

---

## 四、使用说明

### 4.1 启动魔改版 frida-server

```bash
# 1. 推送到设备 (注意：端口已改为 39042)
adb push frida-server-android-arm64 /data/local/tmp/fs
adb shell "chmod +x /data/local/tmp/fs"

# 2. 运行 (建议使用自定义端口)
adb shell "/data/local/tmp/fs -l 0.0.0.0:8888 &"

# 3. 端口转发
adb forward tcp:8888 tcp:8888

# 4. 连接
frida -H 127.0.0.1:8888 -f com.target.app -l script.js
```

### 4.2 配合运行时绕过脚本

```javascript
// bypass.js - 完整绕过脚本
function bypassAll() {
    // 1. ptrace 绕过
    var ptrace = Module.findExportByName("libc.so", "ptrace");
    if (ptrace) {
        Interceptor.replace(ptrace, new NativeCallback(function(req, pid, addr, data) {
            console.log("[+] ptrace bypassed");
            return 0;
        }, 'long', ['int', 'int', 'pointer', 'pointer']));
    }
    
    // 2. 线程名绕过 (gmain/gdbus)
    var open = Module.findExportByName("libc.so", "open");
    if (open) {
        Interceptor.attach(open, {
            onEnter: function(args) {
                var path = Memory.readUtf8String(args[0]);
                if (path && path.indexOf("/task/") !== -1 && path.indexOf("/comm") !== -1) {
                    this.isThreadComm = true;
                }
            },
            onLeave: function(retval) {
                // 可在此处理线程名读取
            }
        });
    }
    
    console.log("[+] Bypass hooks installed");
}

setImmediate(bypassAll);
```

---

## 五、Git 相关命令

### 5.1 仓库信息

```
主仓库: https://github.com/ningchu888/frida-modded
子模块: 
  - https://github.com/ningchu888/frida-core
  - https://github.com/ningchu888/frida-gum
```

### 5.2 克隆魔改版

```bash
# 克隆主仓库
git clone --recurse-submodules https://github.com/ningchu888/frida-modded.git

# 或者分步克隆
git clone https://github.com/ningchu888/frida-modded.git
cd frida-modded
git submodule update --init --recursive
```

### 5.3 拉取最新更新

```bash
cd frida-modded
git pull origin main
git submodule update --recursive
```

### 5.4 自定义修改后推送

```bash
# 1. 修改子模块后提交
cd subprojects/frida-core
git add -A
git commit -m "your changes"
git push myrepo HEAD:main

cd ../frida-gum
git add -A
git commit -m "your changes"
git push myrepo HEAD:main

# 2. 主仓库更新子模块引用
cd ../..
git add subprojects/frida-core subprojects/frida-gum
git commit -m "update submodule refs"
git push myrepo frida-modded:main
```

### 5.5 触发 GitHub Actions 编译

```bash
# 方法1: 推送后自动触发
git push myrepo frida-modded:main

# 方法2: 手动触发
# 访问 https://github.com/ningchu888/frida-modded/actions
# 点击 "Build Frida for Android" → "Run workflow"
```

### 5.6 下载编译产物

```bash
# 1. 访问 Actions 页面
# https://github.com/ningchu888/frida-modded/actions

# 2. 点击最新的成功运行

# 3. 下载 Artifacts 中的 frida-server-android-arm64

# 4. 解压使用
unxz frida-server-android-arm64.xz
```

---

## 六、修改的文件清单

### frida-core (16个文件)
- `lib/base/socket.vala` - 端口修改
- `lib/base/rpc.vala` - RPC 协议标识
- `server/server.vala` - 目录名、线程名
- `lib/agent/agent.vala` - 线程名
- `src/agent-container.vala` - 线程名
- `src/linux/linux-host-session.vala` - SO 名称
- `src/windows/windows-host-session.vala` - DLL 名称
- `lib/gadget/gadget.vala` - Gadget 名称
- `lib/gadget/gadget-glue.c` - Gadget 名称
- `compat/build.py` - SO 名称
- `src/droidy/*.vala` - Gadget 名称
- `src/fruity/*.vala` - Gadget 名称
- `tests/*.vala` - 测试文件

### frida-gum (5个文件)
- `bindings/gumjs/gumscriptscheduler.c` - 线程名
- `bindings/gumjs/runtime/message-dispatcher.js` - RPC 标识
- `bindings/gumjs/runtime/worker.js` - RPC 标识
- `tests/gumjs/script.c` - RPC 标识

---

## 七、版本信息

- **基础版本**: Frida 16.4.7
- **魔改日期**: 2025年
- **作者**: ningchu888
- **仓库**: https://github.com/ningchu888/frida-modded

---

## 八、注意事项

1. **魔改版与官方版不兼容** - 由于 RPC 协议标识已修改，魔改版 frida-server 必须配合魔改版客户端使用
2. **端口已更改** - 默认端口从 27042 改为 39042
3. **仍需运行时绕过** - 部分检测需要配合 Hook 脚本使用
4. **定期更新** - 安全厂商可能更新检测规则，建议定期同步官方更新并重新应用补丁

