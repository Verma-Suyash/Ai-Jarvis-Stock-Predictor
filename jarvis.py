"""
JARVIS - Voice-Controlled Desktop AI Assistant
A Python-based assistant with stock prediction, time-series analysis, and automation.
"""

import os
import sys
import json
import datetime
import threading
import webbrowser
import subprocess
import time
import random
import math

# ── Core libraries (always available) ────────────────────────────────────────
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ── Optional libraries (installed via requirements.txt) ───────────────────────
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("[WARN] speech_recognition not installed. Voice input disabled.")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("[WARN] pyttsx3 not installed. Text-to-speech disabled.")

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("[WARN] pandas/numpy not installed. Stock analysis disabled.")

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("[WARN] matplotlib not installed. Charts disabled.")

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import MinMaxScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("[WARN] scikit-learn not installed. Regression disabled.")

# ══════════════════════════════════════════════════════════════════════════════
#  JARVIS BRAIN – command processing & stock analysis
# ══════════════════════════════════════════════════════════════════════════════

class JarvisBrain:
    def __init__(self):
        self.tts_engine = None
        self._init_tts()

    def _init_tts(self):
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 165)
                self.tts_engine.setProperty("volume", 0.9)
                # prefer a male voice if available
                voices = self.tts_engine.getProperty("voices")
                for v in voices:
                    if "male" in v.name.lower() or "david" in v.name.lower():
                        self.tts_engine.setProperty("voice", v.id)
                        break
            except Exception as e:
                print(f"[WARN] TTS init failed: {e}")

    # ── Speech output ─────────────────────────────────────────────────────────
    def speak(self, text: str):
        print(f"[JARVIS] {text}")
        if self.tts_engine:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception:
                pass

    # ── Command parser ────────────────────────────────────────────────────────
    def process_command(self, command: str) -> str:
        command = command.lower().strip()

        # Greetings
        if any(w in command for w in ["hello", "hi", "hey", "greet"]):
            return self._greet()

        # Time / Date
        if "time" in command:
            return f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}."
        if "date" in command:
            return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}."

        # Stock prediction
        if any(w in command for w in ["stock", "predict", "price", "market", "regression"]):
            ticker = self._extract_ticker(command)
            return self._predict_stock(ticker)

        # Open apps / websites
        if "open" in command:
            return self._open_something(command)

        # System info
        if "system" in command or "cpu" in command or "memory" in command:
            return self._system_info()

        # Weather placeholder
        if "weather" in command:
            return "I can fetch weather data if you configure an API key in config.json."

        # Jokes
        if "joke" in command:
            return self._tell_joke()

        # Help
        if "help" in command or "what can you do" in command:
            return self._help()

        # Wikipedia placeholder
        if "search" in command or "wikipedia" in command or "what is" in command:
            query = command.replace("search", "").replace("wikipedia", "").replace("what is", "").strip()
            url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
            webbrowser.open(url)
            return f"Opening Wikipedia for '{query}'."

        return ("I didn't understand that command. "
                "Try 'help' to see what I can do.")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _greet(self) -> str:
        hour = datetime.datetime.now().hour
        if hour < 12:
            period = "morning"
        elif hour < 17:
            period = "afternoon"
        else:
            period = "evening"
        return (f"Good {period}! I'm JARVIS, your personal AI assistant. "
                "How may I assist you today?")

    def _extract_ticker(self, command: str) -> str:
        """Very simple ticker extractor – looks for uppercase words."""
        words = command.upper().split()
        for w in words:
            if w.isalpha() and 1 < len(w) <= 5 and w not in (
                    "STOCK", "PREDICT", "PRICE", "MARKET", "THE", "FOR",
                    "SHOW", "ME", "GET", "FETCH", "REGRESSION"):
                return w
        return "AAPL"  # default

    def _predict_stock(self, ticker: str) -> str:
        if not (PANDAS_AVAILABLE and ML_AVAILABLE):
            return ("Stock prediction requires pandas, numpy, and scikit-learn. "
                    "Run: pip install pandas numpy scikit-learn")

        # Generate synthetic historical data (replace with yfinance for real data)
        np.random.seed(42)
        n = 90
        trend = np.linspace(100, 150, n)
        noise = np.random.normal(0, 5, n)
        prices = trend + noise

        df = pd.DataFrame({
            "day": np.arange(n),
            "price": prices
        })

        # Linear Regression
        X = df[["day"]].values
        y = df["price"].values
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)

        model = LinearRegression()
        model.fit(X_scaled, y)

        # Predict next 7 days
        future_days = np.arange(n, n + 7).reshape(-1, 1)
        future_scaled = scaler.transform(future_days)
        predictions = model.predict(future_scaled)

        result = (f"📈 {ticker} Stock Prediction (Linear Regression)\n"
                  f"   Based on 90-day synthetic time-series analysis:\n")
        for i, pred in enumerate(predictions, 1):
            result += f"   Day +{i}: ${pred:.2f}\n"
        result += ("   ⚠ This uses synthetic data. "
                   "Install 'yfinance' for real market data.")
        return result

    def _open_something(self, command: str) -> str:
        targets = {
            "youtube": "https://youtube.com",
            "google": "https://google.com",
            "github": "https://github.com",
            "notepad": "notepad" if sys.platform == "win32" else "gedit",
            "calculator": "calc" if sys.platform == "win32" else "gnome-calculator",
        }
        for key, target in targets.items():
            if key in command:
                if target.startswith("http"):
                    webbrowser.open(target)
                    return f"Opening {key.capitalize()} in your browser."
                else:
                    try:
                        subprocess.Popen(target)
                        return f"Opening {key.capitalize()}."
                    except FileNotFoundError:
                        return f"Could not open {key} on this system."
        return "I'm not sure what to open. Try 'open YouTube' or 'open Google'."

    def _system_info(self) -> str:
        info = f"Platform: {sys.platform}\nPython: {sys.version.split()[0]}\n"
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            info += (f"CPU Usage: {cpu}%\n"
                     f"RAM: {ram.used // (1024**2)} MB / "
                     f"{ram.total // (1024**2)} MB")
        except ImportError:
            info += "Install psutil for CPU/RAM info: pip install psutil"
        return info

    def _tell_joke(self) -> str:
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
            "Why did the Python programmer wear glasses? Because they couldn't C#.",
            "A SQL query walks into a bar, walks up to two tables and asks... Can I join you?",
        ]
        return random.choice(jokes)

    def _help(self) -> str:
        return (
            "🤖 JARVIS Commands:\n"
            "  • 'hello' / 'hi'          – Greeting\n"
            "  • 'time' / 'date'         – Current time or date\n"
            "  • 'predict AAPL stock'    – Stock price prediction\n"
            "  • 'open YouTube'          – Open websites/apps\n"
            "  • 'system info'           – CPU & RAM usage\n"
            "  • 'joke'                  – Tell a joke\n"
            "  • 'search <topic>'        – Open Wikipedia\n"
            "  • 'weather'               – Weather (needs API key)\n"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  JARVIS GUI  – Tkinter dark-themed interface
# ══════════════════════════════════════════════════════════════════════════════

class JarvisGUI:
    # ── Colour palette ────────────────────────────────────────────────────────
    BG       = "#0a0e1a"
    PANEL    = "#0f1628"
    ACCENT   = "#00d4ff"
    ACCENT2  = "#0066ff"
    TEXT     = "#e0f0ff"
    DIM      = "#3a4a6a"
    SUCCESS  = "#00ff88"
    WARN     = "#ffaa00"
    FONT_M   = ("Consolas", 11)
    FONT_L   = ("Consolas", 13, "bold")
    FONT_XL  = ("Consolas", 22, "bold")

    def __init__(self, root: tk.Tk):
        self.root = root
        self.brain = JarvisBrain()
        self.recognizer = sr.Recognizer() if SPEECH_AVAILABLE else None
        self.listening = False
        self._build_ui()
        self._startup_sequence()

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        self.root.title("J.A.R.V.I.S  –  AI Desktop Assistant")
        self.root.geometry("1100x720")
        self.root.configure(bg=self.BG)
        self.root.resizable(True, True)

        self._style_ttk()

        # Top header
        self._build_header()

        # Main area: left = terminal, right = side panel
        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        self._build_terminal(main)
        self._build_side_panel(main)

        # Bottom input bar
        self._build_input_bar()

    def _style_ttk(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TProgressbar",
                     troughcolor=self.PANEL,
                     background=self.ACCENT,
                     thickness=6)

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=self.PANEL, height=70)
        hdr.pack(fill=tk.X, padx=12, pady=(12, 8))
        hdr.pack_propagate(False)

        # Logo / name
        tk.Label(hdr, text="J.A.R.V.I.S", font=self.FONT_XL,
                 fg=self.ACCENT, bg=self.PANEL).pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(hdr,
                 text="Just A Rather Very Intelligent System  |  AI Desktop Assistant",
                 font=("Consolas", 9), fg=self.DIM, bg=self.PANEL
                 ).pack(side=tk.LEFT, pady=10)

        # Status dot
        self.status_label = tk.Label(hdr, text="● ONLINE", font=("Consolas", 10, "bold"),
                                     fg=self.SUCCESS, bg=self.PANEL)
        self.status_label.pack(side=tk.RIGHT, padx=20)

        # Clock
        self.clock_label = tk.Label(hdr, text="", font=("Consolas", 12),
                                    fg=self.ACCENT, bg=self.PANEL)
        self.clock_label.pack(side=tk.RIGHT, padx=10)
        self._tick_clock()

    def _build_terminal(self, parent):
        frame = tk.Frame(parent, bg=self.PANEL, bd=1, relief=tk.SOLID,
                         highlightbackground=self.DIM, highlightthickness=1)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        tk.Label(frame, text="  ▸ TERMINAL OUTPUT",
                 font=("Consolas", 9, "bold"), fg=self.ACCENT, bg=self.PANEL,
                 anchor="w").pack(fill=tk.X, pady=(6, 0))

        self.terminal = scrolledtext.ScrolledText(
            frame, font=("Consolas", 11), bg="#050810", fg=self.TEXT,
            insertbackground=self.ACCENT, relief=tk.FLAT, bd=0,
            selectbackground=self.ACCENT2, wrap=tk.WORD, state=tk.DISABLED
        )
        self.terminal.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Tag colours
        self.terminal.tag_config("jarvis", foreground=self.ACCENT)
        self.terminal.tag_config("user",   foreground=self.SUCCESS)
        self.terminal.tag_config("system", foreground=self.WARN)
        self.terminal.tag_config("error",  foreground="#ff4466")

    def _build_side_panel(self, parent):
        side = tk.Frame(parent, bg=self.BG, width=280)
        side.pack(side=tk.RIGHT, fill=tk.Y)
        side.pack_propagate(False)

        # Capabilities card
        self._card(side, "CAPABILITIES",
                   ["🎤  Voice Activation",
                    "📈  Stock Prediction",
                    "📊  Time-Series Regression",
                    "🌐  Web Automation",
                    "🖥  System Monitor",
                    "🤖  NLP Commands"])

        # Tech stack card
        self._card(side, "TECH STACK",
                   ["Python  3.x",
                    "Pandas  +  NumPy",
                    "Seaborn  +  Matplotlib",
                    "scikit-learn  (Regression)",
                    "SpeechRecognition",
                    "pyttsx3  (TTS)",
                    "Tkinter  (UI)"])

        # Module status card
        mod_frame = tk.Frame(side, bg=self.PANEL, bd=0)
        mod_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(mod_frame, text="  MODULE STATUS",
                 font=("Consolas", 9, "bold"), fg=self.ACCENT,
                 bg=self.PANEL, anchor="w").pack(fill=tk.X, pady=(6, 2))

        modules = [
            ("Speech Recognition", SPEECH_AVAILABLE),
            ("Text-to-Speech",     TTS_AVAILABLE),
            ("Pandas / NumPy",     PANDAS_AVAILABLE),
            ("Matplotlib",         MATPLOTLIB_AVAILABLE),
            ("scikit-learn",       ML_AVAILABLE),
        ]
        for name, ok in modules:
            row = tk.Frame(mod_frame, bg=self.PANEL)
            row.pack(fill=tk.X, padx=8, pady=1)
            dot = "●" if ok else "○"
            col = self.SUCCESS if ok else "#ff4466"
            tk.Label(row, text=dot, fg=col, bg=self.PANEL,
                     font=("Consolas", 10)).pack(side=tk.LEFT)
            tk.Label(row, text=f"  {name}", fg=self.TEXT, bg=self.PANEL,
                     font=("Consolas", 9)).pack(side=tk.LEFT)
        mod_frame.pack(fill=tk.X, pady=(0, 8))

    def _card(self, parent, title, items):
        f = tk.Frame(parent, bg=self.PANEL)
        f.pack(fill=tk.X, pady=(0, 8))
        tk.Label(f, text=f"  {title}",
                 font=("Consolas", 9, "bold"), fg=self.ACCENT,
                 bg=self.PANEL, anchor="w").pack(fill=tk.X, pady=(6, 2))
        for item in items:
            tk.Label(f, text=f"   {item}",
                     font=("Consolas", 9), fg=self.TEXT,
                     bg=self.PANEL, anchor="w").pack(fill=tk.X, padx=4)
        tk.Frame(f, bg=self.PANEL, height=6).pack()

    def _build_input_bar(self):
        bar = tk.Frame(self.root, bg=self.PANEL, height=60)
        bar.pack(fill=tk.X, padx=12, pady=(0, 12))
        bar.pack_propagate(False)

        tk.Label(bar, text="›", font=("Consolas", 18, "bold"),
                 fg=self.ACCENT, bg=self.PANEL).pack(side=tk.LEFT, padx=(12, 4), pady=10)

        self.entry = tk.Entry(bar, font=("Consolas", 12),
                              bg="#050810", fg=self.TEXT,
                              insertbackground=self.ACCENT,
                              relief=tk.FLAT, bd=0)
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=14)
        self.entry.bind("<Return>", lambda e: self._send_text())

        self.mic_btn = tk.Button(bar, text="🎤", font=("Consolas", 14),
                                 bg=self.PANEL, fg=self.ACCENT,
                                 activebackground=self.ACCENT, activeforeground=self.BG,
                                 relief=tk.FLAT, cursor="hand2",
                                 command=self._toggle_voice)
        self.mic_btn.pack(side=tk.RIGHT, padx=4, pady=8)

        tk.Button(bar, text="SEND", font=("Consolas", 10, "bold"),
                  bg=self.ACCENT2, fg="white",
                  activebackground=self.ACCENT, activeforeground=self.BG,
                  relief=tk.FLAT, cursor="hand2", padx=10,
                  command=self._send_text).pack(side=tk.RIGHT, padx=(0, 8), pady=10)

        tk.Button(bar, text="CHART", font=("Consolas", 10, "bold"),
                  bg=self.DIM, fg="white",
                  activebackground=self.ACCENT, activeforeground=self.BG,
                  relief=tk.FLAT, cursor="hand2", padx=10,
                  command=self._show_stock_chart).pack(side=tk.RIGHT, padx=(0, 4), pady=10)

    # ── Clock ─────────────────────────────────────────────────────────────────
    def _tick_clock(self):
        self.clock_label.config(
            text=datetime.datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    # ── Terminal output ───────────────────────────────────────────────────────
    def _log(self, text: str, tag: str = "jarvis"):
        self.terminal.config(state=tk.NORMAL)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.terminal.insert(tk.END, f"[{ts}] {text}\n", tag)
        self.terminal.see(tk.END)
        self.terminal.config(state=tk.DISABLED)

    # ── Startup sequence ──────────────────────────────────────────────────────
    def _startup_sequence(self):
        lines = [
            ("system", "Initialising JARVIS subsystems..."),
            ("system", "Loading NLP engine..."),
            ("system", "Calibrating voice recognition..."),
            ("system", f"Python {sys.version.split()[0]} detected."),
            ("system", "All systems nominal."),
            ("jarvis", "Good day. JARVIS is online and ready."),
            ("jarvis", "Type a command below or press 🎤 for voice input."),
            ("jarvis", "Type 'help' to see available commands."),
        ]

        def drip(i=0):
            if i < len(lines):
                tag, msg = lines[i]
                self._log(msg, tag)
                delay = 400 if tag == "system" else 600
                self.root.after(delay, drip, i + 1)
            else:
                self.brain.speak("Good day. JARVIS is online.")

        self.root.after(300, drip)

    # ── Text command ──────────────────────────────────────────────────────────
    def _send_text(self):
        cmd = self.entry.get().strip()
        if not cmd:
            return
        self.entry.delete(0, tk.END)
        self._log(f"YOU: {cmd}", "user")
        self._process(cmd)

    def _process(self, cmd: str):
        def run():
            response = self.brain.process_command(cmd)
            self.root.after(0, self._log, response, "jarvis")
            self.brain.speak(response)

        threading.Thread(target=run, daemon=True).start()

    # ── Voice input ───────────────────────────────────────────────────────────
    def _toggle_voice(self):
        if not SPEECH_AVAILABLE:
            self._log("speech_recognition not installed. Run: pip install SpeechRecognition pyaudio", "error")
            return
        if self.listening:
            self.listening = False
            self.mic_btn.config(fg=self.ACCENT, bg=self.PANEL)
            self.status_label.config(text="● ONLINE", fg=self.SUCCESS)
        else:
            self.listening = True
            self.mic_btn.config(fg=self.BG, bg=self.ACCENT)
            self.status_label.config(text="● LISTENING...", fg=self.WARN)
            threading.Thread(target=self._listen_voice, daemon=True).start()

    def _listen_voice(self):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.root.after(0, self._log, "Listening... (speak now)", "system")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
            text = self.recognizer.recognize_google(audio)
            self.root.after(0, self._log, f"YOU (voice): {text}", "user")
            self.root.after(0, self._process, text)
        except sr.WaitTimeoutError:
            self.root.after(0, self._log, "No speech detected.", "system")
        except sr.UnknownValueError:
            self.root.after(0, self._log, "Could not understand audio.", "error")
        except Exception as e:
            self.root.after(0, self._log, f"Voice error: {e}", "error")
        finally:
            self.listening = False
            self.root.after(0, self.mic_btn.config, {"fg": self.ACCENT, "bg": self.PANEL})
            self.root.after(0, self.status_label.config,
                            {"text": "● ONLINE", "fg": self.SUCCESS})

    # ── Stock chart window ────────────────────────────────────────────────────
    def _show_stock_chart(self):
        if not (MATPLOTLIB_AVAILABLE and PANDAS_AVAILABLE and ML_AVAILABLE):
            self._log("Chart requires matplotlib, pandas, numpy, scikit-learn.", "error")
            return

        import numpy as np
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import MinMaxScaler

        ticker = self.entry.get().upper().strip() or "AAPL"
        self._log(f"Generating stock prediction chart for {ticker}...", "system")

        # Synthetic 90-day data
        np.random.seed(42)
        n = 90
        days = np.arange(n)
        prices = np.linspace(100, 150, n) + np.random.normal(0, 5, n)
        df = pd.DataFrame({"day": days, "price": prices})

        X = df[["day"]].values
        y = df["price"].values
        scaler = MinMaxScaler()
        X_s = scaler.fit_transform(X)
        model = LinearRegression().fit(X_s, y)

        future = np.arange(n, n + 30).reshape(-1, 1)
        preds = model.predict(scaler.transform(future))

        win = tk.Toplevel(self.root)
        win.title(f"📈 {ticker} – Time-Series Regression")
        win.configure(bg=self.BG)
        win.geometry("860x500")

        fig, ax = plt.subplots(figsize=(8.6, 4.5))
        fig.patch.set_facecolor("#0a0e1a")
        ax.set_facecolor("#050810")
        ax.plot(days, prices, color="#00d4ff", lw=1.5, label="Historical")
        ax.plot(np.arange(n, n + 30), preds, color="#00ff88",
                lw=2, linestyle="--", label="Predicted (30 days)")
        ax.axvline(n, color="#ffaa00", lw=1, linestyle=":")
        ax.set_title(f"{ticker} Stock – Linear Regression Forecast",
                     color="white", fontsize=13)
        ax.set_xlabel("Day", color="#3a4a6a")
        ax.set_ylabel("Price (USD)", color="#3a4a6a")
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#1a2a4a")
        ax.legend(facecolor="#0f1628", edgecolor="#00d4ff", labelcolor="white")

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
