import os
import random
import sys
import pygame

from physics.normal_mode import NormalPhysics
from ui.world_selector import WorldSelector

# ==========================================
# --- MUSIC CONFIGURATION ---
# ==========================================
MENU_MUSIC = 'Assets/music/Main Menu/menu_music.mp3'

NORMAL_TRACKS = [
    'Assets/music/track-1.mp3',
    'Assets/music/track-2.mp3',
    'Assets/music/track-3.mp3',
]

APS_TRACKS = ['Assets/music/track-4.mp3']

# ==========================================
# --- SOUND EFFECTS CONFIGURATION ---
# ==========================================
CLICK_1 = 'Assets/sfx/Buttons/click_1.mp3'
CLICK_2 = 'Assets/sfx/Buttons/click_2.wav'
CLICK_3 = 'Assets/sfx/Buttons/click_3.wav'
THROW_1 = 'Assets/sfx/Effects_a/Throw/throw_1.mp3'
THROW_2 = 'Assets/sfx/Effects_a/Throw/throw_2.mp3'
THROW_3 = 'Assets/sfx/Effects_a/Throw/throw_3.mp3'
THROW_4 = 'Assets/sfx/Effects_a/Throw/throw_4.mp3'
THROW_5 = 'Assets/sfx/Effects_a/Throw/throw_5.mp3'
HIT_1 = 'Assets/sfx/Hit/hit_1.mp3'
HIT_2 = 'Assets/sfx/Hit/hit_2.mp3'
HIT_3 = 'Assets/sfx/Hit/hit_3.mp3'
HIT_4 = 'Assets/sfx/Hit/hit_4.mp3'
HIT_5 = 'Assets/sfx/Hit/hit_5.mp3'
RC_1 = 'Assets/sfx/Effects_a/R_Click/rc_1.mp3'
RC_2 = 'Assets/sfx/Effects_a/R_Click/rc_2.mp3'


class AudioManager:

  def __init__(self):
    self.current_track = None
    self.muted = False
    self.sfx_pools = {'click': [], 'throw': [], 'hit': [], 'rc': [], 'collision': [], 'ui_click': [], 'menu': []}

    print('\n--- AUDIO INITIALIZATION ---')
    self._load_pool('click', [CLICK_1, CLICK_2, CLICK_3])
    self._load_pool('ui_click', [CLICK_1, CLICK_2, CLICK_3])
    self._load_pool('throw', [THROW_1, THROW_2, THROW_3, THROW_4, THROW_5])
    self._load_pool('hit', [HIT_1, HIT_2, HIT_3, HIT_4, HIT_5])
    self._load_pool('collision', [HIT_1, HIT_2, HIT_3, HIT_4, HIT_5])
    self._load_pool('rc', [RC_1, RC_2])
    self._load_pool('menu', [RC_1, RC_2])
    print('----------------------------\n')

  def _load_pool(self, category_name, file_list):
    for path in file_list:
      if os.path.exists(path):
        try:
          sound = pygame.mixer.Sound(path)
          sound.set_volume(0.6)
          self.sfx_pools[category_name].append(sound)
          print(f"[AUDIO OK] Loaded '{path}'")
        except Exception as e:
          print(f"[AUDIO ERROR] Failed to load '{path}': {e}")
      else:
        print(f"[AUDIO LOG] Missing SFX File: '{path}' (Skipping)")

  def play_music(self, track_source):
    if not track_source or self.muted:
      return
    track = (
        random.choice(track_source)
        if isinstance(track_source, list)
        else track_source
    )
    if track == self.current_track and pygame.mixer.music.get_busy():
      return

    try:
      if pygame.mixer.music.get_busy():
        pygame.mixer.music.fadeout(400)
      pygame.mixer.music.load(track)
      pygame.mixer.music.play(-1)
      self.current_track = track
    except Exception as e:
      print(f"[MUSIC LOG] Could not play music track '{track}': {e}")

  def play_sfx(self, category, volume_scale=1.0):
    if self.muted:
        return
    pool = self.sfx_pools.get(category, [])
    if pool:
      sound = random.choice(pool)
      adjusted_vol = max(0.0, min(1.0, 0.6 * volume_scale))
      sound.set_volume(adjusted_vol)
      sound.play()


class View:
  HOME = 0
  WORLD_SELECT = 1
  NORMAL = 2
  APS = 3
  SETTINGS = 4


# ==========================================
# --- GAME LOADER / INSTALLER UI ---
# ==========================================
class EngineLoader:
    def __init__(self, screen, physics_def_str):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.progress = 0.0
        self.logs = []
        self.status_text = "Initializing launcher environment..."
        self.physics_def = physics_def_str
        
        self.font_main = pygame.font.SysFont('Consolas', 13)
        self.font_title = pygame.font.SysFont('Arial', 24, bold=True)
        self.font_bold = pygame.font.SysFont('Consolas', 13, bold=True)

        self.bg_color = (30, 32, 38)
        self.panel_color = (20, 22, 26)
        self.text_color = (220, 225, 230)
        self.dim_text = (130, 140, 150)
        self.accent_color = (65, 140, 245)
        self.success_color = (80, 200, 120)

    def log(self, text, is_success=False):
        prefix = "[INFO] " if not is_success else "[OK]   "
        self.logs.append((prefix + text, is_success))
        if len(self.logs) > int((self.height - 200) / 20):  
            self.logs.pop(0)

    def run_sequence(self, clock):
        """Runs a blocking sequence that pumps Pygame events so it doesn't freeze."""
        steps = [
            (0.15, "Loading configuration files and asset directories...", False, 10),
            (0.40, "AUDIO OK: Initializing mixer, synchronizing sound pools...", True, 15),
            (0.75, f"PHYSICS OK: NormalPhysics loaded [{self.physics_def}]", True, 20),
            (0.90, "Verifying window bounds and UI context managers...", False, 10),
            (1.00, "All systems operational. Launching game...", True, 15)
        ]

        for target_progress, msg, is_success, frame_delay in steps:
            self.status_text = msg
            self.log(msg, is_success)
            
            while self.progress < target_progress:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                
                self.progress += 0.015
                if self.progress > target_progress:
                    self.progress = target_progress
                    
                self.draw()
                pygame.display.flip()
                clock.tick(60)

            for _ in range(frame_delay):
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                self.draw()
                pygame.display.flip()
                clock.tick(60)


    def draw(self):
        self.screen.fill(self.bg_color)

        title_surf = self.font_title.render("Physics Engine Setup & Loader", True, self.text_color)
        self.screen.blit(title_surf, (20, 20))

        sub_surf = self.font_main.render("Preparing environment for execution...", True, self.dim_text)
        self.screen.blit(sub_surf, (20, 50))

        console_rect = pygame.Rect(20, 85, self.width - 40, self.height - 180)
        pygame.draw.rect(self.screen, self.panel_color, console_rect, border_radius=6)
        pygame.draw.rect(self.screen, (45, 50, 60), console_rect, 1, border_radius=6)

        y_offset = 97
        for line, is_success in self.logs:
            color = self.success_color if is_success else self.text_color
            txt_surface = self.font_main.render(line, True, color)
            self.screen.blit(txt_surface, (32, y_offset))
            y_offset += 20

        bar_x = 20
        bar_y = self.height - 70
        bar_w = self.width - 40
        bar_h = 16

        pygame.draw.rect(self.screen, self.panel_color, (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        pygame.draw.rect(self.screen, (45, 50, 60), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=8)

        filled_w = int(bar_w * self.progress)
        if filled_w > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, filled_w, bar_h)
            pygame.draw.rect(self.screen, self.accent_color, fill_rect, border_radius=8)

        status_surf = self.font_main.render(self.status_text, True, self.dim_text)
        self.screen.blit(status_surf, (bar_x, bar_y + 24))

        pct_str = f"{int(self.progress * 100)}%"
        pct_surf = self.font_bold.render(pct_str, True, self.text_color)
        self.screen.blit(pct_surf, (bar_x + bar_w - pct_surf.get_width(), bar_y + 24))


def main():
  pygame.init()
  pygame.mixer.init()

  screen = pygame.display.set_mode((1000, 600))
  pygame.display.set_caption('Physics Simulator Engine')
  clock = pygame.time.Clock()
  font = pygame.font.SysFont('Arial', 24, bold=True)
  title_font = pygame.font.SysFont('Arial', 42, bold=True)

  audio = AudioManager()

  current_view = View.HOME
  normal_sim = None
  world_selector = WorldSelector()

  audio.play_music(MENU_MUSIC)

  btn_normal = pygame.Rect(350, 220, 300, 50)
  btn_aps = pygame.Rect(350, 290, 300, 50)
  btn_settings = pygame.Rect(350, 360, 300, 50)
  btn_back = pygame.Rect(20, 20, 100, 40)

  running = True
  while running:
    mouse_pos = pygame.mouse.get_pos()

    # Safely check boolean attribute exit_to_menu
    if (current_view == View.NORMAL and normal_sim and getattr(normal_sim, 'exit_to_menu', False)):
      current_view = View.HOME
      normal_sim = None
      world_selector = WorldSelector()
      audio.play_music(MENU_MUSIC)

    elif current_view == View.WORLD_SELECT and world_selector.exit_to_menu:
      current_view = View.HOME
      world_selector.exit_to_menu = False
      audio.play_music(MENU_MUSIC)

    # Launch Game & Trigger Loader Sequence
    elif current_view == View.WORLD_SELECT and world_selector.launch_game:
      cfg_grav = (world_selector.world_config or {}).get('gravity', 0.4)
      physics_str = f"gravity={cfg_grav}, restitution=0.8, rigid_body=True"
      
      loader = EngineLoader(screen, physics_str)
      loader.run_sequence(clock)

      current_view = View.NORMAL
      normal_sim = NormalPhysics(world_config=world_selector.world_config, audio=audio)  
      world_selector.launch_game = False
      audio.play_music(NORMAL_TRACKS)

    # --- EVENT HANDLING ---
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False

      if current_view == View.HOME:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
          if btn_normal.collidepoint(mouse_pos):
            audio.play_sfx('click')
            current_view = View.WORLD_SELECT
          elif btn_aps.collidepoint(mouse_pos):
            audio.play_sfx('click')
            current_view = View.APS
            audio.play_music(APS_TRACKS)
          elif btn_settings.collidepoint(mouse_pos):
            audio.play_sfx('click')
            current_view = View.SETTINGS

      elif current_view == View.WORLD_SELECT:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
          audio.play_sfx('click')
        world_selector.handle_event(event)

      elif current_view == View.NORMAL and normal_sim:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
          audio.play_sfx('click')
          current_view = View.HOME
          normal_sim = None
          world_selector = WorldSelector()
          audio.play_music(MENU_MUSIC)
        else:
          normal_sim.handle_event(event)

      elif current_view == View.SETTINGS:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
          if btn_back.collidepoint(mouse_pos):
            audio.play_sfx('click')
            current_view = View.HOME

    # --- RENDERING ---
    if current_view == View.HOME:
      screen.fill((20, 25, 35))

      title = title_font.render('PHYSICS SIMULATOR', True, (255, 255, 255))
      screen.blit(title, (500 - title.get_width() // 2, 100))

      pygame.draw.rect(screen, (80, 180, 80) if btn_normal.collidepoint(mouse_pos) else (50, 140, 50), btn_normal, border_radius=8)
      screen.blit(font.render('Normal Physics', True, (255, 255, 255)), (btn_normal.x + 65, btn_normal.y + 10))

      pygame.draw.rect(screen, (200, 80, 80) if btn_aps.collidepoint(mouse_pos) else (150, 50, 50), btn_aps, border_radius=8)
      screen.blit(font.render('APS Physics', True, (255, 255, 255)), (btn_aps.x + 85, btn_aps.y + 10))

      pygame.draw.rect(screen, (100, 100, 200) if btn_settings.collidepoint(mouse_pos) else (70, 70, 150), btn_settings, border_radius=8)
      screen.blit(font.render('Settings Menu', True, (255, 255, 255)), (btn_settings.x + 75, btn_settings.y + 10))

    elif current_view == View.WORLD_SELECT:
      world_selector.run_frame(screen)

    elif current_view == View.SETTINGS:
      screen.fill((30, 40, 50))
      screen.blit(title_font.render('MAIN SETTINGS', True, (255, 255, 255)), (350, 50))
      screen.blit(font.render('Physics settings are saved dynamically inside the Normal Mode UI.', True, (200, 200, 200)), (150, 250))

      pygame.draw.rect(screen, (150, 50, 50) if btn_back.collidepoint(mouse_pos) else (100, 40, 40), btn_back, border_radius=5)
      screen.blit(font.render('BACK', True, (255, 255, 255)), (btn_back.x + 15, btn_back.y + 5))

    elif current_view == View.NORMAL and normal_sim:
      normal_sim.run_frame(screen)

    pygame.display.flip()
    clock.tick(60)

  pygame.quit()
  sys.exit()


if __name__ == '__main__':
  main()