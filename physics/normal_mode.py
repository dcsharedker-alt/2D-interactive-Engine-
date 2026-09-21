import pygame
import math
import random
import sys
import os

# Fix path imports
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from config import Config
from ui.ui_components import Button, IconButton, HSlider, ColorWheelPicker, Modal

class RigidBall:
    def __init__(self, x, y, radius, color, mass=None, density=1.0, restitution=0.7, frozen=False):
        self.x, self.y, self.radius, self.color = x, y, radius, color
        self.density, self.restitution, self.frozen = density, restitution, frozen
        self.mass = mass if mass else density * (math.pi * radius**2)
        self.vx, self.vy, self.fx, self.fy = 0, 0, 0, 0
        self.dragging = False
        self.last_impact_force, self.impact_timer = 0, 0

    def update(self, dt, gravity):
        if self.frozen or self.dragging: return
        self.fy += self.mass * gravity
        ax, ay = self.fx / self.mass, self.fy / self.mass
        self.vx += ax * dt
        self.vy += ay * dt
        self.vx *= 0.995
        self.vy *= 0.995
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.fx, self.fy = 0, 0
        if self.impact_timer > 0: self.impact_timer -= dt

    def draw(self, screen, show_vectors=False, font=None):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, tuple(max(0, c-40) for c in self.color), (int(self.x), int(self.y)), self.radius, 2)
        
        if show_vectors and font:
            # Velocity
            v_mag = math.hypot(self.vx, self.vy)
            if v_mag > 0.1:
                end_x = self.x + (self.vx/v_mag)*50
                end_y = self.y + (self.vy/v_mag)*50
                pygame.draw.line(screen, (0,255,0), (self.x,self.y), (end_x,end_y), 2)
            # Gravity
            pygame.draw.line(screen, (255,165,0), (self.x,self.y), (self.x, self.y+50), 2)
            # Impact
            if self.last_impact_force > 1 and self.impact_timer > 0:
                pygame.draw.circle(screen, (255,255,0), (int(self.x), int(self.y)), int(self.radius + self.last_impact_force), 2)

class AudioManager:
    def __init__(self):
        self.active = False
        try:
            if pygame.mixer.get_init() is None: pygame.mixer.init()
            self.active = True
        except: pass

    def play_hit(self, magnitude):
        if not self.active: return
        freq = 200 + min(1000, magnitude * 100)
        vol = min(1.0, magnitude / 20.0)
        # Generate simple beep
        sample_rate = 44100
        duration = 0.1
        n_samples = int(sample_rate * duration)
        buf = bytearray(n_samples * 2)
        for i in range(n_samples):
            t = i / sample_rate
            val = int(32767 * math.exp(-t*10) * math.sin(2*math.pi*freq*t))
            val = max(-32768, min(32767, val))
            buf[i*2] = val & 0xff
            buf[i*2+1] = (val >> 8) & 0xff
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        sound.set_volume(vol)
        sound.play()

class NormalPhysicsMode:
    def __init__(self, screen, clock, world_config):
        self.screen, self.clock = screen, clock
        self.balls = []
        self.gravity = world_config.get('gravity', 9.8)
        self.show_vectors = False
        self.paused = False
        self.running = True
        self.active_modal = None
        self.audio = AudioManager()
        
        # Toolbar
        self.toolbar_rect = pygame.Rect(20, screen.get_height()//2 - 150, 60, 300)
        self.toolbar_expanded = False
        self.toolbar_buttons = []
        self._init_toolbar()
        
        # Spawn settings
        self.spawn_radius = 20
        self.spawn_color = (random.randint(50,255), random.randint(50,255), random.randint(50,255))
        self.font_small = pygame.font.SysFont("Arial", 14)
        self.font_large = pygame.font.SysFont("Arial", 24)

    def _init_toolbar(self):
        btn_w, btn_h = 40, 40
        start_x = self.toolbar_rect.centerx - btn_w // 2
        # Fixed syntax error here: added 'in buttons_data'
        buttons_data = [
            ("+", self.open_spawn_modal, (50, 200, 50)),
            ("S", self.open_status_modal, (50, 50, 200)),
            ("V", self.toggle_vectors, (200, 200, 50)),
            ("P", self.toggle_pause, (255, 165, 0)),
            ("M", self.open_menu_modal, (100, 100, 100)),
        ]
        
        total_h = len(buttons_data) * (btn_h + 10)
        current_y = self.toolbar_rect.centery - total_h // 2
        
        for label, callback, color in buttons_data:
            rect = pygame.Rect(start_x, current_y, btn_w, btn_h)
            btn = IconButton(rect, label, color)
            btn.callback = callback #type: ignore
            self.toolbar_buttons.append(btn)
            current_y += btn_h + 10

    def open_spawn_modal(self): self.active_modal = SpawnModal(self.screen, self)
    def open_status_modal(self): self.active_modal = StatusModal(self.screen, self)
    def toggle_vectors(self): self.show_vectors = not self.show_vectors
    def toggle_pause(self): self.paused = not self.paused
    def open_menu_modal(self): self.active_modal = MainmenuModal(self.screen, self)

    def handle_event(self, event):
        if self.active_modal:
            if self.active_modal.handle_event(event): self.active_modal = None
            return

        mouse_pos = pygame.mouse.get_pos()
        self.toolbar_expanded = self.toolbar_rect.collidepoint(mouse_pos)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for btn in self.toolbar_buttons:
                    if btn.rect.collidepoint(mouse_pos):
                        btn.handle_event(event)
                        return
                for ball in reversed(self.balls):
                    if math.hypot(ball.x-mouse_pos[0], ball.y-mouse_pos[1]) < ball.radius:
                        ball.dragging = True
                        ball.vx, ball.vy = 0, 0
            elif event.button == 3:
                for ball in self.balls:
                    if math.hypot(ball.x-mouse_pos[0], ball.y-mouse_pos[1]) < ball.radius:
                        self.active_modal = ContextModal(self.screen, self, ball)
                        return
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.paused = not self.paused
            
        if event.type == pygame.MOUSEBUTTONUP:
            for ball in self.balls: ball.dragging = False

    def update(self, dt):
        if self.paused: return
        mouse_pos = pygame.mouse.get_pos()
        mouse_vel = pygame.mouse.get_rel()
        
        for ball in self.balls:
            if ball.dragging:
                ball.x, ball.y = mouse_pos
                ball.vx, ball.vy = mouse_vel[0]*0.5, mouse_vel[1]*0.5
            else:
                ball.update(dt, self.gravity)
                self._resolve_collisions(ball)

    def _resolve_collisions(self, ball):
        w, h = self.screen.get_size()
        hit = False
        force = 0
        
        # Floor
        if ball.y + ball.radius > h - 50:
            ball.y = h - 50 - ball.radius
            if ball.vy > 0:
                force = abs(ball.vy) * ball.mass * 0.5
                ball.vy *= -ball.restitution
                ball.vx *= 0.95
                hit = True
        # Ceiling
        elif ball.y - ball.radius < 0:
            ball.y = ball.radius
            if ball.vy < 0:
                force = abs(ball.vy) * ball.mass * 0.5
                ball.vy *= -ball.restitution
                hit = True
        # Walls
        if ball.x + ball.radius > w:
            ball.x = w - ball.radius
            if ball.vx > 0:
                force = abs(ball.vx) * ball.mass * 0.5
                ball.vx *= -ball.restitution
                hit = True
        elif ball.x - ball.radius < 0:
            ball.x = ball.radius
            if ball.vx < 0:
                force = abs(ball.vx) * ball.mass * 0.5
                ball.vx *= -ball.restitution
                hit = True
        
        if hit and force > 1:
            ball.last_impact_force = force
            ball.impact_timer = 0.5
            self.audio.play_hit(force)

        # Ball-Ball
        for other in self.balls:
            if other == ball: continue
            dx, dy = other.x - ball.x, other.y - ball.y
            dist = math.hypot(dx, dy)
            min_d = ball.radius + other.radius
            if dist < min_d and dist > 0:
                nx, ny = dx/dist, dy/dist
                dvx, dvy = ball.vx - other.vx, ball.vy - other.vy
                vel_n = dvx*nx + dvy*ny
                if vel_n > 0: continue
                e = min(ball.restitution, other.restitution)
                j = -(1+e)*vel_n / (1/ball.mass + 1/other.mass)
                if not ball.frozen:
                    ball.vx += j*nx/ball.mass
                    ball.vy += j*ny/ball.mass
                if not other.frozen:
                    other.vx -= j*nx/other.mass
                    other.vy -= j*ny/other.mass
                # Separate
                overlap = (min_d - dist) / 2
                if not ball.frozen: ball.x -= nx*overlap; ball.y -= ny*overlap
                if not other.frozen: other.x += nx*overlap; other.y += ny*overlap
                
                impact = abs(j)*0.1
                if impact > 1:
                    ball.last_impact_force = impact
                    ball.impact_timer = 0.3
                    self.audio.play_hit(impact)

    def draw(self):
        self.screen.fill((200, 205, 210)) # Light Gray
        
        # Grid
        for x in range(0, self.screen.get_width(), 50):
            pygame.draw.line(self.screen, (180,185,190), (x,0), (x,self.screen.get_height()))
        for y in range(0, self.screen.get_height(), 50):
            pygame.draw.line(self.screen, (180,185,190), (0,y), (self.screen.get_width(),y))
            
        # Ground
        pygame.draw.rect(self.screen, (100,100,100), (0, self.screen.get_height()-50, self.screen.get_width(), 50))

        for ball in self.balls:
            ball.draw(self.screen, self.show_vectors, self.font_small)

        # Toolbar
        w = 200 if self.toolbar_expanded else 60
        tb_rect = pygame.Rect(self.toolbar_rect.x, self.toolbar_rect.y, w, self.toolbar_rect.height)
        pygame.draw.rect(self.screen, (40,44,50), tb_rect, border_radius=15)
        
        for btn in self.toolbar_buttons:
            btn.draw(self.screen)
            if self.toolbar_expanded and btn.rect.collidepoint(pygame.mouse.get_pos()):
                tip = ""
                if btn.label == "+": tip = "Spawn"
                elif btn.label == "S": tip = "Stats"
                elif btn.label == "V": tip = "Vectors"
                elif btn.label == "P": tip = "Pause"
                elif btn.label == "M": tip = "Menu"
                if tip:
                    txt = self.font_small.render(tip, True, (255,255,255))
                    bg = txt.get_rect().inflate(10,5)
                    bg.midleft = (tb_rect.right+10, btn.rect.centery)
                    pygame.draw.rect(self.screen, (0,0,0), bg, border_radius=5)
                    self.screen.blit(txt, bg)

        if self.active_modal: self.active_modal.draw()
        
        if self.paused:
            s = pygame.Surface((self.screen.get_width(), self.screen.get_height())); s.set_alpha(100); s.fill((0,0,0))
            self.screen.blit(s, (0,0))
            txt = self.font_large.render("PAUSED", True, (255,255,255))
            self.screen.blit(txt, (self.screen.get_width()//2-txt.get_width()//2, self.screen.get_height()//2))

    def spawn_ball(self):
        x, y = self.screen.get_width()//2, 100
        self.balls.append(RigidBall(x, y, self.spawn_radius, self.spawn_color))
        self.audio.play_hit(0.5)

# Modals
class SpawnModal(Modal):
    def __init__(self, screen, parent):
        super().__init__(screen, "Spawn", 300, 400)
        self.parent = parent
        self.add_slider("Radius", 5, 100, parent.spawn_radius, lambda v: setattr(parent, 'spawn_radius', int(v)))
        btn = Button(pygame.Rect(self.content_rect.x, self.content_rect.bottom-40, 100, 30), "Spawn")
        btn.callback = parent.spawn_ball
        self.elements.append(('btn', btn))
    
    def draw(self):
        super().draw()
        for item in self.elements:
            if item[0] == 'btn': item[1].draw(self.screen)
    def handle_event(self, event):
        if super().handle_event(event): return True
        for item in self.elements:
            if item[0] == 'btn': item[1].handle_event(event)
        return False

class StatusModal(Modal):
    def __init__(self, screen, parent):
        super().__init__(screen, "Status", 250, 150)
        self.parent = parent
    def draw(self):
        super().draw()
        txt = self.small_font.render(f"Objects: {len(self.parent.balls)}", True, (255,255,255))
        self.screen.blit(txt, (self.content_rect.x, self.content_rect.y))

class ContextModal(Modal):
    def __init__(self, screen, parent, ball):
        super().__init__(screen, "Object", 250, 200)
        self.ball = ball
        self.parent = parent
        btn = Button(pygame.Rect(self.content_rect.x, self.content_rect.y+50, 100, 30), "Delete")
        btn.callback = lambda: parent.balls.remove(ball) if ball in parent.balls else None
        self.elements.append(('btn', btn))
    def draw(self):
        super().draw()
        for item in self.elements:
            if item[0] == 'btn': item[1].draw(self.screen)
    def handle_event(self, event):
        if super().handle_event(event): return True
        for item in self.elements:
            if item[0] == 'btn': item[1].handle_event(event)
        return False

class MainmenuModal(Modal):
    def __init__(self, screen, parent):
        super().__init__(screen, "Menu", 200, 150)
        btn = Button(pygame.Rect(self.content_rect.x+20, self.content_rect.y+50, 160, 40), "Exit")
        btn.callback = lambda: setattr(parent, 'running', False)
        self.elements.append(('btn', btn))
    def draw(self):
        super().draw()
        for item in self.elements:
            if item[0] == 'btn': item[1].draw(self.screen)
    def handle_event(self, event):
        if super().handle_event(event): return True
        for item in self.elements:
            if item[0] == 'btn': item[1].handle_event(event)
        return False