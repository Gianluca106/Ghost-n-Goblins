from random import choice, randrange
from typing import Dict, List, Tuple, Optional
from actor import Actor, Arena, Point, check_collision

# --- COSTANTI GLOBALI ---
GRAVITY = 0.8
MAX_Y_DEATH_OFFSET = 50  # Distanza sotto lo schermo per morire

# --- FUNZIONI DI UTILITÀ ---

def load_sprite_config(filename: str) -> Dict[str, List[Tuple[Point, Point]]]:
    """
    Legge il file di configurazione degli sprite e restituisce un dizionario.
    Format atteso nel file: KEY: x,y,w,h | x,y,w,h
    """
    sprites = {}
    try:
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                if ":" in line:
                    key, frames_str = line.split(":", 1)
                    key = key.strip()
                    frames_data = []
                    
                    raw_frames = frames_str.split("|")
                    for frame in raw_frames:
                        # Pulisce e converte i valori CSV in interi
                        coords = [int(c.strip()) for c in frame.split(",") if c.strip().isdigit()]
                        if len(coords) == 4:
                            # Crea la struttura ((x, y), (w, h))
                            frames_data.append(((coords[0], coords[1]), (coords[2], coords[3])))
                    
                    sprites[key] = frames_data
        return sprites
    except FileNotFoundError:
        print(f"Errore: File sprite '{filename}' non trovato.")
        return {}

# Caricamento globale (Singleton-like per le risorse)
SPRITE_DB = load_sprite_config("sprites.txt")


# --- CLASSI ATTORI ---

class Heart(Actor):
    """Rappresentazione grafica di una vita nell'interfaccia utente."""
    SIZE = (8, 8)
    SPRITE_LOC = (558, 783)
    
    def __init__(self, pos: Point, is_visible: bool):
        self._x, self._y = pos
        self._is_visible = is_visible
        
    def move(self, arena: Arena):
        pass
    
    def set_visible(self, visible: bool):
        self._is_visible = visible
    
    def pos(self) -> Point:
        return self._x, self._y
    
    def size(self) -> Point:
        return self.SIZE
    
    def sprite(self) -> Optional[Point]:
        return self.SPRITE_LOC if self._is_visible else None


class Gate(Actor):
    """Il portale di fine livello."""
    SIZE = (47, 62)
    
    def __init__(self, pos: Point):
        self._x, self._y = pos
        self._w, self._h = self.SIZE
        
    def move(self, arena: Arena):
        pass
    
    def pos(self) -> Point:
        return self._x, self._y
    
    def size(self) -> Point:
        return self._w, self._h
    
    def sprite(self) -> Optional[Point]:
        return None  # Gestito esternamente dalla GUI o texture ripetuta


class Platform(Actor):
    """Elemento statico su cui gli attori possono camminare."""
    
    def __init__(self, pos: Point, size: Point, sprite_pos: Point, semi_solid: bool = False):
        self._x, self._y = pos
        self._w, self._h = size
        self._sprite_x, self._sprite_y = sprite_pos
        self._semi_solid = semi_solid
        
    def move(self, arena: Arena):
        pass
    
    def pos(self) -> Point:
        return self._x, self._y
    
    def size(self) -> Point:
        return self._w, self._h
    
    def sprite(self) -> Point:
        return self._sprite_x, self._sprite_y
    
    def is_semi_solid(self) -> bool:
        return self._semi_solid


class Gravestone(Actor):
    """Ostacolo solido decorativo."""
    
    def __init__(self, pos: Point, size: Point):
        self._x, self._y = pos
        self._w, self._h = size
        
    def move(self, arena: Arena):
        pass
    
    def pos(self) -> Point:
        return self._x, self._y
    
    def size(self) -> Point:
        return self._w, self._h
    
    def sprite(self) -> Optional[Point]:
        return None


class Ladder(Actor):
    """Scala interagibile per il movimento verticale."""
    
    def __init__(self, pos: Point, size: Point):
        self._x, self._y = pos
        self._w, self._h = size
        
    def move(self, arena: Arena):
        pass
    
    def pos(self) -> Point:
        return self._x, self._y
    
    def size(self) -> Point:
        return self._w, self._h
    
    def sprite(self) -> Optional[Point]:
        return None


class Arthur(Actor):
    """Il protagonista del gioco."""
    
    # Costanti di configurazione
    SPEED = 3
    CLIMB_SPEED = 2
    JUMP_FORCE = -10
    MAX_JUMPS = 2
    THROW_COOLDOWN = 10
    THROW_ANIM_DURATION = 12
    BLINK_DURATION = 90
    
    # Caricamento animazioni da database
    R_THROW = SPRITE_DB.get("ARTHUR_THROW_R", [])
    L_THROW = SPRITE_DB.get("ARTHUR_THROW_L", [])
    R_CLIMB = SPRITE_DB.get("ARTHUR_CLIMB_R", [])
    L_CLIMB = SPRITE_DB.get("ARTHUR_CLIMB_L", [])
    R_DEATH = SPRITE_DB.get("ARTHUR_DEATH_R", [])
    L_DEATH = SPRITE_DB.get("ARTHUR_DEATH_L", [])
    
    IDLE_R = SPRITE_DB.get("ARTHUR_IDLE_R", [((0,0),(32,32))])
    IDLE_L = SPRITE_DB.get("ARTHUR_IDLE_L", [((0,0),(32,32))])
    RUN_R = SPRITE_DB.get("ARTHUR_RUN_R", [])
    RUN_L = SPRITE_DB.get("ARTHUR_RUN_L", [])
    JUMP_R = SPRITE_DB.get("ARTHUR_JUMP_R", [((0,0),(32,32))])
    JUMP_L = SPRITE_DB.get("ARTHUR_JUMP_L", [((0,0),(32,32))])
    FALL_R = SPRITE_DB.get("ARTHUR_FALL_R", [((0,0),(32,32))])
    FALL_L = SPRITE_DB.get("ARTHUR_FALL_L", [((0,0),(32,32))])

    def __init__(self, pos: Point, arena: Arena):
        self._x, self._y = pos
        self._w, self._h = 32, 32
        self._dx, self._dy = 0, 0
        
        self._on_ground = False
        self._facing_right = True
        self._state = "idle"
        
        self._animation_frame = 0
        self._animation_counter = 0
        self._camera_offset = 0
        
        self._jumps_remaining = 0
        self._throw_cooldown = 0
        self._throwing_anim_timer = 0
        
        self._lives = 3
        self._blinking = 0 

    def _check_ladder_collision(self, arena: Arena) -> Optional[Ladder]:
        """Controlla se Arthur sta toccando una scala."""
        for other in arena.actors():
            if isinstance(other, Ladder) and check_collision(self, other):
                return other
        return None
    
    def lives(self) -> int:
        return self._lives

    def hit(self, arena: "GngGame"):
        """Gestisce il danno ricevuto."""
        if arena.is_dying() or self._blinking > 0:
            return
        
        self._lives -= 1
        if self._lives <= 0:
            self.die(arena)
        else:
            self._blinking = self.BLINK_DURATION 

    def die(self, arena: "GngGame"):
        """Inizia la sequenza di morte."""
        if not arena.is_dying():
            arena.set_dying(True)
            self._state = "dying"
            self._animation_frame = 0
            self._animation_counter = 0
            self._dx = 0
            self._dy = -4  # Piccolo salto quando muore
            self._on_ground = False 

    def move(self, arena: Arena):
        arena_w, arena_h = arena.size()
        keys = arena.current_keys()
        prev_keys = arena.previous_keys()
        
        if self._blinking > 0:
            self._blinking -= 1

        # --- GESTIONE STATO MORTE ---
        if self._state == "dying":
            self._animation_counter += 1
            if self._animation_counter >= 10:
                old_h = self.size()[1]
                self._animation_frame += 1
                self._animation_counter = 0
                
                if self._animation_frame >= len(self.R_DEATH):
                    arena.kill(self) 
                    arena._game_state = "game_over" 
                    return
                
                # Correzione posizione per cambio altezza sprite
                new_h = self.size()[1]
                self._y += (old_h - new_h)
            
            if not self._on_ground:
                self._dy += GRAVITY
                self._y += self._dy

            self._on_ground = False
            # Collisione minima durante la morte (solo terreno)
            for other in arena.actors():
                if isinstance(other, (Platform, Gravestone)):
                    if check_collision(self, other) and self._dy >= 0:
                        prev_y_bottom = self._y - self._dy + self.size()[1]
                        if prev_y_bottom <= other.pos()[1] + 3:
                            self._y = other.pos()[1] - self.size()[1]
                            self._on_ground = True
                            self._dy = 0
                            break
            return 
        
        # --- GESTIONE SCALE ---
        colliding_ladder = self._check_ladder_collision(arena)

        if self._state == "climbing":
            self._dy, self._dx = 0, 0
            if "ArrowUp" in keys:
                self._y -= self.CLIMB_SPEED
                self._animation_counter += 1
            elif "ArrowDown" in keys:
                self._y += self.CLIMB_SPEED
                self._animation_counter += 1
                # Controllo atterraggio alla base della scala
                for other in arena.actors():
                    if (isinstance(other, Platform) and not other.is_semi_solid()) or \
                       isinstance(other, Gravestone):
                        if check_collision(self, other):
                            self._y = other.pos()[1] - self._h
                            self._state = "idle"
                            self._on_ground = True
                            self._jumps_remaining = self.MAX_JUMPS
                            break
                
            if self._animation_counter >= 5:
                self._animation_frame = (self._animation_frame + 1) % len(self.R_CLIMB)
                self._animation_counter = 0
            
            if not colliding_ladder:
                self._state = "falling"
                self._on_ground = False
            elif "ArrowLeft" in keys or "ArrowRight" in keys:
                self._state = "falling"
                self._on_ground = False
            
            if self._state == "climbing":
                return

        if colliding_ladder and (("ArrowUp" in keys) or ("ArrowDown" in keys)):
            self._state = "climbing"
            self._on_ground = False
            self._dy, self._dx = 0, 0
            # Centra Arthur sulla scala
            self._x = colliding_ladder.pos()[0] + (colliding_ladder.size()[0] / 2) - (self._w / 2)
            return
        
        # --- GESTIONE ATTACCO ---
        if self._throw_cooldown > 0: self._throw_cooldown -= 1
        if self._throwing_anim_timer > 0: self._throwing_anim_timer -= 1
        
        if "Spacebar" in keys and "Spacebar" not in prev_keys and self._throw_cooldown == 0:
            self._throw_cooldown = self.THROW_COOLDOWN
            self._throwing_anim_timer = self.THROW_ANIM_DURATION
            direction = 'right' if self._facing_right else 'left'
            spawn_x = self._x + self._w - 10 if self._facing_right else self._x - 10
            spawn_y = self._y + (self._h / 3)
            arena.spawn(Torch((spawn_x, spawn_y), direction))

        # --- GESTIONE MOVIMENTO ORIZZONTALE ---
        self._dx = 0
        if "ArrowLeft" in keys:
            self._dx = -self.SPEED
            self._facing_right = False
            if self._on_ground: self._state = "running"
        elif "ArrowRight" in keys:
            self._dx = self.SPEED
            self._facing_right = True
            if self._on_ground: self._state = "running"
        else:
            if self._on_ground: self._state = "idle"
        
        # --- GESTIONE SALTO ---
        if "ArrowUp" in keys and "ArrowUp" not in prev_keys:
            if self._jumps_remaining > 0:
                self._dy = self.JUMP_FORCE
                self._on_ground = False
                self._state = "jumping"
                self._jumps_remaining -= 1
        
        # --- FISICA (GRAVITÀ) ---
        if not self._on_ground:
            self._dy += GRAVITY
            if self._dy > 0 and self._state == "jumping":
                self._state = "falling"
        
        prev_y = self._y
        self._x += self._dx
        
        if self._x < 0:
            self._x = 0
        
        self._y += self._dy
        self._on_ground = False
        
        # --- RILEVAMENTO COLLISIONI ---
        for other in arena.actors():
            if not check_collision(self, other):
                continue

            if isinstance(other, (Platform, Gravestone)):
                plat_x, plat_y = other.pos()
                plat_w, plat_h = other.size()
                is_semi_solid = isinstance(other, Platform) and other.is_semi_solid()
                
                # Collisione dall'alto (atterraggio)
                if self._dy >= 0 and prev_y + self._h <= plat_y + 3:
                    self._y = plat_y - self._h
                    self._dy = 0
                    self._on_ground = True
                    self._jumps_remaining = self.MAX_JUMPS
                    if self._dx == 0:
                        self._state = "idle"
                
                # Collisione dal basso (testata)
                elif not is_semi_solid and self._dy < 0 and prev_y >= plat_y + plat_h - 3:
                    self._y = plat_y + plat_h
                    self._dy = 0
                    
                # Collisione laterale
                elif not is_semi_solid:
                    if self._dx > 0:
                        self._x = plat_x - self._w
                    elif self._dx < 0:
                        self._x = plat_x + plat_w
            
            elif isinstance(other, (Zombie, Eyeball)):
                self.hit(arena) 
            
            elif isinstance(other, Gate) and self._facing_right:
                arena._game_state = "level_won" 
                arena.kill(self) 
                return

        # Limiti arena verticale
        if self._y < 0:
            self._y, self._dy = 0, 0
            
        if self._y > arena_h + MAX_Y_DEATH_OFFSET:
            self._lives = 0 
            arena.kill(self)
            arena._game_state = "game_over"
            return
        
        # --- AGGIORNAMENTO TELECAMERA ---
        self._camera_offset = self._x - arena_w // 2
        if self._camera_offset < 0:
            self._camera_offset = 0
        
        # Clamp destro 
        max_offset = 3582 - arena_w
        if self._camera_offset > max_offset:
            self._camera_offset = max_offset
        
        # --- ANIMAZIONE ---
        if self._throwing_anim_timer == 0 and self._state != "climbing":
            self._animation_counter += 1
            if self._animation_counter >= 6:
                self._animation_counter = 0
                if self._state == "running":
                    self._animation_frame = (self._animation_frame + 1) % 4
                else:
                    self._animation_frame = 0
    
    def get_camera_offset(self) -> float:
        return self._camera_offset
    
    def pos(self) -> Point:
        return self._x, self._y
    
    def size(self) -> Point:
        if self._state == "dying":
            frame_index = min(self._animation_frame, len(self.R_DEATH) - 1)
            sprites = self.R_DEATH if self._facing_right else self.L_DEATH
            return sprites[frame_index][1]
        
        if self._state == "idle":
             return self.IDLE_R[0][1] if self._facing_right else self.IDLE_L[0][1]
        
        if self._state == "running":
             return (32, 32)
             
        return self._w, self._h 
    
    def sprite(self) -> Optional[Point]:
        if self._blinking > 0 and self._blinking % 4 < 2:
            return None

        if self._state == "dying":
            frame_index = min(self._animation_frame, len(self.R_DEATH) - 1)
            sprites = self.R_DEATH if self._facing_right else self.L_DEATH
            return sprites[frame_index][0]

        if self._throwing_anim_timer > 0:
            anim_speed = 3
            frame_index = max(0, min(3 - (self._throwing_anim_timer - 1) // anim_speed, 3))
            return self.R_THROW[frame_index][0] if self._facing_right else self.L_THROW[frame_index][0]

        if self._state == "climbing":
            frame_index = self._animation_frame % len(self.R_CLIMB)
            return self.R_CLIMB[frame_index][0] if self._facing_right else self.L_CLIMB[frame_index][0]

        # Animazioni standard (Idle, Run, Jump, Fall)
        if self._facing_right:
            if self._state == "idle": return self.IDLE_R[0][0]
            elif self._state == "running": return self.RUN_R[self._animation_frame][0]
            elif self._state == "jumping": return self.JUMP_R[0][0]
            elif self._state == "falling": return self.FALL_R[0][0]
        else:
            if self._state == "idle": return self.IDLE_L[0][0]
            elif self._state == "running": return self.RUN_L[self._animation_frame][0]
            elif self._state == "jumping": return self.JUMP_L[0][0]
            elif self._state == "falling": return self.FALL_L[0][0]
            
        return self.IDLE_R[0][0]


class Zombie(Actor):
    """Nemico base che cammina, emerge e sprofonda."""
    
    SPEED = 5
    ANIMATION_SPEED = 10
    
    R_WALK = SPRITE_DB.get("ZOMBIE_WALK_R", [])
    L_WALK = SPRITE_DB.get("ZOMBIE_WALK_L", [])
    R_RISE = SPRITE_DB.get("ZOMBIE_RISE_R", [])
    L_RISE = SPRITE_DB.get("ZOMBIE_RISE_L", [])
    R_SINK = SPRITE_DB.get("ZOMBIE_SINK_R", [])
    L_SINK = SPRITE_DB.get("ZOMBIE_SINK_L", [])

    def __init__(self, pos: Point, direction: str):
        self._x, self._ground_y = pos
        self._direction = direction
        
        self._distance_to_travel = randrange(150, 301)
        self._distance_traveled = 0
        
        self._state = "rising"
        self._animation_frame = 0
        self._animation_counter = 0
        
        if self.R_WALK: 
            sprite_pos, sprite_size = self._get_current_sprite()
            self._y = self._ground_y - sprite_size[1]
        else:
            self._y = self._ground_y
        
    def _get_current_sprite(self) -> Tuple[Point, Point]:
        frame = min(self._animation_frame, len(self.R_WALK) - 1)
        if self._direction == 'right':
            if self._state == 'rising': return self.R_RISE[frame]
            if self._state == 'walking': return self.R_WALK[frame]
            if self._state == 'sinking': return self.R_SINK[frame]
        else: 
            if self._state == 'rising': return self.L_RISE[frame]
            if self._state == 'walking': return self.L_WALK[frame]
            if self._state == 'sinking': return self.L_SINK[frame]
        return self.R_WALK[0]

    def move(self, arena: Arena):
        # Collisione con Arthur
        for other in arena.actors():
            if isinstance(other, Arthur) and check_collision(self, other):
                other.hit(arena) 

        # Gestione Animazione
        if self._state == 'sinking':
            self._animation_counter += 1
            if self._animation_counter < self.ANIMATION_SPEED: return
            self.move_sinking(arena)
            
        self._animation_counter += 1
        if self._animation_counter < self.ANIMATION_SPEED: return
        self._animation_counter = 0
        
        if self._state == 'rising': self.move_rising()
        elif self._state == 'walking': self.move_walking(arena)

    def move_sinking(self, arena: Arena):
        self._animation_counter = 0
        self._animation_frame += 1
        if self._animation_frame >= len(self.R_SINK):
            arena.kill(self)
            return
        sprite_pos, sprite_size = self._get_current_sprite()
        self._y = self._ground_y - sprite_size[1]
        
    def move_rising(self):
        self._animation_frame += 1
        if self._animation_frame >= len(self.R_RISE):
            self._animation_frame = 0
            self._state = 'walking'
        sprite_pos, sprite_size = self._get_current_sprite()
        self._y = self._ground_y - sprite_size[1]
        
    def move_walking(self, arena):
        self._animation_frame = (self._animation_frame + 1) % len(self.R_WALK)
        dx = self.SPEED if self._direction == 'right' else -self.SPEED
        self._x += dx
        self._distance_traveled += abs(dx)
        
        sprite_pos, sprite_size = self._get_current_sprite()
        self._y = self._ground_y - sprite_size[1]
        
        # Controllo se è ancora sulla piattaforma
        is_on_ground = False
        my_center_x = self._x + (sprite_size[0] / 2)
        for other in arena.actors():
            if isinstance(other, Platform):
                plat_x, plat_y = other.pos()
                plat_w, plat_h = other.size()
                if plat_y == self._ground_y:
                    if plat_x <= my_center_x <= plat_x + plat_w:
                        is_on_ground = True
                        break
        
        if not is_on_ground:
            self.die(arena)
            return
            
        if self._distance_traveled >= self._distance_to_travel:
            self.die(arena)
    
    def die(self, arena: Arena):
        if self._state != 'sinking':
            self._state = 'sinking'
            self._animation_frame = 0
            self._animation_counter = 0
            
    def pos(self) -> Point: return self._x, self._y
    def size(self) -> Point: return self._get_current_sprite()[1]
    def sprite(self) -> Point: return self._get_current_sprite()[0]


class Torch(Actor):
    """Torica lanciata da Arthur."""
    
    SPEED_X = 5
    SPEED_Y = -5
    GRAVITY_TORCH = 0.5
    ANIMATION_SPEED = 4
    
    SPRITES = SPRITE_DB.get("TORCH", [])

    def __init__(self, pos: Point, direction: str):
        self._x, self._y = pos
        self._dx = self.SPEED_X if direction == 'right' else -self.SPEED_X
        self._dy = self.SPEED_Y
        self._gravity = self.GRAVITY_TORCH
        
        self._animation_frame = 0
        self._animation_counter = 0
        
    def move(self, arena: Arena):
        # Collisioni
        for other in arena.actors():
            if not check_collision(self, other): continue
            
            if isinstance(other, (Zombie, Plant)):
                other.die(arena)
                ground_y = other.pos()[1] + other.size()[1]
                if hasattr(other, '_ground_y'): ground_y = other._ground_y
                arena.spawn(Flame((self._x, ground_y)))
                arena.kill(self)
                return
            
            if isinstance(other, Platform):
                ground_y = other.pos()[1]
                arena.spawn(Flame((self._x, ground_y)))
                arena.kill(self)
                return
            
            if isinstance(other, Gravestone):
                arena.kill(self)
                return

        # Fisica
        self._dy += self._gravity
        self._x += self._dx
        self._y += self._dy
        
        # Animazione
        self._animation_counter = (self._animation_counter + 1) % self.ANIMATION_SPEED
        if self._animation_counter == 0:
             self._animation_frame = (self._animation_frame + 1) % len(self.SPRITES)
             
        if self._y > arena.size()[1]:
             arena.kill(self)

    def pos(self) -> Point: return self._x, self._y
    def size(self) -> Point: return self.SPRITES[min(self._animation_frame, len(self.SPRITES)-1)][1]
    def sprite(self) -> Point: return self.SPRITES[min(self._animation_frame, len(self.SPRITES)-1)][0]


class Flame(Actor):
    """Fiamma che persiste per un breve periodo dopo caduta torcia."""
    
    MAX_AGE = 60
    BASE_SPRITES = SPRITE_DB.get("FLAME", [])
    
    # Costruzione sequenza animazione
    if len(BASE_SPRITES) >= 4:
        SPRITES = [BASE_SPRITES[0], BASE_SPRITES[1]] * 4 + [BASE_SPRITES[2], BASE_SPRITES[3]] * 2
    else:
        SPRITES = BASE_SPRITES 

    def __init__(self, pos: Point):
        self._x, self._ground_y = pos
        self._age = 0
        self._animation_frame = 0
        self._animation_speed = self.MAX_AGE // len(self.SPRITES) if self.SPRITES else 1
        self._animation_counter = 0
        if self.SPRITES:
            self._y = self._ground_y - self.size()[1]
        else:
            self._y = self._ground_y

    def move(self, arena: Arena):
        self._age += 1
        if self._age >= self.MAX_AGE:
            arena.kill(self)
            return
            
        self._animation_counter = (self._animation_counter + 1) % self._animation_speed
        if self._animation_counter == 0:
            self._animation_frame += 1
            if self._animation_frame >= len(self.SPRITES): self._animation_frame = len(self.SPRITES) - 1
            self._y = self._ground_y - self.size()[1]
            
        for other in arena.actors():
            if isinstance(other, (Zombie, Plant)):
                if check_collision(self, other): other.die(arena)

    def pos(self) -> Point: return self._x, self._y
    def size(self) -> Point: return self.SPRITES[min(self._animation_frame, len(self.SPRITES) - 1)][1]
    def sprite(self) -> Point: return self.SPRITES[min(self._animation_frame, len(self.SPRITES) - 1)][0]


class Plant(Actor):
    """Nemico statico che spara proiettili."""
    
    ANIMATION_SPEED = 6
    SHOOT_FRAME = 4
    
    R_SHOOT = SPRITE_DB.get("PLANT_SHOOT_R", [])
    L_SHOOT = SPRITE_DB.get("PLANT_SHOOT_L", [])

    def __init__(self, pos: Point, direction: str):
        self._x, self._ground_y = pos
        self._direction = direction
        self._state = "idle"
        self._animation_frame = 0
        self._animation_counter = 0
        
        self._shoot_cooldown = randrange(40, 80)
        if self.R_SHOOT:
            self._y = self._ground_y - self.size()[1]
        else:
            self._y = self._ground_y

    def move(self, arena: Arena):
        if self._state == "idle":
            self._shoot_cooldown -= 1
            if self._shoot_cooldown <= 0:
                self._state = "shooting"
                self._animation_frame = 0
                self._animation_counter = 0
                
        elif self._state == "shooting":
            self._animation_counter += 1
            if self._animation_counter >= self.ANIMATION_SPEED:
                self._animation_counter = 0
                self._animation_frame += 1
                
                if self._animation_frame == self.SHOOT_FRAME:
                    spawn_x = self._x + self.size()[0] if self._direction == 'right' else self._x
                    spawn_y = self._y + 10
                    arena.spawn(Eyeball((spawn_x, spawn_y), self._direction))
                
                if self._animation_frame >= len(self.R_SHOOT):
                    self._state = "idle"
                    self._animation_frame = 0
                    self._shoot_cooldown = randrange(40, 80)
                    
        self._y = self._ground_y - self.size()[1]

    def die(self, arena: Arena):
        arena.kill(self)

    def pos(self) -> Point: return self._x, self._y
    def size(self) -> Point: return (self.R_SHOOT if self._direction == 'right' else self.L_SHOOT)[min(self._animation_frame, len(self.R_SHOOT) - 1)][1]
    def sprite(self) -> Point: return (self.R_SHOOT if self._direction == 'right' else self.L_SHOOT)[min(self._animation_frame, len(self.R_SHOOT) - 1)][0]


class Eyeball(Actor):
    """Proiettile sparato dalla pianta."""
    
    SPEED = 3
    MAX_AGE = 180
    
    SPRITE_R = SPRITE_DB.get("EYEBALL_R", [((0,0),(17,9))])[0]
    SPRITE_L = SPRITE_DB.get("EYEBALL_L", [((0,0),(17,9))])[0]
    
    def __init__(self, pos: Point, direction: str):
        self._x, self._y = pos
        self._direction = direction
        self._dx = self.SPEED if direction == 'right' else -self.SPEED
        self._age = 0
        
    def move(self, arena: Arena):
        for other in arena.actors():
            if not check_collision(self, other): continue
            if isinstance(other, Arthur):
                other.hit(arena) 
                arena.kill(self)
                return
            if isinstance(other, (Platform, Gravestone)):
                arena.kill(self)
                return
        
        self._x += self._dx
        self._age += 1
        if self._age > self.MAX_AGE:
            arena.kill(self)
            
    def pos(self) -> Point: return self._x, self._y
    def size(self) -> Point: return self.SPRITE_R[1] if self._direction == 'right' else self.SPRITE_L[1]
    def sprite(self) -> Point: return self.SPRITE_R[0] if self._direction == 'right' else self.SPRITE_L[0]


# --- CLASSE GIOCO ---

class GngGame(Arena):
    """Classe principale che gestisce lo stato e il loop di gioco."""
    
    ARENA_SIZE = (640, 237)
    LEVEL_CONFIG_FILE = "level1_config.txt"
    
    # Probabilità di spawn casuale (1 su X tick)
    ZOMBIE_SPAWN_RATE = 300
    PLANT_SPAWN_RATE = 400

    def __init__(self):
        super().__init__(self.ARENA_SIZE)
        self._game_state = "playing"
        self._is_dying = False
        self._player_start_pos = (70, 160)
        self.load_level_config()
        
    def load_level_config(self):
        """Carica la configurazione del livello direttamente dal file txt."""
        arthur_pos = self._player_start_pos
        heart_config = {'x': 51, 'y': 223, 'spacing': 10}
        
        try:
            with open(self.LEVEL_CONFIG_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('['):
                        continue
                    
                    try:
                        if ':' not in line: continue
                        type_str, data = line.split(':', 1)
                        type_str = type_str.strip()
                        data = data.strip()
                    except ValueError:
                        continue

                    if type_str == "ARTHUR":
                        try:
                            x, y = map(int, data.split(','))
                            arthur_pos = (x, y)
                        except ValueError: pass
                    
                    elif type_str == "UI_HEART":
                        try:
                            parts = [int(v.strip()) for v in data.split(',')]
                            heart_config['x'] = parts[0]
                            heart_config['y'] = parts[1]
                            if len(parts) > 2:
                                heart_config['spacing'] = parts[2]
                        except ValueError: pass

                    elif type_str == "ZOMBIE" or type_str == "PLANT":
                        parts = [v.strip() for v in data.split(',')]
                        if len(parts) < 2: continue
                        try:
                            x = int(parts[0])
                            y = int(parts[1])
                            direction = parts[2] if len(parts) > 2 else 'left'
                            
                            if type_str == "ZOMBIE":
                                self.spawn(Zombie((x, y), direction))
                            elif type_str == "PLANT":
                                self.spawn(Plant((x, y), direction))
                        except ValueError: continue

                    else:
                        coords = [v.strip() for v in data.split(',')]
                        if len(coords) < 4: continue
                        try:
                            x, y, w, h = map(int, coords[:4])
                        except ValueError: continue
                        pos, size = (x, y), (w, h)
                        
                        if type_str == "PLATFORM":
                            if len(coords) < 6: continue
                            sprite_pos = (int(coords[4]), int(coords[5]))
                            semi_solid = "SEMISOLID" in coords
                            self.spawn(Platform(pos, size, sprite_pos, semi_solid))
                        elif type_str == "GRAVESTONE":
                            self.spawn(Gravestone(pos, size))
                        elif type_str == "LADDER":
                            self.spawn(Ladder(pos, size))
                        elif type_str == "GATE":
                            self.spawn(Gate(pos))
                            
        except FileNotFoundError:
            print(f"Errore: Il file {self.LEVEL_CONFIG_FILE} non è stato trovato.")

        # Spawn Arthur e UI
        arthur = Arthur(arthur_pos, self)
        self.spawn(arthur)
        
        start_x = heart_config['x']
        y = heart_config['y']
        spacing = heart_config['spacing']
        
        for i in range(arthur.lives()):
            self.spawn(Heart((start_x + (i * spacing), y), True))

    def tick(self, keys=[]):
        """Esegue un tick di gioco, incluso lo spawn casuale dei nemici."""
        if self.is_playing():
            arthur = self.get_arthur()
            if arthur:
                arthur_x, arthur_y = arthur.pos()
                
                # Logica Spawning Casuale
                if randrange(self.ZOMBIE_SPAWN_RATE) == 0:
                    distance = randrange(50, 201)
                    spawn_x = arthur_x + (distance * choice([-1, 1]))
                    direction = 'left' if spawn_x > arthur_x else 'right'
                    spawn_platform = next((a for a in self.actors() if isinstance(a, Platform) and a.pos()[0] <= spawn_x <= a.pos()[0] + a.size()[0] and not a.is_semi_solid()), None)
                    if spawn_platform:
                        ground_y = spawn_platform.pos()[1]
                        self.spawn(Zombie((spawn_x, ground_y), direction))
                        
                if randrange(self.PLANT_SPAWN_RATE) == 0:
                    distance = randrange(50, 201)
                    spawn_x = arthur_x + (distance * choice([-1, 1]))
                    direction = 'left' if spawn_x > arthur_x else 'right'
                    spawn_platform = next((a for a in self.actors() if isinstance(a, Platform) and a.pos()[0] <= spawn_x <= a.pos()[0] + a.size()[0] and not a.is_semi_solid()), None)
                    if spawn_platform:
                        ground_y = spawn_platform.pos()[1]
                        self.spawn(Plant((spawn_x, ground_y), direction))

        super().tick(keys)
        
        if self._is_dying and not self.get_arthur():
            self._is_dying = False

    def is_playing(self) -> bool: return self._game_state == "playing" and self.get_arthur() is not None
    def is_level_won(self) -> bool: return self._game_state == "level_won"
    def is_game_over(self) -> bool: return self._game_state == "game_over"
    def is_dying(self) -> bool: return self._is_dying
    def set_dying(self, value: bool): self._is_dying = value
    def get_arthur(self) -> Optional[Arthur]: return next((a for a in self._actors if isinstance(a, Arthur)), None)
    def get_lives(self) -> int:
        arthur = self.get_arthur()
        return arthur.lives() if arthur else 0