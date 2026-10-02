import os
import sys
import re
import hashlib
import threading
import webbrowser
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "DupSweep"
AUTHOR_NAME = "its.abja (abolfazl jamali)"
AUTHOR_LINK = "https://github.com/itsabja"

BG_CANVAS = "#F5F5F3"
CARD_SURFACE = "#FFFFFF"
BORDER_SOFT = "#E2E2DF"
TEXT_MAIN = "#141416"
TEXT_SUB = "#71717A"
ACCENT_BLACK = "#18181B"
ACCENT_HOVER = "#27272A"
HOVER_LIGHT = "#EDEDEA"
DANGER_TEXT = "#B91C1C"


class DupSweepApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        if os.path.exists("icon.ico"):
            self.iconbitmap("icon.ico")
        self.geometry("860x650")
        self.minsize(780, 580)
        self.configure(bg=BG_CANVAS)

        self._init_styles()

        self.selected_folder = ""
        self.pre_scan_data = {
            "files": [],
            "extensions": {},
            "total_folders": 0,
            "total_files": 0
        }
        self.duplicate_groups = []
        self.current_slide_index = 0

        self.main_container = tk.Frame(self, bg=BG_CANVAS)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.show_home_screen()

    def _init_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure(".", background=BG_CANVAS, font=("Segoe UI", 9))
        
        self.style.configure(
            "SolidBlack.TButton",
            font=("Segoe UI", 9, "bold"),
            background=ACCENT_BLACK,
            foreground="#FFFFFF",
            borderwidth=0,
            relief="flat",
            padding=(14, 7)
        )
        self.style.map("SolidBlack.TButton",
            background=[("active", ACCENT_HOVER), ("disabled", "#D4D4D8")],
            foreground=[("disabled", "#A1A1AA")]
        )

        self.style.configure(
            "Outline.TButton",
            font=("Segoe UI", 9),
            background=CARD_SURFACE,
            foreground=TEXT_MAIN,
            borderwidth=1,
            relief="solid",
            padding=(10, 5)
        )
        self.style.map("Outline.TButton",
            background=[("active", HOVER_LIGHT)]
        )

    def clear_container(self):
        for w in self.main_container.winfo_children():
            w.destroy()

    def _bind_mousewheel(self, widget, canvas):
        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        widget.bind("<MouseWheel>", _on_wheel)
        for child in widget.winfo_children():
            self._bind_mousewheel(child, canvas)

    def _truncate_path(self, path, max_len=65):
        if len(path) <= max_len:
            return path
        half = (max_len - 5) // 2
        return path[:half] + "..." + path[-half:]

    def show_home_screen(self):
        self.clear_container()

        center_box = tk.Frame(self.main_container, bg=CARD_SURFACE, highlightbackground=BORDER_SOFT, highlightthickness=1, padx=40, pady=40)
        center_box.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=580, height=440)

        tk.Label(center_box, text=APP_TITLE, font=("Segoe UI", 26, "bold"), fg=TEXT_MAIN, bg=CARD_SURFACE).pack(pady=(10, 2))
        tk.Label(center_box, text="Secure Duplicate File Detective", font=("Segoe UI", 10), fg=TEXT_SUB, bg=CARD_SURFACE).pack(pady=(0, 25))

        entry_frame = tk.Frame(center_box, bg=CARD_SURFACE)
        entry_frame.pack(fill=tk.X, pady=(0, 15))

        self.path_entry = tk.Entry(entry_frame, font=("Segoe UI", 9), bg=BG_CANVAS, fg=TEXT_MAIN, relief="flat", highlightbackground=BORDER_SOFT, highlightthickness=1)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))
        self.path_entry.insert(0, "Choose target folder to scan...")
        self.path_entry.config(state="readonly")

        browse_btn = ttk.Button(entry_frame, text="Browse", style="Outline.TButton", command=self._browse_folder)
        browse_btn.pack(side=tk.RIGHT)

        self.home_status = tk.Label(center_box, text="Awaiting directory selection.", font=("Segoe UI", 9), fg=TEXT_SUB, bg=CARD_SURFACE)
        self.home_status.pack(pady=(0, 15))

        self.start_scan_btn = ttk.Button(center_box, text="Analyze Directory", style="SolidBlack.TButton", state="disabled", command=self._run_initial_scan)
        self.start_scan_btn.pack(fill=tk.X, ipady=2, pady=(0, 20))

        self.home_progress = ttk.Progressbar(center_box, mode='indeterminate')

        footer = tk.Frame(center_box, bg=CARD_SURFACE)
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        author = tk.Label(footer, text=f"Creator: {AUTHOR_NAME}", font=("Segoe UI", 8, "underline"), fg=TEXT_SUB, cursor="hand2", bg=CARD_SURFACE)
        author.pack()
        author.bind("<Button-1>", lambda e: webbrowser.open_new(AUTHOR_LINK))

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Scan Folder")
        if folder:
            self.selected_folder = os.path.normpath(folder)
            self.path_entry.config(state="normal")
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.selected_folder)
            self.path_entry.config(state="readonly")
            self.start_scan_btn.config(state="normal")
            self.home_status.config(text="Directory verified. Ready to index.", fg=TEXT_MAIN)

    def _run_initial_scan(self):
        self.start_scan_btn.config(state="disabled")
        self.home_progress.pack(fill=tk.X, pady=(0, 15))
        self.home_progress.start(10)
        self.home_status.config(text="Indexing file structure and extensions safely...", fg=TEXT_SUB)

        threading.Thread(target=self._initial_scan_worker, daemon=True).start()

    def _initial_scan_worker(self):
        files_data = []
        ext_counter = {}
        dir_count = 0

        try:
            for root, dirs, files in os.walk(self.selected_folder):
                dir_count += len(dirs)
                for f in files:
                    full_path = os.path.join(root, f)
                    try:
                        stat = os.stat(full_path)
                        ext = os.path.splitext(f)[1].lower() or "[no-ext]"
                        ext_counter[ext] = ext_counter.get(ext, 0) + 1
                        files_data.append({
                            "path": full_path,
                            "filename": f,
                            "size": stat.st_size,
                            "mtime": stat.st_mtime,
                            "ext": ext
                        })
                    except (PermissionError, FileNotFoundError):
                        continue

            self.pre_scan_data = {
                "files": files_data,
                "extensions": ext_counter,
                "total_folders": dir_count,
                "total_files": len(files_data)
            }
            self.after(0, self.show_config_screen)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Read Error", f"Unable to read folder tree:\n{e}"))
            self.after(0, lambda: self.start_scan_btn.config(state="normal"))

    def show_config_screen(self):
        self.clear_container()

        container = tk.Frame(self.main_container, bg=BG_CANVAS, padx=25, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        top_bar = tk.Frame(container, bg=CARD_SURFACE, highlightbackground=BORDER_SOFT, highlightthickness=1, padx=20, pady=15)
        top_bar.pack(fill=tk.X, pady=(0, 15))

        tk.Label(top_bar, text="Detection Strategy & Formats", font=("Segoe UI", 14, "bold"), fg=TEXT_MAIN, bg=CARD_SURFACE).pack(anchor="w")
        info_txt = f"{self.pre_scan_data['total_files']:,} files indexed across {self.pre_scan_data['total_folders']:,} folders."
        tk.Label(top_bar, text=info_txt, font=("Segoe UI", 9), fg=TEXT_SUB, bg=CARD_SURFACE).pack(anchor="w", pady=(2, 0))

        split_frame = tk.Frame(container, bg=BG_CANVAS)
        split_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        left_box = tk.LabelFrame(split_frame, text=" Detection Mode ", font=("Segoe UI", 9, "bold"), bg=CARD_SURFACE, fg=TEXT_MAIN, padx=15, pady=15, relief="solid", bd=1)
        left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.strategy_var = tk.StringVar(value="hybrid")
        modes = [
            ("Smart Hybrid (Default)", "hybrid", "Prioritizes identical file sizes then validates using SHA-256 hash. Ultra-fast and 100% safe."),
            ("Exact Content Hash", "hash", "Compares SHA-256 bit-by-bit for all files irrespective of name/size."),
            ("Identical File Size", "size", "Groups files with identical byte lengths."),
            ("Copy / Name Similarity", "name", "Detects duplicates named like 'file (1).ext' or 'file - Copy.ext'.")
        ]

        for title, val, desc in modes:
            row = tk.Frame(left_box, bg=CARD_SURFACE)
            row.pack(fill=tk.X, pady=6, anchor="w")
            rb = ttk.Radiobutton(row, text=title, value=val, variable=self.strategy_var)
            rb.pack(anchor="w")
            lbl = tk.Label(row, text=desc, font=("Segoe UI", 8), fg=TEXT_SUB, bg=CARD_SURFACE, wraplength=310, justify="left")
            lbl.pack(anchor="w", padx=(24, 0), pady=(1, 0))

        right_box = tk.LabelFrame(split_frame, text=" Include Extensions ", font=("Segoe UI", 9, "bold"), bg=CARD_SURFACE, fg=TEXT_MAIN, padx=12, pady=12, relief="solid", bd=1)
        right_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        btn_row = tk.Frame(right_box, bg=CARD_SURFACE)
        btn_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(btn_row, text="Select All", style="Outline.TButton", command=self._select_all_exts).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_row, text="Clear All", style="Outline.TButton", command=self._clear_all_exts).pack(side=tk.LEFT)

        ext_canvas = tk.Canvas(right_box, bg=CARD_SURFACE, highlightthickness=0)
        ext_scroll = ttk.Scrollbar(right_box, orient="vertical", command=ext_canvas.yview)
        self.ext_list_frame = tk.Frame(ext_canvas, bg=CARD_SURFACE)

        self.ext_list_frame.bind("<Configure>", lambda e: ext_canvas.configure(scrollregion=ext_canvas.bbox("all")))
        ext_canvas.create_window((0, 0), window=self.ext_list_frame, anchor="nw")
        ext_canvas.configure(yscrollcommand=ext_scroll.set)

        ext_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ext_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.ext_checkbox_vars = {}
        for ext, count in sorted(self.pre_scan_data["extensions"].items(), key=lambda x: x[1], reverse=True):
            var = tk.BooleanVar(value=True)
            self.ext_checkbox_vars[ext] = var
            cb = ttk.Checkbutton(self.ext_list_frame, text=f"{ext}   ({count:,})", variable=var)
            cb.pack(anchor="w", pady=2)

        self._bind_mousewheel(right_box, ext_canvas)

        bottom = tk.Frame(container, bg=BG_CANVAS)
        bottom.pack(fill=tk.X)

        ttk.Button(bottom, text="Back", style="Outline.TButton", command=self.show_home_screen).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Run Deep Search", style="SolidBlack.TButton", command=self._run_deep_analysis).pack(side=tk.RIGHT)

    def _select_all_exts(self):
        for v in self.ext_checkbox_vars.values():
            v.set(True)

    def _clear_all_exts(self):
        for v in self.ext_checkbox_vars.values():
            v.set(False)

    def _run_deep_analysis(self):
        chosen_exts = {k for k, v in self.ext_checkbox_vars.items() if v.get()}
        if not chosen_exts:
            messagebox.showwarning("Empty Filter", "Please choose at least one extension.")
            return

        self.busy_win = tk.Toplevel(self)
        self.busy_win.title("Scanning")
        self.busy_win.geometry("340x140")
        self.busy_win.resizable(False, False)
        self.busy_win.configure(bg=CARD_SURFACE)
        self.busy_win.transient(self)
        self.busy_win.grab_set()

        tk.Label(self.busy_win, text="Executing Duplicate Algorithms...", font=("Segoe UI", 9, "bold"), fg=TEXT_MAIN, bg=CARD_SURFACE).pack(pady=(25, 12))
        pb = ttk.Progressbar(self.busy_win, mode='indeterminate')
        pb.pack(fill=tk.X, padx=30)
        pb.start(15)

        strategy = self.strategy_var.get()
        threading.Thread(target=self._deep_worker, args=(strategy, chosen_exts), daemon=True).start()

    def _deep_worker(self, strategy, selected_exts):
        filtered_files = [f for f in self.pre_scan_data["files"] if f["ext"] in selected_exts]
        results = []

        try:
            if strategy == "size":
                size_map = {}
                for f in filtered_files:
                    size_map.setdefault(f["size"], []).append(f)
                results = [grp for grp in size_map.values() if len(grp) > 1]

            elif strategy == "name":
                name_map = {}
                for f in filtered_files:
                    base = os.path.splitext(f["filename"])[0]
                    norm = re.sub(r'(\s*[\(\[\-_]?\s*(?:copy|\d+)\s*[\)\]]?\s*)$', '', base, flags=re.IGNORECASE).strip().lower()
                    name_map.setdefault(norm, []).append(f)
                results = [grp for grp in name_map.values() if len(grp) > 1]

            elif strategy == "hash":
                h_map = {}
                for f in filtered_files:
                    h = self._calc_sha256(f["path"])
                    if h:
                        h_map.setdefault(h, []).append(f)
                results = [grp for grp in h_map.values() if len(grp) > 1]

            elif strategy == "hybrid":
                size_map = {}
                for f in filtered_files:
                    if f["size"] > 0:
                        size_map.setdefault(f["size"], []).append(f)
                
                size_candidates = [grp for grp in size_map.values() if len(grp) > 1]

                for grp in size_candidates:
                    h_map = {}
                    for f in grp:
                        h = self._calc_sha256(f["path"])
                        if h:
                            h_map.setdefault(h, []).append(f)
                    for confirmed in h_map.values():
                        if len(confirmed) > 1:
                            results.append(confirmed)

            self.duplicate_groups = results
            self.current_slide_index = 0
            self.after(0, self._on_deep_finished)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Algorithm Error", str(e)))
            if hasattr(self, 'busy_win'):
                self.busy_win.destroy()

    def _calc_sha256(self, path):
        """Read-only chunk hash to prevent memory overflows or locking"""
        h = hashlib.sha256()
        try:
            with open(path, 'rb') as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            return h.hexdigest()
        except (PermissionError, FileNotFoundError):
            return None

    def _on_deep_finished(self):
        if hasattr(self, 'busy_win'):
            self.busy_win.destroy()

        if not self.duplicate_groups:
            messagebox.showinfo("Clean Directory", "No duplicates were detected according to your rules.")
            return

        self.show_results_slideshow()

    def show_results_slideshow(self):
        self.clear_container()

        container = tk.Frame(self.main_container, bg=BG_CANVAS, padx=25, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        nav = tk.Frame(container, bg=CARD_SURFACE, highlightbackground=BORDER_SOFT, highlightthickness=1, padx=15, pady=10)
        nav.pack(fill=tk.X, pady=(0, 15))

        self.prev_btn = ttk.Button(nav, text="← Previous", style="Outline.TButton", command=self._prev_slide)
        self.prev_btn.pack(side=tk.LEFT)

        self.counter_lbl = tk.Label(nav, text="", font=("Segoe UI", 10, "bold"), fg=TEXT_MAIN, bg=CARD_SURFACE)
        self.counter_lbl.pack(side=tk.LEFT, expand=True)

        self.next_btn = ttk.Button(nav, text="Next →", style="Outline.TButton", command=self._next_slide)
        self.next_btn.pack(side=tk.RIGHT)

        self.slides_frame = tk.Frame(container, bg=BG_CANVAS)
        self.slides_frame.pack(fill=tk.BOTH, expand=True)

        b_bar = tk.Frame(container, bg=BG_CANVAS)
        b_bar.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(b_bar, text="Configure Again", style="Outline.TButton", command=self.show_config_screen).pack(side=tk.LEFT)

        self._render_current_slide()

    def _render_current_slide(self):
        for w in self.slides_frame.winfo_children():
            w.destroy()

        total = len(self.duplicate_groups)
        idx = self.current_slide_index

        self.counter_lbl.config(text=f"Match Group {idx + 1} of {total}")
        self.prev_btn.config(state="normal" if idx > 0 else "disabled")
        self.next_btn.config(state="normal" if idx < total - 1 else "disabled")

        items = self.duplicate_groups[idx]

        canvas = tk.Canvas(self.slides_frame, bg=BG_CANVAS, highlightthickness=0)
        scroll = ttk.Scrollbar(self.slides_frame, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg=BG_CANVAS)

        scroll_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_content, anchor="nw", width=780)
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for file_info in items:
            self._render_item_card(scroll_content, file_info)

        self._bind_mousewheel(self.slides_frame, canvas)

    def _render_item_card(self, parent, file_info):
        card = tk.Frame(parent, bg=CARD_SURFACE, highlightbackground=BORDER_SOFT, highlightthickness=1, padx=14, pady=10)
        card.pack(fill=tk.X, pady=4)

        actions = tk.Frame(card, bg=CARD_SURFACE)
        actions.pack(side=tk.RIGHT, padx=(10, 0))

        open_b = ttk.Button(actions, text="Open", style="Outline.TButton", command=lambda p=file_info["path"]: self._open_file(p))
        open_b.pack(side=tk.LEFT, padx=2)

        loc_b = ttk.Button(actions, text="Locate", style="Outline.TButton", command=lambda p=file_info["path"]: self._locate_in_explorer(p))
        loc_b.pack(side=tk.LEFT, padx=2)

        del_btn = tk.Button(
            actions, text="Delete", font=("Segoe UI", 9),
            bg=CARD_SURFACE, fg=DANGER_TEXT, activebackground="#FEE2E2",
            activeforeground=DANGER_TEXT, relief="solid", bd=1,
            cursor="hand2", padx=8, pady=3,
            command=lambda f=file_info, c=card: self._safe_delete_file(f, c)
        )
        del_btn.pack(side=tk.LEFT, padx=2)

        info = tk.Frame(card, bg=CARD_SURFACE)
        info.pack(side=tk.LEFT, fill=tk.X, expand=True)

        name_lbl = tk.Label(info, text=file_info["filename"], font=("Segoe UI", 10, "bold"), fg=TEXT_MAIN, bg=CARD_SURFACE, anchor="w")
        name_lbl.pack(fill=tk.X)

        truncated_path = self._truncate_path(file_info["path"], max_len=75)
        path_lbl = tk.Label(info, text=truncated_path, font=("Segoe UI", 8), fg=TEXT_SUB, bg=CARD_SURFACE, anchor="w")
        path_lbl.pack(fill=tk.X, pady=(1, 3))

        size_kb = file_info["size"] / 1024
        size_str = f"{size_kb / 1024:.2f} MB" if size_kb >= 1024 else f"{size_kb:.1f} KB"
        mtime_str = datetime.fromtimestamp(file_info["mtime"]).strftime("%Y-%m-%d %H:%M")

        meta_lbl = tk.Label(info, text=f"{size_str}  ·  {mtime_str}", font=("Segoe UI", 8), fg=TEXT_SUB, bg=CARD_SURFACE, anchor="w")
        meta_lbl.pack(fill=tk.X)

    def _open_file(self, file_path):
        try:
            os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("Cannot Open", f"Unable to open target file:\n{e}")

    def _locate_in_explorer(self, file_path):
        try:
            abs_path = os.path.abspath(file_path)
            subprocess.run(["explorer", f"/select,{abs_path}"], check=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reveal in Explorer:\n{e}")

    def _safe_delete_file(self, file_info, card_widget):

        confirm = messagebox.askyesno(
            "Permanent Deletion Confirmation",
            f"Are you completely sure you want to permanently delete this file?\n\nTarget File:\n{file_info['path']}\n\nThis cannot be undone!",
            icon="warning"
        )
        if not confirm:
            return

        try:
            os.remove(file_info["path"])
            current_group = self.duplicate_groups[self.current_slide_index]
            if file_info in current_group:
                current_group.remove(file_info)

            card_widget.destroy()

            if len(current_group) <= 1:
                del self.duplicate_groups[self.current_slide_index]
                if not self.duplicate_groups:
                    messagebox.showinfo("Complete", "All duplicate groups have been addressed!")
                    self.show_home_screen()
                    return
                if self.current_slide_index >= len(self.duplicate_groups):
                    self.current_slide_index = len(self.duplicate_groups) - 1
                self._render_current_slide()

        except Exception as e:
            messagebox.showerror("Delete Blocked", f"Could not remove file (permission or locked by another app):\n{e}")

    def _prev_slide(self):
        if self.current_slide_index > 0:
            self.current_slide_index -= 1
            self._render_current_slide()

    def _next_slide(self):
        if self.current_slide_index < len(self.duplicate_groups) - 1:
            self.current_slide_index += 1
            self._render_current_slide()


if __name__ == "__main__":
    app = DupSweepApp()
    app.mainloop()