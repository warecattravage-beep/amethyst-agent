"""
✦ Onyx Dashboard — Native GUI App
Cross-platform: Windows / Linux / Android (Termux)
Built with Kivy — pure Python, no KV language.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

os.environ["KIVY_NO_CONSOLELOG"] = "1"

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.switch import Switch
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.textinput import TextInput

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.config import Config

# ── Palette ──
BG = (0.11, 0.11, 0.13, 1)
CARD = (0.16, 0.16, 0.20, 1)
BLUE = (0.25, 0.65, 0.95, 1)
GREEN = (0.2, 0.8, 0.4, 1)
RED = (0.9, 0.2, 0.2, 1)
FG = (0.92, 0.92, 0.95, 1)
DIM = (0.55, 0.55, 0.6, 1)


# ── Helpers ──

def row(label_text, right, h=48):
    """Label on left, widget on right."""
    b = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(h),
                  spacing=dp(8), padding=[dp(12), dp(4)])
    b.add_widget(Label(text=label_text, halign='left', color=FG,
                       size_hint_x=0.4))
    b.add_widget(right)
    return b


def styled_btn(text, color=BLUE, cb=None):
    btn = Button(text=text, size_hint_y=None, height=dp(44),
                 background_normal='', background_color=color, color=(1, 1, 1, 1))
    if cb:
        btn.bind(on_release=cb)
    return btn


def maker(label, toggle_cb):
    """Build a messenger/model/skill row with toggle."""
    b = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50),
                  spacing=dp(8), padding=[dp(12), dp(4)])
    b.add_widget(Label(text=label, halign='left', color=FG, size_hint_x=0.5))
    sw = Switch(active_color=GREEN, inactive_color=(0.3, 0.3, 0.35, 1))
    sw.bind(active=toggle_cb)
    b.add_widget(sw)
    return b, sw


# ── Tab: Status ──

class StatusTab(BoxLayout):
    def __init__(self, config, **kw):
        super().__init__(orientation='vertical', padding=dp(16), spacing=dp(8),
                         **kw)
        self.add_widget(Label(text='✦ Status Overview', bold=True,
                              size_hint_y=None, height=dp(30), color=BLUE))
        items = [
            ('Active Model', config.get('active_model', '—')),
            ('Messengers', ', '.join(config.active_messengers) or 'none'),
            ('Skills', f'{len(config.enabled_skills)} active'),
            ('Config', str(Path(config.path).resolve())),
        ]
        for label, val in items:
            v = Label(text=val, color=BLUE, bold=True)
            self.add_widget(row(label, v))
        self.add_widget(BoxLayout())  # spacer
        self.add_widget(styled_btn('▶ Launch Agent (terminal)', GREEN,
                                   lambda b: self._info('Run: onyx start')))

    def _info(self, msg):
        Popup(title='Info', content=Label(text=msg), size_hint=(0.6, 0.3)).open()


# ── Tab: Messengers ──

class MessengerTab(BoxLayout):
    def __init__(self, config, **kw):
        super().__init__(orientation='vertical', padding=dp(16), spacing=dp(4),
                         **kw)
        self.config = config
        self.add_widget(Label(text='Messenger Channels', bold=True,
                              size_hint_y=None, height=dp(30), color=BLUE))
        self.rows = {}
        for name, mcfg in config.get('messengers', {}).items():
            en = mcfg.get('enabled', False)
            r, sw = maker(f'📨 {name}', lambda s, v, n=name: self._tog(n, v))
            sw.active = en
            self.rows[name] = sw
            # Show brief status
            detail = ''
            if name == 'telegram' and mcfg.get('token'):
                detail = f' (token: {mcfg["token"][:8]}...)'
            elif name == 'console':
                detail = f' (prompt: {mcfg.get("prompt", "?")})'
            if detail:
                r.add_widget(Label(text=detail, color=DIM, size_hint_x=0.3))
            self.add_widget(r)

    def _tog(self, name, value):
        self.config.set(f'messengers.{name}.enabled', value)


# ── Tab: Models ──

class ModelTab(BoxLayout):
    def __init__(self, config, **kw):
        super().__init__(orientation='vertical', padding=dp(16), spacing=dp(4),
                         **kw)
        self.config = config
        self.add_widget(Label(text='AI Models', bold=True,
                              size_hint_y=None, height=dp(30), color=BLUE))
        active = config.get('active_model', '')
        for name, mcfg in config.get('models', {}).items():
            is_active = name == active
            r, sw = maker(f'🧠 {name}' + (' (active)' if is_active else ''),
                          lambda s, v, n=name: self._tog_en(n, v))
            sw.active = mcfg.get('enabled', False)

            r.add_widget(Label(text=mcfg.get('model', '?'), color=DIM,
                               size_hint_x=0.3))

            if not is_active:
                btn = Button(text='Use', size_hint=(None, None),
                             size=(dp(56), dp(36)),
                             background_normal='', background_color=BLUE,
                             color=(1, 1, 1, 1))
                btn.bind(on_release=lambda b, n=name: self._set_active(n))
                r.add_widget(btn)

            self.add_widget(r)

    def _tog_en(self, name, value):
        self.config.set(f'models.{name}.enabled', value)

    def _set_active(self, name):
        self.config.set('active_model', name)
        self.config.set(f'models.{name}.enabled', True)
        App.get_running_app().rebuild()


# ── Tab: Skills ──

class SkillTab(BoxLayout):
    def __init__(self, config, **kw):
        super().__init__(orientation='vertical', padding=dp(16), spacing=dp(4),
                         **kw)
        self.config = config
        self.add_widget(Label(text='Skills', bold=True,
                              size_hint_y=None, height=dp(30), color=BLUE))
        for name, scfg in config.get('skills', {}).items():
            r, sw = maker(f'🔧 {name}',
                          lambda s, v, n=name: self._tog(n, v))
            sw.active = scfg.get('enabled', False)
            self.add_widget(r)

    def _tog(self, name, value):
        self.config.set(f'skills.{name}.enabled', value)


# ── Tab: Config ──

class ConfigTab(BoxLayout):
    def __init__(self, config, **kw):
        super().__init__(orientation='vertical', padding=dp(16), spacing=dp(8),
                         **kw)
        self.config = config
        self.add_widget(Label(text='Configuration (edit JSON)', bold=True,
                              size_hint_y=None, height=dp(28), color=BLUE))

        self.ti = TextInput(
            text=json.dumps(config.data, indent=2),
            multiline=True,
            background_color=CARD,
            foreground_color=FG,
            font_size=dp(11),
        )
        sv = ScrollView()
        sv.add_widget(self.ti)
        self.add_widget(sv)

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(12))
        btn_row.add_widget(styled_btn('✓ Save & Reload', GREEN, self._save))
        btn_row.add_widget(styled_btn('📝 Open in Editor', BLUE, self._editor))
        self.add_widget(btn_row)

    def _save(self, btn):
        try:
            data = json.loads(self.ti.text)
            self.config.data = data
            self.config.save()
            Popup(title='Saved',
                  content=Label(text='✅ Config saved and applied'),
                  size_hint=(0.6, 0.3)).open()
            App.get_running_app().rebuild()
        except json.JSONDecodeError as e:
            Popup(title='JSON Error',
                  content=Label(text=str(e)),
                  size_hint=(0.8, 0.3)).open()

    def _editor(self, btn):
        editor = os.environ.get('EDITOR', 'nano')
        try:
            subprocess.Popen([editor, str(self.config.path)])
        except Exception as e:
            Popup(title='Error',
                  content=Label(text=f'Could not open editor: {e}'),
                  size_hint=(0.8, 0.3)).open()


# ── Tab: Logs ──

class LogTab(BoxLayout):
    def __init__(self, config, **kw):
        super().__init__(orientation='vertical', padding=dp(16), spacing=dp(8),
                         **kw)
        self.config = config
        self.lbl = Label(text='(loading...)', color=DIM, halign='left',
                         valign='top')
        sv = ScrollView()
        sv.add_widget(self.lbl)
        self.add_widget(sv)
        self.add_widget(styled_btn('🔄 Refresh', BLUE, self._load))
        Clock.schedule_once(lambda dt: self._load(None), 0.1)

    def _load(self, btn):
        log_file = self.config.resolve('log_file')
        if log_file.exists():
            lines = log_file.read_text().split('\n')
            self.lbl.text = '\n'.join(lines[-40:])
        else:
            self.lbl.text = '(no log file yet — run the agent first)'


# ── App ──

class OnyxDashboard(App):
    def __init__(self, config_path='config.json'):
        super().__init__()
        self.config = Config(config_path)
        self.title = '✦ Onyx Agent'
        Window.size = (820, 620)
        Window.minimum_width, Window.minimum_height = 600, 400
        if hasattr(Window, 'clearcolor'):
            Window.clearcolor = BG

    def build(self):
        self._root = BoxLayout(orientation='vertical')

        # Title bar
        title = BoxLayout(size_hint_y=None, height=dp(52),
                          padding=[dp(16), 0])
        with title.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*BG)
            Rectangle(pos=title.pos, size=title.size)
        title.bind(pos=lambda w, v: title.canvas.before.get_group('bg')[0].__setattr__('pos', v),
                   size=lambda w, v: title.canvas.before.get_group('bg')[0].__setattr__('size', v))
        # simpler: just use background color
        title.add_widget(Label(text='✦ Onyx Agent', font_size=dp(18), bold=True,
                               color=BLUE, halign='left'))
        self._root.add_widget(title)

        # Tabs
        tp = TabbedPanel(do_default_tab=False)
        tp.add_widget(TabbedPanelHeader(text='Status',
                                        content=StatusTab(self.config)))
        tp.add_widget(TabbedPanelHeader(text='Messengers',
                                        content=MessengerTab(self.config)))
        tp.add_widget(TabbedPanelHeader(text='Models',
                                        content=ModelTab(self.config)))
        tp.add_widget(TabbedPanelHeader(text='Skills',
                                        content=SkillTab(self.config)))
        tp.add_widget(TabbedPanelHeader(text='Config',
                                        content=ConfigTab(self.config)))
        tp.add_widget(TabbedPanelHeader(text='Logs',
                                        content=LogTab(self.config)))
        self._root.add_widget(tp)

        return self._root

    def rebuild(self):
        self.config = Config(self.config.path)
        self._root.clear_widgets()
        Clock.schedule_once(lambda dt: self._root.add_widget(self.build()), 0)

    def on_stop(self):
        self.config.save()


def main():
    cfg_path = Path('config.json')
    if not cfg_path.exists():
        Config(str(cfg_path))
    OnyxDashboard(str(cfg_path)).run()


if __name__ == '__main__':
    main()
