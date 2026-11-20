"""Zaklad hry Drum Tycoon: hrani na bici a vydelavani penez."""

import sys
import math

import pygame


WIDTH = 1220
HEIGHT = 780
FPS = 60
UPGRADE_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3)

BACKGROUND = (21, 27, 31)
PANEL = (34, 43, 47)
PANEL_LIGHT = (47, 58, 61)
TEXT = (239, 237, 222)
MUTED = (155, 168, 164)
ACCENT = (238, 119, 74)
GREEN = (151, 204, 139)
RED = (222, 105, 94)


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
        self.cooldown = cooldown
        self.cooldown_left = 0.0

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

        if self.name == "Kopák":
            pygame.draw.ellipse(surface, shadow, self.hit_area.move(0, 12))
            pygame.draw.ellipse(surface, color, self.hit_area)
            pygame.draw.ellipse(surface, (224, 222, 204), self.hit_area, 5)
            center = self.hit_area.center
            pygame.draw.circle(surface, (34, 43, 47), center, 43)
            pygame.draw.circle(surface, (224, 222, 204), center, 43, 3)
            pygame.draw.circle(surface, (34, 43, 47), center, 7)
        elif self.name == "Snare":
            pygame.draw.ellipse(surface, shadow, self.hit_area.move(0, 10))
            pygame.draw.ellipse(surface, color, self.hit_area)
            pygame.draw.ellipse(surface, (235, 231, 211), self.hit_area, 5)
            pygame.draw.ellipse(surface, (235, 231, 211), self.hit_area.inflate(-24, -18), 2)
        else:
            center_x, center_y = self.hit_area.center
            pygame.draw.line(surface, (180, 190, 185), (center_x, center_y),
                             (center_x, center_y + 110), 7)
            pygame.draw.ellipse(surface, shadow, self.hit_area.move(0, 10))
            pygame.draw.ellipse(surface, color, self.hit_area)
            pygame.draw.ellipse(surface, (245, 204, 113), self.hit_area, 4)
            pygame.draw.circle(surface, (255, 229, 160), (center_x, center_y), 7)

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
        self.concert_button = pygame.Rect(882, 622, 300, 58)
        self.concert_cost = 40
        self.concert_duration = 10.0
        self.concert_time_left = 0.0

    def buy_upgrade(self, drum, game):
        if game.money < drum.upgrade_cost:
            game.notice = "Na vylepšení zatím nemáš dost peněz."
            game.notice_timer = 2.0
            return
        game.money -= drum.upgrade_cost
        drum.upgrade()
        game.notice = f"{drum.name} vylepšen!"
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
        game.notice = "Koncert začal: výdělky jsou 2x!"
        game.notice_timer = 2.0

    def update(self, dt):
        self.concert_time_left = max(0.0, self.concert_time_left - dt)

    def draw(self, surface, font, small_font, game):
        pygame.draw.rect(surface, PANEL, (852, 126, 332, 610), border_radius=8)
        surface.blit(font.render("DÍLNA", True, TEXT), (882, 150))
        surface.blit(small_font.render("Vylepšení zvýší odměnu za každý úder.", True, MUTED), (882, 181))
        surface.blit(small_font.render("Klávesy 1–3 | koncert C", True, MUTED), (882, 202))

        self.upgrade_buttons.clear()
        for index, drum in enumerate(self.drums):
            y = 225 + index * 112
            button = pygame.Rect(882, y + 51, 300, 42)
            self.upgrade_buttons[drum] = button
            pygame.draw.line(surface, PANEL_LIGHT, (882, y + 37), (1182, y + 37), 1)
            surface.blit(font.render(f"{drum.name}  |  úroveň {drum.level}", True, TEXT), (882, y))
            surface.blit(small_font.render(f"{drum.income} $ za úder", True, GREEN), (882, y + 27))
            affordable = game.money >= drum.upgrade_cost
            button_color = GREEN if affordable else PANEL_LIGHT
            pygame.draw.rect(surface, button_color, button, border_radius=5)
            label_color = BACKGROUND if affordable else MUTED
            label = small_font.render(
                f"{index + 1}  Lepší {drum.name}  -  {drum.upgrade_cost} $",
                True,
                label_color,
            )
            surface.blit(label, label.get_rect(center=button.center))

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
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 23)
        self.title_font = pygame.font.Font(None, 48)
        self.money = 0
        self.running = True
        self.notice = "Zahraj na bici a vydelavej!"
        self.notice_timer = 3.0

        self.drums = [
            Drum("Snare", pygame.K_j, "J", 2, 30, (198, 104, 76), (140, 315, 180, 82), 0.55),
            Drum("Kopák", pygame.K_SPACE, "MEZERNÍK", 3, 40, (115, 145, 132), (355, 410, 235, 170), 0.80),
            Drum("Činel", pygame.K_k, "K", 2, 35, (201, 168, 82), (575, 275, 205, 62), 0.65),
        ]
        self.shop = Shop(self.drums)

    def handle_hit(self, drum):
        multiplier = 2 if self.shop.concert_time_left > 0 else 1
        income = drum.hit()
        if income is None:
            return
        earned = income * multiplier
        self.money += earned
        self.notice = f"{drum.name}: +{earned} $"
        self.notice_timer = 0.8

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_c:
                self.shop.start_concert(self)
            elif event.key in UPGRADE_KEYS:
                index = UPGRADE_KEYS.index(event.key)
                if index < len(self.drums):
                    self.shop.buy_upgrade(self.drums[index], self)
            else:
                for drum in self.drums:
                    if event.key == drum.key:
                        self.handle_hit(drum)
                        break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for drum, button in self.shop.upgrade_buttons.items():
                if button.collidepoint(event.pos):
                    self.shop.buy_upgrade(drum, self)
                    return
            if self.shop.concert_button.collidepoint(event.pos):
                self.shop.start_concert(self)
                return
            for drum in self.drums:
                if drum.hit_area.collidepoint(event.pos):
                    self.handle_hit(drum)
                    break

    def update(self, dt):
        self.shop.update(dt)
        for drum in self.drums:
            drum.update(dt)
        self.notice_timer = max(0.0, self.notice_timer - dt)

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
        self.draw_concert_crowd()
        self.screen.blit(self.title_font.render("DRUM TYCOON", True, TEXT), (42, 34))
        self.screen.blit(self.small_font.render("Zahraj. Vylepšuj. Vyraz na koncert.", True, MUTED), (46, 83))

        balance = self.title_font.render(f"{self.money} $", True, GREEN)
        self.screen.blit(balance, (WIDTH - balance.get_width() - 42, 38))
        self.screen.blit(self.small_font.render("TVÉ PENÍZE", True, MUTED),
                         (WIDTH - balance.get_width() - 42, 82))

        for drum in self.drums:
            drum.draw(self.screen, self.font, self.small_font)
        self.shop.draw(self.screen, self.font, self.small_font, self)

        if self.notice_timer > 0:
            notice_surface = self.font.render(self.notice, True, ACCENT)
            self.screen.blit(notice_surface, (58, 576))
        self.screen.blit(self.small_font.render("ESC  ukončit", True, MUTED), (58, 697))
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    GameManager().run()
