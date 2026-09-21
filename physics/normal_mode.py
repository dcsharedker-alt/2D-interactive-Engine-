import pygame
import math
import random
import sys
import os

# Add parent directory to path so we can find 'config' and 'ui'
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from config import Config
from ui.ui_components import Button, IconButton, FloatInput, HSlider, ColorWheelPicker, Modal

class RigidBall:
    def __init__(self, x, y, radius, color, mass=None, density=1.0, restitution=0.7, frozen=False):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.density = density
        self.restitution = restitution
        self.frozen = frozen
        
        if mass is None:
            self.mass = density * (math.pi * radius**2)
        else:
            self.mass = mass
            
        self.vx = 0
        self.vy = 0
        self.fx = 0
        self.fy = 0
        self.dragging = False
        self.last_impact_force = 0
        self.impact_timer = 0

    def apply_force(self, fx, fy):
        if not self.frozen:
            self.fx += fx
            self.fy += fy

    def update(self, dt, gravity, drag_coefficient=0.995):
        if self.frozen or self.dragging:
            return

        self.fy += self.mass * gravity
        ax = self.fx / self.mass
        ay = self.fy / self.mass
        self.vx += ax * dt
        self.vy += ay * dt
        self.vx *= drag_coefficient
        self.vy *= drag_coefficient
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.fx = 0
        self.fy = 0

        if self.impact_timer > 0:
            self.impact_timer -= dt
            if self.impact_timer <= 0:
                self.last_impact_force = 0

    def draw(self, screen, show_vectors=False, vector_scale=1.0, show_values=False, font=None):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        border_color = tuple(max(0, c - 40) for c in self.color)
        pygame.draw.circle(screen, border_color, (int(self.x), int(self.y)), self.radius, 2)

        if show_vectors and font:
            vec_len = 10 * vector_scale
            
            # Velocity (Green)
            v_mag = math.hypot(self.vx, self.vy)
            if v_mag > 0.1:
                end_x = self.x + (self.vx / v_mag) * vec_len * 5
                end_y = self.y + (self.vy / v_mag) * vec_len * 5
                pygame.draw.line(screen, (0, 255, 0), (self.x, self.y), (end_x, end_y), 2)
                pygame.draw.circle(screen, (0, 255, 0), (int(end_x), int(end_y)), 3)
                if show_values:
                    txt = font.render(f"{v_mag:.1f}", True, (0, 255, 0))
                    screen.blit(txt, (end_x + 5, end_y))

            # Gravity (Orange)
            g_end_y = self.y + vec_len * 5
            pygame.draw.line(screen, (255, 165, 0), (self.x, self.y), (self.x, g_end_y), 2)
            pygame.draw.circle(screen, (255, 165, 0), (int(self.x), int(g_end_y)), 3)
            
            # Impact Force (Yellow)
            if self.last_impact_force > 0.5 and self.impact_timer > 0:
                alpha = min(255, int(self.impact_timer * 255))
                imp_surf = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
                center = (self.radius * 2, self.radius * 2)
                width = max(1, int(self.last_impact_force * 2))
                pygame.draw.circle(imp_surf, (255, 255, 0, alpha), center, self.radius + 5 + int(self.last_impact_force), width)
                screen.blit(imp_surf, (self.x - self.radius*2, self.y - self.radius*2))


class AudioManager:
    def __init__(self):
        self.mixer_initialized = False
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.mixer_initialized = True
        except Exception as e:
            print(f"Audio init failed: {e}")
            self.mixer_initialized = False

    def generate_hit_sound(self, frequency, duration):
        if not self.mixer_initialized:
            return None
        
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = bytearray(n_samples * 2)
        
        for i in range(n_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 15) 
            val = int(32767 * envelope * math.sin(2 * math.pi * frequency * t * (1 - t*0.5)))
            val = max(-32768, min(32767, val))
            buf[i*2] = val & 0xff
            buf[i*2+1] = (val >> 8) & 0xff
            buf[i*2] = val & 0xff
            buf[i*2+1] = (val >> 8) & 0xff

        return pygame.mixer.Sound(buffer=bytes(buf))

    def play_hit(self, impact_magnitude):
        if not self.mixer_initialized:
            return

        base_freq = 200
        max_freq = 1200
        freq = base_freq + (impact_magnitude * 800)
        freq = min(freq, max_freq)
        
        vol = min(1.0, impact_magnitude / 15.0)
        
        sound = self.generate_hit_sound(freq, 0.15)
        if sound:
            sound.set_volume(vol)
            sound.play()

    def play_music(self, filename, loops=-1):
        if not self.mixer_initialized:
            return
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play(loops)
        except Exception as e:
            print(f"Music load failed: {e}")

    def stop_music(self):
        if self.mixer_initialized:
            pygame.mixer.music.stop()


class NormalPhysicsMode:
    def __init__(self, screen, clock, world_config):
        self.screen = screen
        self.clock = clock
        self.config = Config()
        self.world_config = world_config
        
        self.running = True
        self.paused = False
        
        self.balls = []
        self.particles = []
        
        self.gravity = world_config.get('gravity', 9.8)
        self.show_vectors = False
        self.show_vector_values = False
        self.vector_scale = 1.0
        
        # Toolbar: Left Center, Rounded
        self.toolbar_rect = pygame.Rect(20, screen.get_height()//2 - 150, 60, 300)
        self.toolbar_expanded = False
        self.active_modal = None
        
        self.spawn_radius = 20
        self.spawn_density = 1.0
        self.spawn_restitution = 0.7
        self.spawn_color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        
        self.audio = AudioManager()
        
        self.font_small = pygame.font.SysFont("Arial", 14)
        self.font_med = pygame.font.SysFont("Arial", 18)
        self.font_large = pygame.font.SysFont("Arial", 24)

        self.init_toolbar()

    def init_toolbar(self):
        btn_w, btn_h = 40, 40
        start_x = self.toolbar_rect.centerx - btn_w // 2
        
        buttons_data = [
            ("+", self.open_spawn_modal, (50, 200, 50)),
            ("S", self.open_status_modal, (50, 50, 200)),
            ("V", self.toggle_vectors, (200, 200, 50)),
            ("P", self.toggle_pause, (255, 165, 0)),
            ("M", self.open_menu_modal, (100, 100, 100)),
        ]
        
        self.toolbar_buttons = []
        total_h = len(buttons_data) * (btn_h + 10)
        current_y = self.toolbar_rect.centery - total_h // 2
        
        for label, callback, color in buttons_data:
            rect = pygame.Rect(start_x, current_y, btn_w, btn_h)
            btn = IconButton(rect, label, color, hover_color=tuple(min(255, c+40) for c in color))
            btn.callback = callback
            self.toolbar_buttons.append(btn)
            current_y += btn_h + 10

    def open_spawn_modal(self):
        if self.active_modal: return
        self.active_modal = SpawnModal(self.screen, self)

    def open_status_modal(self):
        if self.active_modal: return
        self.active_modal = StatusModal(self.screen, self)

    def toggle_vectors(self):
        self.show_vectors = not self.show_vectors

    def toggle_pause(self):
        self.paused = not self.paused

    def open_menu_modal(self):
        if self.active_modal: return
        self.active_modal = MainmenuModal(self.screen, self)

    def handle_event(self, event):
        if self.active_modal:
            if self.active_modal.handle_event(event):
                self.active_modal = None
            return

        mouse_pos = pygame.mouse.get_pos()
        if self.toolbar_rect.collidepoint(mouse_pos):
            self.toolbar_expanded = True
        else:
            self.toolbar_expanded = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for btn in self.toolbar_buttons:
                    if btn.rect.collidepoint(mouse_pos):
                        btn.click()
                        return
                
                for ball in reversed(self.balls):
                    dist = math.hypot(ball.x - mouse_pos[0], ball.y - mouse_pos[1])
                    if dist < ball.radius:
                        ball.dragging = True
                        ball.vx = 0
                        ball.vy = 0
                        return
            
            elif event.button == 3:
                for ball in self.balls:
                    dist = math.hypot(ball.x - mouse_pos[0], ball.y - mouse_pos[1])
                    if dist < ball.radius:
                        self.active_modal = ContextModal(self.screen, self, ball)
                        return

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                for ball in self.balls:
                    if ball.dragging:
                        ball.dragging = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.paused = not self.paused

    def update(self, dt):
        if self.paused:
            return

        mouse_pos = pygame.mouse.get_pos()
        mouse_vel = pygame.mouse.get_rel()
        
        for ball in self.balls:
            if ball.dragging:
                ball.x = mouse_pos[0]
                ball.y = mouse_pos[1]
                ball.vx = mouse_vel[0] * 0.5 
                ball.vy = mouse_vel[1] * 0.5
            else:
                ball.update(dt, self.gravity)
                self.resolve_collisions(ball)

    def resolve_collisions(self, ball):
        width, height = self.screen.get_size()
        collided = False
        impact_force = 0

        # Floor
        if ball.y + ball.radius > height - 50:
            ball.y = height - 50 - ball.radius
            if ball.vy > 0:
                impact_force = abs(ball.vy) * ball.mass * 0.5
                ball.vy *= -ball.restitution
                ball.vx *= 0.95
                collided = True
        
        # Ceiling
        elif ball.y - ball.radius < 0:
            ball.y = ball.radius
            if ball.vy < 0:
                impact_force = abs(ball.vy) * ball.mass * 0.5
                ball.vy *= -ball.restitution
                collided = True

        # Walls
        if ball.x + ball.radius > width:
            ball.x = width - ball.radius
            if ball.vx > 0:
                impact_force = abs(ball.vx) * ball.mass * 0.5
                ball.vx *= -ball.restitution
                collided = True
        elif ball.x - ball.radius < 0:
            ball.x = ball.radius
            if ball.vx < 0:
                impact_force = abs(ball.vx) * ball.mass * 0.5
                ball.vx *= -ball.restitution
                collided = True

        if collided and impact_force > 1.0:
            ball.last_impact_force = impact_force
            ball.impact_timer = 0.5
            self.audio.play_hit(impact_force)

        # Ball to Ball
        for other in self.balls:
            if other == ball: continue
            dx = other.x - ball.x
            dy = other.y - ball.y
            dist = math.hypot(dx, dy)
            min_dist = ball.radius + other.radius

            if dist < min_dist and dist > 0:
                nx = dx / dist
                ny = dy / dist
                
                dvx = ball.vx - other.vx
                dvy = ball.vy - other.vy
                vel_along_normal = dvx * nx + dvy * ny

                if vel_along_normal > 0: continue

                e = min(ball.restitution, other.restitution)
                j = -(1 + e) * vel_along_normal
                j /= (1/ball.mass + 1/other.mass)

                ix = j * nx
                iy = j * ny
                
                if not ball.frozen:
                    ball.vx += ix / ball.mass
                    ball.vy += iy / ball.mass
                if not other.frozen:
                    other.vx -= ix / other.mass
                    other.vy -= iy / other.mass

                overlap = min_dist - dist
                corr = overlap / 2.0
                if not ball.frozen:
                    ball.x -= nx * corr
                    ball.y -= ny * corr
                if not other.frozen:
                    other.x += nx * corr
                    other.y += ny * corr
                
                impact = abs(j) * 0.1
                if impact > 1.0:
                    ball.last_impact_force = impact
                    ball.impact_timer = 0.3
                    other.last_impact_force = impact
                    other.impact_timer = 0.3
                    self.audio.play_hit(impact)

    def draw(self):
        # Light Gray Background
        self.screen.fill((200, 205, 210))
        
        # Subtle Grid
        grid_size = 50
        for x in range(0, self.screen.get_width(), grid_size):
            pygame.draw.line(self.screen, (180, 185, 190), (x, 0), (x, self.screen.get_height()), 1)
        for y in range(0, self.screen.get_height(), grid_size):
            pygame.draw.line(self.screen, (180, 185, 190), (0, y), (self.screen.get_width(), y), 1)
            
        # Ground
        pygame.draw.rect(self.screen, (100, 100, 100), (0, self.screen.get_height()-50, self.screen.get_width(), 50))
        pygame.draw.line(self.screen, (50, 50, 50), (0, self.screen.get_height()-50), (self.screen.get_width(), self.screen.get_height()-50), 2)

        for ball in self.balls:
            ball.draw(self.screen, self.show_vectors, self.vector_scale, self.show_vector_values, self.font_small)

        # Toolbar (Rounded Rectangle)
        current_w = 200 if self.toolbar_expanded else 60
        toolbar_draw_rect = pygame.Rect(self.toolbar_rect.x, self.toolbar_rect.y, current_w, self.toolbar_rect.height)
        
        pygame.draw.rect(self.screen, (40, 44, 50), toolbar_draw_rect, border_radius=15)
        pygame.draw.rect(self.screen, (70, 75, 85), toolbar_draw_rect, 2, border_radius=15)
        
        for btn in self.toolbar_buttons:
            btn.draw(self.screen)
            
            # Tooltip on Hover
            if self.toolbar_expanded and btn.rect.collidepoint(pygame.mouse.get_pos()):
                tooltip_text = ""
                if btn.label == "+": tooltip_text = "Spawn Object"
                elif btn.label == "S": tooltip_text = "Simulation Stats"
                elif btn.label == "V": tooltip_text = "Toggle Vectors"
                elif btn.label == "P": tooltip_text = "Pause/Resume"
                elif btn.label == "M": tooltip_text = "Main Menu"
                
                if tooltip_text:
                    txt_surf = self.font_small.render(tooltip_text, True, (255, 255, 255))
                    txt_rect = txt_surf.get_rect(midleft=(toolbar_draw_rect.right + 10, btn.rect.centery))
                    bg_rect = txt_rect.inflate(10, 5)
                    pygame.draw.rect(self.screen, (0, 0, 0), bg_rect, border_radius=5)
                    self.screen.blit(txt_surf, txt_rect)

        if self.active_modal:
            self.active_modal.draw()
            
        if self.paused:
            s = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
            s.set_alpha(100)
            s.fill((0,0,0))
            self.screen.blit(s, (0,0))
            txt = self.font_large.render("PAUSED", True, (255, 255, 255))
            self.screen.blit(txt, (self.screen.get_width()//2 - txt.get_width()//2, self.screen.get_height()//2))

    def spawn_ball(self, x=None, y=None):
        if x is None: x = self.screen.get_width() // 2
        if y is None: y = 100
        ball = RigidBall(x, y, self.spawn_radius, self.spawn_color, 
                         density=self.spawn_density, restitution=self.spawn_restitution)
        self.balls.append(ball)
        self.audio.play_hit(0.5)

# --- Modals ---

class SpawnModal(Modal):
    def __init__(self, screen, parent):
        super().__init__(screen, "Spawn Object", 400, 500)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        self.add_label("Radius")
        self.add_slider("radius", 5, 100, self.parent.spawn_radius, callback=lambda v: setattr(self.parent, 'spawn_radius', int(v)))
        
        self.add_label("Density")
        self.add_slider("density", 0.1, 5.0, self.parent.spawn_density, callback=lambda v: setattr(self.parent, 'spawn_density', v))
        
        self.add_label("Bounciness")
        self.add_slider("restitution", 0.1, 1.2, self.parent.spawn_restitution, callback=lambda v: setattr(self.parent, 'spawn_restitution', v))
        
        self.add_label("Color")
        self.cw = ColorWheelPicker(pygame.Rect(self.content_rect.x + 50, self.content_rect.y + 250, 200, 200), self.parent.spawn_color)
        self.elements.append(self.cw)
        
        btn = Button(pygame.Rect(self.content_rect.centerx - 75, self.content_rect.bottom - 60, 150, 40), "Spawn", (50, 200, 50))
        btn.callback = lambda: self.parent.spawn_ball()
        self.elements.append(btn)

class StatusModal(Modal):
    def __init__(self, screen, parent):
        super().__init__(screen, "Simulation Status", 300, 200)
        self.parent = parent

    def draw_content(self):
        count = len(self.parent.balls)
        total_mass = sum(b.mass for b in self.parent.balls)
        
        text1 = self.font.render(f"Objects: {count}", True, (255, 255, 255))
        text2 = self.font.render(f"Total Mass: {total_mass:.1f}", True, (255, 255, 255))
        text3 = self.font.render(f"FPS: {int(self.parent.clock.get_fps())}", True, (255, 255, 255))
        
        self.screen.blit(text1, (self.content_rect.x + 20, self.content_rect.y + 40))
        self.screen.blit(text2, (self.content_rect.x + 20, self.content_rect.y + 70))
        self.screen.blit(text3, (self.content_rect.x + 20, self.content_rect.y + 100))

class ContextModal(Modal):
    def __init__(self, screen, parent, ball):
        super().__init__(screen, "Object Properties", 250, 250)
        self.parent = parent
        self.ball = ball
        self.setup_ui()

    def setup_ui(self):
        self.add_label(f"Mass: {self.ball.mass:.2f}")
        self.add_label(f"Velocity: {math.hypot(self.ball.vx, self.ball.vy):.2f}")
        
        btn_freeze = Button(pygame.Rect(self.content_rect.x + 20, self.content_rect.y + 80, 100, 30), 
                            "Freeze" if not self.ball.frozen else "Unfreeze", (200, 200, 50))
        btn_freeze.callback = lambda: setattr(self.ball, 'frozen', not self.ball.frozen)
        self.elements.append(btn_freeze)
        
        btn_del = Button(pygame.Rect(self.content_rect.right - 120, self.content_rect.y + 80, 100, 30), "Delete", (200, 50, 50))
        btn_del.callback = lambda: self.parent.balls.remove(self.ball) if self.ball in self.parent.balls else None
        self.elements.append(btn_del)
        
        self.add_label("Apply Impulse")
        btn_imp_x = Button(pygame.Rect(self.content_rect.x + 20, self.content_rect.y + 150, 60, 30), "X+", (50, 50, 200))
        btn_imp_x.callback = lambda: setattr(self.ball, 'vx', self.ball.vx + 5)
        self.elements.append(btn_imp_x)
        
        btn_imp_y = Button(pygame.Rect(self.content_rect.x + 90, self.content_rect.y + 150, 60, 30), "Y+", (50, 50, 200))
        btn_imp_y.callback = lambda: setattr(self.ball, 'vy', self.ball.vy - 5)
        self.elements.append(btn_imp_y)

class MainmenuModal(Modal):
    def __init__(self, screen, parent):
        super().__init__(screen, "Menu", 200, 200)
        self.parent = parent
        btn = Button(pygame.Rect(self.content_rect.x + 20, self.content_rect.y + 50, 160, 40), "Exit to Menu", (200, 50, 50))
        btn.callback = lambda: setattr(self.parent, 'running', False)
        self.elements.append(btn)