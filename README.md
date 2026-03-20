# 🤖 J.A.R.V.I.S — AI Desktop Assistant
### Voice-Controlled | Stock Prediction | Time-Series Regression | Python

---

## 📁 Project Structure

```
jarvis_project/
├── jarvis.py           ← Main application (run this)
├── requirements.txt    ← All Python dependencies
└── README.md           ← This file
```

---

## 🛠 STEP-BY-STEP SETUP (Beginner Friendly)

### STEP 1 — Install Python
- Download Python 3.10 or newer from: https://python.org/downloads
- During install, ✅ CHECK "Add Python to PATH"
- Verify: open a terminal and type `python --version`

---

### STEP 2 — Install VS Code
- Download from: https://code.visualstudio.com
- Install the **Python extension** (search "Python" in Extensions sidebar)

---

### STEP 3 — Open the Project in VS Code
1. Open VS Code
2. Click **File → Open Folder**
3. Select the `jarvis_project` folder

---

### STEP 4 — Open the Terminal in VS Code
- Press **Ctrl + ` ** (backtick key, top-left of keyboard)
- A terminal panel appears at the bottom

---

### STEP 5 — Install Dependencies

**Windows:**
```bash
pip install -r requirements.txt
```

**Mac / Linux:**
```bash
pip3 install -r requirements.txt
```

> ⚠️ If `pyaudio` fails on Windows, run:
> ```
> pip install pipwin
> pipwin install pyaudio
> ```
>
> On Mac:
> ```
> brew install portaudio
> pip install pyaudio
> ```

---

### STEP 6 — Run JARVIS

```bash
python jarvis.py
```

The JARVIS window will open! 🎉

---

## 🎮 How to Use JARVIS

| Command | What it does |
|---|---|
| `hello` | JARVIS greets you |
| `what time is it` | Tells current time |
| `what is today's date` | Tells current date |
| `predict AAPL stock` | Runs stock regression model |
| `open YouTube` | Opens YouTube in browser |
| `open Google` | Opens Google |
| `system info` | Shows CPU & RAM usage |
| `tell me a joke` | JARVIS tells a joke |
| `search machine learning` | Opens Wikipedia |
| `help` | Lists all commands |

### 🎤 Voice Input
- Click the **🎤 microphone button**
- Speak your command clearly
- JARVIS will respond by voice AND show it in the terminal

### 📈 Stock Chart
- Type a ticker (e.g. `AAPL`) in the input box
- Click **CHART** button
- See a 30-day regression forecast chart

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Voice not working | Check microphone is connected & allowed |
| `pyaudio` install fails | See Step 5 special instructions above |
| Chart not showing | Run `pip install matplotlib` |
| `python` command not found | Use `python3` instead |

---

## 📦 Tech Stack (from the assignment)

| Technology | Purpose |
|---|---|
| Python 3.x | Core language |
| Pandas | Time-series data handling |
| NumPy | Numerical computation |
| Seaborn + Matplotlib | Data visualisation |
| scikit-learn | Linear Regression model |
| SpeechRecognition | Voice input |
| pyttsx3 | Text-to-speech output |
| Tkinter | Desktop GUI |

---

## 🚀 Optional: Real Stock Data

Uncomment `yfinance` in requirements.txt, install it, then replace the synthetic data section in `jarvis.py` with:

```python
import yfinance as yf
df = yf.download(ticker, period="3mo", interval="1d")
df["day"] = range(len(df))
df["price"] = df["Close"]
```

---

*Project: SIC/AI/002 — Voice-Controlled Assistant (Jarvis Style)*
*Predicts stock prices using time-series data analysis.*
*Methods: Time-series prep + Regression*
