import pygame
import math
from typing import Optional, Callable, Any

class Button:
    def __init__(self, rect, text, color=(60, 60, 65), hover_color=(80, 80, 85), text_color=(255, 255, 255)):
        self.rect = rect
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        # Fix: Explicitly type callback to accept functions
        self.callback: Optional[Callable[[], Any]] = None 
        self.font = pygame.font.SysFont("Arial", 16)
        self.is_hovered = False

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2, border_radius=8)
        txt_surf = self.font.render(self.text, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback: self.callback()
                return True
        return False

class IconButton:
    def __init__(self, rect, label, color=(60, 60, 65), hover_color=(80, 80, 85)):
        self.rect = rect
        self.label = label
        self.color = color
        self.hover_color = hover_color
        self.callback = None
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.is_hovered = False

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.circle(screen, color, self.rect.center, self.rect.width // 2)
        pygame.draw.circle(screen, (100, 100, 100), self.rect.center, self.rect.width // 2, 2)
        txt_surf = self.font.render(self.label, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback: self.callback()
                return True
        return False

class HSlider:
    def __init__(self, rect, min_val, max_val, initial_val, callback=None):
        self.rect = rect
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.callback = callback
        self.dragging = False
        self.handle_x = self.rect.x + (initial_val - min_val) / (max_val - min_val) * (self.rect.width - 10)

    def draw(self, screen):
        pygame.draw.rect(screen, (60, 60, 65), self.rect, border_radius=5)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, self.handle_x - self.rect.x, self.rect.height)
        pygame.draw.rect(screen, (100, 180, 255), fill_rect, border_radius=5)
        pygame.draw.circle(screen, (200, 200, 200), (int(self.handle_x), self.rect.centery), 8)
        font = pygame.font.SysFont("Arial", 14)
        txt = font.render(f"{self.value:.2f}", True, (255, 255, 255))
        screen.blit(txt, (self.rect.right + 10, self.rect.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.handle_x = max(self.rect.x, min(event.pos[0], self.rect.right))
            ratio = (self.handle_x - self.rect.x) / (self.rect.width - 10)
            self.value = self.min_val + ratio * (self.max_val - self.min_val)
            if self.callback: self.callback(self.value)
        return False

class ColorWheelPicker:
    def __init__(self, rect, initial_color=(255, 0, 0)):
        self.rect = rect
        self.color = initial_color
        self.hue = 0
        self.dragging = False
        self.radius = rect.width // 2
        self.center = rect.center

    def hsv_to_rgb(self, h, s=1.0, v=1.0):
        i = int(h * 6)
        f = h * 6 - i
        p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
        i %= 6
        r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]
        return int(r*255), int(g*255), int(b*255)

    def draw(self, screen):
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            color = self.hsv_to_rgb(angle / 360.0)
            end_pos = (self.center[0] + int(self.radius * 0.9 * math.cos(rad)),
                       self.center[1] - int(self.radius * 0.9 * math.sin(rad)))
            pygame.draw.line(screen, color, self.center, end_pos, 4)
        pygame.draw.circle(screen, self.color, self.center, int(self.radius * 0.5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            dist = math.hypot(event.pos[0]-self.center[0], event.pos[1]-self.center[1])
            if dist < self.radius: self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dx, dy = event.pos[0] - self.center[0], event.pos[1] - self.center[1]
            self.hue = (math.atan2(-dy, dx) / (2*math.pi)) % 1.0
            self.color = self.hsv_to_rgb(self.hue)
        return False

class Modal:
    def __init__(self, screen, title, width=400, height=300):
        self.screen = screen
        self.title = title
        self.rect = pygame.Rect((screen.get_width()-width)//2, (screen.get_height()-height)//2, width, height)
        self.content_rect = pygame.Rect(self.rect.x+20, self.rect.y+50, width-40, height-70)
        self.elements = []
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 16)
        self.close_rect = pygame.Rect(self.rect.right-40, self.rect.y+10, 30, 30)
        self.dragging = False
        self.drag_offset = (0,0)

    def add_label(self, text):
        self.elements.append(('label', text))

    def add_slider(self, name, min_v, max_v, init_v, callback=None):
        y = self.content_rect.y + 20 + len([e for e in self.elements if e[0]=='slider'])*40
        self.elements.append(('slider', HSlider(pygame.Rect(self.content_rect.x, y, 200, 10), min_v, max_v, init_v, callback)))

    def draw(self):
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        pygame.draw.rect(self.screen, (45, 45, 48), self.rect, border_radius=10)
        pygame.draw.rect(self.screen, (80, 80, 85), self.rect, 2, border_radius=10)
        pygame.draw.rect(self.screen, (60, 60, 65), (self.rect.x, self.rect.y, self.rect.width, 40), border_top_left_radius=10, border_top_right_radius=10)
        self.screen.blit(self.font.render(self.title, True, (255,255,255)), (self.rect.x+20, self.rect.y+10))
        pygame.draw.circle(self.screen, (200, 50, 50), self.close_rect.center, 15)
        pygame.draw.line(self.screen, (255,255,255), (self.close_rect.left+5, self.close_rect.top+5), (self.close_rect.right-5, self.close_rect.bottom-5), 2)
        pygame.draw.line(self.screen, (255,255,255), (self.close_rect.right-5, self.close_rect.top+5), (self.close_rect.left+5, self.close_rect.bottom-5), 2)
        
        y_off = 0
        for item in self.elements:
            if item[0] == 'label':
                lbl = self.small_font.render(item[1], True, (255,255,255))
                self.screen.blit(lbl, (self.content_rect.x, self.content_rect.y + 10 + y_off))
                y_off += 25
            elif item[0] == 'slider':
                item[1].draw(self.screen)
                y_off += 40

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.close_rect.collidepoint(event.pos): return True
            if pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 40).collidepoint(event.pos):
                self.dragging = True
                self.drag_offset = (event.pos[0]-self.rect.x, event.pos[1]-self.rect.y)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.rect.x, self.rect.y = event.pos[0]-self.drag_offset[0], event.pos[1]-self.drag_offset[1]
            self.content_rect.x, self.content_rect.y = self.rect.x+20, self.rect.y+50
            self.close_rect.x, self.close_rect.y = self.rect.right-40, self.rect.y+10
        
        for item in self.elements:
            if item[0] == 'slider': item[1].handle_event(event)
        return False