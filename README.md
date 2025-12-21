# Desktop-screen-pen
A tool that allows users to draw anywhere on the screen.

<p>
  <img src="./image/showcase/showcase.gif" width="850">
</p>

<br>

## 🛠️ Why I Built This
- I often need to jot down notes, highlight ideas, or illustrate concepts directly on my desktop.
- Being able to turn my computer into a simple **“blackboard”** whenever I need it is super handy.
- I’m also using this project as a chance to get better at building desktop apps with **PySide2 / Qt**.

<br>

## 🧩 Features
- ✏️ **Free Drawing** – Draw anywhere on your screen with smooth strokes
- &nbsp;█&nbsp; **Eraser Tools** – Normal eraser + rectangular crop eraser
- 🎨 **Brush Controls** – Change size, shape, and 7 colors instantly
- ↩️ **Undo / Redo** – Full history tracking for every stroke
- 🖼️ **Screenshot Export** – Save with black or transparent background
- 🧰 **Floating Toolbar** – Quick access to all tools in one place

<br>

## 📂 Project Structure  
```
Desktop pen/
│── image/
│   ├── toolbar/       # toolbar icon
│   └── showcase/      # Demonstration gif
│── main.py
│── window.py
│── toolbar.py
│── controller.py
│── canva.py
├── LICENSE            # MIT license
└── README.md          # Project documentation
```

<br>

## 🔗 Dependencies
This project uses **PySide2 (Qt for Python)** for the GUI and **mss** for screen capture.

<br>

## ⚙️ Requirements
Install dependencies before running:
```bash
pip install PySide2 mss
```

<br>


## ▶️ How to Run
1. Clone & run:
```bash
git clone https://github.com/Benjikuo/Desktop-screen-pen.git
python main.py
```
2. Draw on the screen with a floating toolbar at the top for all drawing controls.

<br>

## 💻 Keyboard and Mouse Controls
### [Keyboard]
**Mode Toggles:**
| Key | Action | Mode |
|-----|--------|-------------|
| `1`       | Toggle the **board**       | transparent / black |
| `2` , `Z` | Toggle the **tool**        | pen / highlight / eraser / crop eraser |
| `3`       | Toggle the **stroke size** | 4px / 6px / 10px / 14px / 20px / 30px / 50px |
| `4` , `X` | Toggle the **shape**       | free pen / line / rectangle |
| `5` , `C` | Toggle the **color**       | ⬜white / 🟥red / 🟧orange / 🟨yellow / 🟩green / 🟦blue / 🟪purple |

*(**+Shift**: toggles in the opposite direction)*

<br>

**Direct Actions:**
| Key | Action | Description |
|-----|--------|-------------|
| `6` , `S` or `Ctrl + S`         | Save  | Save with current background |
| `7` , `D` or `Ctrl + Z`         | Undo  | Undo the last change |
| `8` , `F` or `Ctrl + Y`         | Redo  | Redo the last change |
| `9` , `A` or `Ctrl + X`         | Clear | Clear all strokes |
| `0` , `Q` , `Ctrl + R` or `Esc` | Quit  | Quit the program |

<br>

**✨ Quick Mode Toggles:**
| Key | Action | Description |
|-----|--------|-------------| 
| `W` | Toggle mode   | Cycle through **transparent / black / view mode** |
| `E` | Toggle eraser | Press again to switch to **crop-eraser** |
| `R` | Toggle pen    | Press again to switch to **highlighter** |

*(**+Shift**: toggles in the opposite direction)*

<br>

**✏️ Tool Shortcuts:**
| Key | Tool |
|-----|------|
| `Space` | ⚪ White pen |
| `T`     | 🔴 Red pen |
| `Y`     | 🟠 Orange pen |
| `G`     | 🟡 Yellow pen |
| `H`     | 🟢 Green pen |
| `B`     | 🔵 Blue pen |
| `N`     | 🟣 Purple pen |
| `V`     | 🟥 Red square outline tool |

---

### [Mouse]
| button \ item | Canva | Toolbar | Button |
|---------------|-------|---------|--------|
| left click   | Draw              | Set **drawing** mode | Select the tools  |
| middle click | Close the program | Close the program    | Close the program |
| right click  | Set **view** mode | Set **view** mode    | Set **view** mode |

The **mouse wheel** up and down can control the **brush size**.

<br>

## 📜 License
Released under the **MIT License**.  
You are free to use, modify, and share it for learning or personal projects.

**Draw anything you can imagine!**
