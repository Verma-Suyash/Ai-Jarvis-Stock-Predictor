"""
JARVIS v2 - Voice-Controlled AI Assistant
Features:
  - Wake word: "Hey Jarvis"
  - Stock prediction in Indian Rupees (INR)
  - Full speech responses (pyttsx3)
  - Time-series Linear Regression
  - Tkinter dark UI
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

import tkinter as tk
from tkinter import ttk, scrolledtext

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("[WARN] speech_recognition not installed. Run: pip install SpeechRecognition pyaudio")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("[WARN] pyttsx3 not installed. Run: pip install pyttsx3")

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("[WARN] pandas/numpy not installed. Run: pip install pandas numpy")

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("[WARN] matplotlib not installed. Run: pip install matplotlib")

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import MinMaxScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("[WARN] scikit-learn not installed. Run: pip install scikit-learn")

# ── USD to INR conversion rate (update as needed) ─────────────────────────────
USD_TO_INR = 83.5

# ── Indian stock base prices (approximate, in INR) ────────────────────────────
INDIAN_STOCKS = {
    # NSE / BSE Indian stocks
    "RELIANCE": 2850.0,
    "TCS":      3900.0,
    "INFY":     1500.0,
    "WIPRO":     480.0,
    "HDFC":     1650.0,
    "ICICI":     950.0,
    "SBI":       620.0,
    "LT":       3400.0,
    "HCL":      1350.0,
    "BAJAJ":    7200.0,
    "TATA":      950.0,
    "ADANI":    2400.0,
    "ITC":       430.0,
    "MARUTI":  10500.0,
    "ASIAN":    3200.0,
    # US stocks converted to INR
    "AAPL":   15000.0,   # ~$180 * 83.5
    "GOOGL":  11500.0,
    "MSFT":   27000.0,
    "TSLA":   16500.0,
    "AMZN":   15200.0,
    "META":   37000.0,
}

# ══════════════════════════════════════════════════════════════════════════════
#  TTS ENGINE  –  singleton so it doesn't reinitialise every call
# ══════════════════════════════════════════════════════════════════════════════

class TTSEngine:
    def __init__(self):
        self.engine = None
        self.lock = threading.Lock()
        self._init()

    def _init(self):
        if not TTS_AVAILABLE:
            return
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 160)
            self.engine.setProperty("volume", 1.0)
            voices = self.engine.getProperty("voices")
            # prefer a male / deeper voice
            for v in voices:
                if any(k in v.name.lower() for k in ["male", "david", "george", "mark"]):
                    self.engine.setProperty("voice", v.id)
                    break
        except Exception as e:
            print(f"[WARN] TTS init error: {e}")
            self.engine = None

    def speak(self, text: str):
        """Speak text in a thread-safe way."""
        print(f"[JARVIS SPEAKS] {text}")
        if not self.engine:
            return
        def _run():
            with self.lock:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"[WARN] TTS speak error: {e}")
        threading.Thread(target=_run, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
#  JARVIS BRAIN
# ══════════════════════════════════════════════════════════════════════════════

class JarvisBrain:
    def __init__(self, tts: TTSEngine):
        self.tts = tts

    def speak(self, text: str):
        self.tts.speak(text)

    # ── Main command dispatcher ───────────────────────────────────────────────
    def process_command(self, command: str) -> str:
        cmd = command.lower().strip()

        # Remove wake word if accidentally included
        for ww in ["hey jarvis", "jarvis"]:
            if cmd.startswith(ww):
                cmd = cmd[len(ww):].strip()

        if not cmd:
            return "Yes? How can I help you?"

        if any(w in cmd for w in ["hello", "hi", "hey", "good morning", "good evening"]):
            return self._greet()

        if "time" in cmd:
            t = datetime.datetime.now().strftime("%I:%M %p")
            return f"The current time is {t}."

        if "date" in cmd:
            d = datetime.datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {d}."

        if any(w in cmd for w in ["stock", "predict", "price", "share", "market"]):
            ticker = self._extract_ticker(cmd)
            return self._predict_stock(ticker)

        if "open" in cmd:
            return self._open_something(cmd)

        if any(w in cmd for w in ["system", "cpu", "memory", "ram"]):
            return self._system_info()

        if "weather" in cmd:
            return "Please configure a weather API key to fetch live weather data."

        if "joke" in cmd:
            return self._tell_joke()

        if any(w in cmd for w in ["help", "what can you do", "commands"]):
            return self._help()

        if any(w in cmd for w in ["search", "wikipedia", "what is", "who is"]):
            query = cmd
            for rem in ["search", "wikipedia", "what is", "who is"]:
                query = query.replace(rem, "")
            query = query.strip()
            webbrowser.open(f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}")
            return f"Opening Wikipedia for {query}."

        if any(w in cmd for w in ["bye", "goodbye", "exit", "quit", "shut down"]):
            return "Goodbye! Have a great day. Shutting down JARVIS."

        return "I didn't catch that. Say 'help' to see what I can do."

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _greet(self) -> str:
        hour = datetime.datetime.now().hour
        period = "morning" if hour < 12 else ("afternoon" if hour < 17 else "evening")
        return (f"Good {period}! I'm JARVIS, your personal AI assistant. "
                "How may I assist you today?")

    def _extract_ticker(self, cmd: str) -> str:
        """Extract stock ticker from command."""
        # Check known Indian stocks first
        cmd_upper = cmd.upper()
        for ticker in INDIAN_STOCKS:
            if ticker in cmd_upper:
                return ticker
        # Fallback: look for short uppercase-looking words
        words = cmd.upper().split()
        skip = {"STOCK", "PREDICT", "PRICE", "SHARE", "MARKET",
                "THE", "FOR", "SHOW", "ME", "GET", "OF", "IN",
                "RUPEES", "INR", "INDIAN", "TODAY"}
        for w in words:
            if w.isalpha() and 1 < len(w) <= 8 and w not in skip:
                return w
        return "RELIANCE"  # sensible Indian default

    def _predict_stock(self, ticker: str) -> str:
        if not (PANDAS_AVAILABLE and ML_AVAILABLE):
            return ("Stock prediction needs pandas, numpy, scikit-learn. "
                    "Run: pip install pandas numpy scikit-learn")

        # Base price in INR
        base_price = INDIAN_STOCKS.get(ticker.upper(), 1000.0)

        np.random.seed(42)
        n = 90
        trend = np.linspace(base_price, base_price * 1.12, n)
        noise = np.random.normal(0, base_price * 0.03, n)
        prices = trend + noise

        df = pd.DataFrame({"day": np.arange(n), "price": prices})
        X = df[["day"]].values
        y = df["price"].values

        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)
        model = LinearRegression()
        model.fit(X_scaled, y)

        future = np.arange(n, n + 7).reshape(-1, 1)
        preds = model.predict(scaler.transform(future))

        lines = [f"Stock prediction for {ticker} in Indian Rupees:"]
        for i, p in enumerate(preds, 1):
            lines.append(f"  Day +{i}: ₹{p:,.2f}")

        # Speech-friendly version (no special chars)
        speech_lines = [f"Stock prediction for {ticker}."]
        for i, p in enumerate(preds, 1):
            speech_lines.append(f"Day {i}: {p:,.0f} rupees.")

        speech_text = " ".join(speech_lines[:4])  # speak first 4 days
        self.tts.speak(speech_text)

        lines.append("  ⚠ Uses synthetic data. Install yfinance for live NSE/BSE data.")
        return "\n".join(lines)

    def _open_something(self, cmd: str) -> str:
        targets = {
            "youtube":    "https://youtube.com",
            "google":     "https://google.com",
            "github":     "https://github.com",
            "nse":        "https://nseindia.com",
            "bse":        "https://bseindia.com",
            "moneycontrol": "https://moneycontrol.com",
            "zerodha":    "https://zerodha.com",
        }
        for key, url in targets.items():
            if key in cmd:
                webbrowser.open(url)
                return f"Opening {key.capitalize()}."
        return "I'm not sure what to open. Try 'open NSE' or 'open YouTube'."

    def _system_info(self) -> str:
        info = f"Platform: {sys.platform} | Python: {sys.version.split()[0]}"
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            info += (f"\nCPU Usage: {cpu}%"
                     f"\nRAM: {ram.used // (1024**2)} MB / "
                     f"{ram.total // (1024**2)} MB")
        except ImportError:
            info += "\nInstall psutil for CPU/RAM info: pip install psutil"
        return info

    def _tell_joke(self) -> str:
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "Why did the Python programmer wear glasses? Because they couldn't C sharp.",
            "A SQL query walks into a bar and asks two tables: Can I join you?",
            "Why do Java developers wear glasses? Because they don't C sharp!",
        ]
        return random.choice(jokes)

    def _help(self) -> str:
        return (
            "JARVIS Commands:\n"
            "  • 'hey jarvis hello'              – Wake and greet\n"
            "  • 'hey jarvis what time is it'    – Current time\n"
            "  • 'hey jarvis predict RELIANCE'   – Stock in Rupees\n"
            "  • 'hey jarvis predict TCS stock'  – TCS prediction\n"
            "  • 'hey jarvis open NSE'           – Open NSE website\n"
            "  • 'hey jarvis system info'        – CPU & RAM\n"
            "  • 'hey jarvis tell me a joke'     – Joke\n"
            "  • 'hey jarvis search pandas'      – Wikipedia search\n"
            "  • 'hey jarvis goodbye'            – Shut down\n"
            "\n  Supported stocks: RELIANCE, TCS, INFY, WIPRO, HDFC,\n"
            "  ICICI, SBI, LT, HCL, BAJAJ, TATA, ADANI, ITC, MARUTI,\n"
            "  ASIAN, AAPL, GOOGL, MSFT, TSLA, AMZN, META"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  WAKE WORD LISTENER  –  runs in background thread
# ══════════════════════════════════════════════════════════════════════════════

class WakeWordListener:
    WAKE_PHRASES = ["hey jarvis", "hey travis", "a jarvis", "jarvis"]  # fuzzy matches

    def __init__(self, on_wake_callback, on_command_callback, tts: TTSEngine):
        self.on_wake = on_wake_callback
        self.on_command = on_command_callback
        self.tts = tts
        self.recognizer = sr.Recognizer() if SPEECH_AVAILABLE else None
        self.running = False
        self._thread = None

    def start(self):
        if not SPEECH_AVAILABLE:
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _loop(self):
        """Continuously listen for wake word, then capture command."""
        while self.running:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)
                text = self.recognizer.recognize_google(audio).lower()

                # Check for wake word
                if any(phrase in text for phrase in self.WAKE_PHRASES):
                    self.on_wake()
                    self.tts.speak("Yes, I'm listening.")

                    # Now listen for the actual command
                    with sr.Microphone() as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                        audio2 = self.recognizer.listen(source, timeout=6, phrase_time_limit=10)
                    command = self.recognizer.recognize_google(audio2)
                    self.on_command(command)

            except sr.WaitTimeoutError:
                pass  # silence, keep looping
            except sr.UnknownValueError:
                pass  # couldn't understand
            except Exception as e:
                if self.running:
                    print(f"[Wake listener error] {e}")
                time.sleep(1)


# ══════════════════════════════════════════════════════════════════════════════
#  JARVIS GUI
# ══════════════════════════════════════════════════════════════════════════════

class JarvisGUI:
    BG      = "#0a0e1a"
    PANEL   = "#0f1628"
    ACCENT  = "#00d4ff"
    ACCENT2 = "#0055cc"
    TEXT    = "#e0f0ff"
    DIM     = "#3a4a6a"
    SUCCESS = "#00ff88"
    WARN    = "#ffaa00"
    ERROR   = "#ff4466"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.tts = TTSEngine()
        self.brain = JarvisBrain(self.tts)
        self.wake_listener = None
        self.recognizer = sr.Recognizer() if SPEECH_AVAILABLE else None
        self.manual_listening = False
        self._build_ui()
        self._start_wake_listener()
        self._startup_sequence()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.root.title("J.A.R.V.I.S  —  AI Desktop Assistant")
        self.root.geometry("1120x740")
        self.root.configure(bg=self.BG)
        self.root.resizable(True, True)
        self._build_header()
        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self._build_terminal(main)
        self._build_side_panel(main)
        self._build_input_bar()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=self.PANEL, height=72)
        hdr.pack(fill=tk.X, padx=12, pady=(12, 8))
        hdr.pack_propagate(False)

        tk.Label(hdr, text="J.A.R.V.I.S", font=("Consolas", 22, "bold"),
                 fg=self.ACCENT, bg=self.PANEL).pack(side=tk.LEFT, padx=18, pady=10)

        tk.Label(hdr,
                 text="Just A Rather Very Intelligent System  |  Say  \"Hey Jarvis\"  to wake",
                 font=("Consolas", 9), fg=self.DIM, bg=self.PANEL
                 ).pack(side=tk.LEFT, pady=14)

        self.status_label = tk.Label(hdr, text="● STANDBY", font=("Consolas", 10, "bold"),
                                     fg=self.WARN, bg=self.PANEL)
        self.status_label.pack(side=tk.RIGHT, padx=18)

        self.clock_label = tk.Label(hdr, text="", font=("Consolas", 13),
                                    fg=self.ACCENT, bg=self.PANEL)
        self.clock_label.pack(side=tk.RIGHT, padx=10)
        self._tick_clock()

    def _build_terminal(self, parent):
        frame = tk.Frame(parent, bg=self.PANEL,
                         highlightbackground=self.DIM, highlightthickness=1)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        tk.Label(frame, text="  ▸ TERMINAL OUTPUT",
                 font=("Consolas", 9, "bold"), fg=self.ACCENT,
                 bg=self.PANEL, anchor="w").pack(fill=tk.X, pady=(6, 0))

        self.terminal = scrolledtext.ScrolledText(
            frame, font=("Consolas", 11), bg="#050810", fg=self.TEXT,
            insertbackground=self.ACCENT, relief=tk.FLAT, bd=0,
            selectbackground=self.ACCENT2, wrap=tk.WORD, state=tk.DISABLED
        )
        self.terminal.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.terminal.tag_config("jarvis", foreground=self.ACCENT)
        self.terminal.tag_config("user",   foreground=self.SUCCESS)
        self.terminal.tag_config("system", foreground=self.WARN)
        self.terminal.tag_config("wake",   foreground="#ff88ff")
        self.terminal.tag_config("error",  foreground=self.ERROR)

    def _build_side_panel(self, parent):
        side = tk.Frame(parent, bg=self.BG, width=290)
        side.pack(side=tk.RIGHT, fill=tk.Y)
        side.pack_propagate(False)

        self._card(side, "HOW TO USE",
                   ['1. Say "Hey Jarvis" to wake',
                    "2. Wait for 'I'm listening'",
                    "3. Speak your command",
                    "   OR type below & press Enter"])

        self._card(side, "STOCK COMMANDS",
                   ["• predict RELIANCE",
                    "• predict TCS stock",
                    "• INFY share price",
                    "• predict WIPRO",
                    "• HDFC stock price",
                    "  → All in ₹ Rupees"])

        self._card(side, "SUPPORTED STOCKS",
                   ["Indian: RELIANCE  TCS  INFY",
                    "        WIPRO  HDFC  ICICI",
                    "        SBI  LT  HCL  BAJAJ",
                    "        TATA  ADANI  ITC",
                    "        MARUTI  ASIAN",
                    "US→INR: AAPL  GOOGL  MSFT",
                    "        TSLA  AMZN  META"])

        # Module status
        mod = tk.Frame(side, bg=self.PANEL)
        mod.pack(fill=tk.X, pady=(0, 8))
        tk.Label(mod, text="  MODULE STATUS",
                 font=("Consolas", 9, "bold"), fg=self.ACCENT,
                 bg=self.PANEL, anchor="w").pack(fill=tk.X, pady=(6, 2))
        modules = [
            ("Wake Word",      SPEECH_AVAILABLE),
            ("Speech Input",   SPEECH_AVAILABLE),
            ("Voice Output",   TTS_AVAILABLE),
            ("Stock / Pandas", PANDAS_AVAILABLE),
            ("Chart",          MATPLOTLIB_AVAILABLE),
            ("Regression",     ML_AVAILABLE),
        ]
        for name, ok in modules:
            row = tk.Frame(mod, bg=self.PANEL)
            row.pack(fill=tk.X, padx=8, pady=1)
            tk.Label(row, text="●" if ok else "○",
                     fg=self.SUCCESS if ok else self.ERROR,
                     bg=self.PANEL, font=("Consolas", 10)).pack(side=tk.LEFT)
            tk.Label(row, text=f"  {name}", fg=self.TEXT,
                     bg=self.PANEL, font=("Consolas", 9)).pack(side=tk.LEFT)
        tk.Frame(mod, bg=self.PANEL, height=6).pack()

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
        bar = tk.Frame(self.root, bg=self.PANEL, height=62)
        bar.pack(fill=tk.X, padx=12, pady=(0, 12))
        bar.pack_propagate(False)

        tk.Label(bar, text="›", font=("Consolas", 18, "bold"),
                 fg=self.ACCENT, bg=self.PANEL).pack(side=tk.LEFT, padx=(12, 4))

        self.entry = tk.Entry(bar, font=("Consolas", 12),
                              bg="#050810", fg=self.TEXT,
                              insertbackground=self.ACCENT, relief=tk.FLAT, bd=0)
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=14)
        self.entry.bind("<Return>", lambda e: self._send_text())
        self.entry.insert(0, "Type a command or say 'Hey Jarvis'...")
        self.entry.bind("<FocusIn>",  lambda e: self._clear_placeholder())
        self.entry.bind("<FocusOut>", lambda e: self._restore_placeholder())

        self.mic_btn = tk.Button(
            bar, text="🎤", font=("Consolas", 14),
            bg=self.PANEL, fg=self.ACCENT,
            activebackground=self.ACCENT, activeforeground=self.BG,
            relief=tk.FLAT, cursor="hand2", command=self._manual_mic)
        self.mic_btn.pack(side=tk.RIGHT, padx=4, pady=8)

        tk.Button(bar, text="SEND", font=("Consolas", 10, "bold"),
                  bg=self.ACCENT2, fg="white",
                  activebackground=self.ACCENT, activeforeground=self.BG,
                  relief=tk.FLAT, cursor="hand2", padx=12,
                  command=self._send_text).pack(side=tk.RIGHT, padx=(0, 8), pady=10)

        tk.Button(bar, text="📈 CHART", font=("Consolas", 10, "bold"),
                  bg=self.DIM, fg="white",
                  activebackground=self.ACCENT, activeforeground=self.BG,
                  relief=tk.FLAT, cursor="hand2", padx=10,
                  command=self._show_chart).pack(side=tk.RIGHT, padx=(0, 4), pady=10)

    # ── Placeholder helpers ───────────────────────────────────────────────────
    def _clear_placeholder(self):
        if self.entry.get() == "Type a command or say 'Hey Jarvis'...":
            self.entry.delete(0, tk.END)

    def _restore_placeholder(self):
        if not self.entry.get():
            self.entry.insert(0, "Type a command or say 'Hey Jarvis'...")

    # ── Clock ─────────────────────────────────────────────────────────────────
    def _tick_clock(self):
        self.clock_label.config(text=datetime.datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    # ── Terminal logger ───────────────────────────────────────────────────────
    def _log(self, text: str, tag: str = "jarvis"):
        self.terminal.config(state=tk.NORMAL)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.terminal.insert(tk.END, f"[{ts}] {text}\n", tag)
        self.terminal.see(tk.END)
        self.terminal.config(state=tk.DISABLED)

    # ── Startup ───────────────────────────────────────────────────────────────
    def _startup_sequence(self):
        lines = [
            ("system", "Initialising JARVIS subsystems..."),
            ("system", "Loading NLP engine..."),
            ("system", "Loading stock database (INR)..."),
            ("system", f"Python {sys.version.split()[0]} detected."),
            ("system", "All systems nominal."),
            ("jarvis", "Good day. JARVIS is online."),
            ("jarvis", 'Say "Hey Jarvis" to wake me, or type below.'),
            ("jarvis", "Try: 'Hey Jarvis, predict RELIANCE stock'"),
        ]

        def drip(i=0):
            if i < len(lines):
                tag, msg = lines[i]
                self._log(msg, tag)
                self.root.after(450 if tag == "system" else 650, drip, i + 1)
            else:
                self._set_status("● LISTENING FOR WAKE WORD", self.SUCCESS)
                self.tts.speak("Good day. I am JARVIS. Say Hey Jarvis to wake me.")

        self.root.after(300, drip)

    # ── Wake word listener ────────────────────────────────────────────────────
    def _start_wake_listener(self):
        if not SPEECH_AVAILABLE:
            return
        self.wake_listener = WakeWordListener(
            on_wake_callback=self._on_wake,
            on_command_callback=self._on_voice_command,
            tts=self.tts
        )
        self.wake_listener.start()

    def _on_wake(self):
        self.root.after(0, self._log, '🔔 Wake word detected: "Hey Jarvis"', "wake")
        self.root.after(0, self._set_status, "● LISTENING...", self.WARN)

    def _on_voice_command(self, command: str):
        self.root.after(0, self._log, f"YOU (voice): {command}", "user")
        self.root.after(0, self._set_status, "● PROCESSING...", self.ACCENT)
        self.root.after(0, self._process, command)

    # ── Manual mic button ─────────────────────────────────────────────────────
    def _manual_mic(self):
        if not SPEECH_AVAILABLE:
            self._log("SpeechRecognition not installed.", "error")
            return
        if self.manual_listening:
            return
        self.manual_listening = True
        self.mic_btn.config(fg=self.BG, bg=self.ACCENT)
        self._set_status("● LISTENING...", self.WARN)

        def listen():
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                    self.root.after(0, self._log, "Listening... speak now", "system")
                    audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio)
                self.root.after(0, self._log, f"YOU (voice): {text}", "user")
                self.root.after(0, self._process, text)
            except sr.WaitTimeoutError:
                self.root.after(0, self._log, "No speech detected.", "system")
            except sr.UnknownValueError:
                self.root.after(0, self._log, "Could not understand. Please try again.", "error")
            except Exception as e:
                self.root.after(0, self._log, f"Mic error: {e}", "error")
            finally:
                self.manual_listening = False
                self.root.after(0, self.mic_btn.config,
                                {"fg": self.ACCENT, "bg": self.PANEL})
                self.root.after(0, self._set_status,
                                "● LISTENING FOR WAKE WORD", self.SUCCESS)

        threading.Thread(target=listen, daemon=True).start()

    # ── Text command ──────────────────────────────────────────────────────────
    def _send_text(self):
        cmd = self.entry.get().strip()
        if not cmd or cmd == "Type a command or say 'Hey Jarvis'...":
            return
        self.entry.delete(0, tk.END)
        self._log(f"YOU: {cmd}", "user")
        self._process(cmd)

    # ── Process & respond ─────────────────────────────────────────────────────
    def _process(self, cmd: str):
        def run():
            response = self.brain.process_command(cmd)
            self.root.after(0, self._log, response, "jarvis")
            self.root.after(0, self._set_status,
                            "● LISTENING FOR WAKE WORD", self.SUCCESS)
            # Speak — but only if the stock method hasn't already spoken
            if not any(w in cmd.lower() for w in ["stock", "predict", "price", "share"]):
                self.tts.speak(response)
            # Check for shutdown
            if any(w in cmd.lower() for w in ["bye", "goodbye", "exit", "quit", "shut down"]):
                self.root.after(2500, self.root.destroy)

        threading.Thread(target=run, daemon=True).start()

    def _set_status(self, text: str, color: str):
        self.status_label.config(text=text, fg=color)

    # ── Stock Chart ───────────────────────────────────────────────────────────
    def _show_chart(self):
        if not (MATPLOTLIB_AVAILABLE and PANDAS_AVAILABLE and ML_AVAILABLE):
            self._log("Chart requires matplotlib, pandas, scikit-learn.", "error")
            return

        raw = self.entry.get().upper().strip()
        ticker = raw if raw in INDIAN_STOCKS else "RELIANCE"
        base_price = INDIAN_STOCKS.get(ticker, 1000.0)

        self._log(f"Generating chart for {ticker} (₹)...", "system")

        np.random.seed(42)
        n = 90
        prices = np.linspace(base_price, base_price * 1.12, n) + \
                 np.random.normal(0, base_price * 0.03, n)

        X = np.arange(n).reshape(-1, 1)
        scaler = MinMaxScaler()
        X_s = scaler.fit_transform(X)
        model = LinearRegression().fit(X_s, prices)

        future = np.arange(n, n + 30).reshape(-1, 1)
        preds = model.predict(scaler.transform(future))

        win = tk.Toplevel(self.root)
        win.title(f"📈 {ticker} — Stock Forecast (₹ INR)")
        win.configure(bg=self.BG)
        win.geometry("880x500")

        fig, ax = plt.subplots(figsize=(8.8, 4.6))
        fig.patch.set_facecolor("#0a0e1a")
        ax.set_facecolor("#050810")
        ax.plot(np.arange(n), prices, color="#00d4ff", lw=1.5, label="Historical (90 days)")
        ax.plot(np.arange(n, n + 30), preds, color="#00ff88",
                lw=2, linestyle="--", label="Forecast (30 days)")
        ax.axvline(n, color="#ffaa00", lw=1, linestyle=":", alpha=0.7)
        ax.set_title(f"{ticker}  —  Linear Regression Forecast  |  Prices in ₹ INR",
                     color="white", fontsize=12, pad=12)
        ax.set_xlabel("Day", color="#3a4a6a", fontsize=10)
        ax.set_ylabel("Price (₹ INR)", color="#3a4a6a", fontsize=10)
        ax.tick_params(colors="white")
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f"₹{x:,.0f}"))
        for spine in ax.spines.values():
            spine.set_edgecolor("#1a2a4a")
        ax.legend(facecolor="#0f1628", edgecolor="#00d4ff", labelcolor="white")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.tts.speak(f"Here is the 30-day forecast chart for {ticker}.")


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
