# DupSweep

DupSweep is a high-performance desktop utility designed for deterministic duplicate file detection, selective filtering, and manual inspection. It provides granular control over how file equality is established—from rapid file-size matching to cryptographic content hashing—wrapped in a responsive, non-blocking interface.

The project is built entirely on the Python standard library with zero external runtime dependencies and can be compiled into a standalone, native Windows executable.

---

## Distribution

### Recommended: Standalone Portable Binary (Windows x64)

For end users and deployment environments without an existing Python runtime, it is recommended to download the official pre-compiled standalone binary:

1. Open the [Releases](https://github.com/itsabja/DupSweep/releases) page.
2. Under the latest version (`v1.0.0`), download:
   ```
   DupSweep-v1.0.0-windows-x64.exe
   ```
3. Run the executable directly. No installer, elevated privileges, or runtime packages are required.

---

## Technical Overview

### Detection Pipeline

The detection architecture executes across three segregated stages:

```
[Target Directory Selection]
              │
              ▼
    [Directory Indexing Engine]
      ├── Threaded recursive traversal (os.walk)
      ├── Metadata collection (absolute path, size in bytes, mtime)
      └── Dynamic file extension frequency distribution
              │
              ▼
    [Strategy Execution Stage]
      ├── Smart Hybrid (Size partition -> SHA-256 chunk hash)
      ├── Exact Content Hash (Linear SHA-256 verification)
      ├── Identical File Size (Byte length equality)
      └── Name Pattern Analysis (RegEx normalization)
              │
              ▼
    [Interactive Slide Pagination]
      ├── Match group navigation
      ├── Target inspection (Explorer select, system launch)
      └── Permanent removal with strict exception handling
```

### Detection Modes

- **Smart Hybrid (`hybrid`) [Default]**: Segregates files by byte size first. Groups with duplicate sizes are subsequently verified using chunked SHA-256 hashing. This eliminates unnecessary I/O on unique files and ensures collision-free identification.
- **Exact Content Hash (`hash`)**: Calculates the complete SHA-256 digest of every file irrespective of filename or file size.
- **Identical File Size (`size`)**: Partitions files purely by identical byte length. Useful for rapid diagnostics across large media datasets.
- **Name Pattern Normalization (`name`)**: Uses regular expressions to match duplicate naming artifacts (e.g., `filename (1).ext`, `filename - Copy.ext`) regardless of content variance.

### Memory and Concurrency Architecture

- **Chunked File Streaming**: Hash calculations read files sequentially in 64 KB (`65,536` bytes) buffers. Memory usage remains constant even when processing multi-gigabyte disk images or archives.
- **Background Worker Threads**: Heavy I/O workloads (directory indexing and hashing passes) run within isolated daemon threads, preventing UI lockups and keeping the Tkinter event loop responsive.
- **Safe Explorer Integration**: Explorer interaction isolates file paths using explicit parameter passing to avoid shell parsing vulnerabilities.

---

## Source Execution

### System Requirements

- Windows 10 / 11 (64-bit)
- Python 3.8 or higher
- Tcl/Tk support enabled in Python installation

### Setup and Launch

1. Clone the repository:
   ```cmd
   git clone https://github.com/itsabja/DupSweep.git
   cd DupSweep
   ```

2. Confirm Python availability:
   ```cmd
   python --version
   ```

3. Launch the application:
   ```cmd
   python dupsweep.py
   ```

---

## Compilation from Source

The official release binary is built using Nuitka to translate the Python codebase into optimized C before producing the final portable PE executable.

### Compilation Prerequisites

1. Install Nuitka and compression dependencies:
   ```cmd
   pip install nuitka zstandard
   ```

2. Ensure a supported C compiler is present in system `PATH` (e.g., MinGW-w64 or Microsoft Visual C++ Build Tools).

### Build Procedure

Run the compilation command from the repository root:

```cmd
python -m nuitka --mode=onefile --enable-plugin=tk-inter --windows-console-mode=disable --windows-icon-from-ico=icon.ico --assume-yes-for-downloads --output-filename=DupSweep-v1.0.0-windows-x64.exe dupsweep.py
```

### Build Parameters Explained

| Parameter | Function |
| :--- | :--- |
| `--mode=onefile` | Packages the application and all runtime assets into a single portable binary. |
| `--enable-plugin=tk-inter` | Directs Nuitka to automatically bundle required Tcl/Tk runtimes and libraries. |
| `--windows-console-mode=disable` | Prevents the default command prompt terminal from opening behind the graphical interface. |
| `--windows-icon-from-ico=icon.ico` | Embeds the application icon into the Windows executable resource table. |
| `--assume-yes-for-downloads` | Allows Nuitka to download missing toolchain components (such as portable MinGW or dependency walkers) automatically. |
| `--output-filename=...` | Sets the output binary name to match the official release naming schema. |

Upon completion, the compiled file `DupSweep-v1.0.0-windows-x64.exe` will be located in the working directory.

---

## Security and System Operation Details

- **Read-Only Inspection**: Directory evaluation and hashing passes operate under standard read access without writing lock markers or temporary cache indices to target directories.
- **Safe Explorer Revealing**: Explorer selection uses direct subprocess argument lists rather than interpolated shell strings, ensuring reliability with special characters and spaces.
- **Explicit Deletion Handlers**: File removals invoke `os.remove()` exclusively upon explicit modal confirmation. System and file-access errors are captured to prevent application termination when files are locked by external processes.

---

## Maintainer

- **Abolfazl Jamali (its.abja)**
- Profile: [https://github.com/itsabja](https://github.com/itsabja)

---

## License

This project is released under the terms of the MIT License. See the [LICENSE](LICENSE) file for complete text.
