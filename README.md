# 🧹 DupSweep - Secure Duplicate File Detective

DupSweep is a lightweight, responsive desktop application built with Python and Tkinter that safely detects and manages duplicate files using multiple scanning strategies (including SHA-256 content hashing).

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)

---

## ✨ Features

- **Zero External Dependencies:** Built entirely with Python's Standard Library.
- **Multiple Detection Strategies:**
  - **Smart Hybrid (Recommended):** Filters identical sizes first, then confirms via SHA-256 chunked hashing.
  - **Exact Hash:** Byte-by-byte SHA-256 verification.
  - **Identical Size:** Instant scan for identical byte lengths.
  - **Copy Pattern:** RegEx detection for `(1)`, `- Copy`, etc.
- **Selective Extension Filtering:** Pick which file extensions to process.
- **Interactive Review:** Step through duplicate groups slide-by-slide.
- **File Actions:** Directly open files, reveal them in File Explorer, or permanently delete them with safety confirmations.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher installed on Windows.

### Installation & Run

1. Clone the repository:
   ```bash
   git clone https://github.com/itsabja/DupSweep.git
   cd DupSweep
   ```

2. Run the application:
   ```bash
   python dupsweep.py
   ```

---

## 🛠️ Build Executable (.exe)

If you want to compile this into a standalone Windows `.exe` using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --icon=icon.ico dupsweep.py
```
The executable will be generated inside the `dist/` directory.

---

## 👤 Author

- **Abolfazl Jamali (its.abja)**
- GitHub: [@itsabja](https://github.com/itsabja)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.