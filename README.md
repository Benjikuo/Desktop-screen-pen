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

## ⚙️ Requirements
Install dependencies before running:
```bash
pip install PySide2
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
| `1` | Toggle the **background**  | transparent / black |
| `2` | Toggle the **tool**        | pen / highlight / eraser / crop eraser |
| `3` | Toggle the **stroke size** | 4px / 6px / 10px / 14px / 20px / 30px / 50px |
| `4` | Toggle the **shape**       | free pen / line / rectangle |
| `5` | Toggle the **color**       | ⬜white / 🟥red / 🟧orange / 🟨yellow / 🟩green / 🟦blue / 🟪purple |

*(**+Shift**: toggles in the opposite direction)*

<br>

**Direct Actions:**
| Key | Action | Description |
|-----|--------|-------------|
| `6` | Save  | Save with current background |
| `7` | Undo  | Undo the last change |
| `8` | Redo  | Redo the last change |
| `9` | Clear | Clear all strokes |
| `0` | Quit  | Quit the program |

<br>

**✨ Quick Mode Toggles:**
| Key | Action | Description |
|-----|--------|-------------| 
| `W` | Toggle drawing mode | Cycle through **transparent / black / view mode** |
| `E` | Toggle eraser       | Press again to switch to **crop-eraser** |
| `R` | Toggle pen          | Press again to switch to **highlighter** |
| `Z` | Toggle tool         | Same as key `2` |
| `X` | Toggle shape        | Same as key `4` |
| `C` | Toggle color        | Same as key `5` |

*(**+Shift**: toggles in the opposite direction)*
 
<br>

**✨ Quick Actions:**
| Key | Action | Description |
|-----|--------|-------------|
| `Ctrl + S` or `S`   | Save board   | Same as key `6` |
| `Ctrl + Z` or `D`   | Undo         | Undo but skips “clear” in history |
| `Ctrl + Y` or `F`   | Redo         | Redo but skips “clear” in history |
| `Ctrl + R` or `Esc` | Quit program | Same as key `0` |

<br>

**✏️ Tool Shortcuts:**
| Key | Tool |
|-----|------|
| `T` | 🟡 Yellow pen |
| `G` | 🔴 Red pen |
| `B` | 🔵 Blue pen |
| `V` | 🟥 Red rectangle pen |

---

### [Mouse]
| button \ item | Canva | Toolbar | Button |
|---------------|-------|---------|--------|
| left click   | Draw              | Set draw mode     | Change drawing control |
| middle click | Close the program | Close the program | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-- |
| right click  | Set view mode     | Set white pen     | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-- |

<br>

## 📜 License
This project is released under the **MIT License**.  
You are free to use, modify, and share it for learning or personal projects.

**Draw anything you can imagine!**
