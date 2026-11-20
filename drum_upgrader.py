"""Zaklad hry Drum Tycoon: hrani na bici a vydelavani penez."""

import sys
import math
import json
import os

import pygame


WIDTH = 1220
HEIGHT = 780
FPS = 60
UPGRADE_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3)
SPEED_UPGRADE_KEYS = (pygame.K_F1, pygame.K_F2, pygame.K_F3)

BACKGROUND = (21, 27, 31)
PANEL = (34, 43, 47)
PANEL_LIGHT = (47, 58, 61)
TEXT = (239, 237, 222)
MUTED = (155, 168, 164)
ACCENT = (238, 119, 74)
GREEN = (151, 204, 139)
RED = (222, 105, 94)

LOCATIONS = (
    {"name": "Půda u babičky", "cost": 0, "multiplier": 1.0},
    {"name": "Park", "cost": 250, "multiplier": 1.25},
    {"name": "Herna / pokoj", "cost": 750, "multiplier": 1.50},
    {"name": "Staveniště", "cost": 2000, "multiplier": 2.00},
    {"name": "Dům boháče", "cost": 5000, "multiplier": 3.00},
)


class Drum:
    """Hratelny nastroj, ktery pri uderu vydelava penize."""

    def __init__(
        self,
        name,
        key,
        key_label,
        income,
        upgrade_cost,
        color,
        hit_area,
        cooldown=0.99,
        purchase_cost=0,
        owned=True,
    ):
        self.name = name
        self.key = key
        self.key_label = key_label
        self.income = income
        self.base_income = income
        self.upgrade_cost = upgrade_cost
        self.level = 0
        self.color = color
        self.hit_area = pygame.Rect(hit_area)
        self.flash_timer = 0.0
        self.base_cooldown = cooldown
        self.cooldown = cooldown
        self.cooldown_left = 0.0
        self.speed_level = 0
        self.speed_upgrade_cost = round(upgrade_cost * 1.8)
        self.max_speed_level = 5
        self.purchase_cost = purchase_cost
        self.owned = owned

    def hit(self):
        if self.cooldown_left > 0:
            return None
        self.flash_timer = 0.16
        self.cooldown_left = self.cooldown
        # Zvuk lze pozdeji prehrat pres pygame.mixer.Sound.
        return self.income

    def upgrade(self):
        self.level += 1
        self.income += self.base_income
        self.upgrade_cost = round(self.upgrade_cost * 1.65)

    def upgrade_speed(self):
        if self.speed_level >= self.max_speed_level:
            return
        self.speed_level += 1
        cooldown_multipliers = (1.0, 0.75, 0.50, 0.25, 0.10, 0.0)
        self.cooldown = round(
            self.base_cooldown * cooldown_multipliers[self.speed_level],
            2,
        )
        self.cooldown_left = min(self.cooldown_left, self.cooldown)
        self.speed_upgrade_cost = round(self.speed_upgrade_cost * 1.75)

    def update(self, dt):
        self.flash_timer = max(0.0, self.flash_timer - dt)
        self.cooldown_left = max(0.0, self.cooldown_left - dt)

    def draw(self, surface, font, small_font):
        active = self.flash_timer > 0
        ready = self.cooldown_left <= 0
        color = (255, 215, 125) if active else (
            self.color if ready else (86, 96, 96)
        )
        shadow = (12, 17, 20)
        visual_tier = min(5, self.level + self.speed_level)
        level_ring_width = 3 + min(self.level, 4)

        if self.name == "Kopák":
            pygame.draw.ellipse(surface, shadow, self.hit_area.move(0, 12))
            pygame.draw.ellipse(surface, color, self.hit_area)
            pygame.draw.ellipse(surface, (224, 222, 204), self.hit_area, 5)
            center = self.hit_area.center
            pygame.draw.circle(surface, (34, 43, 47), center, 43)
            pygame.draw.circle(surface, (224, 222, 204), center, 43, 3)
            pygame.draw.circle(surface, (34, 43, 47), center, 7)
        elif self.name == "Snare":
            rect = self.hit_area
            cx, cy = rect.center
            pygame.draw.ellipse(surface, (10, 14, 16), rect.move(0, 13).inflate(18, 8))

            shell = rect.inflate(12, 20)
            pygame.draw.ellipse(surface, (24, 29, 31), shell.move(0, 28))
            pygame.draw.ellipse(surface, color, shell)
            rim_color = (
                (238, 232, 210),
                (210, 225, 215),
                (177, 210, 221),
                (159, 193, 235),
                (183, 169, 255),
                (238, 180, 255),
            )[visual_tier]
            pygame.draw.ellipse(surface, rim_color, shell, level_ring_width)

            pygame.draw.ellipse(surface, shadow, rect.move(0, 8).inflate(4, 4))
            pygame.draw.ellipse(surface, rim_color, rect.inflate(4, 2))
            pygame.draw.ellipse(surface, color, rect)
            pygame.draw.ellipse(surface, (255, 248, 220), rect.inflate(-12, -10), 3)

            rivet_count = 8 + visual_tier * 2
            for index in range(rivet_count):
                angle = index * 360 / rivet_count
                lx = int(cx + 78 * pygame.math.Vector2(1, 0).rotate(angle).x)
                ly = int(cy + 35 * pygame.math.Vector2(1, 0).rotate(angle).y)
                rivet_radius = 4 + min(visual_tier, 3)
                pygame.draw.circle(surface, rim_color, (lx, ly), rivet_radius)
                pygame.draw.circle(surface, (55, 62, 62), (lx, ly), rivet_radius, 2)

            pygame.draw.line(surface, (190, 196, 188), (cx - 55, cy + 48),
                             (cx - 75, cy + 96), 7)
            pygame.draw.line(surface, (190, 196, 188), (cx + 55, cy + 48),
                             (cx + 75, cy + 96), 7)
            pygame.draw.line(surface, (190, 196, 188), (cx - 75, cy + 96),
                             (cx + 75, cy + 96), 7)

            highlight = rect.inflate(-20, -24)
            pygame.draw.arc(surface, (255, 238, 190), highlight,
                            math.radians(200), math.radians(340), 4)
            pygame.draw.circle(surface, (255, 246, 210), (cx - 48, cy - 9), 4)
        elif self.name == "Tom":
            rect = self.hit_area
            cx, cy = rect.center
            pygame.draw.ellipse(surface, (10, 14, 16), rect.move(0, 12).inflate(12, 8))
            pygame.draw.rect(surface, (52, 58, 60), (cx - 58, cy + 12, 116, 70), border_radius=12)
            pygame.draw.ellipse(surface, shadow, rect.move(0, 7).inflate(8, 4))
            pygame.draw.ellipse(surface, rim_color if 'rim_color' in locals() else color, rect.inflate(6, 2), level_ring_width)
            pygame.draw.ellipse(surface, color, rect)
            pygame.draw.ellipse(surface, (255, 224, 190), rect.inflate(-18, -14), 3)
            pygame.draw.line(surface, (185, 194, 188), (cx - 42, cy + 65), (cx - 58, cy + 112), 7)
            pygame.draw.line(surface, (185, 194, 188), (cx + 42, cy + 65), (cx + 58, cy + 112), 7)
        elif self.name in ("Hi-Hat", "Crash"):
            center_x, center_y = self.hit_area.center
            small = self.name == "Hi-Hat"
            width = 150 if small else 210
            top_rect = pygame.Rect(center_x - width // 2, center_y - 18, width, 36)
            bottom_rect = pygame.Rect(center_x - width // 2, center_y + 8, width, 28)
            cymbal_color = (220, 190, 106) if visual_tier < 3 else (255, 220, 145)
            pygame.draw.line(surface, (150, 160, 154), (center_x, center_y - 18), (center_x, center_y + 128), 7)
            pygame.draw.ellipse(surface, (8, 12, 14), bottom_rect.move(0, 8))
            pygame.draw.ellipse(surface, cymbal_color, bottom_rect, level_ring_width)
            pygame.draw.ellipse(surface, cymbal_color, top_rect, level_ring_width)
            pygame.draw.circle(surface, (255, 238, 170), (center_x, center_y), 7)
        else:
            center_x, center_y = self.hit_area.center
            cymbal_colors = (
                (201, 168, 82),
                (220, 183, 92),
                (231, 197, 102),
                (246, 208, 112),
                (255, 220, 125),
                (255, 238, 170),
            )
            cymbal_gold = cymbal_colors[visual_tier]
            pygame.draw.ellipse(
                surface,
                (8, 12, 14),
                self.hit_area.move(0, 14).inflate(18, 12),
            )

            stand_width = 7 + min(self.level, 4)
            pygame.draw.line(surface, (56, 62, 63), (center_x, center_y + 18),
                             (center_x, center_y + 128), stand_width)
            pygame.draw.line(surface, cymbal_gold, (center_x - 42, center_y + 128),
                             (center_x + 42, center_y + 128), stand_width)
            pygame.draw.line(surface, cymbal_gold, (center_x - 42, center_y + 128),
                             (center_x - 18, center_y + 82), stand_width - 1)
            pygame.draw.line(surface, cymbal_gold, (center_x + 42, center_y + 128),
                             (center_x + 18, center_y + 82), stand_width - 1)

            pygame.draw.line(surface, (220, 220, 197), (center_x, center_y + 12),
                             (center_x, center_y - 18), 5)
            pygame.draw.ellipse(surface, shadow, self.hit_area.move(0, 9).inflate(12, 8))
            pygame.draw.ellipse(surface, color, self.hit_area.inflate(8, 4))
            pygame.draw.ellipse(
                surface,
                cymbal_gold,
                self.hit_area.inflate(8, 4),
                level_ring_width,
            )
            pygame.draw.ellipse(surface, (255, 239, 166),
                                self.hit_area.inflate(-18, -16), 3)
            pygame.draw.circle(surface, (255, 244, 186), (center_x, center_y), 9)
            pygame.draw.circle(surface, (92, 76, 48), (center_x, center_y), 9, 3)

            for step in range(self.speed_level):
                notch_x = center_x - 55 + step * 22
                pygame.draw.circle(
                    surface,
                    cymbal_gold,
                    (notch_x, center_y + 10),
                    5,
                )

            pygame.draw.arc(surface, (255, 250, 205),
                            self.hit_area.inflate(-12, -14),
                            math.radians(175),
                            math.radians(315),
                            3)

        if active:
            ring_color = (255, 215, 125)
            ring_radius = 58
            pygame.draw.circle(surface, ring_color,
                               (self.hit_area.centerx, self.hit_area.centery),
                               ring_radius, 3)

        if self.name in ("Snare", "Činel"):
            badge_y = self.hit_area.bottom + 7
            start_x = self.hit_area.centerx - 40
            for index in range(5):
                pip_color = (
                    (238, 180, 255) if self.name == "Snare"
                    else (255, 220, 125)
                ) if index < visual_tier else (73, 82, 82)
                pygame.draw.circle(
                    surface,
                    pip_color,
                    (start_x + index * 20, badge_y),
                    4,
                )

        label = font.render(self.name, True, TEXT)
        if ready:
            key_text = self.key_label
        else:
            key_text = f"{self.key_label}  |  {self.cooldown_left:.1f} s"
        key_label = small_font.render(key_text, True, MUTED)
        surface.blit(label, label.get_rect(center=(self.hit_area.centerx, self.hit_area.bottom + 27)))
        surface.blit(key_label, key_label.get_rect(center=(self.hit_area.centerx, self.hit_area.bottom + 51)))


class Shop:
    """Obchod s vylepsenimi a koncertnim bonusem."""

    def __init__(self, drums):
        self.drums = drums
        self.upgrade_buttons = {}
        self.speed_upgrade_buttons = {}
        self.concert_button = pygame.Rect(882, 694, 300, 38)
        self.location_button = pygame.Rect(58, 126, 750, 50)
        self.location_upgrade_button = pygame.Rect(604, 133, 194, 36)
        self.concert_cost = 40
        self.concert_duration = 10.0
        self.concert_time_left = 0.0
        self.instrument_buttons = {}

    def buy_instrument(self, drum, game):
        if drum.owned:
            return
        if game.money < drum.purchase_cost:
            game.notice = f"Na nákup {drum.name} potřebuješ {drum.purchase_cost} $."
            game.notice_timer = 2.0
            return
        game.money -= drum.purchase_cost
        drum.owned = True
        game.save_game()
        game.notice = f"{drum.name} byl přidán do sestavy!"
        game.notice_timer = 2.5

    def buy_upgrade(self, drum, game):
        if game.money < drum.upgrade_cost:
            game.notice = "Na vylepšení zatím nemáš dost peněz."
            game.notice_timer = 2.0
            return
        game.money -= drum.upgrade_cost
        drum.upgrade()
        game.save_game()
        game.notice = f"{drum.name} vylepšen!"
        game.notice_timer = 2.0

    def buy_speed_upgrade(self, drum, game):
        if drum.speed_level >= drum.max_speed_level:
            game.notice = f"{drum.name}: maximální rychlost dosažena."
            game.notice_timer = 2.0
            return
        if game.money < drum.speed_upgrade_cost:
            game.notice = "Na zrychlení zatím nemáš dost peněz."
            game.notice_timer = 2.0
            return
        game.money -= drum.speed_upgrade_cost
        drum.upgrade_speed()
        game.save_game()
        game.notice = f"{drum.name}: cooldown snížen!"
        game.notice_timer = 2.0

    def start_concert(self, game):
        if self.concert_time_left > 0:
            return
        if game.money < self.concert_cost:
            game.notice = "Na koncert zatím nemáš dost peněz."
            game.notice_timer = 2.0
            return
        game.money -= self.concert_cost
        self.concert_time_left = self.concert_duration
        game.save_game()
        game.notice = "Koncert začal: výdělky jsou 2x!"
        game.notice_timer = 2.0

    def buy_location(self, game):
        if game.location_level >= len(LOCATIONS) - 1:
            game.notice = "Všechna místa jsou už odemčená."
            game.notice_timer = 2.0
            return
        next_location = LOCATIONS[game.location_level + 1]
        if game.money < next_location["cost"]:
            game.notice = f"Na přesun potřebuješ {next_location['cost']} $."
            game.notice_timer = 2.0
            return
        game.money -= next_location["cost"]
        game.location_level += 1
        game.save_game()
        game.notice = f"Nyní hraješ: {LOCATIONS[game.location_level]['name']}!"
        game.notice_timer = 2.5

    def update(self, dt):
        self.concert_time_left = max(0.0, self.concert_time_left - dt)

    def draw(self, surface, font, small_font, game):
        current_location = LOCATIONS[game.location_level]
        pygame.draw.rect(surface, (46, 52, 54), self.location_button, border_radius=8)
        pygame.draw.rect(surface, PANEL_LIGHT, self.location_button, 2, border_radius=8)
        location_label = font.render(
            f"MÍSTO: {current_location['name']}",
            True,
            TEXT,
        )
        surface.blit(location_label, (72, self.location_button.y + 8))
        multiplier_text = f"Výdělek: {current_location['multiplier']:g}x"
        surface.blit(
            small_font.render(multiplier_text, True, GREEN),
            (72, self.location_button.y + 31),
        )

        if game.location_level < len(LOCATIONS) - 1:
            next_location = LOCATIONS[game.location_level + 1]
            affordable = game.money >= next_location["cost"]
            next_button = pygame.Rect(604, self.location_button.y + 7, 194, 36)
            pygame.draw.rect(
                surface,
                GREEN if affordable else PANEL_LIGHT,
                next_button,
                border_radius=6,
            )
            next_label = small_font.render(
                f"Přesun  {next_location['cost']} $",
                True,
                BACKGROUND if affordable else MUTED,
            )
            surface.blit(next_label, next_label.get_rect(center=next_button.center))
            self.location_upgrade_button = next_button
        else:
            next_button = pygame.Rect(604, self.location_button.y + 7, 194, 36)
            pygame.draw.rect(surface, (117, 153, 113), next_button, border_radius=6)
            next_label = small_font.render("Nejlepší místo", True, TEXT)
            surface.blit(next_label, next_label.get_rect(center=next_button.center))
            self.location_upgrade_button = next_button

        pygame.draw.rect(surface, PANEL, (852, 126, 332, 610), border_radius=8)
        surface.blit(font.render("DÍLNA", True, TEXT), (882, 150))
        surface.blit(small_font.render("Vylepšení zvýší odměnu za každý úder.", True, MUTED), (882, 181))
        pygame.draw.line(surface, PANEL_LIGHT, (882, 214), (1182, 214), 1)

        self.upgrade_buttons.clear()
        self.speed_upgrade_buttons.clear()
        self.instrument_buttons.clear()
        owned_index = 0
        for index, drum in enumerate(self.drums):
            if not drum.owned:
                continue
            y = 218 + owned_index * 76
            owned_index += 1
            card = pygame.Rect(872, y, 320, 70)
            pygame.draw.rect(surface, PANEL_LIGHT, card, border_radius=8)

            name_label = font.render(drum.name, True, TEXT)
            surface.blit(name_label, (882, y + 4))
            level_text = f"Úroveň {drum.level}"
            level_label = small_font.render(level_text, True, MUTED)
            level_badge = pygame.Rect(1082, y + 3, 100, 22)
            pygame.draw.rect(surface, BACKGROUND, level_badge, border_radius=12)
            surface.blit(level_label, level_label.get_rect(center=level_badge.center))

            income_text = f"+{drum.income} $ / úder"
            cooldown_text = "bez pauzy" if drum.cooldown == 0 else f"{drum.cooldown:.2f} s pauza"
            income_label = small_font.render(income_text, True, GREEN)
            cooldown_label = small_font.render(cooldown_text, True, MUTED)
            surface.blit(income_label, (882, y + 27))
            surface.blit(cooldown_label, cooldown_label.get_rect(right=1182, y=y + 27))

            button = pygame.Rect(882, y + 42, 148, 24)
            self.upgrade_buttons[drum] = button
            affordable = game.money >= drum.upgrade_cost
            button_color = GREEN if affordable else PANEL_LIGHT
            pygame.draw.rect(surface, button_color, button, border_radius=5)
            label_color = BACKGROUND if affordable else MUTED
            label = small_font.render(
                f"{index + 1}  Síla  {drum.upgrade_cost} $",
                True,
                label_color,
            )
            surface.blit(label, label.get_rect(center=button.center))

            speed_button = pygame.Rect(1034, y + 42, 148, 24)
            self.speed_upgrade_buttons[drum] = speed_button
            maxed = drum.speed_level >= drum.max_speed_level
            affordable = game.money >= drum.speed_upgrade_cost
            if maxed:
                speed_color = (117, 153, 113)
                speed_text = f"F{index + 1}  Rychlost MAX"
            else:
                speed_color = ACCENT if affordable else PANEL_LIGHT
                speed_text = (
                    f"F{index + 1}  Rychlost {drum.speed_level}/{drum.max_speed_level}"
                    f"  •  {drum.speed_upgrade_cost} $"
                )
            pygame.draw.rect(surface, speed_color, speed_button, border_radius=5)
            speed_label = small_font.render(
                speed_text,
                True,
                TEXT if (maxed or affordable) else MUTED,
            )
            surface.blit(speed_label, speed_label.get_rect(center=speed_button.center))

        purchase_y = 218 + owned_index * 76
        for drum in self.drums:
            if drum.owned:
                continue
            button = pygame.Rect(872, purchase_y, 320, 38)
            self.instrument_buttons[drum] = button
            pygame.draw.rect(surface, ACCENT if game.money >= drum.purchase_cost else PANEL_LIGHT,
                             button, border_radius=6)
            label = small_font.render(
                f"Koupit {drum.name}  -  {drum.purchase_cost} $",
                True,
                TEXT if game.money >= drum.purchase_cost else MUTED,
            )
            surface.blit(label, label.get_rect(center=button.center))
            purchase_y += 42

        active = self.concert_time_left > 0
        concert_color = ACCENT if not active else (117, 153, 113)
        pygame.draw.rect(surface, concert_color, self.concert_button, border_radius=5)
        if active:
            label_text = f"Koncert: 2x  ({self.concert_time_left:.1f} s)"
        else:
            label_text = f"C  Odehrát koncert  -  {self.concert_cost} $"
        label = font.render(label_text, True, TEXT)
        surface.blit(label, label.get_rect(center=self.concert_button.center))


class GameManager:
    """Spravuje herni smycku, vstupy, ekonomiku a vykreslovani."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Drum Tycoon")
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        self.display = pygame.display.set_mode((WIDTH, HEIGHT))
        self.fullscreen = False
        self.current_resolution = (WIDTH, HEIGHT)
        self.settings_open = False
        self.settings_buttons = {}
        self.settings_button = pygame.Rect(320, 34, 202, 52)
        self.keybind_waiting = None
        self.resolution_options = (
            ("1220 x 780", (1220, 780)),
            ("1366 x 768", (1366, 768)),
            ("1600 x 900", (1600, 900)),
            ("1920 x 1080", (1920, 1080)),
        )
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 23)
        self.title_font = pygame.font.Font(None, 48)
        self.money = 0
        self.running = True
        self.notice = "Zahraj na bici a vydelavej!"
        self.notice_timer = 3.0
        self.location_level = 0

        self.drums = [
            Drum("Snare", pygame.K_j, "J", 2, 30, (198, 104, 76), (140, 315, 180, 82), 0.55),
            Drum("Kopák", pygame.K_SPACE, "MEZERNÍK", 3, 40, (115, 145, 132), (355, 410, 235, 170), 0.80),
            Drum("Činel", pygame.K_k, "K", 2, 35, (201, 168, 82), (575, 275, 205, 62), 0.65),
            Drum("Hi-Hat", pygame.K_h, "H", 2, 45, (205, 177, 92), (75, 430, 150, 50), 0.45, 300, False),
            Drum("Tom", pygame.K_t, "T", 4, 75, (118, 88, 132), (250, 300, 150, 100), 0.60, 500, False),
            Drum("Crash", pygame.K_l, "L", 5, 100, (215, 190, 92), (620, 210, 210, 50), 0.70, 800, False),
        ]
        self.shop = Shop(self.drums)
        self.save_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "drum_tycoon_save.json",
        )
        self.load_game()
        if self.fullscreen:
            self.set_fullscreen()
        elif self.current_resolution != (WIDTH, HEIGHT):
            self.set_resolution(self.current_resolution)

    def save_game(self):
        data = {
            "money": max(0, int(self.money)),
            "drums": {
                drum.name: {
                    "level": drum.level,
                    "income": drum.income,
                    "upgrade_cost": drum.upgrade_cost,
                    "speed_level": drum.speed_level,
                    "speed_upgrade_cost": drum.speed_upgrade_cost,
                    "owned": drum.owned,
                    "key": drum.key,
                    "key_label": drum.key_label,
                }
                for drum in self.drums
            },
            "fullscreen": self.fullscreen,
            "resolution": list(self.current_resolution),
            "location_level": self.location_level,
        }
        try:
            with open(self.save_path, "w", encoding="utf-8") as save_file:
                json.dump(data, save_file, ensure_ascii=False, indent=2)
        except OSError as error:
            self.notice = f"Uložení selhalo: {error}"
            self.notice_timer = 3.0

    def load_game(self):
        if not os.path.exists(self.save_path):
            return
        try:
            with open(self.save_path, "r", encoding="utf-8") as save_file:
                data = json.load(save_file)
        except (OSError, json.JSONDecodeError):
            return

        self.money = max(0, int(data.get("money", 0)))
        drum_data = data.get("drums", {})
        cooldown_multipliers = (1.0, 0.75, 0.50, 0.25, 0.10, 0.0)

        for drum in self.drums:
            saved = drum_data.get(drum.name)
            if not isinstance(saved, dict):
                continue

            drum.level = max(0, int(saved.get("level", 0)))
            drum.income = max(drum.base_income, int(saved.get("income", drum.income)))
            drum.upgrade_cost = max(
                1,
                int(saved.get("upgrade_cost", drum.upgrade_cost)),
            )

            drum.speed_level = min(
                drum.max_speed_level,
                max(0, int(saved.get("speed_level", 0))),
            )
            drum.cooldown = round(
                drum.base_cooldown * cooldown_multipliers[drum.speed_level],
                2,
            )
            drum.cooldown_left = 0.0
            drum.speed_upgrade_cost = max(
                1,
                int(saved.get(
                    "speed_upgrade_cost",
                    drum.speed_upgrade_cost,
                )),
            )
            drum.owned = bool(saved.get("owned", drum.owned))
            saved_key = saved.get("key")
            if isinstance(saved_key, int):
                drum.key = saved_key
            saved_key_label = saved.get("key_label")
            if isinstance(saved_key_label, str) and saved_key_label:
                drum.key_label = saved_key_label

        resolution = data.get("resolution")
        if (
            isinstance(resolution, list)
            and len(resolution) == 2
            and all(isinstance(value, int) and value > 0 for value in resolution)
        ):
            self.current_resolution = tuple(resolution)
        self.fullscreen = bool(data.get("fullscreen", False))
        self.location_level = min(
            len(LOCATIONS) - 1,
            max(0, int(data.get("location_level", 0))),
        )

    def set_resolution(self, resolution):
        self.fullscreen = False
        self.current_resolution = resolution
        self.display = pygame.display.set_mode(resolution)
        self.save_game()

    def set_fullscreen(self):
        info = pygame.display.Info()
        resolution = (info.current_w, info.current_h)
        self.fullscreen = True
        self.current_resolution = resolution
        self.display = pygame.display.set_mode(resolution, pygame.FULLSCREEN)
        self.save_game()

    def logical_mouse_position(self, position):
        display_width, display_height = self.display.get_size()
        scale = min(display_width / WIDTH, display_height / HEIGHT)
        rendered_width = WIDTH * scale
        rendered_height = HEIGHT * scale
        offset_x = (display_width - rendered_width) / 2
        offset_y = (display_height - rendered_height) / 2
        return (
            int((position[0] - offset_x) / scale),
            int((position[1] - offset_y) / scale),
        )

    def draw_settings(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 12, 14, 205))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(170, 110, 880, 590)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=10)
        pygame.draw.rect(self.screen, PANEL_LIGHT, panel, 3, border_radius=10)
        self.screen.blit(
            self.title_font.render("NASTAVENÍ OBRAZU", True, TEXT),
            (panel.x + 30, panel.y + 20),
        )

        self.settings_buttons.clear()
        y = panel.y + 78
        self.settings_buttons["fullscreen"] = pygame.Rect(panel.x + 30, y, 390, 44)

        mode_text = "FULLSCREEN: ZAPNUTO" if self.fullscreen else "FULLSCREEN: VYPNUTO"
        mode_color = GREEN if self.fullscreen else PANEL_LIGHT
        pygame.draw.rect(
            self.screen,
            mode_color,
            self.settings_buttons["fullscreen"],
            border_radius=6,
        )
        label = self.font.render(mode_text, True, TEXT if self.fullscreen else MUTED)
        self.screen.blit(label, label.get_rect(center=self.settings_buttons["fullscreen"].center))

        y += 58
        self.screen.blit(
            self.small_font.render("Rozlišení okna:", True, MUTED),
            (panel.x + 30, y),
        )
        y += 28
        for label_text, resolution in self.resolution_options:
            button = pygame.Rect(panel.x + 30, y, 390, 38)
            self.settings_buttons[resolution] = button
            selected = not self.fullscreen and self.current_resolution == resolution
            button_color = ACCENT if selected else PANEL_LIGHT
            pygame.draw.rect(self.screen, button_color, button, border_radius=6)
            text_color = TEXT if selected else MUTED
            label = self.font.render(label_text, True, text_color)
            self.screen.blit(label, label.get_rect(center=button.center))
            y += 50

        key_x = panel.x + 450
        key_y = panel.y + 78
        self.screen.blit(
            self.small_font.render("KLÁVESY NÁSTROJŮ:", True, MUTED),
            (key_x, key_y),
        )
        key_y += 34
        for drum in self.drums:
            if not drum.owned:
                continue
            button = pygame.Rect(key_x, key_y, 400, 38)
            self.settings_buttons[f"bind:{drum.name}"] = button
            waiting = self.keybind_waiting == drum.name
            pygame.draw.rect(
                self.screen,
                ACCENT if waiting else PANEL_LIGHT,
                button,
                border_radius=6,
            )
            label_text = (
                f"Stiskni klávesu..."
                if waiting
                else f"{drum.name}:  {drum.key_label}"
            )
            label = self.font.render(label_text, True, TEXT)
            self.screen.blit(label, label.get_rect(center=button.center))
            key_y += 46

        close_button = pygame.Rect(350, panel.bottom - 74, 520, 42)
        self.settings_buttons["close"] = close_button
        pygame.draw.rect(self.screen, GREEN, close_button, border_radius=6)
        close_label = self.font.render("Zavřít nastavení  (F10 / ESC)", True, BACKGROUND)
        self.screen.blit(close_label, close_label.get_rect(center=close_button.center))

    def handle_hit(self, drum):
        location_multiplier = LOCATIONS[self.location_level]["multiplier"]
        concert_multiplier = 2 if self.shop.concert_time_left > 0 else 1
        multiplier = location_multiplier * concert_multiplier
        income = drum.hit()
        if income is None:
            return
        earned = round(income * multiplier)
        self.money += earned
        self.save_game()
        self.notice = f"{drum.name}: +{earned} $"
        self.notice_timer = 0.8

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
            if self.settings_open and self.keybind_waiting:
                drum = next(
                    (item for item in self.drums if item.name == self.keybind_waiting),
                    None,
                )
                if event.key == pygame.K_ESCAPE:
                    self.keybind_waiting = None
                    return
                if drum:
                    conflict = next(
                        (
                            item for item in self.drums
                            if item is not drum and item.owned and item.key == event.key
                        ),
                        None,
                    )
                    if conflict:
                        self.notice = f"Klávesa je už přiřazená nástroji {conflict.name}."
                        self.notice_timer = 2.5
                    else:
                        drum.key = event.key
                        drum.key_label = pygame.key.name(event.key).upper()
                        self.save_game()
                        self.notice = f"{drum.name}: klávesa {drum.key_label}"
                        self.notice_timer = 2.0
                self.keybind_waiting = None
                return
            if event.key == pygame.K_ESCAPE:
                if self.settings_open:
                    self.settings_open = False
                else:
                    self.running = False
            elif event.key == pygame.K_F10:
                self.settings_open = not self.settings_open
            if self.settings_open:
                continue_event = False
            else:
                continue_event = True
            if not continue_event:
                return
            if event.key == pygame.K_c:
                self.shop.start_concert(self)
            elif event.key in UPGRADE_KEYS:
                index = UPGRADE_KEYS.index(event.key)
                if index < len(self.drums):
                    self.shop.buy_upgrade(self.drums[index], self)
            elif event.key in SPEED_UPGRADE_KEYS:
                index = SPEED_UPGRADE_KEYS.index(event.key)
                if index < len(self.drums):
                    self.shop.buy_speed_upgrade(self.drums[index], self)
            else:
                for drum in self.drums:
                    if not drum.owned:
                        continue
                    if event.key == drum.key:
                        self.handle_hit(drum)
                        break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            position = self.logical_mouse_position(event.pos)
            if self.settings_open:
                if self.settings_buttons.get("fullscreen").collidepoint(position):
                    if self.fullscreen:
                        self.set_resolution((WIDTH, HEIGHT))
                    else:
                        self.set_fullscreen()
                    return
                for resolution, button in self.settings_buttons.items():
                    if isinstance(resolution, tuple) and button.collidepoint(position):
                        self.set_resolution(resolution)
                        return
                for key, button in self.settings_buttons.items():
                    if isinstance(key, str) and key.startswith("bind:"):
                        drum_name = key.split(":", 1)[1]
                        if button.collidepoint(position):
                            self.keybind_waiting = drum_name
                            return
                if self.settings_buttons.get("close").collidepoint(position):
                    self.settings_open = False
                    return
            if self.settings_open:
                return
            if self.settings_button.collidepoint(position):
                self.settings_open = True
                return
            if self.shop.location_upgrade_button.collidepoint(position):
                self.shop.buy_location(self)
                return
            for drum, button in self.shop.instrument_buttons.items():
                if button.collidepoint(position):
                    self.shop.buy_instrument(drum, self)
                    return
            for drum, button in self.shop.upgrade_buttons.items():
                if button.collidepoint(position):
                    self.shop.buy_upgrade(drum, self)
                    return
            for drum, button in self.shop.speed_upgrade_buttons.items():
                if button.collidepoint(position):
                    self.shop.buy_speed_upgrade(drum, self)
                    return
            if self.shop.concert_button.collidepoint(position):
                self.shop.start_concert(self)
                return
            for drum in self.drums:
                if not drum.owned:
                    continue
                if drum.hit_area.collidepoint(position):
                    self.handle_hit(drum)
                    break

    def update(self, dt):
        self.shop.update(dt)
        for drum in self.drums:
            if drum.owned:
                drum.update(dt)
        self.notice_timer = max(0.0, self.notice_timer - dt)

    def draw_location_background(self):
        location_level = self.location_level
        ground_y = 548

        if location_level == 0:
            pygame.draw.rect(self.screen, (89, 72, 57), (56, 176, 750, 372))
            pygame.draw.rect(self.screen, (55, 49, 43), (56, 176, 750, 22))
            for x in range(80, 780, 72):
                pygame.draw.line(
                    self.screen,
                    (105, 91, 68),
                    (x, 198),
                    (x - 20, ground_y),
                    4,
                )
            pygame.draw.rect(self.screen, (72, 65, 53), (88, 230, 150, 140))
            for x in (110, 220):
                pygame.draw.rect(self.screen, (48, 44, 38), (x, 255, 22, 115))
        elif location_level == 1:
            pygame.draw.rect(self.screen, (97, 139, 104), (56, 176, 750, 372))
            pygame.draw.ellipse(self.screen, (70, 112, 75), (70, 210, 230, 250))
            pygame.draw.ellipse(self.screen, (78, 122, 82), (550, 220, 230, 240))
            pygame.draw.circle(self.screen, (255, 220, 120), (720, 210), 34)
        elif location_level == 2:
            pygame.draw.rect(self.screen, (84, 79, 68), (56, 176, 750, 372))
            pygame.draw.rect(self.screen, (134, 126, 108), (56, 176, 750, 45))
            pygame.draw.rect(self.screen, (66, 72, 75), (100, 245, 170, 120))
            pygame.draw.rect(self.screen, (55, 60, 62), (618, 245, 150, 120))
        elif location_level == 3:
            pygame.draw.rect(self.screen, (115, 105, 89), (56, 176, 750, 372))
            pygame.draw.rect(self.screen, (82, 75, 65), (56, 176, 750, 50))
            for x in (130, 250, 370, 490, 610, 730):
                pygame.draw.line(self.screen, (224, 156, 82), (x, 220), (x, 548), 12)
        else:
            pygame.draw.rect(self.screen, (69, 82, 96), (56, 176, 750, 372))
            pygame.draw.rect(self.screen, (35, 42, 49), (56, 176, 750, 48))
            pygame.draw.polygon(
                self.screen,
                (128, 138, 143),
                ((70, 548), (90, 250), (772, 250), (792, 548)),
            )
            for x in (140, 260, 380, 500, 620, 740):
                pygame.draw.rect(self.screen, (242, 202, 105), (x, 300, 42, 72))

    def draw_concert_crowd(self):
        if self.shop.concert_time_left <= 0:
            return

        elapsed = self.shop.concert_duration - self.shop.concert_time_left
        pulse = int((math.sin(elapsed * 5.0) + 1) * 18)
        stage_y = 170

        pygame.draw.rect(
            self.screen,
            (70, 52, 66),
            (56, stage_y - 18, 750, 150),
            border_radius=6,
        )
        pygame.draw.rect(
            self.screen,
            (238, 119, 74),
            (56, stage_y - 18, 750, 5),
        )

        banner = self.title_font.render("KONCERT", True, (255, 215, 125))
        self.screen.blit(banner, banner.get_rect(center=(431, stage_y + 15)))

        light_colors = [
            (238, 119, 74),
            (151, 204, 139),
            (201, 168, 82),
        ]
        for index, x in enumerate((120, 431, 742)):
            color = tuple(min(255, channel + pulse) for channel in light_colors[index])
            pygame.draw.circle(self.screen, color, (x, stage_y - 8), 9)
            pygame.draw.polygon(
                self.screen,
                tuple(max(30, channel - 55) for channel in color),
                (
                    (x - 7, stage_y),
                    (x - 42, stage_y + 130),
                    (x + 42, stage_y + 130),
                    (x + 7, stage_y),
                ),
            )

        people = [
            (82, 265, (115, 145, 132)),
            (140, 278, (198, 104, 76)),
            (198, 260, (201, 168, 82)),
            (256, 276, (115, 145, 132)),
            (314, 258, (198, 104, 76)),
            (372, 275, (201, 168, 82)),
            (430, 262, (115, 145, 132)),
            (488, 278, (198, 104, 76)),
            (546, 260, (201, 168, 82)),
            (604, 275, (115, 145, 132)),
            (662, 258, (198, 104, 76)),
            (720, 276, (201, 168, 82)),
            (778, 260, (115, 145, 132)),
        ]
        for index, (x, y, shirt) in enumerate(people):
            arm_up = math.sin(elapsed * 7.0 + index * 1.3) > -0.15
            pygame.draw.circle(self.screen, (68, 48, 44), (x, y - 20), 10)
            pygame.draw.rect(self.screen, shirt, (x - 13, y - 10, 26, 39), border_radius=7)
            if arm_up:
                arm_direction = -1 if index % 2 == 0 else 1
                pygame.draw.line(
                    self.screen,
                    (68, 48, 44),
                    (x + arm_direction * 11, y),
                    (x + arm_direction * 24, y - 29),
                    5,
                )
            else:
                pygame.draw.line(
                    self.screen,
                    (68, 48, 44),
                    (x - 11, y),
                    (x - 27, y + 12),
                    5,
                )
                pygame.draw.line(
                    self.screen,
                    (68, 48, 44),
                    (x + 11, y),
                    (x + 27, y + 12),
                    5,
                )

    def draw(self):
        self.screen.fill(BACKGROUND)
        pygame.draw.rect(self.screen, PANEL, (36, 126, 790, 610), border_radius=8)
        pygame.draw.rect(self.screen, PANEL_LIGHT, (56, 548, 750, 2))
        self.draw_location_background()
        self.draw_concert_crowd()
        self.screen.blit(self.title_font.render("DRUM TYCOON", True, TEXT), (42, 34))
        self.screen.blit(self.small_font.render("Zahraj. Vylepšuj. Vyraz na koncert.", True, MUTED), (46, 83))

        balance = self.title_font.render(f"{self.money} $", True, GREEN)
        self.screen.blit(balance, (WIDTH - balance.get_width() - 42, 38))
        self.screen.blit(self.small_font.render("TVÉ PENÍZE", True, MUTED),
                         (WIDTH - balance.get_width() - 42, 82))

        for drum in self.drums:
            if drum.owned:
                drum.draw(self.screen, self.font, self.small_font)
        self.shop.draw(self.screen, self.font, self.small_font, self)

        if self.notice_timer > 0:
            notice_surface = self.font.render(self.notice, True, ACCENT)
            self.screen.blit(notice_surface, (58, 576))
        pygame.draw.rect(self.screen, PANEL_LIGHT, self.settings_button, border_radius=6)
        pygame.draw.circle(
            self.screen,
            MUTED,
            (self.settings_button.left + 30, self.settings_button.centery),
            10,
            3,
        )
        pygame.draw.circle(
            self.screen,
            PANEL_LIGHT,
            (self.settings_button.left + 30, self.settings_button.centery),
            4,
        )
        settings_label = self.font.render("Nastavení  F10", True, TEXT)
        self.screen.blit(
            settings_label,
            settings_label.get_rect(center=self.settings_button.center),
        )

        if self.settings_open:
            self.draw_settings()

        display_width, display_height = self.display.get_size()
        scale = min(display_width / WIDTH, display_height / HEIGHT)
        rendered_width = int(WIDTH * scale)
        rendered_height = int(HEIGHT * scale)
        scaled_screen = pygame.transform.smoothscale(
            self.screen,
            (rendered_width, rendered_height),
        )
        self.display.fill((0, 0, 0))
        self.display.blit(
            scaled_screen,
            ((display_width - rendered_width) // 2, (display_height - rendered_height) // 2),
        )
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
        self.save_game()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    GameManager().run()
