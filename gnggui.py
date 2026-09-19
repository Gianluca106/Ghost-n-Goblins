import g2d
from typing import Dict, Tuple, Optional
from actor import Actor, Point
from gnggame import GngGame, Arthur, Heart, Platform, Gravestone, Gate 

# --- FUNZIONE DI UTILITÀ PER CONFIGURAZIONE ---
def load_gui_config(filename: str) -> dict:
    """Carica configurazioni miste (int, stringhe, coordinate) da file."""
    config = {}
    try:
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 1. Se ci sono virgole, è una coordinata sprite (x,y,w,h)
                    if "," in value:
                        parts = [int(v.strip()) for v in value.split(",") if v.strip().isdigit()]
                        if len(parts) == 4:
                            config[key] = ((parts[0], parts[1]), (parts[2], parts[3]))
                    
                    # 2. Se è solo un numero, converti in int
                    elif value.isdigit():
                        config[key] = int(value)
                    
                    # 3. Altrimenti è una stringa (es. CHAR_SET)
                    else:
                        config[key] = value
        return config
    except FileNotFoundError:
        print(f"Errore: File configurazione {filename} non trovato.")
        return {}

# --- CARICAMENTO COSTANTI GUI ---
SPRITE_DATA = load_gui_config("gui_config.txt")

# Default fallback values
DEFAULT_FONT_W = 8
DEFAULT_FONT_H = 8
DEFAULT_SPACING = 1
DEFAULT_GATE_SPRITE = ((3458, 138), (47, 62))

if not SPRITE_DATA:
    SPRITE_DATA = {
        'FONT_W': DEFAULT_FONT_W, 
        'FONT_H': DEFAULT_FONT_H, 
        'FONT_SPACING': DEFAULT_SPACING,
        'CHAR_SET_1': "0123456789", 
        'CHAR_SET_2': "ABCDEFGHIJKLMNO", 
        'CHAR_SET_3': "PQRSTUVWXYZ"
    }

# --- FUNZIONI DI DISEGNO TESTO ---

def get_char_sprite(char: str) -> Optional[Tuple[Point, Point]]:
    """Calcola la posizione dello sprite per un dato carattere."""
    char = char.upper()
    
    w = SPRITE_DATA.get('FONT_W', DEFAULT_FONT_W)
    h = SPRITE_DATA.get('FONT_H', DEFAULT_FONT_H)
    spacing = SPRITE_DATA.get('FONT_SPACING', DEFAULT_SPACING)
    
    sets = [
        (SPRITE_DATA.get('CHAR_SET_1', ""), 568, 736),
        (SPRITE_DATA.get('CHAR_SET_2', ""), 567, 764),
        (SPRITE_DATA.get('CHAR_SET_3', ""), 558, 773)
    ]
    
    for char_set, start_x, start_y in sets:
        if char in char_set:
            index = char_set.index(char)
            x = start_x + index * (w + spacing)
            return (x, start_y), (w, h)
        
    return None

def get_text_width(text: str) -> int:
    """Restituisce la larghezza in pixel della stringa renderizzata."""
    valid_chars = 0
    for char in text.upper():
        if get_char_sprite(char):
            valid_chars += 1
            
    w = SPRITE_DATA.get('FONT_W', DEFAULT_FONT_W)
    spacing = SPRITE_DATA.get('FONT_SPACING', DEFAULT_SPACING)
    
    if valid_chars == 0:
        return 0
        
    return valid_chars * w + (valid_chars - 1) * spacing
    
def draw_text_custom(text: str, pos: Point, camera_offset: float = 0):
    """Disegna testo sullo schermo usando gli sprite caricati."""
    start_x, start_y = pos
    current_x = start_x
    
    w = SPRITE_DATA.get('FONT_W', DEFAULT_FONT_W)
    spacing = SPRITE_DATA.get('FONT_SPACING', DEFAULT_SPACING)
    
    for char in text:
        sprite_data = get_char_sprite(char)
        if sprite_data:
            sprite_pos, sprite_size = sprite_data
            g2d.draw_image("ghosts-goblins.png", 
                           (current_x - camera_offset, start_y), 
                           sprite_pos, 
                           sprite_size)
            current_x += w + spacing
        else:
            # Spazio vuoto
            current_x += 3 * spacing


class GngGui:
    """Classe principale per la gestione dell'interfaccia e del rendering."""
    
    SPRITESHEET_MAIN = "ghosts-goblins.png"
    SPRITESHEET_BG = "ghosts-goblins-bg.png"
    
    def __init__(self):
        self._game = GngGame()
        self._camera_offset = 0
        
        g2d.load_image(self.SPRITESHEET_BG)
        g2d.load_image(self.SPRITESHEET_MAIN)

        g2d.init_canvas(self._game.size())
        g2d.main_loop(self.tick)

    def _draw_actors(self):
        """Itera su tutti gli attori e li disegna nella posizione corretta."""
        for a in self._game.actors():
            sprite_pos = a.sprite()
            if sprite_pos is None:
                continue

            world_x, world_y = a.pos()
            screen_x = world_x - self._camera_offset
            screen_y = world_y
            
            # Selezione Texture
            image_src = self.SPRITESHEET_MAIN
            if isinstance(a, (Platform, Gravestone, Gate)):
                 image_src = self.SPRITESHEET_BG
            
            # Disegno specifico per tipo
            if isinstance(a, Platform):
                if not a.is_semi_solid():
                    g2d.draw_image(image_src, (screen_x, screen_y), sprite_pos, a.size())
            
            elif isinstance(a, Gravestone):
                g2d.draw_image(image_src, (screen_x, screen_y), (35, 169), a.size())
            
            elif isinstance(a, Gate):
                gate_sprite = SPRITE_DATA.get('GATE', DEFAULT_GATE_SPRITE)
                g2d.draw_image(image_src, (screen_x, screen_y), gate_sprite[0], a.size())
            
            elif isinstance(a, Heart):
                g2d.draw_image(image_src, (world_x, world_y), sprite_pos, a.size())
            
            else:
                # Attori dinamici standard (Arthur, Nemici)
                g2d.draw_image(image_src, (screen_x, screen_y), sprite_pos, a.size())

    def _draw_background(self):
        """Disegna lo sfondo con scorrimento."""
        bg_x = -self._camera_offset
        # Dimensioni hardcoded della mappa originale
        g2d.draw_image(self.SPRITESHEET_BG, (bg_x, 0), (3, 11), (3582, 237))

    def _draw_ui(self):
        """Disegna l'HUD (Vite e testi)."""
        lives_count = self._game.get_lives()
        
        draw_text_custom("VITE", (10, 220))

        hearts = [a for a in self._game.actors() if isinstance(a, Heart)]
        hearts.sort(key=lambda h: h.pos()[0])
        for i, heart in enumerate(hearts):
            heart.set_visible(i < lives_count)

    def _draw_game_state_screen(self, title: str, subtitle: str, title_color: Point):
        """Disegna overlay per Game Over o Vittoria."""
        arena_w, arena_h = self._game.size()
        
        title_w = get_text_width(title)
        subtitle_w = get_text_width(subtitle)
        center_x = arena_w // 2
        
        title_x = center_x - title_w // 2
        subtitle_x = center_x - subtitle_w // 2
        
        g2d.set_color((0, 0, 0))
        g2d.draw_rect((0,0), (arena_w, arena_h)) 
        
        g2d.set_color(title_color) 
        draw_text_custom(title, (title_x, arena_h//2 - 25))
        
        g2d.set_color((255, 255, 255))
        draw_text_custom(subtitle, (subtitle_x, arena_h//2 + 5))
        
        if "Enter" in g2d.current_keys():
            self._game = GngGame()

    def tick(self):
        """Loop principale di aggiornamento e rendering."""
        
        if self._game.is_level_won():
            self._draw_game_state_screen("LIVELLO TERMINATO", "PREMERE INVIO PER IL LIVELLO SUCCESSIVO", (0, 255, 0))
            return
            
        elif self._game.is_game_over():
            self._draw_game_state_screen("GAME OVER", "PREMI INVIO PER GIOCARE ANCORA", (255, 0, 0))
            return
            
        # --- Aggiornamento Logica ---
        self._game.tick(g2d.current_keys())
        
        # Aggiornamento Camera
        arthur = self._game.get_arthur()
        if arthur:
            self._camera_offset = arthur.get_camera_offset()
        
        # --- Rendering ---
        g2d.clear_canvas()
        self._draw_background()
        self._draw_actors()
        self._draw_ui()


def main():
    gui = GngGui()

if __name__ == "__main__":
    main()