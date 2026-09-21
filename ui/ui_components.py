import pygame
import math

class Button:
    def __init__(self, rect, text, color=(60, 60, 65), hover_color=(80, 80, 85), text_color=(255, 255, 255)):
        self.rect = rect
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.callback = None
        self.font = pygame.font.SysFont("Arial", 16)
        self.is_hovered = False

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2, border_radius=8)
        
        txt_surf = self.font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and event.button == 1:
                if self.callback:
                    self.callback()
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
        # Circle background
        center = self.rect.center
        pygame.draw.circle(screen, color, center, self.rect.width // 2)
        pygame.draw.circle(screen, (100, 100, 100), center, self.rect.width // 2, 2)
        
        # Text
        txt_surf = self.font.render(self.label, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=center)
        screen.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and event.button == 1:
                if self.callback:
                    self.callback()
                return True
        return False

class FloatInput:
    def __init__(self, rect, initial_value=0.0, min_val=0.0, max_val=100.0):
        self.rect = rect
        self.value = initial_value
        self.min_val = min_val
        self.max_val = max_val
        self.active = False
        self.font = pygame.font.SysFont("Arial", 16)
        self.input_text = str(initial_value)

    def draw(self, screen):
        color = (100, 180, 255) if self.active else (60, 60, 65)
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2, border_radius=5)
        
        txt_surf = self.font.render(self.input_text, True, (255, 255, 255))
        screen.blit(txt_surf, (self.rect.x + 10, self.rect.y + 5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                try:
                    val = float(self.input_text)
                    self.value = max(self.min_val, min(self.max_val, val))
                    self.input_text = str(self.value)
                except:
                    self.input_text = str(self.value)
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                if event.unicode.isdigit() or event.unicode == '.':
                    self.input_text += event.unicode
        return False

class HSlider:
    def __init__(self, rect, min_val, max_val, initial_val, callback=None):
        self.rect = rect
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.callback = callback
        self.dragging = False
        self.handle_x = self._value_to_x(initial_val)

    def _value_to_x(self, val):
        ratio = (val - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + ratio * (self.rect.width - 10)

    def _x_to_value(self, x):
        ratio = (x - self.rect.x) / (self.rect.width - 10)
        ratio = max(0, min(1, ratio))
        return self.min_val + ratio * (self.max_val - self.min_val)

    def draw(self, screen):
        # Track
        pygame.draw.rect(screen, (60, 60, 65), self.rect, border_radius=5)
        # Fill
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, self.handle_x - self.rect.x, self.rect.height)
        pygame.draw.rect(screen, (100, 180, 255), fill_rect, border_radius=5)
        # Handle
        pygame.draw.circle(screen, (200, 200, 200), (int(self.handle_x), self.rect.centery), 8)
        
        # Value Text
        font = pygame.font.SysFont("Arial", 14)
        txt = font.render(f"{self.value:.2f}", True, (255, 255, 255))
        screen.blit(txt, (self.rect.right + 10, self.rect.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) or abs(event.pos[0] - self.handle_x) < 10:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.handle_x = max(self.rect.x, min(event.pos[0], self.rect.right))
            self.value = self._x_to_value(self.handle_x)
            if self.callback:
                self.callback(self.value)
        return False

class ColorWheelPicker:
    def __init__(self, rect, initial_color=(255, 0, 0)):
        self.rect = rect
        self.color = initial_color
        self.hue = 0
        self.sat = 1.0
        self.val = 1.0
        self.dragging = False
        self.radius = rect.width // 2
        self.center = rect.center

    def hsv_to_rgb(self, h, s, v):
        # Simple HSV to RGB conversion
        i = int(h * 6)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        i %= 6
        if i == 0: r, g, b = v, t, p
        elif i == 1: r, g, b = q, v, p
        elif i == 2: r, g, b = p, v, t
        elif i == 3: r, g, b = p, q, v
        elif i == 4: r, g, b = t, p, v
        elif i == 5: r, g, b = v, p, q
        return int(r*255), int(g*255), int(b*255)

    def draw(self, screen):
        # Draw simple color circle
        for angle in range(0, 360, 5):
            rad = math.radians(angle)
            h = angle / 360.0
            color = self.hsv_to_rgb(h, 1.0, 1.0)
            start_pos = self.center
            end_pos = (self.center[0] + int(self.radius * 0.9 * math.cos(rad)),
                       self.center[1] - int(self.radius * 0.9 * math.sin(rad)))
            pygame.draw.line(screen, color, start_pos, end_pos, 4)
        
        # Inner white circle for saturation/value (simplified)
        pygame.draw.circle(screen, self.color, self.center, int(self.radius * 0.5))
        pygame.draw.circle(screen, (255, 255, 255), self.center, int(self.radius * 0.5), 2)

    def handle_event(self, event):
        # Simplified interaction
        if event.type == pygame.MOUSEBUTTONDOWN:
            dist = math.hypot(event.pos[0]-self.center[0], event.pos[1]-self.center[1])
            if dist < self.radius:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dx = event.pos[0] - self.center[0]
            dy = event.pos[1] - self.center[1]
            angle = math.atan2(-dy, dx)
            self.hue = (angle / (2*math.pi)) % 1.0
            self.color = self.hsv_to_rgb(self.hue, self.sat, self.val)
        return False

class Modal:
    def __init__(self, screen, title, width=400, height=300):
        self.screen = screen
        self.title = title
        self.width = width
        self.height = height
        self.rect = pygame.Rect(
            (screen.get_width() - width) // 2,
            (screen.get_height() - height) // 2,
            width, height
        )
        self.elements = []
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 16)
        self.drag_offset = (0, 0)
        self.dragging = False
        
        # Content area inside modal
        self.content_rect = pygame.Rect(
            self.rect.x + 20, self.rect.y + 50, self.width - 40, self.height - 70
        )

    def add_label(self, text):
        lbl = pygame.font.SysFont("Arial", 16).render(text, True, (255, 255, 255))
        self.elements.append(('label', text, lbl))

    def add_slider(self, name, min_v, max_v, init_v, callback=None):
        y_pos = self.content_rect.y + 20 + len([e for e in self.elements if e[0]=='slider'])*40
        slider = HSlider(pygame.Rect(self.content_rect.x, y_pos, 200, 10), min_v, max_v, init_v, callback)
        self.elements.append(('slider', name, slider))

    def draw(self):
        # Overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Modal BG
        pygame.draw.rect(self.screen, (45, 45, 48), self.rect, border_radius=10)
        pygame.draw.rect(self.screen, (80, 80, 85), self.rect, 2, border_radius=10)
        
        # Title Bar
        pygame.draw.rect(self.screen, (60, 60, 65), (self.rect.x, self.rect.y, self.rect.width, 40), 
                         border_top_left_radius=10, border_top_right_radius=10)
        title_txt = self.font.render(self.title, True, (255, 255, 255))
        self.screen.blit(title_txt, (self.rect.x + 20, self.rect.y + 10))
        
        # Close Button
        close_rect = pygame.Rect(self.rect.right - 40, self.rect.y + 10, 30, 30)
        pygame.draw.circle(self.screen, (200, 50, 50), close_rect.center, 15)
        pygame.draw.line(self.screen, (255, 255, 255), (close_rect.left+5, close_rect.top+5), (close_rect.right-5, close_rect.bottom-5), 2)
        pygame.draw.line(self.screen, (255, 255, 255), (close_rect.right-5, close_rect.top+5), (close_rect.left+5, close_rect.bottom-5), 2)
        
        # Store close rect for event handling
        self.close_rect = close_rect

        # Draw Elements
        current_y = self.content_rect.y + 10
        for item in self.elements:
            if item[0] == 'label':
                txt_surf = self.small_font.render(item[1], True, (255, 255, 255))
                self.screen.blit(txt_surf, (self.content_rect.x, current_y))
                current_y += 25
            elif item[0] == 'slider':
                item[2].draw(self.screen)
                current_y += 40
            elif isinstance(item, (Button, HSlider, ColorWheelPicker)):
                item.draw(self.screen)

    def handle_event(self, event):
        # Close button
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.close_rect.collidepoint(event.pos):
                return True # Signal to close
            
            # Drag logic
            title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 40)
            if title_rect.collidepoint(event.pos):
                self.dragging = True
                self.drag_offset = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
        
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.rect.x = event.pos[0] - self.drag_offset[0]
            self.rect.y = event.pos[1] - self.drag_offset[1]
            self.content_rect.x = self.rect.x + 20
            self.content_rect.y = self.rect.y + 50
            self.close_rect.x = self.rect.right - 40
            self.close_rect.y = self.rect.y + 10

        # Pass events to elements
        for item in self.elements:
            if isinstance(item, (Button, HSlider, ColorWheelPicker)):
                if item.handle_event(event):
                    pass # Event consumed
        return False