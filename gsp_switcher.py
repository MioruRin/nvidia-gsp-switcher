import subprocess
import sys
import ctypes
import os
import winreg
import tkinter as tk
from tkinter import ttk, messagebox

# ---------- 渚濊禆鑷姩瀹夎 ----------
def install_package(package):
    """浣跨敤 pip 闈欓粯瀹夎渚濊禆鍖?""
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
    """妫€鏌ュ苟瀹夎蹇呰鐨勪緷璧栧簱锛岃繑鍥炴槸鍚︽垚鍔熷鍏?""
    try:
        import ttkbootstrap
        return True
    except ImportError:
        print("姝ｅ湪鑷姩瀹夎鐣岄潰缇庡寲缁勪欢 ttkbootstrap锛岃绋嶅€?..")
        if install_package("ttkbootstrap"):
            print("瀹夎鎴愬姛锛岀户缁惎鍔ㄧ▼搴忋€?)
            return True
        else:
            print("鑷姩瀹夎澶辫触锛屽皢浣跨敤鍩虹鐣岄潰鏍峰紡銆?)
            return False

# 鎻愬墠妫€娴嬩緷璧栵紙姝ゆ椂杩樻湭鍒涘缓绐楀彛锛?
HAS_TTKB = ensure_dependencies()
if HAS_TTKB:
    import ttkbootstrap as ttkb
    from ttkbootstrap.constants import *
    from ttkbootstrap import Style
    from ttkbootstrap.dialogs import Messagebox

# ---------- 鏉冮檺鎻愬崌 ----------
def is_admin():
    """妫€鏌ュ綋鍓嶈繘绋嬫槸鍚﹀叿鏈夌鐞嗗憳鏉冮檺"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    """灏濊瘯浠ョ鐞嗗憳鏉冮檺閲嶅惎鑴氭湰锛岃嫢澶辫触鍒欏脊鍑烘彁绀?""
    # 鏋勫缓瀹屾暣鍛戒护琛屽弬鏁帮紙闄勫姞 --admin 鏍囪锛岄伩鍏嶆柊杩涚▼鍐嶆瑙﹀彂鎻愭潈锛?
    args_list = [f'"{arg}"' for arg in sys.argv]
    args_list.append("--admin")
    args = " ".join(args_list)
    ret = ctypes.windll.shell32.ShellExecuteW(
        None,           # 鐖剁獥鍙?
        "runas",        # 鎿嶄綔锛氫互绠＄悊鍛樿韩浠借繍琛?
        sys.executable, # 鍙墽琛屾枃浠惰矾寰?
        args,           # 鍛戒护琛屽弬鏁?
        None,           # 宸ヤ綔鐩綍
        1               # 绐楀彛鏄剧ず妯″紡锛氭甯告樉绀?
    )
    # ShellExecuteW 杩斿洖鍊?鈮?32 琛ㄧず璋冪敤澶辫触
    if ret <= 32:
        # 姝ゆ椂杩樻病鏈?GUI锛岄渶瑕佷复鏃跺垱寤轰竴涓殣钘忕獥鍙ｆ潵寮瑰嚭閿欒鎻愮ず
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showerror(
            "鏉冮檺涓嶈冻",
            "闇€瑕佺鐞嗗憳鏉冮檺鎵嶈兘淇敼娉ㄥ唽琛ㄤ腑鐨?GSP 璁剧疆銆俓n\n"
            "璇峰彸閿偣鍑绘湰绋嬪簭锛岄€夋嫨鈥滀互绠＄悊鍛樿韩浠借繍琛屸€濓紝"
            "鎴栧悓鎰忓嵆灏嗗脊鍑虹殑鐢ㄦ埛甯愭埛鎺у埗锛圲AC锛夌獥鍙ｃ€?
        )
        temp_root.destroy()
    # 鏃犺鎴愬姛涓庡惁锛屽綋鍓嶈繘绋嬮兘蹇呴』閫€鍑猴紙鎴愬姛鐨勫満鍚堟柊杩涚▼浼氬惎鍔級
    sys.exit()

# ---------- 娉ㄥ唽琛ㄦ搷浣?----------
BASE_KEY = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"

def get_nvidia_devices():
    """鎵弿娉ㄥ唽琛紝鑾峰彇鎵€鏈?NVIDIA 鏄惧崱鍙婂叾 GSP 鐘舵€?""
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
        print(f"娉ㄥ唽琛ㄨ闂嚭閿? {e}")
    return devices

def set_gsp(subkey, enable):
    """鍚敤鎴栫鐢ㄦ寚瀹氭樉鍗″瓙閿殑 GSP 鍔熻兘"""
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
        print(f"璁剧疆 GSP 澶辫触 ({subkey}): {e}")
        return False

# ---------- GUI 鐣岄潰 ----------
class GSPGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NVIDIA GSP 寮€鍏?)
        self.root.geometry("560x420")
        self.root.resizable(True, True)
        self.root.minsize(500, 380)

        if HAS_TTKB:
            self.style = Style(theme="darkly")
            self.ttk = ttkb
            # 寰皟鏆楄壊涓婚 Treeview 鏍峰紡
            self.style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
            self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        else:
            self.style = ttk.Style()
            self.ttk = ttk

        self.create_widgets()
        self.refresh_status()

    def _btn(self, parent, text, command, bootstyle=None):
        """鍒涘缓鎸夐挳锛堝吋瀹?ttkbootstrap / 鏍囧噯 ttk锛?""
        kwargs = {"text": text, "command": command}
        if HAS_TTKB and bootstyle:
            kwargs["bootstyle"] = bootstyle
        return self.ttk.Button(parent, **kwargs)

    def create_widgets(self):
        # 鈹€鈹€ 椤堕儴鏍囬鏍?鈹€鈹€
        header = self.ttk.Frame(self.root)
        header.pack(fill="x", padx=20, pady=(15, 5))

        self.ttk.Label(
            header,
            text="NVIDIA GSP 鍔熻兘鎺у埗",
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w")

        # 鈹€鈹€ 鏄惧崱鍒楄〃 鈹€鈹€
        list_frame = self.ttk.LabelFrame(self.root, text=" 妫€娴嬪埌鐨?NVIDIA 鏄惧崱 ")
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
        self.tree.heading("device", text="鏄惧崱鍨嬪彿")
        self.tree.heading("status", text="GSP 鐘舵€?)
        self.tree.column("device", width=360, anchor="w")
        self.tree.column("status", width=100, anchor="center")

        scrollbar = self.ttk.Scrollbar(inner_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鈹€鈹€ 鎸夐挳鍖?鈹€鈹€
        btn_frame = self.ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=20, pady=(0, 5))

        self.enable_btn = self._btn(btn_frame, " 鍚敤 GSP", self.enable_all, "success")
        self.enable_btn.pack(side="left", padx=(0, 6))

        self.disable_btn = self._btn(btn_frame, " 绂佺敤 GSP", self.disable_all, "danger")
        self.disable_btn.pack(side="left", padx=6)

        self.refresh_btn = self._btn(btn_frame, " 鍒锋柊", self.refresh_status, "secondary")
        self.refresh_btn.pack(side="right", padx=(6, 0))

        # 鈹€鈹€ 鐘舵€佹彁绀?鈹€鈹€
        self.status_text = tk.StringVar(value="灏辩华")
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
            text="淇敼 GSP 鍚庨渶閲嶅惎鐢熸晥",
            font=("Segoe UI", 8),
            foreground="#888" if HAS_TTKB else "gray"
        ).pack(side="right")

    def refresh_status(self):
        """鍒锋柊鍒楄〃涓墍鏈夋樉鍗＄殑 GSP 鐘舵€?""
        for item in self.tree.get_children():
            self.tree.delete(item)
        devices = get_nvidia_devices()
        if not devices:
            self.tree.insert("", "end", values=("[鏈壘鍒?NVIDIA 鏄惧崱]", ""))
            self.status_text.set("鏈娴嬪埌璁惧")
            return

        for dev in devices:
            tag = "on" if dev["enabled"] else "off"
            status_text = "鈼?GSP 宸插惎鐢? if dev["enabled"] else "鈼?GSP 宸茬鐢?
            self.tree.insert("", "end", values=(dev["desc"], status_text), tags=(tag,))

        # 鐘舵€佽鏌撹壊
        if HAS_TTKB:
            self.tree.tag_configure("on", foreground="#00bc8c")
            self.tree.tag_configure("off", foreground="#e74c3c")
        else:
            self.tree.tag_configure("on", foreground="green")
            self.tree.tag_configure("off", foreground="red")

        self.status_text.set(f"妫€娴嬪埌 {len(devices)} 涓澶?)

    def enable_all(self):
        self._set_all_gsp(True)

    def disable_all(self):
        self._set_all_gsp(False)

    def _set_all_gsp(self, enable):
        devices = get_nvidia_devices()
        if not devices:
            self.show_message("鏈娴嬪埌浠讳綍 NVIDIA 鏄惧崱銆?, "璀﹀憡")
            return
        success_count = 0
        for dev in devices:
            if set_gsp(dev["key"], enable):
                success_count += 1
        action = "鍚敤" if enable else "绂佺敤"
        if success_count:
            self.status_text.set(f"宸?{action} {success_count} 涓澶?)
            self.show_message(
                f"宸叉垚鍔?{action} {success_count} 涓澶囩殑 GSP 鍔熻兘銆俓n\n"
                "璇峰姟蹇呴噸鍚绠楁満浣夸慨鏀圭敓鏁堛€?,
                "鎿嶄綔鎴愬姛"
            )
        else:
            self.status_text.set("鎿嶄綔澶辫触")
            self.show_message("鎿嶄綔澶辫触锛岃妫€鏌ユ槸鍚︽嫢鏈夌鐞嗗憳鏉冮檺銆?, "閿欒")
        self.refresh_status()

    def show_message(self, message, title="鎻愮ず"):
        """鏄剧ず娑堟伅瀵硅瘽妗嗭紙鍏煎涓ょ鏍峰紡锛?""
        if HAS_TTKB:
            Messagebox.show_info(title=title, message=message)
        else:
            messagebox.showinfo(title, message)

# ---------- 绋嬪簭鍏ュ彛 ----------
if __name__ == "__main__":
    # 绗竴姝ワ細纭繚浠ョ鐞嗗憳鏉冮檺杩愯
    # 鑻ョ敱 VBS/bat 鍚姩鍣ㄤ紶鍏?--admin 鍒欎俊浠诲閮ㄥ凡鎻愭潈锛岃烦杩囦簩娆?UAC
    already_elevated = "--admin" in sys.argv
    if not is_admin() and not already_elevated:
        run_as_admin()

    # 绗簩姝ワ細鍒涘缓涓荤獥鍙ｏ紙宸茬粡鎻愭潈鎴愬姛锛?
    if HAS_TTKB:
        root = ttkb.Window(themename="darkly")
    else:
        root = tk.Tk()

    app = GSPGUI(root)
    root.mainloop()