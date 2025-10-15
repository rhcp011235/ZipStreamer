import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import shutil

class MultiPartExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Archive Stream Extractor")
        self.root.geometry("650x430")
        self.root.resizable(False, False)

        self.archive_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.delete_parts = tk.BooleanVar(value=True)

        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="📁 Select Archive (ZIP, 7Z.001, RAR):").pack(anchor='w', padx=10, pady=(10, 0))
        frame1 = tk.Frame(self.root)
        frame1.pack(fill='x', padx=10)
        tk.Entry(frame1, textvariable=self.archive_path, width=60).pack(side='left', fill='x', expand=True)
        tk.Button(frame1, text="Browse", command=self.select_archive).pack(side='right', padx=(5,0))

        tk.Label(self.root, text="📂 Output Folder:").pack(anchor='w', padx=10, pady=(10, 0))
        frame2 = tk.Frame(self.root)
        frame2.pack(fill='x', padx=10)
        tk.Entry(frame2, textvariable=self.output_path, width=60).pack(side='left', fill='x', expand=True)
        tk.Button(frame2, text="Browse", command=self.select_output).pack(side='right', padx=(5,0))

        tk.Checkbutton(self.root, text="✅ Automatically delete parts after use", variable=self.delete_parts).pack(anchor='w', padx=10, pady=(10, 0))

        tk.Button(self.root, text="▶ Start Extraction", command=self.start_extraction).pack(pady=10)

        self.log = scrolledtext.ScrolledText(self.root, height=12, state='disabled')
        self.log.pack(fill='both', expand=True, padx=10, pady=(0,10))

    def select_archive(self):
        path = filedialog.askopenfilename(filetypes=[("Archives", "*.zip *.rar *.7z *.001 *.z01 *.r00")])
        if path:
            self.archive_path.set(path)

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_path.set(path)

    def log_message(self, msg):
        self.log.config(state='normal')
        self.log.insert(tk.END, msg + "\n")
        self.log.yview(tk.END)
        self.log.config(state='disabled')

    def start_extraction(self):
        archive = self.archive_path.get()
        outdir = self.output_path.get()

        if not archive or not outdir:
            messagebox.showerror("Missing Info", "Select both archive and output folder.")
            return

        if not shutil.which("7z"):
            messagebox.showerror("7-Zip Not Found", "Please install 7-Zip and ensure '7z.exe' is in your PATH.")
            return

        threading.Thread(target=self.extract_archive, args=(archive, outdir), daemon=True).start()

    def extract_archive(self, archive, outdir):
        self.log_message(f"🔍 Extracting {os.path.basename(archive)}")

        base_dir = os.path.dirname(archive)
        base_name = self.get_base_name(os.path.basename(archive))

        # Match all parts (.7z.001, .002, .003, .rar, .r00, etc.)
        parts = [f for f in os.listdir(base_dir) if f.startswith(base_name) and any(f.endswith(ext) for ext in ['.zip', '.z01', '.z02', '.7z.001', '.7z.002', '.7z.003', '.rar', '.r00', '.r01', '.001', '.002'])]
        parts = sorted(parts)
        parts_fullpath = [os.path.join(base_dir, f) for f in parts]
        used_parts = set()

        # Record original sizes
        part_sizes = {p: os.path.getsize(p) for p in parts_fullpath}

        def monitor_parts():
            # Wait until they stop changing for N seconds, then delete
            last_check = {}
            still_needed = set(parts_fullpath)

            while still_needed:
                time.sleep(3)
                for part in list(still_needed):
                    try:
                        size = os.path.getsize(part)
                        if last_check.get(part) == size:
                            if self.delete_parts.get():
                                os.remove(part)
                                self.log_message(f"🗑 Deleted: {os.path.basename(part)}")
                                still_needed.remove(part)
                        else:
                            last_check[part] = size
                    except FileNotFoundError:
                        still_needed.remove(part)

        monitor_thread = threading.Thread(target=monitor_parts, daemon=True)
        monitor_thread.start()

        # Run extraction
        cmd = ["7z", "x", archive, f"-o{outdir}"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)

        for line in proc.stdout:
            self.log_message(line.strip())

        proc.wait()
        monitor_thread.join(timeout=15)

        if proc.returncode == 0:
            self.log_message("✅ Extraction complete!")
        else:
            self.log_message("❌ Error during extraction.")

    def get_base_name(self, filename):
        for ext in ['.7z.001', '.7z.002', '.001', '.zip', '.z01', '.rar', '.r00']:
            if filename.endswith(ext):
                return filename[:filename.index(ext)]
        return os.path.splitext(filename)[0]

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiPartExtractorGUI(root)
    root.mainloop()
