# NVIDIA GSP Switcher

一键开关 NVIDIA GPU 的 GSP（GPU System Processor）固件模式，带图形界面的 Windows 小工具。

## 什么是 GSP？

GSP 是 NVIDIA RTX 30 系及更新显卡上的**独立微控制器**，负责接管原本由 CPU 处理的 GPU 调度任务：
- **启用 GSP**：释放 CPU 开销，适合多 GPU 或虚拟化场景
- **禁用 GSP**：某些游戏/超频场景下能减少延迟抖动，也是社区调优的常见手段

## 截图

```
┌───────────────────────────────────────┐
│  NVIDIA GSP 功能控制                   │
├───────────────────────────────────────┤
│  ┌─ 检测到的 NVIDIA 显卡 ────────────┐ │
│  │  显卡型号          GSP 状态       │ │
│  │  ● RTX 5090 D    ● GSP 已启用    │ │
│  └──────────────────────────────────┘ │
│  [ 启用 GSP ] [ 禁用 GSP ]    [ 刷新 ]│
│  检测到 1 个设备     重启后生效       │
└───────────────────────────────────────┘
```

## 功能

- 自动扫描系统所有 NVIDIA 显卡
- 一键启用/禁用 GSP（修改注册表 `EnableGpuFirmware`）
- ttkbootstrap 暗色现代化界面（回退至标准 tkinter）
- 自动依赖安装 + UAC 管理员提权
- 修改后提示重启

## 使用方法

**方式一：VBS 启动器（推荐）**

双击 `NVIDIA GSP 开关.vbs` → 同意 UAC → 主界面出现

**方式二：命令行**

```powershell
python gsp_switcher.py --admin
```

**方式三：右键运行**

右键 `gsp_switcher.py` → 以管理员身份运行

## 依赖

- Python 3.8+
- ttkbootstrap（脚本会自动安装，也可手动：`pip install ttkbootstrap`）

## 工作原理

```
双击 .vbs
  └─ ShellExecute("runas") → UAC 弹窗
      └─ python gsp_switcher.py --admin
          └─ 扫描 HKLM\...\Class\{4d36e968-...} 注册表
              └─ 修改 EnableGpuFirmware 键值
                  └─ 提示重启
```

注册表路径：`HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\00XX`

## 兼容性

| 系统 | 状态 |
|------|------|
| Windows 11 | 测试通过 |
| Windows 10 | 理论支持 |
| RTX 30/40/50 系列 | 支持 |

## 注意事项

- 需要管理员权限
- **修改后必须重启生效**
- 仅在 NVIDIA 显卡上有效

## License

MIT
