import pygame
import random
import math
import json
import os

pygame.init()
info = pygame.display.Info()
W, H = info.current_w, info.current_h
screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
clock = pygame.time.Clock()

font_m = pygame.font.SysFont('sans-serif', 100, bold=True)
font_s = pygame.font.SysFont('sans-serif', 50, bold=True)

CLR_BG = (10, 10, 25)
CLR_PLAT = (45, 55, 85)
CLR_COIN = (255, 215, 0)
CLR_ENEMY = (255, 60, 100)
CLR_ACCENT = (0, 210, 255)

GRAVITY, JUMP_PWR, SPEED = 1.5, -45, 18
SAVE_FILE = "save.dat"

b_rad = H // 12
pad = 80
rect_l = pygame.Rect(pad, H - b_rad*2 - pad, b_rad*2, b_rad*2)
rect_r = pygame.Rect(pad*2 + b_rad*2, H - b_rad*2 - pad, b_rad*2, b_rad*2)
rect_j = pygame.Rect(W - b_rad*2 - pad, H - b_rad*2 - pad, b_rad*2, b_rad*2)
rect_p = pygame.Rect(W - 120, 40, 80, 80)

def draw_modern_btn(surf, rect, color, active, icon_type, text=""):
    cx, cy = rect.center
    r = rect.width // 2 if icon_type != "rect" else 0
    if active:
        pygame.draw.rect(surf, color, (rect.x, rect.y + 4, rect.w, rect.h), border_radius=15) if icon_type=="rect" else pygame.draw.circle(surf, color, (cx, cy + 4), r)
        pygame.draw.rect(surf, (255,255,255), (rect.x, rect.y + 4, rect.w, rect.h), 4, border_radius=15) if icon_type=="rect" else pygame.draw.circle(surf, (255,255,255), (cx, cy + 4), r, 4)
    else:
        pygame.draw.rect(surf, (30,35,60), rect, border_radius=15) if icon_type=="rect" else pygame.draw.circle(surf, (30,35,60), (cx, cy), r)
        pygame.draw.rect(surf, color, rect, 3, border_radius=15) if icon_type=="rect" else pygame.draw.circle(surf, color, (cx, cy), r, 3)
    off = 4 if active else 0
    if text:
        txt = font_s.render(text, True, (255, 255, 255))
        surf.blit(txt, (cx - txt.get_width()//2, cy - txt.get_height()//2 + off))
    elif icon_type == "left":
        pygame.draw.polygon(surf, (255,255,255), [(cx+r*0.3, cy-r*0.4+off), (cx+r*0.3, cy+r*0.4+off), (cx-r*0.3, cy+off)])
    elif icon_type == "right":
        pygame.draw.polygon(surf, (255,255,255), [(cx-r*0.3, cy-r*0.4+off), (cx-r*0.3, cy+r*0.4+off), (cx+r*0.3, cy+off)])
    elif icon_type == "jump":
        pygame.draw.polygon(surf, (255,255,255), [(cx-r*0.4, cy+r*0.3+off), (cx+r*0.4, cy+r*0.3+off), (cx, cy-r*0.4+off)])

class Enemy:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect.x, rect.y - 45, 45, 45)
        self.start, self.end, self.vel = rect.left, rect.right - 45, 8
    def move(self):
        self.rect.x += self.vel
        if self.rect.x <= self.start or self.rect.x >= self.end: self.vel *= -1

class Game:
    def __init__(self):
        self.skins = [(0, 210, 255), (255, 80, 255), (80, 255, 150), (255, 255, 255)]
        self.load_data()
        self.state = "MENU"
        self.b_start = pygame.Rect(W//2-200, H//2-160, 400, 100)
        self.b_skin = pygame.Rect(W//2-200, H//2-40, 400, 100)
        self.b_reset = pygame.Rect(W//2-200, H//2+80, 400, 100)
        self.b_exit = pygame.Rect(W//2-200, H//2+200, 400, 100)
        self.b_to_menu = pygame.Rect(W//2-200, H*0.75, 400, 100)
        self.reset_game()

    def load_data(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                self.wallet = data.get("wallet", 0)
                self.high_score = data.get("high_score", 0)
                self.s_idx = data.get("s_idx", 0)
        else:
            self.wallet, self.high_score, self.s_idx = 0, 0, 0

    def save_data(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump({"wallet": self.wallet, "high_score": self.high_score, "s_idx": self.s_idx}, f)

    def reset_all_data(self):
        self.wallet, self.high_score, self.s_idx = 0, 0, 0
        self.save_data()

    def reset_game(self):
        self.px, self.py, self.p_vel_y, self.score, self.on_ground = W//2, H-300, 0, 0, False
        self.camera_y, self.particles, self.touches = self.py-H//2, [], {}
        self.platforms = [pygame.Rect(0, H-100, W, 100)]
        self.coins, self.enemies = [], []
        for i in range(1, 15): self.add_plat(H-(i*250))

    def add_plat(self, y):
        pw = random.randint(350, 550)
        new_p = pygame.Rect(random.randint(50, W - pw - 50), y, pw, 80)
        self.platforms.append(new_p)
        if random.random() > 0.7: self.coins.append(pygame.Rect(new_p.centerx-25, new_p.top-60, 50, 50))
        if random.random() > 0.8: self.enemies.append(Enemy(new_p))

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: self.save_data(); return
                if e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION):
                    tx, ty = e.x*W, e.y*H
                    self.touches[e.finger_id] = (tx, ty)
                    if self.state == "MENU":
                        if self.b_start.collidepoint(tx, ty): self.state = "PLAYING"; self.reset_game()
                        elif self.b_skin.collidepoint(tx, ty): self.s_idx = (self.s_idx + 1) % len(self.skins)
                        elif self.b_reset.collidepoint(tx, ty): self.reset_all_data()
                        elif self.b_exit.collidepoint(tx, ty): self.save_data(); return
                    elif self.state == "PLAYING" and rect_p.collidepoint(tx, ty): self.state = "PAUSE"
                    elif self.state == "PAUSE" and rect_p.collidepoint(tx, ty): self.state = "PLAYING"
                    elif self.state == "OVER" and self.b_to_menu.collidepoint(tx, ty): self.state = "MENU"
                if e.type == pygame.FINGERUP:
                    if e.finger_id in self.touches: del self.touches[e.finger_id]
            if self.state == "MENU": self.draw_m()
            elif self.state == "PLAYING": self.upd(); self.draw_g()
            elif self.state == "PAUSE": self.draw_g(); self.draw_p()
            elif self.state == "OVER": self.draw_o()
            pygame.display.flip(); clock.tick(60)

    def upd(self):
        ml, mr, j = False, False, False
        for tx, ty in self.touches.values():
            if rect_l.collidepoint(tx, ty): ml = True
            elif rect_r.collidepoint(tx, ty): mr = True
            elif rect_j.collidepoint(tx, ty): j = True
        if ml: self.px -= SPEED
        if mr: self.px += SPEED
        if j and self.on_ground: self.p_vel_y = JUMP_PWR
        self.p_vel_y += GRAVITY; self.py += self.p_vel_y
        self.camera_y += (self.py - H//2 - self.camera_y) * 0.12
        p_r = pygame.Rect(self.px, self.py, 80, 80)
        self.on_ground = False
        for pl in self.platforms:
            if p_r.colliderect(pl) and self.p_vel_y > 0 and self.py+75 <= pl.top+30:
                self.py, self.p_vel_y, self.on_ground = pl.top-80, 0, True
        for en in self.enemies:
            en.move()
            if p_r.colliderect(en.rect): self.die()
        for c in self.coins[:]:
            if p_r.colliderect(c): self.p_vel_y = -55; self.coins.remove(c); self.score += 1000
        if self.platforms[-1].top - self.camera_y > -600: self.add_plat(self.platforms[-1].top-250)
        self.score = max(self.score, int(-self.py // 10 + H // 10))
        if self.py - self.camera_y > H + 500: self.die()

    def die(self):
        self.state = "OVER"
        self.high_score = max(self.high_score, self.score)
        self.wallet += self.score
        self.save_data()

    def draw_m(self):
        screen.fill(CLR_BG); time = pygame.time.get_ticks() * 0.005
        for i in range(8):
            x, y = W//2+math.sin(time+i)*200, H//2+math.cos(time*0.5+i)*150
            pygame.draw.circle(screen, (30, 45, 90), (int(x), int(y)), 100, 2)
        draw_modern_btn(screen, self.b_start, (0, 180, 0), any(self.b_start.collidepoint(t) for t in self.touches.values()), "rect", "ИГРАТЬ")
        draw_modern_btn(screen, self.b_skin, (80, 80, 80), any(self.b_skin.collidepoint(t) for t in self.touches.values()), "rect", "СКИН")
        draw_modern_btn(screen, self.b_reset, (200, 100, 0), any(self.b_reset.collidepoint(t) for t in self.touches.values()), "rect", "СБРОС")
        draw_modern_btn(screen, self.b_exit, (180, 0, 0), any(self.b_exit.collidepoint(t) for t in self.touches.values()), "rect", "ВЫХОД")
        screen.blit(font_m.render("УЛЬТРА ПРЫЖОК", True, self.skins[self.s_idx]), (W//2-300, H//8))
        screen.blit(font_s.render(f"КОШЕЛЕК: {self.wallet}", True, CLR_COIN), (40, 40))
        screen.blit(font_s.render(f"РЕКОРД: {self.high_score}", True, CLR_ACCENT), (W-350, 40))

    def draw_g(self):
        screen.fill(CLR_BG)
        for pl in self.platforms:
            pygame.draw.rect(screen, CLR_PLAT, pl.move(0, -self.camera_y), border_radius=22)
            pygame.draw.rect(screen, (70, 85, 120), pl.move(0, -self.camera_y), 4, border_radius=22)
        for c in self.coins:
            pygame.draw.circle(screen, CLR_COIN, (c.centerx, int(c.centery-self.camera_y)), 25)
            pygame.draw.circle(screen, (255,255,255), (c.centerx, int(c.centery-self.camera_y)), 25, 3)
        for en in self.enemies: pygame.draw.rect(screen, CLR_ENEMY, en.rect.move(0, -self.camera_y), border_radius=12)
        pygame.draw.rect(screen, self.skins[self.s_idx], (self.px, self.py-self.camera_y, 80, 80), border_radius=18)
        pygame.draw.rect(screen, (255,255,255), (self.px, self.py-self.camera_y, 80, 80), 4, border_radius=18)
        draw_modern_btn(screen, rect_l, CLR_ACCENT, any(rect_l.collidepoint(t) for t in self.touches.values()), "left")
        draw_modern_btn(screen, rect_r, CLR_ACCENT, any(rect_r.collidepoint(t) for t in self.touches.values()), "right")
        draw_modern_btn(screen, rect_j, CLR_ENEMY, any(rect_j.collidepoint(t) for t in self.touches.values()), "jump")
        pygame.draw.rect(screen, (100, 100, 100), rect_p, border_radius=10)
        screen.blit(font_s.render("||", True, (255,255,255)), (W-105, 55))
        screen.blit(font_s.render(f"СЧЕТ: {self.score}", True, (255,255,255)), (40, 40))

    def draw_p(self):
        s = pygame.Surface((W, H)); s.set_alpha(150); s.fill((0,0,0)); screen.blit(s, (0,0))
        screen.blit(font_m.render("ПАУЗА", True, (255,255,255)), (W//2-150, H//2-50))

    def draw_o(self):
        screen.fill((30, 10, 20))
        screen.blit(font_m.render("КОНЕЦ ИГРЫ", True, CLR_ENEMY), (W//2-300, H//4))
        screen.blit(font_s.render(f"СЧЕТ: {self.score}", True, (255,255,255)), (W//2-130, H//2))
        screen.blit(font_s.render(f"РЕКОРД: {self.high_score}", True, CLR_ACCENT), (W//2-140, H//2+70))
        draw_modern_btn(screen, self.b_to_menu, (100, 100, 100), any(self.b_to_menu.collidepoint(t) for t in self.touches.values()), "rect", "МЕНЮ")

if __name__ == "__main__":
    Game().run()
    pygame.quit()
    