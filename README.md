# Word 转 PDF 工具

一个把 Word 文档（`.doc` / `.docx`）批量转换为 PDF 的小工具。基于 **LibreOffice 无头模式**，排版保真度高，免费、跨平台、无需安装 Microsoft Office。

## 功能

- 添加单个 / 多个 Word 文件，或整个文件夹（递归扫描）
- 自定义输出目录
- 批量转换，逐文件显示「待转换 / 转换中 / 已完成 / 失败」状态与输出路径
- 进度条 + 日志，后台线程转换，界面不卡顿
- 一键打开输出文件夹

## 使用步骤

### 1. 安装 LibreOffice（必须）

从 https://www.libreoffice.org/ 下载并安装。程序会按下面的顺序自动查找：

1. 环境变量 `SOFFICE_PATH`（或 `LIBREOFFICE_PATH`）
2. 系统 `PATH` 里的 `soffice` / `libreoffice`
3. 各平台常见安装路径：
   - **Windows**：`C:\Program Files\LibreOffice\...`、`%LOCALAPPDATA%\Programs\LibreOffice\...`，以及各盘符根目录下的 `LibreOffice\program\soffice.exe`（装在非系统盘也能自动找到）
   - **macOS**：`/Applications/LibreOffice.app/Contents/MacOS/soffice`
   - **Linux**：`/usr/bin/soffice`、`/snap/bin/libreoffice` 等

如果都找不到（例如装在非标准路径），可以二选一：

- 设置环境变量 `SOFFICE_PATH` 指向 `soffice.exe`：

  ```bat
  set SOFFICE_PATH=D:\你的路径\LibreOffice\program\soffice.exe
  ```

- 或者在主界面点击「手动选择…」按钮，直接指定 `soffice.exe`。

### 2. 运行（开发模式）

需要 Python 3.8+（仅用标准库，无需 pip 安装任何包）：

```bash
python main.py
```

### 3. 打包成独立 exe（可选，给没有 Python 的人用）

```bash
build.bat        # Windows 双击运行，或命令行执行
```

生成的 `dist\Word2PDF.exe` 双击即用。

> 打包产物（`build\`、`dist\`、`venv\`、`*.spec`）都已在 `.gitignore` 中排除。
> 想发布 exe 请走 **GitHub Releases** 上传，不要提交进仓库，否则会永久撑大仓库历史。

## 文件说明

| 文件 | 作用 |
|------|------|
| `main.py` | GUI 主程序（tkinter） |
| `converter.py` | 核心转换逻辑（LibreOffice 无头调用） |
| `build.bat` | 一键打包成 exe |
| `requirements.txt` | 打包所需依赖（pyinstaller） |
| `.gitignore` | 排除虚拟环境与打包产物 |

## 命令行快速转换（不用界面）

```bash
python converter.py 文档.docx            # 输出到同目录
python converter.py 文档.docx D:\out     # 指定输出目录
```

## 常见问题

- **转换没反应 / 提示找不到引擎**：确认 LibreOffice 已安装；若装在非标准路径，可把 `soffice.exe` 所在目录加入系统 PATH，或设置环境变量 `SOFFICE_PATH`。
- **`.doc` 老格式能转吗**：可以，LibreOffice 同样支持。
- **中文乱码**：安装 LibreOffice 时建议勾选东亚语言支持；大多数情况下默认即可正常显示。
