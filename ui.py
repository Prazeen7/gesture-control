"""Desktop presentation for the gesture controller."""
import tkinter as tk
from tkinter import ttk

BG = '#eef3f7'
CARD = '#ffffff'
INK = '#182b3a'
MUTED = '#607386'
ACCENT = '#087f8c'


def build(app, settings):
    root = app.root
    root.title('Gesture Control')
    root.geometry(f'940x{min(820, root.winfo_screenheight() - 90)}')
    root.minsize(780, 620)
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', font=('Segoe UI', 10), background=BG, foreground=INK)
    style.configure('TFrame', background=BG)
    style.configure('TLabel', background=BG)
    style.configure('Muted.TLabel', foreground=MUTED)
    style.configure('Title.TLabel', font=('Segoe UI', 25, 'bold'))
    style.configure('Heading.TLabel', font=('Segoe UI', 12, 'bold'))
    style.configure('TButton', padding=(14, 10), background='#e0e9ef', borderwidth=0)
    style.map('TButton', background=[('active', '#cbdce6')])
    style.configure('Accent.TButton', background=ACCENT, foreground='white')
    style.map('Accent.TButton', background=[('active', '#066773')])
    style.configure('Pages.TNotebook', borderwidth=0, tabmargins=0)
    style.layout('Pages.TNotebook.Tab', [])
    style.configure('Card.TFrame', background=CARD)
    style.configure('Card.TLabel', background=CARD)
    style.configure('CardTitle.TLabel', background=CARD, font=('Segoe UI', 13, 'bold'))
    style.configure('CardMuted.TLabel', background=CARD, foreground=MUTED)
    style.configure('TScale', troughcolor='#dce7ed', background=ACCENT)
    shell = ttk.Frame(root, padding=24)
    shell.pack(fill='both', expand=True)
    header = ttk.Frame(shell)
    header.pack(fill='x')
    ttk.Label(header, text='Gesture Control', style='Title.TLabel').pack(side='left')
    ttk.Checkbutton(header, text='Two-hand mode', variable=app.two_hands,
                    command=app.change_hand_mode).pack(side='right')
    ttk.Label(shell, text='Move, click and scroll with your hands.', style='Muted.TLabel').pack(anchor='w', pady=(2, 16))
    toolbar = ttk.Frame(shell)
    toolbar.pack(fill='x')
    ttk.Button(toolbar, text='Start camera', style='Accent.TButton', command=app.start).pack(side='left', padx=(0, 8))
    app.pause_button = ttk.Button(toolbar, text='Enable control', command=app.toggle)
    app.pause_button.pack(side='left', padx=(0, 8))
    ttk.Button(toolbar, text='Recenter hand', command=app.recenter).pack(side='left', padx=(0, 8))
    ttk.Button(toolbar, text='Stop camera', command=app.stop).pack(side='right')
    modes = ttk.Frame(shell)
    modes.pack(fill='x', pady=(12, 0))
    ttk.Label(modes, text='Control mode', style='Heading.TLabel').pack(side='left', padx=(0, 12))
    selector = ttk.Combobox(modes, textvariable=app.control_mode,
                           values=('Mouse', 'Volume', 'Air keyboard'), state='readonly', width=18)
    selector.pack(side='left')
    selector.bind('<<ComboboxSelected>>', app.change_control_mode)
    ttk.Checkbutton(modes, text='Sci-fi HUD', variable=app.hud_enabled).pack(side='right')
    status_box = ttk.Frame(shell, style='Card.TFrame', padding=(14, 10))
    status_box.pack(fill='x', pady=(14, 16))
    ttk.Label(status_box, text='●', foreground=ACCENT, style='Card.TLabel').pack(side='left', padx=(0, 10))
    app.status = tk.StringVar(value='Ready • Start camera, position your hand, then enable control')
    status_label = ttk.Label(status_box, textvariable=app.status, style='Card.TLabel', wraplength=730)
    status_label.pack(side='left', fill='x', expand=True)
    status_box.bind('<Configure>', lambda e: status_label.configure(wraplength=max(300, e.width - 64)))
    navigation = ttk.Frame(shell, style='Card.TFrame', padding=5, height=58)
    navigation.pack(fill='x', pady=(0, 8))
    navigation.grid_propagate(False)
    navigation.rowconfigure(0, weight=1)
    tabs = ttk.Notebook(shell, style='Pages.TNotebook')
    app.pages = tabs
    tabs.pack(fill='both', expand=True)
    guide_tab = ttk.Frame(tabs)
    tabs.add(guide_tab, text='Gesture guide')
    guide_canvas = tk.Canvas(guide_tab, bg=BG, highlightthickness=0)
    guide_bar = ttk.Scrollbar(guide_tab, command=guide_canvas.yview)
    guide_bar.pack(side='right', fill='y')
    guide_canvas.pack(side='left', fill='both', expand=True)
    guide_canvas.configure(yscrollcommand=guide_bar.set)
    app.guide = ttk.Frame(guide_canvas, padding=(0, 14, 8, 0))
    guide_window = guide_canvas.create_window((0, 0), window=app.guide, anchor='nw')
    app.guide.bind('<Configure>', lambda _: guide_canvas.configure(scrollregion=guide_canvas.bbox('all')))
    guide_canvas.bind('<Configure>', lambda e: guide_canvas.itemconfigure(guide_window, width=e.width))
    settings_tab = ttk.Frame(tabs)
    tabs.add(settings_tab, text='Settings')
    app.navigation_buttons = []
    def select_page(index):
        tabs.select(index)
        for i, button in enumerate(app.navigation_buttons):
            button.configure(bg=ACCENT if i == index else CARD,
                             fg='white' if i == index else MUTED)
    for i, title in enumerate(('Gesture guide', 'Controls & settings')):
        button = tk.Button(navigation, text=title, command=lambda index=i: select_page(index),
                           font=('Segoe UI', 11, 'bold'), relief='flat', bd=0, cursor='hand2',
                           width=1, highlightthickness=0, padx=12, pady=10,
                           activebackground='#dcebef', activeforeground=INK)
        button.grid(row=0, column=i, sticky='nsew', padx=3)
        navigation.columnconfigure(i, weight=1, uniform='navigation')
        app.navigation_buttons.append(button)
    select_page(0)
    app.update_guide()
    # Camera controls and live status stay visible above all pages.
    canvas = tk.Canvas(settings_tab, bg=BG, highlightthickness=0)
    bar = ttk.Scrollbar(settings_tab, command=canvas.yview)
    bar.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True)
    canvas.configure(yscrollcommand=bar.set)
    tuning = ttk.Frame(canvas, padding=(4, 18, 16, 18))
    window = canvas.create_window((0, 0), window=tuning, anchor='nw')
    tuning.bind('<Configure>', lambda _: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window, width=e.width))
    def wheel(event):
        if tabs.select() == str(settings_tab):
            canvas.yview_scroll(-int(event.delta / 120), 'units')
        elif tabs.select() == str(guide_tab):
            guide_canvas.yview_scroll(-int(event.delta / 120), 'units')
    root.bind('<MouseWheel>', wheel)
    ttk.Label(tuning, text='Make it feel right', style='Heading.TLabel').pack(anchor='w')
    ttk.Label(tuning, text='Changes apply immediately. Save to keep them for your next session.', style='Muted.TLabel').pack(anchor='w', pady=(3, 16))
    row = ttk.Frame(tuning, style='Card.TFrame', padding=14)
    row.pack(fill='x', pady=(0, 16))
    ttk.Label(row, text='Scroll amount', style='CardTitle.TLabel').pack(side='left')
    initial = max(.01, settings['scroll_step'])
    app.values['scroll_step'] = tk.DoubleVar(value=initial)
    app.scroll_input = tk.StringVar(value=f'{initial:g}')
    ttk.Entry(row, textvariable=app.scroll_input, width=10, font=('Segoe UI', 12)).pack(side='left', padx=20)
    app.scroll_hint = ttk.Label(row, text='No upper limit • try 2, 20 or 50', style='CardMuted.TLabel')
    app.scroll_hint.pack(side='left')
    app.scroll_input.trace_add('write', app.update_scroll_speed)
    specs = [('mouse_speed', 'Mouse speed', 'Higher values cover more screen with less hand movement.', .4, 2.5),
             ('vertical_range', 'Vertical hand travel', 'Lower values make the top and bottom easier to reach.', .1, .5),
             ('smooth', 'Cursor responsiveness', 'Lower feels smoother; higher follows your hand faster.', .05, 1),
             ('pinch_threshold', 'Pinch sensitivity', 'Higher recognizes a click with fingertips farther apart.', .015, .1),
             ('click_cooldown', 'Click cooldown', 'Seconds between clicks. Release each pinch before clicking again.', .1, 2),
             ('drag_hold', 'Pinch hold to drag', 'Hold this many seconds to grab; release the pinch to drop.', .25, 1.5),
             ('scroll_threshold', 'Scroll activation distance', 'Lower values need a smaller palm movement to choose direction.', .005, .06)]
    for key, title, help_text, low, high in specs:
        box = ttk.Frame(tuning, style='Card.TFrame', padding=14)
        box.pack(fill='x', pady=(0, 8))
        ttk.Label(box, text=title, style='CardTitle.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(box, text=help_text, style='CardMuted.TLabel').grid(row=1, column=0, sticky='w', pady=(3, 8))
        value = tk.DoubleVar(value=max(low, min(high, settings[key])))
        app.values[key] = value
        readout = ttk.Label(box, width=7, anchor='e', style='CardTitle.TLabel')
        readout.grid(row=0, column=1, sticky='e')
        def update(*_, v=value, output=readout):
            output.config(text=f'{v.get():.3f}')
        value.trace_add('write', update)
        ttk.Scale(box, from_=low, to=high, variable=value).grid(row=2, column=0, columnspan=2, sticky='ew')
        box.columnconfigure(0, weight=1)
        update()
    # Use the default webcam without exposing hardware indexes in the UI.
    app.camera = tk.StringVar(value='0')
    footer = ttk.Frame(shell)
    footer.pack(fill='x', pady=(16, 0))
    ttk.Label(footer, text='SPACE  Pause / resume     ESC  Stop camera', style='Muted.TLabel').pack(side='left')
    ttk.Button(footer, text='Restore defaults', command=app.reset).pack(side='right', padx=(8, 0))
    ttk.Button(footer, text='Save settings', style='Accent.TButton', command=app.save).pack(side='right')


def render_guide(app):
    for widget in app.guide.winfo_children():
        widget.destroy()
    two = app.two_hands.get()
    mode = app.control_mode.get()
    title = ('Two hands, clear roles' if two else 'One hand, complete control') if mode == 'Mouse' else mode
    intro = ('Right hand aims. Left hand clicks or drags. Either palm scrolls.' if two else 'Point, pinch, hold to drag, or scroll with one hand.') if mode == 'Mouse' else ('Finger distance sets Windows volume. Mouse actions are paused.' if mode == 'Volume' else 'Aim at camera keys, then pinch to type into the focused app.')
    ttk.Label(app.guide, text=title, style='Heading.TLabel').pack(anchor='w')
    ttk.Label(app.guide, text=intro, style='Muted.TLabel').pack(anchor='w', pady=(3, 12))
    grid = ttk.Frame(app.guide)
    grid.pack(fill='both', expand=True)
    cards = [
        ('☝️', '01  Move the cursor', 'RIGHT HAND' if two else 'EITHER HAND',
         'Point your index finger and move gently. Enable at a comfortable height to set the center.', 'Recenter hand adjusts your comfortable position.'),
        ('🤏', '02  Click & drag', 'LEFT HAND' if two else 'SAME HAND',
         'Short pinch + release clicks. Hold the pinch to grab, then move the pointing hand to drag.', 'Release the pinch to drop. Aim at a window title bar to move it.'),
        ('✋', '03  Palm scrolling' if two else '03  Pause', 'EITHER OPEN PALM' if two else 'OPEN PALM',
         'Open your palm. Move UP or DOWN once to lock the scroll direction. Reposition freely while it continues.' if two else 'Raise all four fingers to pause cursor movement and clicks.',
         'STOP: close your palm. Reopen to choose a new direction.' if two else 'Point your index finger to resume movement.'),
        ('✌️', '04  Auto scroll' if two else '04  Scroll', 'RIGHT HAND' if two else 'TWO FINGERS',
         'Raise index + middle fingers to continue in the last palm-scroll direction. Fold the other fingers.' if two else 'Raise index + middle. Shift up/down and hold to scroll; fold the other fingers.',
         'STOP: return to one pointing finger.' if two else 'Return to starting height or lower the middle finger to stop.')]
    if mode == 'Volume':
        cards = [
            ('🔊', '01  Choose volume', 'EXPLICIT MODE', 'Select Volume, start the camera, then enable control. Mouse clicks and scrolling are suspended.', 'Use Pause control to stop changing volume.'),
            ('🤏', '02  Adjust distance', 'RIGHT HAND' if two else 'EITHER HAND', 'Spread thumb and index to raise volume. Bring them closer to lower it.', 'A line and level meter show the current volume.'),
            ('✋', '03  Keep it steady', 'HAND-RELATIVE RANGE', 'The gap is measured relative to palm size. Volume moves gradually to reduce sudden jumps.', 'Taking your hand out of view holds the current level.'),
            ('☝️', '04  Return to mouse', 'MODE SELECTOR', 'Choose Mouse when finished. Each mode change pauses control; enable it again when ready.', 'Volume control uses your default Windows audio output.')]
    elif mode == 'Air keyboard':
        cards = [
            ('⌨️', '01  Prepare to type', 'FOCUSED APP', 'Select Air keyboard and enable control. Focus the app or text field you want to type into.', 'The virtual keys appear over the camera preview.'),
            ('☝️', '02  Aim at a key', 'RIGHT HAND' if two else 'EITHER HAND', 'Move the pointing index onto a camera-preview key. The highlighted key is your current target.', 'Mouse movement is suspended in keyboard mode.'),
            ('🤏', '03  Pinch to type', 'LEFT HAND' if two else 'SAME HAND', 'Pinch briefly to select the highlighted key. Separate fingertips before typing the next key.', 'The target locks when the pinch starts.'),
            ('🔠', '04  More keys', 'LAYERS & EDITING', 'Shift capitalizes the next letter. 123 / ABC switches layers. Space, Back and Enter edit your text.', 'Pause control stops all typing. Supports basic English input.')]
    app.guide_cards = []
    for i, (icon, heading, role, description, stop) in enumerate(cards):
        card = ttk.Frame(grid, style='Card.TFrame', padding=16)
        card.grid(row=i//2, column=i%2, sticky='nsew', padx=(0, 8) if i%2==0 else (8, 0), pady=(0, 12))
        ttk.Label(card, text=f'{icon}   {role}', font=('Segoe UI Emoji', 12), foreground=ACCENT, style='Card.TLabel').pack(anchor='w')
        ttk.Label(card, text=heading, style='CardTitle.TLabel').pack(anchor='w', pady=(8, 6))
        body = ttk.Label(card, text=description, style='Card.TLabel', wraplength=330)
        body.pack(anchor='w', fill='x')
        note = ttk.Label(card, text=stop, style='CardMuted.TLabel', wraplength=330)
        note.pack(anchor='w', fill='x', pady=(10, 0))
        card.bind('<Configure>', lambda e, labels=(body,note): [label.configure(wraplength=max(200,e.width-32)) for label in labels])
        app.guide_cards.append(card)
    for col in range(2):
        grid.columnconfigure(col, weight=1, uniform='cards')
    for row in range(2):
        grid.rowconfigure(row, weight=1)
    ttk.Label(app.guide, text='GET STARTED   1  Choose mode     2  Start camera     3  Enable control',
              style='Muted.TLabel', wraplength=820).pack(anchor='w', pady=(0, 4))
