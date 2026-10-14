"""Eevee – słodka nakładka na pulpit (Windows).

Uruchom:  pythonw eevee.pyw   (albo kliknij dwukrotnie "Uruchom Eevee.bat")

Sterowanie:
  lewy klik           – pogłaszcz (serduszka, iskierki, podskok)
  podwójny klik       – super skok z gwiazdkami
  kursor na głowie    – Eevee mruczy
  przeciągnij         – przenieś Eevee (potrząśnij nią, a zakręci jej się w głowie)
  prawy klik          – menu z wszystkimi sztuczkami
"""
import ctypes
import datetime
import math
import random
import time
import tkinter as tk

SIZE = 1.0          # ogólna skala Eevee (np. 1.3 = większa)
KEY = '#ff00fe'       # kolor przezroczystości okna

BROWN = '#C98B4F'
BROWN_L = '#DDA56C'
BROWN_D = '#A96B35'
OUT = '#4E2C14'
CREAM = '#FBEBCB'
CREAM_D = '#E6CC9C'
TIP = '#5E3A1E'
INNER = '#7E4822'
INNER_L = '#9C5F31'
EYE = '#1E0F06'
IRIS = '#5B3218'
IRIS_L = '#94633A'
BLUSH = '#F4A3A3'
BLUSH_H = '#F7838F'
NOSE = '#3A1F10'
MOUTH = '#A93A48'
PINK = '#F59AAE'
PAD = '#F2A7B0'
HEART_COLORS = ['#FF6F91', '#FF8FB1', '#FF4D6D', '#FFB3C6']
NOTE_COLORS = ['#B07CFF', '#FF7FBF', '#6FB7FF']
WING_COLORS = [('#9AD0FF', '#4A8FD6'), ('#FFB3E6', '#D664B0'), ('#FFE680', '#D6A82B'), ('#B9F2A1', '#5FB04A')]

CLICK_PHRASES = ['Vee! ♥', 'Hihi!', 'Jeszcze!', 'Eevee~! ♥', 'Mrrr~', 'Łaskocze!', 'Vui vui!']
IDLE_PHRASES = ['Vee!', 'Eevee~', 'Pobawimy się?', 'Nudzi mi się...', 'Mrr~', 'Vui?', 'Głaszcz mnie!',
                'Co robisz?', 'Jestem głodna...']
NIGHT_PHRASES = ['Późno już...', 'Idziemy spać?', '*ziew*']

# ogon (względem punktu zaczepienia)
TAIL = [(-4, 4), (14, -2), (28, -12), (40, -26), (52, -38), (50, -44), (58, -56), (56, -62), (64, -74),
        (60, -80), (62, -92), (54, -104), (42, -112), (30, -113), (20, -106), (21, -94), (26, -82),
        (24, -68), (18, -54), (8, -40), (-6, -22)]
TAIL_TIP = [(61, -82), (62, -92), (54, -104), (42, -112), (30, -113), (20, -106), (21, -96), (29, -90),
            (34, -96), (41, -87), (48, -93), (54, -84)]
TAIL_FUR = [[(30, -30), (38, -40)], [(40, -52), (46, -64)], [(44, -70), (50, -80)]]
TAIL_PIVOT = (22, -26)
NECK = (0, -62)

HEART = []
for _i in range(24):
    _a = _i / 24 * 2 * math.pi
    HEART.append((16 * math.sin(_a) ** 3 / 16,
                  -(13 * math.cos(_a) - 5 * math.cos(2 * _a) - 2 * math.cos(3 * _a) - math.cos(4 * _a)) / 16))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def rot(pts, pivot, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    px, py = pivot
    return [(px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c) for x, y in pts]


def ell(x, y, rx, ry, n=16):
    return [(x + rx * math.cos(i * 2 * math.pi / n), y + ry * math.sin(i * 2 * math.pi / n)) for i in range(n)]


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def envelope(p, ramp=0.2):
    return smooth01(p / ramp) * smooth01((1 - p) / ramp)


def star_pts(x, y, r, inner=0.4, n=5, ang=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        a = ang + i * math.pi / n
        rr = r if i % 2 == 0 else r * inner
        pts += [x + math.cos(a) * rr, y + math.sin(a) * rr]
    return pts


def work_area(root):
    try:
        from ctypes import wintypes
        r = wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0)
        return r.left, r.top, r.right, r.bottom
    except Exception:
        return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight() - 48


class Eevee:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
        try:
            ctypes.windll.winmm.timeBeginPeriod(1)  # dokładniejszy zegar = płynniejsza animacja
        except Exception:
            pass
        self.root = root = tk.Tk()
        try:
            dpi = ctypes.windll.user32.GetDpiForSystem()
        except Exception:
            dpi = 96
        self.k = k = dpi / 96 * SIZE
        self.W, self.H = int(250 * k), int(280 * k)
        self.cx, self.gy = self.W / 2, self.H - 10 * k

        root.title('Eevee')
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        root.config(bg=KEY)
        root.attributes('-transparentcolor', KEY)
        self.area = work_area(root)
        _, _, right, bottom = self.area
        root.geometry(f'{self.W}x{self.H}+{right - self.W - 10}+{bottom - self.H}')

        self.c = tk.Canvas(root, width=self.W, height=self.H, bg=KEY, highlightthickness=0)
        self.c.pack()
        self.c.bind('<ButtonPress-1>', self.on_press)
        self.c.bind('<B1-Motion>', self.on_drag)
        self.c.bind('<ButtonRelease-1>', self.on_release)
        self.c.bind('<Double-Button-1>', self.on_double)
        self.c.bind('<Button-3>', self.on_menu)

        now = time.perf_counter()
        self.t0 = self.last = now
        self.next_blink = now + 2
        self.blink_start = -10
        self.happy_until = 0
        self.surprise_until = 0
        self.dizzy_until = 0
        self.star_eyes_until = 0
        self.jump = None
        self.land = -10
        self.spin = None
        self.twitch = None
        self.act = None
        self.facing = 1
        self.sleeping = False
        self.wake_at = 0
        self.next_zzz = 0
        self.sing_until = 0
        self.next_note = 0
        self.look_until = 0
        self.look = (0.0, 0.0)
        self.hover = 0.0
        self.purring = False
        self.next_purr_heart = 0
        self.bfly = None
        self.nose_scr = (self.cx, self.gy - 85 * k)
        self.last_interact = now
        self.next_action = now + random.uniform(5, 8)
        self.next_top = now
        self.particles = []
        self.bubble = None
        self.bubble_start = 0
        self.bubble_until = 0
        self.pets = 0
        self.press = None
        self.dragging = False
        self.drag_path = 0.0
        self.drag_turns = 0
        self.drag_dir = 0
        self.drag_last = (0, 0)
        self.skip_release = False
        self.sx = self.sy = 1.0
        self.jy = 0.0
        self.lean = 0.0
        self.breath = 0.0
        self.stack = []

        self.say('Hej! Jestem Madzia ♥', 3)
        self.start_jump(24, 0.45, 2)
        self.loop()

    # ================= akcje =================
    def say(self, text, dur=2.2):
        self.bubble = text
        self.bubble_start = time.perf_counter()
        self.bubble_until = self.bubble_start + dur

    def start_jump(self, h=24, dur=0.45, n=1):
        if not self.jump:
            self.jump = (time.perf_counter(), dur, h, n)

    def start_spin(self):
        self.spin = (time.perf_counter(), 0.7)
        self.start_jump(18, 0.7, 1)

    def start_act(self, name, dur, **data):
        if self.sleeping:
            self.wake()
        self.act = dict(name=name, start=time.perf_counter(), dur=dur, fired=False, **data)

    def act_is(self, *names):
        return self.act is not None and self.act['name'] in names

    def head_scr(self):
        return self.cx, self.gy - 100 * self.k

    def spawn(self, kind, x, y, vx, vy, life, size, color, g=0.0, text='', drag=0.0, grow=False, outline=''):
        self.particles.append(dict(kind=kind, x=x, y=y, vx=vx, vy=vy, life=life, max=life, size=size,
                                   color=color, g=g, text=text, drag=drag, grow=grow, outline=outline,
                                   rot=random.uniform(0, 6.28), spin=random.uniform(-3, 3)))

    def burst(self, x, y, hearts=6, sparkles=8):
        k = self.k
        for _ in range(hearts):
            self.spawn('heart', x, y, random.uniform(-55, 55) * k, -random.uniform(50, 110) * k,
                       random.uniform(1.0, 1.7), random.uniform(7, 12) * k, random.choice(HEART_COLORS),
                       g=25 * k)
        for i in range(sparkles):
            a = i / sparkles * 2 * math.pi + random.uniform(-0.2, 0.2)
            sp = random.uniform(90, 150) * k
            self.spawn('sparkle', x, y, math.cos(a) * sp, math.sin(a) * sp, random.uniform(0.45, 0.75),
                       random.uniform(5, 8) * k, '#FFE066', drag=3.0)

    def pet(self, x, y):
        now = time.perf_counter()
        self.last_interact = now
        if self.sleeping:
            self.wake()
            self.surprise_until = now + 0.8
            self.say('!', 1.2)
            return
        self.pets += 1
        self.happy_until = now + 2.2
        self.burst(x, y)
        if self.pets % 10 == 0:
            self.start_spin()
            self.star_eyes_until = now + 3
            self.say('Kocham cię! ♥', 3)
            for _ in range(18):
                self.spawn('heart', random.uniform(0, self.W), random.uniform(-20, 40) * self.k,
                           random.uniform(-15, 15) * self.k, random.uniform(40, 80) * self.k,
                           random.uniform(2.2, 3.2), random.uniform(7, 13) * self.k,
                           random.choice(HEART_COLORS))
        else:
            self.start_jump(16, 0.35, 1)
            if random.random() < 0.5:
                self.say(random.choice(CLICK_PHRASES))

    def super_jump(self):
        now = time.perf_counter()
        if self.sleeping:
            self.wake()
        self.jump = None
        self.start_jump(42, 0.7, 1)
        self.spin = (now, 0.7)
        self.happy_until = now + 2.5
        self.star_eyes_until = now + 2.5
        self.say('Jupiii!', 1.8)
        hx, hy = self.head_scr()
        k = self.k
        for i in range(12):
            a = i / 12 * 2 * math.pi
            self.spawn('star', hx, hy + 30 * k, math.cos(a) * 140 * k, math.sin(a) * 140 * k, 1.0,
                       random.uniform(6, 9) * k, random.choice(['#FFE066', '#FFB3E6', '#9AD0FF']),
                       drag=2.0, outline='#C99A1E')

    def fall_asleep(self):
        now = time.perf_counter()
        self.act = None
        self.sleeping = True
        self.wake_at = now + random.uniform(25, 55)
        self.next_zzz = now + 0.5
        self.bubble = None

    def wake(self):
        self.sleeping = False
        self.last_interact = time.perf_counter()
        self.next_action = self.last_interact + random.uniform(6, 12)
        self.start_jump(22, 0.45, 1)
        self.twitch = (time.perf_counter(), 0)

    def sing(self):
        if self.sleeping:
            self.wake()
        self.sing_until = time.perf_counter() + 2.6
        self.say('♪ Vee-vee-vee ♪', 2.6)

    def walk(self):
        left, _, right, _ = self.area
        x = self.root.winfo_x()
        lo, hi = left, right - self.W
        if hi <= lo:
            return
        dist = random.uniform(120, 380) * self.k * random.choice([-1, 1])
        target = max(lo, min(hi, x + dist))
        if abs(target - x) < 40 * self.k:
            target = max(lo, min(hi, x - dist))
        speed = 75 * self.k
        self.start_act('walk', abs(target - x) / speed, x0=x, x1=target)

    def summon_butterfly(self):
        if self.bfly:
            return
        k = self.k
        side = random.choice([-1, 1])
        self.bfly = dict(x=self.cx + side * self.W * 0.55, y=self.gy - random.uniform(140, 200) * k,
                         phase='fly', t0=time.perf_counter(), col=random.choice(WING_COLORS))
        self.surprise_until = time.perf_counter() + 0.8

    def random_action(self, now):
        night = datetime.datetime.now().hour >= 22 or datetime.datetime.now().hour < 6
        idle = now - self.last_interact
        if (idle > 75 and random.random() < 0.3) or (night and idle > 40 and random.random() < 0.35):
            self.fall_asleep()
            return
        names = ['hop', 'spin', 'hearts', 'sing', 'talk', 'twitch', 'look', 'sparkle', 'walk', 'butterfly',
                 'sneeze', 'yawn', 'tilt', 'wave', 'groom', 'shake']
        weights = [2.5, 1.2, 1.5, 1, 1.5, 1.5, 1.5, 1, 2, 1.2, 0.8, 3 if night else 1, 1.5, 1.2, 1, 0.8]
        a = random.choices(names, weights)[0]
        hx, hy = self.head_scr()
        k = self.k
        if a == 'hop':
            self.start_jump(22, 0.42, random.choice([1, 2, 3]))
        elif a == 'spin':
            self.start_spin()
        elif a == 'hearts':
            self.happy_until = now + 1.5
            for _ in range(3):
                self.spawn('heart', hx + random.uniform(-30, 30) * k, hy - 30 * k, random.uniform(-20, 20) * k,
                           -random.uniform(40, 70) * k, 1.6, random.uniform(7, 10) * k,
                           random.choice(HEART_COLORS))
        elif a == 'sing':
            self.sing()
        elif a == 'talk':
            self.say(random.choice(NIGHT_PHRASES if night else IDLE_PHRASES))
        elif a == 'twitch':
            self.twitch = (now, random.choice([-1, 0, 1]))
        elif a == 'look':
            self.look_until = now + 2.4
        elif a == 'sparkle':
            for _ in range(7):
                self.spawn('sparkle', hx + random.uniform(-90, 90) * k, hy + random.uniform(-80, 90) * k,
                           0, -10 * k, random.uniform(0.6, 1.2), random.uniform(5, 9) * k, '#FFE066')
        elif a == 'walk':
            self.walk()
        elif a == 'butterfly':
            self.summon_butterfly()
        elif a == 'sneeze':
            self.start_act('sneeze', 1.7)
        elif a == 'yawn':
            self.start_act('yawn', 2.3)
            self.say('*ziew*', 2)
        elif a == 'tilt':
            self.start_act('tilt', 2.0, side=random.choice([-1, 1]))
            self.spawn('text', hx + 40 * k, hy - 50 * k, 0, -18 * k, 1.6, 22 * k, '#6B8CFF', text='?')
        elif a == 'wave':
            self.start_act('wave', 2.4)
            self.say('Hej hej!', 2)
        elif a == 'groom':
            self.start_act('groom', 2.6)
        elif a == 'shake':
            self.start_act('shake', 1.0)
            self.say('Brrr!', 1.4)

    # ================= mysz =================
    def on_press(self, e):
        self.press = (e.x_root, e.y_root, self.root.winfo_x(), self.root.winfo_y())
        self.dragging = False
        self.drag_path = 0.0
        self.drag_turns = 0
        self.drag_dir = 0
        self.drag_last = (e.x_root, e.y_root)

    def on_drag(self, e):
        if not self.press:
            return
        x0, y0, wx, wy = self.press
        dx, dy = e.x_root - x0, e.y_root - y0
        if not self.dragging and abs(dx) + abs(dy) > 5:
            self.dragging = True
            self.act = None
            if self.sleeping:
                self.wake()
            self.surprise_until = time.perf_counter() + 0.6
            self.say('Wiii!', 1.5)
        if self.dragging:
            lx, ly = self.drag_last
            mx = e.x_root - lx
            self.drag_path += math.hypot(mx, e.y_root - ly)
            if abs(mx) > 3:
                d = 1 if mx > 0 else -1
                if self.drag_dir and d != self.drag_dir:
                    self.drag_turns += 1
                self.drag_dir = d
            self.drag_last = (e.x_root, e.y_root)
            self.root.geometry(f'+{wx + dx}+{wy + dy}')

    def on_release(self, e):
        now = time.perf_counter()
        if self.skip_release:
            self.skip_release = False
        elif self.dragging:
            self.dragging = False
            self.land = now
            self.last_interact = now
            if self.drag_turns >= 6 and self.drag_path > 500 * self.k:
                self.dizzy_until = now + 3.5
                self.say('Kręci mi się... @_@', 3)
        elif self.press:
            self.pet(e.x, e.y)
        self.press = None

    def on_double(self, e):
        self.skip_release = True
        self.press = None
        self.last_interact = time.perf_counter()
        self.super_jump()

    def on_menu(self, e):
        m = tk.Menu(self.root, tearoff=0)
        hx, hy = self.head_scr()
        m.add_command(label='Pogłaszcz', command=lambda: self.pet(hx, hy))
        m.add_command(label='Super skok', command=self.super_jump)
        m.add_command(label='Obrót', command=self.start_spin)
        m.add_command(label='Zaśpiewaj', command=self.sing)
        m.add_command(label='Pomachaj', command=lambda: (self.start_act('wave', 2.4), self.say('Hej hej!', 2)))
        m.add_command(label='Otrzep się', command=lambda: (self.start_act('shake', 1.0), self.say('Brrr!', 1.4)))
        m.add_command(label='Spacer', command=self.walk)
        m.add_command(label='Zawołaj motylka', command=self.summon_butterfly)
        m.add_separator()
        if self.sleeping:
            m.add_command(label='Obudź', command=self.wake)
        else:
            m.add_command(label='Idź spać', command=self.fall_asleep)
        m.add_command(label='Zamknij', command=self.quit)
        m.tk_popup(e.x_root, e.y_root)

    def quit(self):
        if self.sleeping:
            self.wake()
        self.act = None
        self.say('Pa pa! ♥', 2)
        self.start_act('wave', 1.2)
        self.root.after(1200, self.root.destroy)

    # ================= pętla =================
    def loop(self):
        now = time.perf_counter()
        dt = min(0.05, now - self.last)
        self.last = now
        self.update(now, dt)
        self.draw(now, now - self.t0)
        spent = int((time.perf_counter() - now) * 1000)
        self.root.after(max(5, 33 - spent), self.loop)

    def update(self, now, dt):
        k = self.k
        if not self.sleeping and now >= self.next_blink:
            self.blink_start = now
            self.next_blink = now + (0.35 if random.random() < 0.15 else random.uniform(2, 5.5))
        if self.twitch and now - self.twitch[0] > 0.3:
            self.twitch = None

        # --- akcje czasowe ---
        if self.act:
            a = self.act
            p = (now - a['start']) / a['dur'] if a['dur'] > 0 else 1
            if a['name'] == 'walk':
                x = a['x0'] + (a['x1'] - a['x0']) * min(1.0, p)
                self.root.geometry(f'+{int(x)}+{self.root.winfo_y()}')
                self.facing = -1 if a['x1'] > a['x0'] else 1
            elif a['name'] == 'sneeze':
                if not a['fired'] and p < 0.4 and (not self.bubble or self.bubble_until < now + 0.1):
                    self.say('A... a...', 1.0)
                if not a['fired'] and p >= 0.45:
                    a['fired'] = True
                    self.say('Apsik!', 1.3)
                    self.land = now
                    self.twitch = (now, 0)
                    nx, ny = self.nose_scr
                    for _ in range(7):
                        self.spawn('puff', nx, ny, random.uniform(-70, 70) * k, random.uniform(-10, 40) * k,
                                   random.uniform(0.5, 0.8), random.uniform(3, 6) * k, '#FFFFFF', drag=3)
                    if self.bfly:
                        self.bfly['phase'] = 'leave'
                        self.bfly['t0'] = now
            elif a['name'] == 'shake':
                if random.random() < 0.6:
                    hx, hy = self.head_scr()
                    self.spawn('fur', hx + random.uniform(-40, 40) * k, hy + random.uniform(0, 80) * k,
                               random.uniform(-120, 120) * k, -random.uniform(20, 80) * k, 0.6,
                               random.uniform(1.5, 3) * k, random.choice([BROWN, CREAM, BROWN_L]), g=200 * k)
            if p >= 1:
                if a['name'] == 'walk':
                    self.facing = 1
                    self.land = now
                    if random.random() < 0.4:
                        self.say(random.choice(['Tu jest fajnie!', 'Vee!', 'Uff!']), 1.6)
                self.act = None

        # --- skoki, obroty ---
        self.sx = self.sy = 1.0
        self.jy = 0.0
        self.lean = 0.0
        if self.jump:
            st, dur, h, n = self.jump
            p = (now - st) / dur
            if p >= n:
                self.jump = None
                self.land = now
            else:
                q = p % 1
                self.jy = h * 4 * q * (1 - q)
                s = math.sin(math.pi * q)
                self.sy += 0.08 * s
                self.sx -= 0.06 * s
        if now - self.land < 0.18:
            s = math.sin(math.pi * (now - self.land) / 0.18)
            self.sy -= 0.1 * s
            self.sx += 0.08 * s
        if self.spin:
            st, dur = self.spin
            p = (now - st) / dur
            if p >= 1:
                self.spin = None
            else:
                self.sx *= math.cos(2 * math.pi * p)
        if self.act:
            a = self.act
            p = min(1.0, (now - a['start']) / a['dur'])
            if a['name'] == 'walk':
                self.jy += abs(math.sin((now - a['start']) * 9)) * 3
                self.lean = math.sin((now - a['start']) * 9) * 2
            elif a['name'] == 'shake':
                self.lean = math.sin((now - a['start']) * 40) * 9 * envelope(p, 0.15)
            elif a['name'] == 'yawn':
                self.sy *= 1 + 0.06 * envelope(p, 0.35)
            elif a['name'] == 'sneeze' and p < 0.45:
                self.sy *= 1 + 0.05 * smooth01(p / 0.45)
        if now < self.dizzy_until:
            self.lean += math.sin(now * 4) * 5
        self.sx *= self.facing
        if self.dragging:
            self.sy *= 1.07
            self.sx *= 0.95
            self.jy = 3 + math.sin(now * 12) * 2
            self.lean = math.sin(now * 5) * 6

        self.breath = math.sin((now - self.t0) * (1.3 if self.sleeping else 2.4))

        # --- motylek ---
        b = self.bfly
        if b:
            el = now - b['t0']
            if b['phase'] == 'fly':
                tx = self.cx + 80 * k * math.sin(el * 1.3)
                ty = self.gy - 175 * k + 28 * k * math.sin(el * 2.3)
                f = min(1.0, dt * 2.0)
                b['x'] += (tx - b['x']) * f
                b['y'] += (ty - b['y']) * f
                if el > 6:
                    if random.random() < 0.5:
                        b['phase'], b['t0'] = 'land', now
                    else:
                        b['phase'], b['t0'] = 'leave', now
                        self.start_jump(34, 0.55, 1)
                        self.happy_until = now + 1.5
                        self.say('Hop!', 1.2)
            elif b['phase'] == 'land':
                nx, ny = self.nose_scr
                f = min(1.0, dt * 4.0)
                b['x'] += (nx - b['x']) * f
                b['y'] += (ny - 5 * k - b['y']) * f
                if el > 3.0 and not self.act_is('sneeze'):
                    self.start_act('sneeze', 1.7)
            else:
                b['x'] += 90 * k * dt * (1 if b['x'] < self.cx + 20 * k else 1.5)
                b['y'] -= 130 * k * dt
                if b['y'] < -30 * k or b['x'] > self.W + 30 * k:
                    self.bfly = None

        # --- wzrok ---
        tx = ty = 0.0
        if not self.sleeping:
            target = None
            if self.bfly:
                target = (self.root.winfo_rootx() + self.bfly['x'], self.root.winfo_rooty() + self.bfly['y'])
            elif now < self.look_until:
                tx = -2.8 if (self.look_until - now) > 1.2 else 2.8
            else:
                try:
                    target = self.root.winfo_pointerxy()
                except tk.TclError:
                    pass
            if target:
                hx = self.root.winfo_rootx() + self.cx
                hy = self.root.winfo_rooty() + self.gy - 100 * k
                dx, dy = target[0] - hx, target[1] - hy
                d = math.hypot(dx, dy)
                if d > 1:
                    f = min(1.0, d / (150 * k))
                    tx, ty = dx / d * f * 2.8, dy / d * f * 2.2
        lx, ly = self.look
        a = min(1.0, dt * 10)
        self.look = (lx + (tx - lx) * a, ly + (ty - ly) * a)

        # --- mruczenie (kursor nad głową) ---
        over = False
        if not self.sleeping and not self.dragging and not self.act:
            try:
                px, py = self.root.winfo_pointerxy()
                hx = self.root.winfo_rootx() + self.cx
                hy = self.root.winfo_rooty() + self.gy - 100 * k
                over = math.hypot(px - hx, py - hy) < 48 * k
            except tk.TclError:
                pass
        self.hover = self.hover + dt if over else 0.0
        was = self.purring
        self.purring = self.hover > 0.8
        if self.purring:
            self.last_interact = now
            if not was:
                self.say('Mrrr~ ♥', 2)
            if now >= self.next_purr_heart:
                self.next_purr_heart = now + 0.7
                hx, hy = self.head_scr()
                self.spawn('heart', hx + random.uniform(-35, 35) * k, hy - 25 * k, random.uniform(-15, 15) * k,
                           -50 * k, 1.3, random.uniform(5, 8) * k, random.choice(HEART_COLORS))

        # --- sen ---
        if self.sleeping:
            if now >= self.next_zzz:
                self.next_zzz = now + 1.3
                x, y = self.cx + 34 * k * (1 if self.sx >= 0 else -1), self.gy - 140 * k
                self.spawn('text', x, y, 14 * k, -24 * k, 2.6, 13 * k, '#7F9CF5',
                           text=random.choice(['z', 'Z']), grow=True)
            if now >= self.wake_at:
                self.wake()
                self.say('*ziew* Vee?', 2.2)
        elif not self.dragging and not self.act and not self.bfly and not self.purring \
                and now >= self.next_action:
            self.random_action(now)
            self.next_action = now + random.uniform(5, 12)

        if now < self.sing_until and now >= self.next_note:
            self.next_note = now + 0.35
            self.spawn('text', self.cx + random.uniform(-25, 25) * k, self.gy - 80 * k,
                       random.uniform(-35, 35) * k, -random.uniform(45, 70) * k, 1.4, 16 * k,
                       random.choice(NOTE_COLORS), text=random.choice(['♪', '♫']))

        alive = []
        for p in self.particles:
            p['life'] -= dt
            if p['life'] <= 0:
                continue
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += p['g'] * dt
            p['rot'] += p['spin'] * dt
            if p['drag']:
                f = max(0.0, 1 - p['drag'] * dt)
                p['vx'] *= f
                p['vy'] *= f
            alive.append(p)
        self.particles = alive

        if self.bubble and now >= self.bubble_until:
            self.bubble = None

        if now >= self.next_top:
            self.next_top = now + 2
            self.root.attributes('-topmost', True)

    # ================= rysowanie =================
    def push(self, pivot, deg):
        a = math.radians(deg)
        self.stack.append((pivot[0], pivot[1], math.cos(a), math.sin(a)))

    def pop(self):
        self.stack.pop()

    def P(self, x, y):
        for px, py, c, s in reversed(self.stack):
            x, y = px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c
        return self.cx + x * self.k * self.sx, self.gy + (y * self.sy - self.jy) * self.k

    def lw(self, w):
        return max(1, round(w * self.k))

    def poly(self, pts, fill, outline=OUT, w=2, smooth=True):
        flat = [v for p in pts for v in self.P(*p)]
        self.c.create_polygon(flat, fill=fill, outline=outline or '',
                              width=self.lw(w) if outline else 0, smooth=smooth)

    def oval(self, x, y, rx, ry, fill, outline=OUT, w=2):
        self.poly(ell(x, y, rx, ry), fill, outline, w)

    def line(self, pts, fill=OUT, w=2, smooth=True):
        flat = [v for p in pts for v in self.P(*p)]
        self.c.create_line(flat, fill=fill, width=self.lw(w), smooth=smooth,
                           capstyle='round', joinstyle='round')

    def shaded(self, x, y, rx, ry, base=BROWN, shade=BROWN_D, w=2):
        self.oval(x, y, rx, ry, shade, None)
        self.oval(x - rx * 0.08, y - ry * 0.1, rx * 0.9, ry * 0.86, base, None)
        self.oval(x, y, rx, ry, '', OUT, w)

    def draw(self, now, t):
        self.c.delete('all')
        self.draw_shadow()
        self.draw_eevee(now, t)
        self.draw_butterfly(t)
        self.draw_particles(t)
        self.draw_bubble(now)

    def draw_shadow(self):
        k = self.k
        f = max(0.4, 1 - self.jy / 70)
        rx, ry = 44 * k * f * abs(self.sx) ** 0.3, 7 * k * f
        y = self.gy + 1 * k
        self.c.create_oval(self.cx - rx, y - ry, self.cx + rx, y + ry, fill='#000000', outline='',
                           stipple='gray25')

    def draw_eevee(self, now, t):
        act = self.act['name'] if self.act else None
        ap = min(1.0, (now - self.act['start']) / self.act['dur']) if self.act else 0
        ae = envelope(ap, 0.2) if self.act else 0
        sleeping = self.sleeping
        dizzy = now < self.dizzy_until
        surprised = now < self.surprise_until
        purring = self.purring
        happy = (now < self.happy_until or (self.dragging and not surprised) or purring) and not dizzy
        singing = now < self.sing_until
        landed = self.bfly is not None and self.bfly['phase'] == 'land' and now - self.bfly['t0'] > 0.6
        mirror = 1 if self.sx >= 0 else -1
        lx, ly = self.look
        lx *= mirror

        hy = -98 + self.breath * 1.3 + (5 if sleeping else 0)
        tilt = 0.0
        if act == 'tilt':
            tilt = 15 * ae * self.act['side']
        elif act == 'wave':
            tilt = -7 * ae
        elif act == 'groom':
            tilt = 6 * ae
        elif act == 'sneeze':
            if ap < 0.45:
                hy -= 4 * smooth01(ap / 0.45)
            else:
                hy += 3 * envelope((ap - 0.45) / 0.55, 0.3)
        elif act == 'yawn':
            tilt = -4 * ae
        if sleeping:
            tilt = 7
        if dizzy:
            tilt = math.sin(now * 5) * 10
        if purring:
            tilt = math.sin(now * 2) * 6

        # stopy przy chodzeniu
        step = [0.0, 0.0]
        if act == 'walk':
            ph = (now - self.act['start']) * 9
            step = [max(0.0, math.sin(ph)) * 5, max(0.0, -math.sin(ph)) * 5]

        # łapka (prawa) – machanie / mycie
        paw_lift, paw_target = 0.0, (12, -6)
        if act == 'wave':
            paw_lift = ae
            paw_target = (30 + 5 * math.sin(now * 12), -78)
        elif act == 'groom':
            paw_lift = ae
            paw_target = (8 + 1.5 * math.sin(now * 10), -74 + 2 * math.sin(now * 10))

        self.push((0, 0), self.lean)

        # ---- ogon ----
        if happy or purring:
            ang = math.sin(t * 14) * 16
        elif sleeping:
            ang = math.sin(t * 1.2) * 3 - 4
        elif act == 'walk':
            ang = math.sin(t * 9) * 12
        elif act == 'shake':
            ang = math.sin(t * 40) * 18
        else:
            ang = math.sin(t * 3) * 8 + math.sin(t * 0.7) * 3
        px, py = TAIL_PIVOT
        self.push(TAIL_PIVOT, ang)
        tail = [(px + x, py + y) for x, y in TAIL]
        self.poly(tail, BROWN, None)
        self.poly([(px + x, py + y) for x, y in TAIL_TIP], CREAM, None)
        for seg in TAIL_FUR:
            self.line([(px + x, py + y) for x, y in seg], BROWN_D, 1.6)
        self.line([(px + 34, py - 100), (px + 40, py - 94)], CREAM_D, 1.4)
        self.poly(tail, '', OUT)
        self.pop()

        # ---- tylne łapy i ciało ----
        for i, s in enumerate((-1, 1)):
            self.shaded(s * 27, -15, 15, 13)
        for i, s in enumerate((-1, 1)):
            fy = -4 - step[1 - i] * 0.6
            self.shaded(s * 35, fy, 11, 6)
            for d in (-3, 2):
                self.line([(s * 35 + s * d, fy + 1), (s * 35 + s * d, fy + 5)], OUT, 1.2, smooth=False)
        self.shaded(0, -34, 36, 30 * (1 + 0.03 * self.breath))

        # ---- kryza ----
        for layer, (col, scale, dy) in enumerate(((CREAM_D, 1.08, 3), (CREAM, 1.0, 0))):
            mane = [(-34, -72)]
            n = 12
            for i in range(n + 1):
                a = math.pi - i / n * math.pi
                r = (1.0 if i % 2 == 0 else 0.74) * scale
                sway = math.sin(t * 2.4 + i) * 0.6
                p = (math.cos(a) * 40 * r + sway, -62 + dy + math.sin(a) * 27 * r)
                mane += [p, p] if i % 2 == 0 else [p]
            mane.append((34, -72))
            self.poly(mane, col, OUT if layer == 1 else None)
        for x in (-20, -7, 7, 20):
            self.line([(x * 0.9, -58), (x * 1.1, -46)], CREAM_D, 1.4)

        # ---- głowa ----
        self.push(NECK, tilt)
        for s in (-1, 1):
            self.draw_ear(s, hy, now, sleeping, dizzy, surprised, act, ap)
        # policzkowe kępki i grzywka
        for s in (-1, 1):
            self.poly([(s * 38, hy + 2), (s * 52, hy + 8), (s * 43, hy + 13), (s * 50, hy + 21),
                       (s * 35, hy + 22)], BROWN, OUT, smooth=False)
        self.poly([(-12, hy - 32), (-7, hy - 47), (-1, hy - 37), (5, hy - 47), (8, hy - 38), (14, hy - 43),
                   (13, hy - 31)], BROWN, OUT, smooth=False)
        self.oval(0, hy, 46, 38, BROWN_D, None)
        self.oval(-3, hy - 3, 42, 34, BROWN, None)
        self.oval(-16, hy - 21, 13, 6.5, BROWN_L, None)
        self.oval(0, hy, 46, 38, '', OUT)
        self.line([(-3, hy - 34), (0, hy - 29), (3, hy - 34)], BROWN_D, 1.3)

        self.draw_face(now, hy, lx, ly, sleeping, dizzy, surprised, happy, singing, purring, landed, act, ap)
        self.nose_scr = self.P(0, hy + 12)

        if sleeping:  # bańka z noska
            r = 3 + 2.5 * (self.breath + 1)
            self.oval(5 + r * 0.7, hy + 15 + r * 0.3, r, r, '#EAF6FF', '#8FC7FF', 1.2)
            self.oval(5 + r * 0.4, hy + 14, r * 0.25, r * 0.25, 'white', None)
        if dizzy:
            hx, hy2 = self.P(0, hy - 46)
            for i in range(3):
                a = now * 4 + i * 2 * math.pi / 3
                sx, sy = hx + math.cos(a) * 34 * self.k, hy2 + math.sin(a) * 8 * self.k
                self.c.create_polygon(star_pts(sx, sy, 6 * self.k), fill='#FFE066', outline='#C99A1E')
        self.pop()

        # ---- przednie łapki ----
        for i, s in enumerate((-1, 1)):
            base = (s * 12, -6 - step[i])
            lift = paw_lift if s == 1 else 0.0
            if lift > 0.02:
                pos = lerp(base, paw_target, lift)
                sh = (s * 16, -40)
                self.line([sh, pos], OUT, 16, smooth=False)
                self.line([sh, pos], BROWN, 12, smooth=False)
                self.shaded(pos[0], pos[1], 10, 8.5)
                if lift > 0.5:
                    self.oval(pos[0], pos[1] + 1.5, 4.2, 3.2, PAD, None)
                    for d in (-4.5, 0, 4.5):
                        self.oval(pos[0] + d, pos[1] - 4 + abs(d) * 0.25, 1.7, 1.7, PAD, None)
            else:
                self.shaded(base[0], base[1], 10, 7.5)
                for d in (-3, 3):
                    self.line([(base[0] + d, base[1] + 2), (base[0] + d, base[1] + 5.5)], OUT, 1.3, smooth=False)
        self.pop()

    def draw_ear(self, s, hy, now, sleeping, dizzy, surprised, act, ap):
        pts = [(s * 38, hy - 14), (s * 60, hy - 50), (s * 66, hy - 88), (s * 66, hy - 88),
               (s * 32, hy - 66), (s * 12, hy - 34)]
        angle = 0.0
        if sleeping or dizzy:
            angle += s * 24
        if surprised:
            angle -= s * 7
        if act == 'sneeze' and ap > 0.45:
            angle += s * 20 * envelope((ap - 0.45) / 0.55, 0.3)
        if act == 'walk':
            angle += s * 3 * math.sin(now * 18)
        if self.twitch:
            st, side = self.twitch
            p = (now - st) / 0.3
            if p < 1 and side in (0, s):
                angle += s * 16 * math.sin(math.pi * p)
        pts = rot(pts, lerp(pts[0], pts[5], 0.5), angle)
        ba, mo, tp, _, mi, bb = pts
        cen = ((ba[0] + mo[0] + tp[0] + mi[0] + bb[0]) / 5, (ba[1] + mo[1] + tp[1] + mi[1] + bb[1]) / 5)
        self.poly(pts, BROWN, None)
        self.poly([lerp(cen, p, 0.62) for p in pts], INNER, None)
        low = lerp(ba, bb, 0.5)
        self.poly([lerp(low, lerp(cen, p, 0.62), 0.6) for p in pts], INNER_L, None)
        self.poly([lerp(mo, tp, 0.55), tp, lerp(mi, tp, 0.55)], TIP, None, smooth=False)
        self.line([lerp(mo, tp, 0.55), lerp(mi, tp, 0.55)], OUT, 1.2, smooth=False)
        self.line([lerp(cen, low, 0.3), lerp(cen, tp, 0.3)], BROWN_D, 1.2, smooth=False)
        self.poly(pts, '', OUT)

    def draw_face(self, now, hy, lx, ly, sleeping, dizzy, surprised, happy, singing, purring, landed, act, ap):
        bt = now - self.blink_start
        closed = sleeping or act in ('yawn', 'groom') or (act == 'sneeze' and 0.3 < ap < 0.6)
        squint = act == 'sneeze' and ap < 0.3
        stars = now < self.star_eyes_until
        for s in (-1, 1):
            ex = s * 17 + lx * 0.5
            ey = hy + 4 + ly * 0.4
            if dizzy:
                pts = []
                for i in range(22):
                    a = i * 0.6 + now * 6 * s
                    r = 0.35 * i
                    pts.append((ex + math.cos(a) * r, ey + math.sin(a) * r * 1.2))
                self.line(pts, EYE, 1.6)
            elif closed:
                self.line([(ex - 7, ey - 1), (ex, ey + 3), (ex + 7, ey - 1)], OUT, 2.4)
                self.line([(ex + s * 7, ey - 1), (ex + s * 9.5, ey - 3)], OUT, 1.5)
            elif happy:
                self.line([(ex - 7.5, ey + 3), (ex, ey - 4.5), (ex + 7.5, ey + 3)], EYE, 2.8)
            elif squint or bt < 0.05 or 0.10 <= bt < 0.15:
                self.draw_eye(s, ex, ey, lx, ly, 1.0, False, landed)
                self.poly([(ex - 9.5, ey - 12), (ex + 9.5, ey - 12), (ex + 9.5, ey), (ex - 9.5, ey)],
                          BROWN, None, smooth=False)
                self.line([(ex - 8.5, ey), (ex, ey + 1), (ex + 8.5, ey)], EYE, 2.2)
            elif bt < 0.10:
                self.line([(ex - 7, ey + 1), (ex, ey + 2.5), (ex + 7, ey + 1)], EYE, 2.6)
            else:
                self.draw_eye(s, ex, ey, lx, ly, 0.6 if surprised else 1.0, stars, landed)
            col = BLUSH_H if (happy or purring) else BLUSH
            self.oval(s * 30, hy + 15, 7.5, 4.2, col, None)
            if happy or purring:
                for d in (-3, 0, 3):
                    self.line([(s * 30 + d + 1, hy + 13), (s * 30 + d - 1, hy + 17)], '#E06A7A', 1.1,
                              smooth=False)

        # nosek
        self.poly([(-3.2, hy + 11.5), (3.2, hy + 11.5), (0, hy + 15)], NOSE, None)
        self.oval(-1, hy + 12.2, 0.9, 0.6, '#8A6A55', None)

        m = hy + 18
        if act == 'yawn':
            o = envelope(ap, 0.35)
            self.oval(0, m + 3 + 4 * o, 2.5 + 4 * o, 2 + 7 * o, MOUTH, OUT, 1.5)
            self.oval(0, m + 5 + 8 * o, 1.5 + 3 * o, 1 + 2.5 * o, PINK, None)
        elif act == 'sneeze' and 0.4 < ap < 0.65:
            self.oval(0, m + 4, 5, 5, MOUTH, OUT, 1.5)
        elif act == 'groom':
            self.line([(-6, m), (-3, m + 3), (0, m), (3, m + 3), (6, m)], OUT, 1.6)
            lick = 2.5 + 2 * abs(math.sin(now * 10))
            self.oval(0, m + 2 + lick * 0.6, 2.6, lick, PINK, OUT, 1)
        elif dizzy:
            self.line([(-7, m + 2), (-3.5, m), (0, m + 2), (3.5, m), (7, m + 2)], OUT, 1.6)
        elif surprised or (sleeping is False and landed):
            self.oval(0, m + 3, 2.4, 2.8, MOUTH, OUT, 1.2)
        elif sleeping:
            self.oval(0, m + 2, 1.8, 2, MOUTH, OUT, 1)
        elif happy or singing or act == 'wave':
            self.poly([(-6.5, m), (6.5, m), (0, m + 9)], MOUTH, OUT, 1.5)
            self.oval(0, m + 5.5, 2.6, 2, PINK, None)
        else:
            self.line([(-6, m), (-3, m + 3), (0, m), (3, m + 3), (6, m)], OUT, 1.6)

    def draw_eye(self, s, ex, ey, lx, ly, ps, stars, landed):
        self.oval(ex, ey, 8.5, 11, EYE, None)
        ix, iy = ex + lx * 0.5, ey + 1.5 + ly * 0.5
        if landed:
            ix, iy = ex - s * 2.4, ey + 2.5
        self.oval(ix, iy + 0.5, 6.5, 8, IRIS, None)
        self.oval(ix, iy + 4.5, 4.5, 3.2, IRIS_L, None)
        self.oval(ix, iy + 0.5, 3.6 * ps, 4.6 * ps, EYE, None)
        if stars:
            x, y = self.P(ex - 2.5 + lx * 0.3, ey - 4)
            self.c.create_polygon(star_pts(x, y, 4.5 * self.k, 0.42, 4, self.t0), fill='white', outline='')
        else:
            self.oval(ex - 3 + lx * 0.4, ey - 4.5, 3.2, 3.6, 'white', None)
        self.oval(ex + 3, ey + 5, 1.5, 1.5, 'white', None)
        self.line([(ex + s * 6.5, ey - 8), (ex + s * 10.5, ey - 11)], EYE, 1.8)

    def draw_butterfly(self, t):
        b = self.bfly
        if not b:
            return
        c, k = self.c, self.k
        x, y = b['x'], b['y']
        landed = b['phase'] == 'land'
        f = 0.35 + 0.65 * abs(math.sin(t * (6 if landed else 20)))
        light, dark = b['col']
        for s in (-1, 1):
            w1 = 7 * k * f
            c.create_oval(x + s * w1 * 0.2, y - 9 * k, x + s * (w1 * 2 + 1), y + 1 * k, fill=light, outline=dark)
            w2 = 5 * k * f
            c.create_oval(x + s * w2 * 0.2, y - 1 * k, x + s * (w2 * 2 + 1), y + 7 * k, fill=light, outline=dark)
        c.create_line(x, y - 6 * k, x, y + 6 * k, fill='#3A2A20', width=max(1, round(2 * k)), capstyle='round')
        for s in (-1, 1):
            c.create_line(x, y - 6 * k, x + s * 4 * k, y - 11 * k, fill='#3A2A20', width=1)

    def draw_particles(self, t):
        c = self.c
        for p in self.particles:
            f = p['life'] / p['max']
            s = p['size'] * min(1.0, f * 3)
            x, y = p['x'], p['y']
            kind = p['kind']
            if kind == 'heart':
                flat = [v for hx, hy in HEART for v in (x + hx * s, y + hy * s)]
                c.create_polygon(flat, fill=p['color'], outline='#D6336C', width=1, smooth=True)
            elif kind == 'sparkle':
                c.create_polygon(star_pts(x, y, s, 0.35, 4, p['rot'] + t * 3), fill=p['color'], outline='#F5B700')
            elif kind == 'star':
                c.create_polygon(star_pts(x, y, s, 0.45, 5, p['rot']), fill=p['color'], outline=p['outline'])
            elif kind == 'puff':
                r = p['size'] * (1.6 - 0.8 * f)
                c.create_oval(x - r, y - r, x + r, y + r, fill='white', outline='#B8C4CC')
            elif kind == 'fur':
                c.create_oval(x - s, y - s * 0.6, x + s, y + s * 0.6, fill=p['color'], outline='')
            else:
                size = p['size'] * (1.5 - 0.7 * f) if p['grow'] else s
                font = ('Segoe UI', -max(1, int(size)), 'bold')
                o = max(1, round(self.k))
                for dx, dy in ((-o, 0), (o, 0), (0, -o), (0, o)):
                    c.create_text(x + dx, y + dy, text=p['text'], font=font, fill='white')
                c.create_text(x, y, text=p['text'], font=font, fill=p['color'])

    def draw_bubble(self, now):
        if not self.bubble:
            return
        k, c = self.k, self.c
        age = now - self.bubble_start
        pop = min(1.0, age / 0.15)
        bx = self.cx
        by = self.gy - 200 * k - 4 * k * math.sin(math.pi * min(1.0, age / 0.3))
        font = ('Segoe UI', -max(6, int(14 * k * (0.6 + 0.4 * pop))), 'bold')
        tid = c.create_text(bx, by, text=self.bubble, font=font, fill=OUT, anchor='s')
        x0, y0, x1, y1 = c.bbox(tid)
        pad = 8 * k
        x0, y0, x1, y1 = x0 - pad, y0 - pad * 0.6, x1 + pad, y1 + pad * 0.6
        r = pad
        pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
               x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        c.create_polygon(bx - 7 * k, y1 - 2, bx + 5 * k, y1 - 2, bx + 6 * k, y1 + 10 * k,
                         fill='white', outline=OUT, width=self.lw(1.5))
        c.create_polygon(pts, fill='white', outline=OUT, width=self.lw(1.5), smooth=True)
        c.create_line(bx - 6 * k, y1, bx + 4 * k, y1, fill='white', width=self.lw(2))
        c.tag_raise(tid)


if __name__ == '__main__':
    Eevee().root.mainloop()
