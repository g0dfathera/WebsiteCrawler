import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import asyncio
import aiohttp
import sys

from WebCrawler import crawl_website, save_links_to_csv

class CrawlerGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Async Web Crawler")
        self.root.geometry("700x500")

        self.url_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="fast")

        self.output_text = None
        self.collected_links = {}
        self.visited = set()

        self.pause_event = asyncio.Event()
        self.pause_event.set()   
        self.stop_event = asyncio.Event()
        self.stop_event.clear() 

        self.setup_widgets()
        self.setup_close_handling()

    def setup_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Start URL:").pack(anchor=tk.W)
        ttk.Entry(frame, textvariable=self.url_var, width=80).pack(anchor=tk.W)

        ttk.Label(frame, text="Crawl Mode:").pack(anchor=tk.W)
        ttk.Combobox(frame, textvariable=self.mode_var, values=["fast", "slow"], state="readonly").pack(anchor=tk.W)

        ttk.Button(frame, text="Start Crawling", command=self.start_crawling).pack(pady=5)

        pause_stop_frame = ttk.Frame(frame)
        pause_stop_frame.pack(pady=5)

        self.pause_button = ttk.Button(pause_stop_frame, text="Pause", command=self.toggle_pause, state="disabled")
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(pause_stop_frame, text="Stop", command=self.stop_crawling, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(frame, text="Save As...", command=self.save_as).pack(pady=5)

        self.output_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=20)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=10)
        self.output_text.configure(state='disabled')

    def setup_close_handling(self):
        self.root.protocol("WM_DELETE_WINDOW", self.exit_cleanly)

    def log(self, text):
        print(text)
        self.output_text.configure(state='normal')
        self.output_text.insert('end', text + '\n')
        self.output_text.see('end')
        self.output_text.configure(state='disabled')

    def start_crawling(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a URL to crawl.")
            return

        mode = self.mode_var.get()
        max_depth = 3 if mode == "fast" else None
        max_urls = 50 if mode == "fast" else None

        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')

        self.collected_links = {}
        self.visited = set()

        self.pause_event.set()  
        self.stop_event.clear()  

        self.pause_button.config(state="normal", text="Pause")
        self.stop_button.config(state="normal")
        self.root.focus_get()  
        self.url_var.set(url)

        # Disable inputs during crawling
        self.disable_inputs(True)

        # Run crawl in a separate thread to avoid blocking GUI
        thread = threading.Thread(target=self.run_async_crawl, args=(url, max_depth, max_urls))
        thread.daemon = True
        thread.start()

    def disable_inputs(self, disable=True):
        state = "disabled" if disable else "normal"

        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Combobox):
                widget.configure(state=state)


    def toggle_pause(self):
        if self.pause_event.is_set():
            self.pause_event.clear() 
            self.pause_button.config(text="Resume")
            self.log("Crawling paused.")
        else:
            self.pause_event.set()   
            self.pause_button.config(text="Pause")
            self.log("Crawling resumed.")

    def stop_crawling(self):
        self.stop_event.set()
        self.pause_event.set()
        self.pause_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        self.log("Crawling stopped.")

    def run_async_crawl(self, url, max_depth, max_urls):
        asyncio.run(self._crawl(url, max_depth, max_urls))

    async def _crawl(self, url, max_depth, max_urls):
        try:
            async with aiohttp.ClientSession() as session:
                await crawl_website(
                    url,
                    session,
                    max_depth=max_depth,
                    max_urls=max_urls,
                    log_func=self.log,
                    pause_event=self.pause_event,
                    stop_event=self.stop_event,
                    collected_links=self.collected_links
                )
        except Exception as e:
            self.log(f"Error: {e}")

        self.log(f"\nDone. Found {len(self.collected_links)} links.")

        self.pause_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        self.disable_inputs(False)

    def save_as(self):
        if not self.collected_links:
            messagebox.showwarning("Nothing to Save", "No links collected.")
            return

        filetype = messagebox.askquestion("Save as", "Save as CSV? Click 'No' to save as TXT.")

        if filetype == 'yes':
            filetypes = [("CSV files", "*.csv")]
            default_ext = ".csv"
            save_func = self.save_as_csv
        else:
            filetypes = [("Text files", "*.txt")]
            default_ext = ".txt"
            save_func = self.save_as_txt

        filepath = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            filetypes=filetypes,
            title="Save file as"
        )
        if filepath:
            save_func(filepath)

    def save_as_csv(self, filepath):
        try:
            save_links_to_csv(self.collected_links, filepath)
            messagebox.showinfo("Saved", f"Links saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV: {e}")

    def save_as_txt(self, filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for link in self.collected_links:
                    f.write(link + "\n")
            messagebox.showinfo("Saved", f"Links saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save TXT: {e}")

    def exit_cleanly(self):
        self.stop_event.set()
        self.pause_event.set()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = CrawlerGUI(root)
    root.mainloop()
