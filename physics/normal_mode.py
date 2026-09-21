import math
import random
import sys
import pygame

# Initialize Pygame & Mixer
pygame.init()
pygame.mixer.init()

TEASER_PALETTE = [
    (190, 60, 60), (60, 180, 90), (80, 120, 220), 
    (170, 70, 180), (230, 150, 40), (70, 160, 160)
]

class AudioManager:
    def __init__(self, audio):
        self.muted = False
        self.audio = audio 
        self.sfx = {'collision': None, 'ui_click': None, 'throw': None}

    def play_sfx(self, category, volume_scale=1.0):
        if not self.muted and self.sfx.get(category):
            pass

# ==========================================
# CUSTOM NATIVE UI WIDGETS
# ==========================================
class Button:
    def __init__(self, x, y, w, h, text, text_color=(255, 255, 255), bg_color=(40, 50, 65)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.text_color = text_color
        self.base_bg = bg_color
        self.hover = False

    def draw(self, screen, font, active=False):
        color = (80, 150, 220) if active else ((min(255, self.base_bg[0]+20), min(255, self.base_bg[1]+20), min(255, self.base_bg[2]+20)) if self.hover else self.base_bg)
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        pygame.draw.rect(screen, (20, 25, 30), self.rect, 2, border_radius=6)
        txt = font.render(self.text, True, self.text_color)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def update_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)


class IconButton:
    def __init__(self, x, y, w, h, icon_text, full_text):
        self.rect = pygame.Rect(x, y, w, h)
        self.icon_text = icon_text
        self.full_text = full_text
        self.hover = False

    def draw(self, screen, font, font_small):
        color = (70, 80, 100) if self.hover else (45, 55, 70)
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (20, 25, 30), self.rect, 2, border_radius=8)
        
        txt = font.render(self.icon_text, True, (240, 240, 240))
        screen.blit(txt, txt.get_rect(center=self.rect.center))

        if self.hover:
            tt_txt = font_small.render(self.full_text, True, (255, 255, 255))
            tt_rect = tt_txt.get_rect(midleft=(self.rect.right + 12, self.rect.centery))
            bg_rect = tt_rect.inflate(16, 12)
            pygame.draw.rect(screen, (30, 35, 45), bg_rect, border_radius=4)
            pygame.draw.rect(screen, (100, 150, 200), bg_rect, 1, border_radius=4)
            screen.blit(tt_txt, tt_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def update_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)


class FloatInput:
    def __init__(self, x, y, w, h, init_val, min_val, max_val):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = str(float(init_val))
        self.active = False
        self.min_val = min_val
        self.max_val = max_val

    def draw(self, screen, font):
        color = (100, 200, 255) if self.active else (60, 70, 90)
        pygame.draw.rect(screen, (20, 24, 30), self.rect, border_radius=4)
        pygame.draw.rect(screen, color, self.rect, 2, border_radius=4)
        txt = font.render(self.text + ("|" if self.active else ""), True, (240, 240, 240))
        screen.blit(txt, (self.rect.x + 5, self.rect.y + (self.rect.height - txt.get_height())//2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
                self.clamp_val()
            else:
                if event.unicode.isdigit() or (event.unicode == '.' and '.' not in self.text):
                    self.text += event.unicode
                    
    def clamp_val(self):
        try:
            v = float(self.text)
            v = max(self.min_val, min(self.max_val, v))
            self.text = str(v)
        except ValueError:
            self.text = str(self.min_val)

    def get_val(self):
        try:
            return float(self.text)
        except ValueError:
            return self.min_val
        
    def set_val(self, val):
        if not self.active:
            self.text = f"{float(val):.1f}"


class HSlider:
    def __init__(self, x, y, w, min_val, max_val, init_val):
        self.rect = pygame.Rect(x, y-10, w, 20)
        self.min_val = min_val
        self.max_val = max_val 
        self.val = init_val
        self.dragging = False

    def draw(self, screen):
        cy = self.rect.centery
        pygame.draw.line(screen, (60, 70, 90), (self.rect.x, cy), (self.rect.right, cy), 4)
        span = self.max_val - self.min_val
        pct = (self.val - self.min_val) / span if span > 0 else 0
        pct = max(0.0, min(1.0, pct))
        kx = self.rect.x + pct * self.rect.width
        pygame.draw.circle(screen, (100, 200, 255), (int(kx), cy), 8)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_val(event.pos[0])
        return False

    def update_val(self, mx):
        span = self.rect.width
        pct = (mx - self.rect.x) / span if span > 0 else 0
        pct = max(0.0, min(1.0, pct))
        self.val = self.min_val + pct * (self.max_val - self.min_val)


# ==========================================
# RIGID BODY & VECTORS
# ==========================================
def draw_arrow(surface, color, start, end, thickness=3):
    if start == end: 
        return
    pygame.draw.line(surface, color, start, end, thickness)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    p1 = (end[0] - 10 * math.cos(angle - 0.5), end[1] - 10 * math.sin(angle - 0.5))
    p2 = (end[0] - 10 * math.cos(angle + 0.5), end[1] - 10 * math.sin(angle + 0.5))
    pygame.draw.polygon(surface, color, [end, p1, p2])

class RigidBall:
    def __init__(self, x, y, radius=20, density=1.0, color=None):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(random.uniform(-3, 3))
        self.vy = float(random.uniform(-1, 1))
        self.radius = float(radius)
        self.density = float(density)
        self.mass = (math.pi * (self.radius**2)) * self.density * 0.01
        self.restitution = 0.8  
        
        self.color = color or random.choice(TEASER_PALETTE)
        self.is_dragged = False
        self.is_frozen = False
        self.bounce_events = [] 

    def update(self, dt, gravity):
        for b in self.bounce_events[:]:
            b['life'] -= dt * 4
            if b['life'] <= 0:
                self.bounce_events.remove(b)

        if self.is_frozen or self.is_dragged:
            return
            
        self.vy += gravity * dt * 60
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60

    def resolve_wall_collisions(self, bounds):
        min_x, max_x, min_y, max_y = bounds
        collided, nx, ny, impact = False, 0, 0, 0

        if self.x - self.radius < min_x:
            self.x = min_x + self.radius
            impact = abs(self.vx)
            self.vx = -self.vx * self.restitution
            collided, nx, ny = True, 1, 0
        elif self.x + self.radius > max_x:
            self.x = max_x - self.radius
            impact = abs(self.vx)
            self.vx = -self.vx * self.restitution
            collided, nx, ny = True, -1, 0

        if self.y - self.radius < min_y:
            self.y = min_y + self.radius
            impact = abs(self.vy)
            self.vy = -self.vy * self.restitution
            collided, nx, ny = True, 0, 1
        elif self.y + self.radius > max_y: 
            self.y = max_y - self.radius
            impact = abs(self.vy)
            self.vy = -self.vy * self.restitution
            collided, nx, ny = True, 0, -1
            if abs(self.vy) < 0.5:
                self.vy = 0
                self.vx *= 0.95

        if collided and impact > 0.8:
            self.bounce_events.append({'nx': nx, 'ny': ny, 'mag': impact, 'life': 1.0})

    def draw(self, surface, is_selected=False, settings=None, font=None, gravity_val=1.0):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius))
        
        highlight = (min(255, self.color[0]+50), min(255, self.color[1]+50), min(255, self.color[2]+50))
        pygame.draw.circle(surface, highlight, (int(self.x - self.radius*0.3), int(self.y - self.radius*0.3)), int(self.radius*0.35))
        pygame.draw.circle(surface, (15, 18, 28), (int(self.x), int(self.y)), int(self.radius), 2)

        if self.is_frozen:
            pygame.draw.circle(surface, (100, 200, 255), (int(self.x), int(self.y)), 6)

        if is_selected:
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), int(self.radius) + 4, 2)

        if settings:
            show_names = settings.get('show_names', False)
            show_numbers = settings.get('show_numbers', False)

            if settings.get('bounce'):
                for b in self.bounce_events:
                    length = self.radius + 15 + (b['mag'] * 3 * b['life'])
                    end_pos = (self.x + b['nx'] * length, self.y + b['ny'] * length)
                    draw_arrow(surface, (255, 220, 50), (self.x, self.y), end_pos)
                    
                    labels = []
                    if show_names: labels.append("Impact")
                    if show_numbers: labels.append(f"{b['mag']:.1f}")
                    if labels and font:
                        txt = font.render(" | ".join(labels), True, (255, 220, 50))
                        surface.blit(txt, (end_pos[0] + 5, end_pos[1] - 10))

            if settings.get('gravity') and not self.is_frozen:
                g_len = self.radius + (self.mass * 0.1)
                end_pos = (self.x, self.y + g_len)
                draw_arrow(surface, (230, 150, 40), (self.x, self.y), end_pos)
                
                labels = []
                if show_names: labels.append("Gravity")
                if show_numbers: labels.append(f"{self.mass * gravity_val * 60:.1f}")
                if labels and font:
                    txt = font.render(" | ".join(labels), True, (230, 150, 40))
                    surface.blit(txt, (end_pos[0] + 5, end_pos[1] - 10))
                
            speed = math.hypot(self.vx, self.vy)
            if settings.get('velocity') and speed > 0.5 and not self.is_frozen:
                end_pos = (self.x + (self.vx * 4), self.y + (self.vy * 4))
                draw_arrow(surface, (60, 220, 90), (self.x, self.y), end_pos)
                
                labels = []
                if show_names: labels.append("Velocity")
                if show_numbers: labels.append(f"{speed:.1f}")
                if labels and font:
                    txt = font.render(" | ".join(labels), True, (60, 220, 90))
                    surface.blit(txt, (end_pos[0] + 5, end_pos[1] - 10))


# ==========================================
# MAIN ENGINE
# ==========================================
class NormalPhysics:
    def __init__(self, world_config, width=1200, height=700):
        self.width = width
        self.height = height
        self.gravity = 1.0
        self.world_config = world_config
        self.bg_color = (20, 24, 30)
        
        self.in_main_menu = True
        self.manual_pause = False
        self.active_modal = None  # None, 'settings', 'spawn', 'status'
        
        self.balls = []
        self.selected_ball = None
        self.drag_start = None

        self.font_large = pygame.font.SysFont('Consolas', 36, bold=True)
        self.font = pygame.font.SysFont('Consolas', 15, bold=True)
        self.font_small = pygame.font.SysFont('Consolas', 12)
        
        self.vectors = {
            'velocity': True, 
            'gravity': True, 
            'bounce': True,
            'show_names': False,
            'show_numbers': False
        }
        
        self.init_ui_elements()

    def init_ui_elements(self):
        # --- Main Menu UI ---
        self.btn_start = Button(self.width//2 - 100, self.height//2, 200, 50, "START SIMULATION", bg_color=(60, 180, 90))

        # --- Professional Center-Left Toolbar ---
        tb_w, tb_h = 56, 230
        tb_x, tb_y = 15, self.height // 2 - tb_h // 2
        self.toolbar_rect = pygame.Rect(tb_x, tb_y, tb_w, tb_h)
        
        b_x = tb_x + 8
        self.toolbar_btns = {
            'status': IconButton(b_x, tb_y + 15, 40, 40, "i", "Status"),
            'spawn': IconButton(b_x, tb_y + 65, 40, 40, "+", "Spawn Object"),
            'settings': IconButton(b_x, tb_y + 115, 40, 40, "Se", "Settings"),
            'menu': IconButton(b_x, tb_y + 175, 40, 40, "M", "Main Menu")
        }

        # --- Modal Menus Setup ---
        modal_w, modal_h = 350, 450
        self.modal_rect = pygame.Rect(self.width // 2 - modal_w // 2, self.height // 2 - modal_h // 2, modal_w, modal_h)
        mx, my = self.modal_rect.x, self.modal_rect.y

        self.btn_close_modal = Button(mx + 20, my + 390, modal_w - 40, 40, "Close Menu", bg_color=(190, 60, 60))

        # Settings Modal UI
        self.btn_vel = Button(mx + 20, my + 60, modal_w - 40, 35, "Enable Velocity Arrows (Green)", text_color=(100, 255, 120))
        self.btn_grav = Button(mx + 20, my + 110, modal_w - 40, 35, "Enable Gravity Arrows (Orange)", text_color=(255, 180, 80))
        self.btn_bnce = Button(mx + 20, my + 160, modal_w - 40, 35, "Enable Force Arrows (Yellow)", text_color=(255, 255, 100))
        self.btn_names = Button(mx + 20, my + 230, modal_w - 40, 35, "Show Force Names")
        self.btn_nums = Button(mx + 20, my + 280, modal_w - 40, 35, "Show Force Numbers")

        # Spawn Modal UI
        self.spawn_color = TEASER_PALETTE[0]
        self.ui_den_slider = HSlider(mx + 20, my + 80, 200, 0.1, 20.0, 1.0)
        self.ui_den_input = FloatInput(mx + 240, my + 65, 60, 30, 1.0, 0.1, 999.0)
        self.ui_siz_slider = HSlider(mx + 20, my + 150, 200, 10, 100, 25)
        self.ui_siz_input = FloatInput(mx + 240, my + 135, 60, 30, 25, 5.0, 999.0)
        
        self.wheel_radius = 60
        self.wheel_center = (mx + 220, my + 270)
        self.color_wheel_surf = pygame.Surface((self.wheel_radius*2, self.wheel_radius*2), pygame.SRCALPHA)
        for x in range(self.wheel_radius*2):
            for y in range(self.wheel_radius*2):
                dx = x - self.wheel_radius
                dy = y - self.wheel_radius
                dist = math.hypot(dx, dy)
                if dist <= self.wheel_radius:
                    angle = math.degrees(math.atan2(dy, dx)) % 360
                    sat = min(1.0, dist / self.wheel_radius)
                    c = pygame.Color(0)
                    c.hsva = (angle, sat * 100, 100, 100)
                    self.color_wheel_surf.set_at((x, y), c)
                    
        self.btn_create = Button(mx + 20, my + 390, modal_w // 2 - 25, 40, "Spawn", bg_color=(60, 180, 90))
        self.btn_close_spawn = Button(mx + modal_w // 2 + 5, my + 390, modal_w // 2 - 25, 40, "Close", bg_color=(190, 60, 60))

        # --- Right Click Context Menu ---
        self.ctx_active = False
        self.ctx_ball = None
        self.ctx_mode = "main" 
        self.ctx_rect = pygame.Rect(0, 0, 140, 100)
        self.ctx_vx_input = FloatInput(0, 0, 50, 25, 0, -100, 100)
        self.ctx_vy_input = FloatInput(0, 0, 50, 25, 0, -100, 100)

    def reset_simulation(self):
        self.balls = [RigidBall(random.randint(100, self.width - 100), random.randint(100, self.height - 300)) for _ in range(5)]
        self.manual_pause = False
        self.active_modal = None
        self.ctx_active = False

    def handle_collisions(self):
        for i in range(len(self.balls)):
            for j in range(i + 1, len(self.balls)):
                b1, b2 = self.balls[i], self.balls[j]
                dx, dy = b2.x - b1.x, b2.y - b1.y
                dist = math.hypot(dx, dy)
                min_dist = b1.radius + b2.radius

                if 0 < dist < min_dist:
                    overlap = min_dist - dist
                    nx, ny = dx / dist, dy / dist

                    if not b1.is_frozen and not b1.is_dragged:
                        b1.x -= nx * overlap * 0.5
                        b1.y -= ny * overlap * 0.5
                    if not b2.is_frozen and not b2.is_dragged:
                        b2.x += nx * overlap * 0.5
                        b2.y += ny * overlap * 0.5

                    kx, ky = b1.vx - b2.vx, b1.vy - b2.vy
                    p = 2 * (nx * kx + ny * ky) / (b1.mass + b2.mass)

                    if not b1.is_frozen and not b1.is_dragged:
                        b1.vx -= p * b2.mass * nx
                        b1.vy -= p * b2.mass * ny
                    if not b2.is_frozen and not b2.is_dragged:
                        b2.vx += p * b1.mass * nx
                        b2.vy += p * b1.mass * ny

                    rel_speed = math.hypot(kx, ky)
                    if rel_speed > 0.5:
                        b1.bounce_events.append({'nx': nx, 'ny': ny, 'mag': rel_speed, 'life': 1.0})
                        b2.bounce_events.append({'nx': -nx, 'ny': -ny, 'mag': rel_speed, 'life': 1.0})

    def handle_event(self, event):
        pos = pygame.mouse.get_pos()

        if self.in_main_menu:
            self.btn_start.update_hover(pos)
            if self.btn_start.is_clicked(event):
                self.in_main_menu = False
                self.reset_simulation()
            return

        # Spacebar toggles manual pause
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.manual_pause = not self.manual_pause

        # Modal UI Intercepts all inputs if open
        if self.active_modal:
            self.btn_close_modal.update_hover(pos)
            
            if self.active_modal == 'settings':
                self.btn_vel.update_hover(pos)
                self.btn_grav.update_hover(pos)
                self.btn_bnce.update_hover(pos)
                self.btn_names.update_hover(pos)
                self.btn_nums.update_hover(pos)
                
                if self.btn_vel.is_clicked(event): self.vectors['velocity'] = not self.vectors['velocity']
                if self.btn_grav.is_clicked(event): self.vectors['gravity'] = not self.vectors['gravity']
                if self.btn_bnce.is_clicked(event): self.vectors['bounce'] = not self.vectors['bounce']
                if self.btn_names.is_clicked(event): self.vectors['show_names'] = not self.vectors['show_names']
                if self.btn_nums.is_clicked(event): self.vectors['show_numbers'] = not self.vectors['show_numbers']
                
                if self.btn_close_modal.is_clicked(event):
                    self.active_modal = None

            elif self.active_modal == 'spawn':
                self.btn_create.update_hover(pos)
                self.btn_close_spawn.update_hover(pos)
                self.ui_den_input.handle_event(event)
                self.ui_siz_input.handle_event(event)
                self.ui_den_slider.handle_event(event)
                self.ui_siz_slider.handle_event(event)
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    dx, dy = pos[0] - self.wheel_center[0], pos[1] - self.wheel_center[1]
                    dist = math.hypot(dx, dy)
                    if dist <= self.wheel_radius:
                        angle = math.degrees(math.atan2(dy, dx)) % 360
                        sat = min(1.0, dist / self.wheel_radius)
                        c = pygame.Color(0)
                        c.hsva = (angle, sat * 100, 100, 100)
                        self.spawn_color = (c.r, c.g, c.b)
                        
                if self.btn_create.is_clicked(event):
                    self.balls.append(RigidBall(
                        self.width // 2, 80, 
                        radius=int(self.ui_siz_input.get_val()), 
                        density=float(self.ui_den_input.get_val()), 
                        color=self.spawn_color
                    ))
                    self.active_modal = None
                
                if self.btn_close_spawn.is_clicked(event):
                    self.active_modal = None
                    
            elif self.active_modal == 'status':
                if self.btn_close_modal.is_clicked(event):
                    self.active_modal = None
            return 
            
        # Context Menu Interactions
        if self.ctx_active and self.ctx_ball:
            if self.ctx_mode == 'add_vel':
                self.ctx_vx_input.handle_event(event)
                self.ctx_vy_input.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.ctx_rect.collidepoint(pos):
                    if self.ctx_mode == 'main':
                        if pos[1] < self.ctx_rect.y + 50:
                            self.ctx_ball.is_frozen = not self.ctx_ball.is_frozen
                            if self.ctx_ball.is_frozen: 
                                self.ctx_ball.vx = 0.0
                                self.ctx_ball.vy = 0.0
                            self.ctx_active = False
                        else:
                            self.ctx_mode = 'add_vel'
                    else:
                        btn_apply = pygame.Rect(self.ctx_rect.x + 10, self.ctx_rect.bottom - 35, 120, 25)
                        if btn_apply.collidepoint(pos):
                            self.ctx_ball.vx += self.ctx_vx_input.get_val()
                            self.ctx_ball.vy += self.ctx_vy_input.get_val()
                            self.ctx_active = False
                else:
                    self.ctx_active = False
                return

        # Floating Toolbar Updates
        for key, btn in self.toolbar_btns.items():
            btn.update_hover(pos)
            if btn.is_clicked(event):
                if key == 'menu':
                    self.in_main_menu = True
                    self.balls.clear()
                else:
                    self.active_modal = key
                return

        # Left Click Dragging
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for ball in reversed(self.balls):
                if math.hypot(ball.x - pos[0], ball.y - pos[1]) <= ball.radius:
                    self.selected_ball = ball
                    self.selected_ball.is_dragged = True
                    self.drag_start = pos
                    break

        # Right Click Context Menu
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            for ball in reversed(self.balls):
                if math.hypot(ball.x - pos[0], ball.y - pos[1]) <= ball.radius:
                    self.ctx_active = True
                    self.ctx_ball = ball
                    mx = min(pos[0], self.width - 140)
                    my = min(pos[1], self.height - 100)
                    self.ctx_rect.topleft = (mx, my)
                    self.ctx_mode = 'main'
                    self.ctx_vx_input.set_val(0)
                    self.ctx_vy_input.set_val(0)
                    self.ctx_vx_input.rect.topleft = (self.ctx_rect.x + 10, self.ctx_rect.y + 30)
                    self.ctx_vy_input.rect.topleft = (self.ctx_rect.x + 70, self.ctx_rect.y + 30)
                    break

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.selected_ball:
                if self.drag_start:
                    dx, dy = pos[0] - self.drag_start[0], pos[1] - self.drag_start[1]
                    if math.hypot(dx, dy) > 10:
                        self.selected_ball.vx = dx * 0.15
                        self.selected_ball.vy = dy * 0.15
                self.selected_ball.is_dragged = False
                self.selected_ball = None
                self.drag_start = None

        elif event.type == pygame.MOUSEMOTION:
            if self.selected_ball and self.selected_ball.is_dragged:
                self.selected_ball.x = max(self.selected_ball.radius, min(self.width - self.selected_ball.radius, pos[0]))
                self.selected_ball.y = max(self.selected_ball.radius, min(self.height - self.selected_ball.radius, pos[1]))

    def run_frame(self, screen):
        dt = 1.0 / 60.0
        mouse_pos = pygame.mouse.get_pos()

        screen.fill(self.bg_color)

        if self.in_main_menu:
            title = self.font_large.render("PHYSICS SANDBOX", True, (255, 255, 255))
            screen.blit(title, title.get_rect(center=(self.width//2, self.height//2 - 80)))
            self.btn_start.draw(screen, self.font)
            return

        # Modal Updates
        if self.active_modal == 'spawn':
            if not self.ui_den_input.active: 
                self.ui_den_input.set_val(self.ui_den_slider.val)
            else: 
                self.ui_den_slider.val = min(self.ui_den_slider.max_val, self.ui_den_input.get_val())
            if not self.ui_siz_input.active: 
                self.ui_siz_input.set_val(self.ui_siz_slider.val)
            else: 
                self.ui_siz_slider.val = min(self.ui_siz_slider.max_val, self.ui_siz_input.get_val())

        # Physics Updates (Only when not paused & modal not open)
        is_paused = self.manual_pause or (self.active_modal is not None)
        if not is_paused:
            for ball in self.balls:
                ball.update(dt, self.gravity)
                ball.resolve_wall_collisions((0, self.width, 0, self.height))
            self.handle_collisions()

        # Render Physics Space Background & Grid
        for x in range(0, self.width, 50): 
            pygame.draw.line(screen, (30, 34, 42), (x, 0), (x, self.height))
        for y in range(0, self.height, 50): 
            pygame.draw.line(screen, (30, 34, 42), (0, y), (self.width, y))

        if self.selected_ball and self.selected_ball.is_dragged and self.drag_start:
            pygame.draw.line(screen, (255, 100, 100), (self.selected_ball.x, self.selected_ball.y), mouse_pos, 2)

        for ball in self.balls:
            ball.draw(screen, is_selected=(ball == self.selected_ball), settings=self.vectors, font=self.font_small, gravity_val=self.gravity)

        # Context Menu Draw
        if self.ctx_active and self.ctx_ball and not self.active_modal:
            pygame.draw.rect(screen, (35, 40, 50), self.ctx_rect, border_radius=8)
            pygame.draw.rect(screen, (70, 140, 220), self.ctx_rect, 2, border_radius=8)
            
            title = self.font.render(f"Mass: {self.ctx_ball.mass:.1f}", True, (200, 210, 220))
            screen.blit(title, (self.ctx_rect.x + 10, self.ctx_rect.y + 5))

            if self.ctx_mode == 'main':
                f_txt = "Unfreeze" if self.ctx_ball.is_frozen else "Freeze"
                pygame.draw.rect(screen, (50, 60, 75), (self.ctx_rect.x, self.ctx_rect.y+25, self.ctx_rect.w, 35))
                screen.blit(self.font.render(f_txt, True, (255, 255, 255)), (self.ctx_rect.x + 15, self.ctx_rect.y + 35))
                
                pygame.draw.rect(screen, (40, 50, 65), (self.ctx_rect.x, self.ctx_rect.y+60, self.ctx_rect.w, 35))
                screen.blit(self.font.render("+ Velocity", True, (255, 255, 255)), (self.ctx_rect.x + 15, self.ctx_rect.y + 70))
            else:
                self.ctx_vx_input.draw(screen, self.font)
                self.ctx_vy_input.draw(screen, self.font)
                btn = pygame.Rect(self.ctx_rect.x + 10, self.ctx_rect.bottom - 35, 120, 25)
                pygame.draw.rect(screen, (60, 180, 90), btn, border_radius=4)
                screen.blit(self.font.render("Apply", True, (255, 255, 255)), (btn.x + 35, btn.y + 5))

        # Render Floating Toolbar
        pygame.draw.rect(screen, (28, 33, 42), self.toolbar_rect, border_radius=12)
        pygame.draw.rect(screen, (50, 60, 75), self.toolbar_rect, 2, border_radius=12)
        for btn in self.toolbar_btns.values():
            btn.draw(screen, self.font, self.font_small)

        # Spacebar Manual Pause Overlay
        if self.manual_pause and not self.active_modal:
            pause_txt = self.font.render("PAUSED - PRESS SPACE TO RESUME", True, (255, 100, 100))
            bg_rect = pause_txt.get_rect(center=(self.width // 2, 30))
            pygame.draw.rect(screen, (20, 24, 30), bg_rect.inflate(20, 10), border_radius=5)
            pygame.draw.rect(screen, (255, 100, 100), bg_rect.inflate(20, 10), 2, border_radius=5)
            screen.blit(pause_txt, bg_rect)

        # Center Modal Overlay
        if self.active_modal:
            # Alpha darkened background
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((10, 12, 15, 150))
            screen.blit(overlay, (0, 0))

            # Modal Box
            pygame.draw.rect(screen, (30, 35, 45), self.modal_rect, border_radius=12)
            pygame.draw.rect(screen, (70, 140, 220), self.modal_rect, 3, border_radius=12)
            
            title_txt = self.font_large.render(self.active_modal.upper(), True, (255, 255, 255))
            screen.blit(title_txt, title_txt.get_rect(center=(self.modal_rect.centerx, self.modal_rect.y + 30)))
            pygame.draw.line(screen, (60, 70, 90), (self.modal_rect.x + 20, self.modal_rect.y + 50), (self.modal_rect.right - 20, self.modal_rect.y + 50), 2)

            if self.active_modal == 'status':
                txt_obj = self.font.render(f"Objects in Scene: {len(self.balls)}", True, (200, 200, 200))
                screen.blit(txt_obj, (self.modal_rect.x + 30, self.modal_rect.y + 80))
                total_mass = sum(b.mass for b in self.balls)
                txt_mass = self.font.render(f"Total Combined Mass: {total_mass:.1f}", True, (200, 200, 200))
                screen.blit(txt_mass, (self.modal_rect.x + 30, self.modal_rect.y + 120))
                self.btn_close_modal.draw(screen, self.font)

            elif self.active_modal == 'settings':
                self.btn_vel.draw(screen, self.font, active=self.vectors['velocity'])
                self.btn_grav.draw(screen, self.font, active=self.vectors['gravity'])
                self.btn_bnce.draw(screen, self.font, active=self.vectors['bounce'])
                pygame.draw.line(screen, (60, 70, 90), (self.modal_rect.x + 20, self.modal_rect.y + 215), (self.modal_rect.right - 20, self.modal_rect.y + 215), 2)
                self.btn_names.draw(screen, self.font, active=self.vectors['show_names'])
                self.btn_nums.draw(screen, self.font, active=self.vectors['show_numbers'])
                self.btn_close_modal.draw(screen, self.font)

            elif self.active_modal == 'spawn':
                screen.blit(self.font.render("Density / Mass", True, (180, 180, 180)), (self.modal_rect.x + 20, self.modal_rect.y + 60))
                self.ui_den_slider.draw(screen)
                self.ui_den_input.draw(screen, self.font)
                
                screen.blit(self.font.render("Radius (Size)", True, (180, 180, 180)), (self.modal_rect.x + 20, self.modal_rect.y + 130))
                self.ui_siz_slider.draw(screen)
                self.ui_siz_input.draw(screen, self.font)

                screen.blit(self.font.render("Spawn Color", True, (180, 180, 180)), (self.modal_rect.x + 20, self.modal_rect.y + 210))
                screen.blit(self.color_wheel_surf, (self.wheel_center[0] - self.wheel_radius, self.wheel_center[1] - self.wheel_radius))
                
                # Show chosen color
                pygame.draw.circle(screen, self.spawn_color, (self.modal_rect.x + 80, self.wheel_center[1]), 30)
                pygame.draw.circle(screen, (255,255,255), (self.modal_rect.x + 80, self.wheel_center[1]), 32, 3)

                self.btn_create.draw(screen, self.font)
                self.btn_close_spawn.draw(screen, self.font)


if __name__ == '__main__':
    sim = NormalPhysics(width=1200, height=700, world_config="")
    screen = pygame.display.set_mode((sim.width, sim.height))
    pygame.display.set_caption('Physics Engine - Professional UI')
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            sim.handle_event(event)
            
        sim.run_frame(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()