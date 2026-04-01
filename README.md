# 🛰 SPACE SWITCH DASHBOARD
### Maya 2023+ // NOISE.SYS Extension

> **Animator-focused space switching without the gimbal lock headache.**
> Three-stage workflow, auto rotation-order detection, world/aim/object space, baking tools.
> Includes a standalone web prototype for previewing setups before opening Maya.

![SPACE SWITCH DASHBOARD — NOISE.SYS](https://raw.githubusercontent.com/akamrt/NOISE.SYS/main/demo.gif)

---

## ✨ Features

| | |
|---|
| 🌍 **World / Aim / Object Space** — Switch parent space with clean world-space results |
| 🎯 **Anti-Gimbal Lock** — Auto analyses rotation range and picks the safest rotation order |
| 📐 **Three-Stage Workflow** — CREATE → BAKE → REBUILD keeps your hierarchy intact |
| 🔧 **No Expressions** — Pure constraint + keyframe approach, fast and portable |
| 🏗️ **Locator Stack** — Build up a stack of spaces to switch between at runtime |
| 🕹️ **Web Prototype** — Preview the UI and workflow before opening Maya |
| 🎛️ **Dockable Window** — Drops into Maya's channel box / credential area |

---

## 📦 Compatibility

| Maya Version | Status |
|---|---|
| 2023 | ✅ |
| 2024 | ✅ |
| 2025 | ✅ |

---

## 🚀 Install

### Maya Script Editor (fastest)
1. Copy `space_switch_ui.py` into your Maya scripts folder:
   ```
   ~/Documents/maya/scripts/
   ```
2. In Maya Script Editor (Python tab):
   ```python
   import space_switch_ui
   space_switch_ui.launch()
   ```

### Shelf Button
1. Save as Python file above
2. Maya: `Windows → General Editors → Script Editor`
3. Run the import line above
4. Right-click shelf → `Add New Item → Python`
5. Paste: `import space_switch_ui; space_switch_ui.launch()`

---

## 🔄 Three-Stage Workflow

```
┌─────────────────────────────────────────────────────┐
│  CREATE  →  Build locator hierarchy from current    │
│             frame. No constraints yet — just clean   │
│             world-space reference positions.         │
├─────────────────────────────────────────────────────┤
│  BAKE    →  Bake source animation to locators       │
│             with Euler filter. Sets up temp         │
│             constraints for clean world-space keys.  │
├─────────────────────────────────────────────────────┤
│  REBUILD →  Delete source constraints.               │
│             Apply new parent constraints to          │
│             the original object using baked keys.    │
└─────────────────────────────────────────────────────┘
```

---

## 🎛️ Space Modes

| Mode | What it does |
|---|---|
| `WORLD` | World-space follow — parent constraint to world |
| `OBJECT` | Object-space follow — parent constraint to target |
| `AIM` | Aim at target, up-vector locked to world Y |
| `CAMERA` | Object-space follow using a camera as reference |

---

## 🛰️ Web Prototype

Open `index.html` in any browser for a standalone preview of the dashboard UI.

**Features:** locator stack editor, mode selector, stage runner, baking options, simulated 3D viewport.

---

## 📁 File Structure

```
Space-Switch/
├── space_switch_ui.py          # Main Maya dashboard (1535 lines)
├── space_switch_world_space.py  # World-space companion script
├── SpaceSwitch_AimSpace.mel   # MEL aim-space script (Richard Lico)
├── SpaceSwitch_WorldSpace.mel  # MEL world-space script (Richard Lico)
├── index.html                  # Standalone web prototype
└── README.md
```

---

## 🙏 Credits

Nathan Thompson — [@akamrt](https://github.com/akamrt)
NOISE.SYS Extension Series — [github.com/akamrt/NOISE.SYS](https://github.com/akamrt/NOISE.SYS)

MEL components by Richard Lico — [Animation Sherpa](https://animationsherpa.com)
