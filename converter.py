"""Word 转 PDF 核心模块：基于 LibreOffice 无头模式。

只依赖标准库，跨平台（Windows / macOS / Linux）。
转换保真度高，且无需安装 Microsoft Office。
"""

import os
import shutil
import subprocess
import tempfile


def find_soffice():
    """自动查找 LibreOffice 可执行文件，找不到返回 None。"""
    # 1. 先查 PATH
    name = (
        shutil.which("soffice")
        or shutil.which("libreoffice")
        or shutil.which("soffice.bin")
    )
    if name:
        return name

    # 2. 常见安装路径
    candidates = [
        r"D:\LibreOffice\program\soffice.exe",
        
    ]
    for c in candidates:
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
