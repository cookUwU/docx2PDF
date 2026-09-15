"""Word 转 PDF 核心模块：基于 LibreOffice 无头模式。

只依赖标准库，跨平台（Windows / macOS / Linux）。
转换保真度高，且无需安装 Microsoft Office。
"""

import os
import shutil
import subprocess
import sys
import tempfile


def _default_candidates():
    """按平台给出 LibreOffice 的常见安装路径（不含任何机器专属路径）。"""
    if sys.platform.startswith("win"):
        cands = []
        # 1) 标准的 Program Files 系列
        for var in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
            base = os.environ.get(var)
            if base:
                cands.append(
                    os.path.join(base, "LibreOffice", "program", "soffice.exe")
                )
        # 2) 当前用户目录下的安装
        local = os.environ.get("LOCALAPPDATA")
        if local:
            cands.append(
                os.path.join(
                    local, "Programs", "LibreOffice", "program", "soffice.exe"
                )
            )
        # 3) 逐个盘符根目录探测，覆盖装在非系统盘的情况（不写死具体盘符）
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            root = letter + ":\\"
            if os.path.isdir(root):
                cands.append(
                    os.path.join(root, "LibreOffice", "program", "soffice.exe")
                )
        return cands

    if sys.platform == "darwin":
        return ["/Applications/LibreOffice.app/Contents/MacOS/soffice"]

    return [
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
        "/usr/bin/libreoffice",
        "/opt/libreoffice/program/soffice",
        "/snap/bin/libreoffice",
    ]


def find_soffice():
    """自动查找 LibreOffice 可执行文件，找不到返回 None。

    查找顺序：环境变量 SOFFICE_PATH → 系统 PATH → 各平台常见安装路径。
    """
    # 0. 环境变量优先，方便装在自定义位置的用户
    env_path = os.environ.get("SOFFICE_PATH") or os.environ.get("LIBREOFFICE_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    # 1. 再查 PATH
    name = (
        shutil.which("soffice")
        or shutil.which("libreoffice")
        or shutil.which("soffice.bin")
    )
    if name:
        return name

    # 2. 最后查常见安装路径
    for c in _default_candidates():
        if c and os.path.exists(c):
            return c
    return None


def convert_to_pdf(input_path, out_dir, soffice_path=None):
    """把单个 Word 文档转为 PDF，返回生成的 pdf 路径。

    :param input_path: .doc / .docx 文件路径
    :param out_dir: 输出目录（不存在则创建）
    :param soffice_path: 指定 soffice 路径；为空时自动查找
    """
    soffice = soffice_path or find_soffice()
    if not soffice:
        raise RuntimeError(
            "未找到 LibreOffice，请先安装：https://www.libreoffice.org/"
        )
    if not os.path.isfile(input_path):
        raise RuntimeError(f"文件不存在：{input_path}")

    os.makedirs(out_dir, exist_ok=True)

    # 每次用独立临时用户配置，避免多实例之间的 profile 锁冲突
    profile = os.path.join(tempfile.gettempdir(), f"lo_profile_{os.getpid()}")
    profile_url = "file:///" + profile.replace(os.sep, "/")

    cmd = [
        soffice,
        "--headless",
        "--norestore",
        "--nofirststartwizard",
        f"-env:UserInstallation={profile_url}",
        "--convert-to",
        "pdf",
        "--outdir",
        out_dir,
        input_path,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "转换失败").strip())

    base = os.path.splitext(os.path.basename(input_path))[0]
    pdf = os.path.join(out_dir, base + ".pdf")
    if not os.path.exists(pdf):
        raise RuntimeError(
            "未生成 PDF 文件：" + (proc.stdout or proc.stderr or "未知错误")
        )
    return pdf


if __name__ == "__main__":
    # 命令行单文件快速测试：python converter.py input.docx
    import sys

    if len(sys.argv) < 2:
        print("用法：python converter.py <word文件> [输出目录]")
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(src))
    print("soffice:", find_soffice())
    out = convert_to_pdf(src, dst)
    print("已生成：", out)
