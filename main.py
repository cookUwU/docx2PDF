#!/usr/bin/env python3
"""Word 转 PDF 工具 —— GUI 界面（tkinter）+ LibreOffice 无头引擎。

功能：
  - 添加单个 / 多个 Word 文件，或整个文件夹（递归）
  - 自定义输出目录
  - 批量转换，逐文件显示状态与输出路径
  - 进度条 + 日志，转换在后台线程进行，界面不卡顿
  - 一键打开输出文件夹
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import converter


class Word2PDFApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Word 转 PDF 工具")
        self.root.geometry("780x620")
        self.root.minsize(680, 540)

        self.items = []  # 每个元素: {"path","status","out","iid"}
        self.out_dir = tk.StringVar(value=os.path.expanduser("~/Desktop"))
        self.soffice_path = tk.StringVar(value="")
        self.running = False

        self._build_ui()
        self._detect_engine()

    # ---------------- UI 构建 ----------------
    def _build_ui(self):
        # 工具栏
        f_tool = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        f_tool.pack(fill=tk.X)
        ttk.Button(f_tool, text="添加文件", command=self.add_files).pack(side=tk.LEFT, padx=4)
        ttk.Button(f_tool, text="添加文件夹", command=self.add_folder).pack(side=tk.LEFT, padx=4)
        ttk.Button(f_tool, text="移除选中", command=self.remove_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(f_tool, text="清空列表", command=self.clear_list).pack(side=tk.LEFT, padx=4)

        # 输出目录
        f_out = ttk.LabelFrame(self.root, text="输出目录", padding=(10, 6))
        f_out.pack(fill=tk.X, padx=10, pady=6)
        ttk.Entry(f_out, textvariable=self.out_dir).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(f_out, text="浏览", command=self.browse_out).pack(side=tk.LEFT)

        # 引擎状态
        self.engine_var = tk.StringVar(value="检测中…")
        f_eng = ttk.Frame(self.root, padding=(10, 0))
        f_eng.pack(fill=tk.X)
        ttk.Label(f_eng, text="转换引擎：").pack(side=tk.LEFT)
        ttk.Label(f_eng, textvariable=self.engine_var, foreground="#1d9e75").pack(side=tk.LEFT)
        ttk.Button(f_eng, text="手动选择…", command=self.browse_engine).pack(side=tk.LEFT, padx=8)

        # 文件列表
        f_list = ttk.LabelFrame(self.root, text="待转换文件", padding=(10, 6))
        f_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        self.tree = ttk.Treeview(
            f_list, columns=("file", "status", "out"), show="headings", height=12
        )
        self.tree.heading("file", text="文件名")
        self.tree.heading("status", text="状态")
        self.tree.heading("out", text="输出路径")
        self.tree.column("file", width=260)
        self.tree.column("status", width=90)
        self.tree.column("out", width=320)
        vsb = ttk.Scrollbar(f_list, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # 进度条
        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 6))

        # 日志
        f_log = ttk.LabelFrame(self.root, text="日志", padding=(10, 6))
        f_log.pack(fill=tk.BOTH, padx=10, pady=(0, 6))
        self.log = scrolledtext.ScrolledText(f_log, height=6, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH)

        # 底部按钮
        f_bot = ttk.Frame(self.root, padding=(10, 6, 10, 10))
        f_bot.pack(fill=tk.X)
        self.btn_run = ttk.Button(f_bot, text="开始转换", command=self.start)
        self.btn_run.pack(side=tk.LEFT, padx=4)
        ttk.Button(f_bot, text="打开输出文件夹", command=self.open_out).pack(side=tk.LEFT, padx=4)

    def _detect_engine(self):
        path = converter.find_soffice()
        if path:
            self.soffice_path.set(path)
            self.engine_var.set("LibreOffice ✓  " + os.path.dirname(os.path.dirname(path)))
        else:
            self.engine_var.set("未找到 LibreOffice（请安装）")
            messagebox.showwarning(
                "缺少转换引擎",
                "未检测到 LibreOffice。\n请到 https://www.libreoffice.org/ 下载安装，"
                "否则无法转换。",
            )

    # ---------------- 文件操作 ----------------
    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="选择 Word 文档",
            filetypes=[("Word 文档", "*.docx *.doc"), ("所有文件", "*.*")],
        )
        self._add_paths(list(paths))

    def add_folder(self):
        d = filedialog.askdirectory(title="选择包含 Word 文档的文件夹")
        if not d:
            return
        found = []
        for root, _, files in os.walk(d):
            for fn in files:
                if fn.lower().endswith((".docx", ".doc")):
                    found.append(os.path.join(root, fn))
        self._add_paths(found)

    def _add_paths(self, paths):
        existing = {it["path"] for it in self.items}
        added = 0
        for p in paths:
            if p not in existing:
                iid = self.tree.insert("", tk.END, values=(os.path.basename(p), "待转换", ""))
                self.items.append({"path": p, "status": "待转换", "out": "", "iid": iid})
                existing.add(p)
                added += 1
        if added:
            self._log(f"已添加 {added} 个文件")

    def remove_selected(self):
        for iid in self.tree.selection():
            self.items = [it for it in self.items if it.get("iid") != iid]
            self.tree.delete(iid)

    def clear_list(self):
        self.items.clear()
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    def browse_out(self):
        d = filedialog.askdirectory(title="选择输出目录")
        if d:
            self.out_dir.set(d)

    def open_out(self):
        d = self.out_dir.get()
        if os.path.isdir(d):
            os.startfile(d)  # Windows
        else:
            messagebox.showinfo("提示", "输出目录不存在")

    def browse_engine(self):
        p = filedialog.askopenfilename(
            title="选择 LibreOffice 的 soffice.exe",
            filetypes=[("LibreOffice", "soffice.exe"), ("所有文件", "*.*")],
        )
        if p and os.path.isfile(p):
            self.soffice_path.set(p)
            self.engine_var.set("已手动指定：" + p)
            self._log(f"已指定转换引擎：{p}")

    # ---------------- 转换流程 ----------------
    def start(self):
        if self.running:
            return
        if not self.items:
            messagebox.showinfo("提示", "请先添加文件")
            return
        if not self.soffice_path.get():
            messagebox.showerror("错误", "未检测到 LibreOffice，无法转换")
            return

        self.running = True
        self.btn_run.configure(state=tk.DISABLED)
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.items)
        threading.Thread(target=self._convert_all, daemon=True).start()

    def _convert_all(self):
        out_dir = self.out_dir.get()
        soffice = self.soffice_path.get()
        for idx, item in enumerate(self.items, start=1):
            if item["status"] == "已完成":
                self.root.after(0, self.progress.configure, {"value": idx})
                continue
            self._set_status(item, "转换中…")
            try:
                pdf = converter.convert_to_pdf(item["path"], out_dir, soffice)
                item["out"] = pdf
                self._set_status(item, "已完成")
                self._log(f"✓ {os.path.basename(item['path'])}  →  {pdf}")
            except Exception as e:  # noqa: BLE001
                item["out"] = ""
                self._set_status(item, "失败")
                self._log(f"✗ {os.path.basename(item['path'])}  :  {e}")
            self.root.after(0, self.progress.configure, {"value": idx})
        self.root.after(0, self._finish)

    def _finish(self):
        self.running = False
        self.btn_run.configure(state=tk.NORMAL)
        self._log("转换完成。")
        messagebox.showinfo("完成", "全部文件处理完毕。")

    # ---------------- UI 更新辅助 ----------------
    def _set_status(self, item, status):
        item["status"] = status
        iid = item["iid"]
        out = item.get("out", "")
        self.root.after(0, self._update_row, iid, status, out)

    def _update_row(self, iid, status, out):
        self.tree.set(iid, "status", status)
        self.tree.set(iid, "out", out)

    def _log(self, msg):
        self.root.after(0, self._append_log, msg)

    def _append_log(self, msg):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.configure(state=tk.DISABLED)
        self.log.see(tk.END)


def main():
    root = tk.Tk()
    # 高 DPI 适配（Windows）
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:  # noqa: BLE001
        pass
    Word2PDFApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
