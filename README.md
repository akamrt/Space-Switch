# ⬡ SPACE SWITCH

### Animator-Focused Maya Space Switching Dashboard

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   ██████╗ ██╗     ██╗████████╗ ██████╗██╗  ██╗               │
│  ██╔════╝ ██║     ██║╚══██╔══╝██╔════╝██║  ██║               │
│  ██║  ███╗██║     ██║   ██║   ██║     ███████║               │
│  ██║   ██║██║     ██║   ██║   ██║     ██╔══██║               │
│  ╚██████╔╝███████╗██║   ██║   ╚██████╗██║  ██║               │
│   ╚═════╝ ╚══════╝╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝               │
│                                                              │
│      SPACE  SWITCHING  MADE  FOR  ANIMATORS                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

> **No more gimbal lock. No broken hierarchies. Just clean space switches.**

---

## ✨ Features

| | |
|---|---|
| 🔄 **Multi-Mode Switching** | Switch between World, Parent, Aim, and Custom Locator spaces |
| 🛡️ **Anti-Gimbal Lock** | Quaternion interpolation + auto rotation order detection |
| 📍 **Locator-Based Parenting** | Switch parent spaces without breaking your rig hierarchy |
| 🎬 **Bake to Keyframes** | Full bake with transform cleanup and hierarchy preservation |
| 🎯 **Aim Space Support** | MEL-powered aim constraint space switching |
| ⚡ **Fast Iteration** | Auto-reload on re-run — edit and iterate in seconds |
| 🎨 **Color-Coded Locators** | 8-color Maya override palette for visual clarity |

---

## 📋 Compatibility

| Maya Version | Status |
|---|---|
| Maya 2023 | ✅ Supported |
| Maya 2024 | ✅ Supported |
| Maya 2025 | ✅ Supported |

---

## 🚀 Installation

### Option 1 — Drag & Drop (Easiest)
1. Open Maya
2. Open **Script Editor** → **Python** tab
3. Open `space_switch_ui.py` in a text editor
4. Copy the entire file contents
5. Paste into Maya Script Editor Python tab
6. Click **Ctrl+Enter** (or the play button) to run

### Option 2 — Shelf Button
1. Save `space_switch_ui.py` to a permanent location:
   ```
   ~/maya/scripts/space_switch_ui.py
   ```
2. In Maya Script Editor, run:
   ```python
   import space_switch_ui
   ```
   Or add a shelf button with:
   ```mel
   python("import space_switch_ui");
   ```

### Option 3 — UserSetup (Permanent Install)
1. Create/edit your `userSetup.py` (Maya scripts directory):
   ```python
   # ~/maya/<version>/scripts/userSetup.py
   import maya.utils
   def startup():
       import space_switch_ui
   maya.utils.executeDeferred(startup)
   ```

---

## 📖 Usage — Three-Stage Workflow

The dashboard uses a **Create → Bake → Rebuild** pipeline:

### Stage 1 — CREATE
1. Select the objects you want to space-switch
2. Click **CREATE LOCATORS**
3. Choose your space mode:
   - 🌍 **World** — switch to world origin
   - 👪 **Parent** — switch to direct parent
   - 🎯 **Aim** — switch using aim constraint
   - 📍 **Locator** — switch to custom locator
4. Locators are created at the current frame with matching transforms

### Stage 2 — BAKE
1. Click **BAKE** with the same selected objects
2. Set your frame range (Start / End)
3. Animation is baked to the locator hierarchy
4. Unused locators cleaned up automatically

### Stage 3 — REBUILD
1. Click **REBUILD** to re-apply constraints
2. Original objects now switch between spaces via constraints
3. Hierarchy stays intact — no broken rigs

### Anti-Gimbal Lock
- **Auto Rotation Order** — automatically detects the best rotation order for your animation range
- **Quaternion Interpolation** — no more flipping at 90° angles
- Toggle manually in the dashboard if needed

---

## 📁 File Structure

```
Space-Switch/
├── space_switch_ui.py            # Main dashboard UI + core logic (Python)
├── space_switch_world_space.py    # World space companion script (Python)
├── SpaceSwitch_AimSpace.mel      # MEL aim constraint space switcher
├── SpaceSwitch_WorldSpace.mel     # MEL world space helper
└── README.md                      # This file
```

### File Descriptions

| File | Lines | Purpose |
|---|---|---|
| `space_switch_ui.py` | ~1200 | Main dashboard — full UI + SpaceSwitch class with gimbal protection |
| `space_switch_world_space.py` | ~150 | World-space switching companion |
| `SpaceSwitch_AimSpace.mel` | ~193 | MEL script — aim constraint space switching |
| `SpaceSwitch_WorldSpace.mel` | ~81 | MEL script — world space helper commands |

---

## 🧩 How It Works

```
Original Object          Locator Stack           Target Space
────────────────        ────────────────        ─────────────
  rig_ctrl ────────────► [locator_1] ──────────► world
                        [locator_2] ──────────► parent
                        [locator_3] ──────────► aim
                        [locator_N] ──────────► custom locator
```

- **Constraints** drive the relationship — no direct parenting
- **Color-coded locators** keep the outliner readable
- **Quaternion math** ensures smooth interpolation through gimbal-prone angles

---

## ⚠️ Tips

- **Save your scene** before baking — always
- Use **Locator mode** for the most flexibility
- The dashboard is **dockable** — drag it to any panel
- **Auto-reload** is enabled — re-paste the script to update without restarting Maya
- For complex shots, try baking **per character** rather than the whole scene

---

## 🤝 Credits

Built for animators, by animators.
Tested at Framestore on production rigs.

---

```
MIT License — use it, break it, improve it.
```
