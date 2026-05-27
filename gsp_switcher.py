import subprocess
import sys
import ctypes
import os
import winreg
import tkinter as tk
from tkinter import ttk, messagebox

# ---------- 依赖自动安装 ----------
def install_package(package):
    """使用 pip 静默安装依赖包"""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def ensure_dependencies():
    """检查并安装必要的依赖库，返回是否成功导入"""
    try:
        import ttkbootstrap
        return True
    except ImportError:
        print("正在自动安装界面美化组件 ttkbootstrap，请稍候...")
        if install_package("ttkbootstrap"):
            print("安装成功，继续启动程序。")
            return True
        else:
            print("自动安装失败，将使用基础界面样式。")
            return False

# 提前检测依赖（此时还未创建窗口）
HAS_TTKB = ensure_dependencies()
if HAS_TTKB:
    import ttkbootstrap as ttkb
    from ttkbootstrap.constants import *
    from ttkbootstrap import Style
    from ttkbootstrap.dialogs import Messagebox

# ---------- 权限提升 ----------
def is_admin():
    """检查当前进程是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    """尝试以管理员权限重启脚本，若失败则弹出提示"""
    # 构建完整命令行参数（附加 --admin 标记，避免新进程再次触发提权）
    args_list = [f'"{arg}"' for arg in sys.argv]
    args_list.append("--admin")
    args = " ".join(args_list)
    ret = ctypes.windll.shell32.ShellExecuteW(
        None,           # 父窗口
        "runas",        # 操作：以管理员身份运行
        sys.executable, # 可执行文件路径
        args,           # 命令行参数
        None,           # 工作目录
        1               # 窗口显示模式：正常显示
    )
    # ShellExecuteW 返回值 ≤ 32 表示调用失败
    if ret <= 32:
        # 此时还没有 GUI，需要临时创建一个隐藏窗口来弹出错误提示
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showerror(
            "权限不足",
            "需要管理员权限才能修改注册表中的 GSP 设置。\n\n"
            "请右键点击本程序，选择“以管理员身份运行”，"
            "或同意即将弹出的用户帐户控制（UAC）窗口。"
        )
        temp_root.destroy()
    # 无论成功与否，当前进程都必须退出（成功的场合新进程会启动）
    sys.exit()

# ---------- 注册表操作 ----------
BASE_KEY = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"

def get_nvidia_devices():
    """扫描注册表，获取所有 NVIDIA 显卡及其 GSP 状态"""
    devices = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, BASE_KEY) as key:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        try:
                            desc, _ = winreg.QueryValueEx(subkey, "DriverDesc")
                            if "nvidia" in desc.lower():
                                try:
                                    val, _ = winreg.QueryValueEx(subkey, "EnableGpuFirmware")
                                    enabled = (val == 1)
                                except FileNotFoundError:
                                    enabled = False
                                devices.append({
                                    "key": subkey_name,
                                    "desc": desc,
                                    "enabled": enabled
                                })
                        except FileNotFoundError:
                            pass
                    i += 1
                except OSError:
                    break
    except Exception as e:
        print(f"注册表访问出错: {e}")
    return devices

def set_gsp(subkey, enable):
    """启用或禁用指定显卡子键的 GSP 功能"""
    try:
        full_path = f"{BASE_KEY}\\{subkey}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, full_path, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                winreg.SetValueEx(key, "EnableGpuFirmware", 0, winreg.REG_DWORD, 1)
            else:
                try:
                    winreg.DeleteValue(key, "EnableGpuFirmware")
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"设置 GSP 失败 ({subkey}): {e}")
        return False

# ---------- GUI 界面 ----------
class GSPGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NVIDIA GSP 开关")
        self.root.geometry("560x420")
        self.root.resizable(True, True)
        self.root.minsize(500, 380)

        if HAS_TTKB:
            self.style = Style(theme="darkly")
            self.ttk = ttkb
            # 微调暗色主题 Treeview 样式
            self.style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
            self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        else:
            self.style = ttk.Style()
            self.ttk = ttk

        self.create_widgets()
        self.refresh_status()

    def _btn(self, parent, text, command, bootstyle=None):
        """创建按钮（兼容 ttkbootstrap / 标准 ttk）"""
        kwargs = {"text": text, "command": command}
        if HAS_TTKB and bootstyle:
            kwargs["bootstyle"] = bootstyle
        return self.ttk.Button(parent, **kwargs)

    def create_widgets(self):
        # ── 顶部标题栏 ──
        header = self.ttk.Frame(self.root)
        header.pack(fill="x", padx=20, pady=(15, 5))

        self.ttk.Label(
            header,
            text="NVIDIA GSP 功能控制",
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w")

        # ── 显卡列表 ──
        list_frame = self.ttk.LabelFrame(self.root, text=" 检测到的 NVIDIA 显卡 ")
        list_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        inner_frame = self.ttk.Frame(list_frame)
        inner_frame.pack(fill="both", expand=True, padx=8, pady=8)

        columns = ("device", "status")
        self.tree = self.ttk.Treeview(
            inner_frame,
            columns=columns,
            show="headings",
            height=6
        )
        self.tree.heading("device", text="显卡型号")
        self.tree.heading("status", text="GSP 状态")
        self.tree.column("device", width=360, anchor="w")
        self.tree.column("status", width=100, anchor="center")

        scrollbar = self.ttk.Scrollbar(inner_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ── 按钮区 ──
        btn_frame = self.ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=20, pady=(0, 5))

        self.enable_btn = self._btn(btn_frame, " 启用 GSP", self.enable_all, "success")
        self.enable_btn.pack(side="left", padx=(0, 6))

        self.disable_btn = self._btn(btn_frame, " 禁用 GSP", self.disable_all, "danger")
        self.disable_btn.pack(side="left", padx=6)

        self.refresh_btn = self._btn(btn_frame, " 刷新", self.refresh_status, "secondary")
        self.refresh_btn.pack(side="right", padx=(6, 0))

        # ── 状态提示 ──
        self.status_text = tk.StringVar(value="就绪")
        status_bar = self.ttk.Frame(self.root)
        status_bar.pack(fill="x", side="bottom", padx=20, pady=(0, 8))

        self.info_label = self.ttk.Label(
            status_bar,
            textvariable=self.status_text,
            font=("Segoe UI", 9)
        )
        self.info_label.pack(side="left")

        self.ttk.Label(
            status_bar,
            text="修改 GSP 后需重启生效",
            font=("Segoe UI", 8),
            foreground="#888" if HAS_TTKB else "gray"
        ).pack(side="right")

    def refresh_status(self):
        """刷新列表中所有显卡的 GSP 状态"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        devices = get_nvidia_devices()
        if not devices:
            self.tree.insert("", "end", values=("[未找到 NVIDIA 显卡]", ""))
            self.status_text.set("未检测到设备")
            return

        for dev in devices:
            tag = "on" if dev["enabled"] else "off"
            status_text = "● GSP 已启用" if dev["enabled"] else "○ GSP 已禁用"
            self.tree.insert("", "end", values=(dev["desc"], status_text), tags=(tag,))

        # 状态行染色
        if HAS_TTKB:
            self.tree.tag_configure("on", foreground="#00bc8c")
            self.tree.tag_configure("off", foreground="#e74c3c")
        else:
            self.tree.tag_configure("on", foreground="green")
            self.tree.tag_configure("off", foreground="red")

        self.status_text.set(f"检测到 {len(devices)} 个设备")

    def enable_all(self):
        self._set_all_gsp(True)

    def disable_all(self):
        self._set_all_gsp(False)

    def _set_all_gsp(self, enable):
        devices = get_nvidia_devices()
        if not devices:
            self.show_message("未检测到任何 NVIDIA 显卡。", "警告")
            return
        success_count = 0
        for dev in devices:
            if set_gsp(dev["key"], enable):
                success_count += 1
        action = "启用" if enable else "禁用"
        if success_count:
            self.status_text.set(f"已 {action} {success_count} 个设备")
            self.show_message(
                f"已成功 {action} {success_count} 个设备的 GSP 功能。\n\n"
                "请务必重启计算机使修改生效。",
                "操作成功"
            )
        else:
            self.status_text.set("操作失败")
            self.show_message("操作失败，请检查是否拥有管理员权限。", "错误")
        self.refresh_status()

    def show_message(self, message, title="提示"):
        """显示消息对话框（兼容两种样式）"""
        if HAS_TTKB:
            Messagebox.show_info(title=title, message=message)
        else:
            messagebox.showinfo(title, message)

# ---------- 程序入口 ----------
if __name__ == "__main__":
    # 第一步：确保以管理员权限运行
    # 若由 VBS/bat 启动器传入 --admin 则信任外部已提权，跳过二次 UAC
    already_elevated = "--admin" in sys.argv
    if not is_admin() and not already_elevated:
        run_as_admin()

    # 第二步：创建主窗口（已经提权成功）
    if HAS_TTKB:
        root = ttkb.Window(themename="darkly")
    else:
        root = tk.Tk()

    app = GSPGUI(root)
    root.mainloop()