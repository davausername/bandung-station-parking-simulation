import pygame
import random
import math
import heapq
import numpy as np
from collections import deque
from functools import lru_cache
import itertools
import csv 

# =========================================================
# CONFIGURATION & TIME SCALE
# =========================================================

CELL_SIZE = 20
FPS = 60

WINDOW_WIDTH = 1280 
WINDOW_HEIGHT = 720

# Parameters
PHYSICS_TIME_SCALE = 20.0  
GRID_SIZE_M = 5.0          

# ==============================================================================
# CONFIG: POISSON LAMBDA FOR BANDUNG STATION (KEBON KAWUNG TRAFFIC)
# ==============================================================================
LAMBDA_NORMAL = {
    0: 2.0,  1: 1.0,  2: 0.5,  3: 1.0, 
    4: 4.5,  5: 8.5,                   
    6: 14.0, 7: 18.0, 8: 15.5,         
    9: 9.0,  10: 8.0,                  
    11: 10.5, 12: 12.0, 13: 9.5,       
    14: 11.0, 15: 14.5,                
    16: 19.0, 17: 24.0, 18: 22.0,      
    19: 15.0, 20: 11.5,                
    21: 13.0, 22: 9.5,                 
    23: 4.5
}

LAMBDA_WEEKEND = {
    0: 4.0,  1: 2.5,  2: 1.0,  3: 1.5, 
    4: 5.5,  5: 9.5,                   
    6: 13.0, 7: 15.5, 8: 17.0,         
    9: 16.0, 10: 18.5, 11: 19.0,       
    12: 22.0, 13: 20.0, 14: 24.0,      
    15: 32.0, 16: 40.0, 17: 45.0,      
    18: 42.0, 19: 36.0, 20: 26.0,      
    21: 18.5, 22: 14.0, 23: 8.0        
}

# =========================================================
# STRUKTUR MAP
# =========================================================
MAP_GRID = [
    "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
    "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
    "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
    "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
    ".................xx.....EEE..........",
    ".................xx.....EEE..........",
    ".................xx.....EEE..........",
    "................Sxx.....EEE..........",
    "...............SRRRRRRRREEE..........",
    "...............SRRRRS.RRRRR..........",
    "...............SRSSRS.RRRRR..........",
    "...............SRSSRS.SRRRRR.........",
    "...............SRSSRS.SRSSRR.........",
    "...............SRSSRS.SRSSRR.........",
    "...............SRSSRS.SRSSRS.........",
    "...............SRSSRS.SRS.RS.........",
    "...............SRSSRS.SRSSRS.........",
    "...............SRSSRS.SRSSRS.........",
    "...............SRSSRS.SRSSRS.........",
    "...............SRSSRS.SRSSRS.........",
    "...............SRSSRS.SRSSRS.........",
    "...RRRRRRRRRRRRRRSSRS.SRSSRS.........", 
    "...R...........SRSSRS.SRSSRS.........",
    "...R...........SRSSRS.SRSSRS.........",
    "...R...........SRSSRS.SRSSRS.........",
    "...R...........SRSSRS.SRS.RS.........",
    "...R...........SRSSRS.+RSSRS.........", 
    "...R...........SRSSRS.+RSSRS.........",
    "...R...........SRSSRS.+RSSRS.........",
    "...R...........SRRRRRRRRRRRR.........",
    "...R...........SRRRRRRRRRRRR.........",
    "...RRRRRRRRRRRRRRRRDDDDDRRRR.........",
    "..BBBBBBBBBBBBBBBBBBBBBBBBBBBB.......",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB....",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
]

GRID_WIDTH = len(MAP_GRID[0]) 
GRID_HEIGHT = len(MAP_GRID)   
UI_WIDTH = WINDOW_WIDTH - (GRID_WIDTH * CELL_SIZE) 

COLORS = {
    'M': (80, 80, 80), 'E': (0, 154, 73), 'x': (192, 57, 43),  
    'R': (65, 65, 65), 'S': (241, 196, 15), 'D': (155, 89, 182),
    '+': (41, 128, 185), '.': (27, 94, 32), 'B': (245, 235, 210),
    'T': (100, 100, 100)
}

COLORS_CAR = [
    (41, 128, 185), (240, 240, 240), (139, 69, 19), 
    (128, 128, 128), (192, 192, 192)
]

EXIT_GATES = [(17, 5), (18, 5)]
ENTRANCE_GATES = [(24, 8), (25, 8), (26, 8)]
GATE_CELLS = EXIT_GATES + ENTRANCE_GATES

SLOT_REGISTRY = {}
for y, row in enumerate(MAP_GRID):
    for x, tile in enumerate(row):
        if tile == 'S': SLOT_REGISTRY[(x, y)] = 'S_FREE'
        elif tile == 'D': SLOT_REGISTRY[(x, y)] = 'D_FREE'
        elif tile == '+': SLOT_REGISTRY[(x, y)] = '+_FREE'

# =========================================================
# UI CLASSES
# =========================================================
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        
    def draw(self, surface, font, mouse_pos):
        current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=6)
        
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def is_clicked(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(mouse_pos)
        return False

class Slider:
    def __init__(self, x, y, width, min_val, max_val, initial_val, text, format_str="{:.2f}"):
        self.rect = pygame.Rect(x, y, width, 10)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.text = text
        self.format_str = format_str
        self.dragging = False
        self.handle_radius = 8
        self.handle_pos = self._get_handle_x()

    def _get_handle_x(self):
        percent = (self.val - self.min_val) / (self.max_val - self.min_val)
        return int(self.rect.left + percent * self.rect.width)

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_rect = pygame.Rect(self.handle_pos - self.handle_radius, self.rect.centery - self.handle_radius, self.handle_radius*2, self.handle_radius*2)
            if handle_rect.collidepoint(mouse_pos) or self.rect.collidepoint(mouse_pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                rel_x = max(self.rect.left, min(mouse_pos[0], self.rect.right))
                percent = (rel_x - self.rect.left) / self.rect.width
                self.val = self.min_val + percent * (self.max_val - self.min_val)
                self.handle_pos = rel_x

    def draw(self, surface, font):
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=5)
        active_rect = pygame.Rect(self.rect.left, self.rect.top, self.handle_pos - self.rect.left, self.rect.height)
        pygame.draw.rect(surface, (52, 152, 219), active_rect, border_radius=5)
        pygame.draw.circle(surface, (236, 240, 241), (self.handle_pos, self.rect.centery), self.handle_radius)
        lbl = font.render(self.text, True, (200, 200, 200))
        val_lbl = font.render(self.format_str.format(self.val), True, (255, 255, 255))
        surface.blit(lbl, (self.rect.left, self.rect.top - 20))
        surface.blit(val_lbl, (self.rect.right - val_lbl.get_width(), self.rect.top - 20))

# =========================================================
# PATHFINDING (A*) - DIKEMBALIKAN KE ASLI
# =========================================================
def get_road_dirs(x, y):
    dirs = []
    if y < 4: return [(-1, 0)] 
    
    if x >= 22: dirs.append((0, 1)) 
    elif x <= 20: dirs.append((0, -1)) 
    
    if y == 8 or y == 9:
        dirs.append((-1, 0))
        dirs.append((1, 0))
    elif 4 <= y <= 11: 
        dirs.append((1, 0))  
    elif y >= 29: 
        dirs.append((-1, 0))
        dirs.append((1, 0))
    elif 20 <= y <= 22: 
        dirs.append((1, 0))
        dirs.append((-1, 0))
        
    return dirs if dirs else [(0,1), (0,-1), (1,0), (-1,0)]

counter = itertools.count()

@lru_cache(maxsize=4096)
def find_path(start_x, start_y, target_x, target_y, allowed_chars, obstacles=frozenset(), boundary_active=False):
    queue = []
    heapq.heappush(queue, (0, next(counter), 0, start_x, start_y, tuple()))
    visited = {}
    
    while queue:
        _, _, cost, cx, cy, path = heapq.heappop(queue)
        
        if (cx, cy) == (target_x, target_y):
            return path
            
        if (cx, cy) in visited and visited[(cx, cy)] <= cost:
            continue
        visited[(cx, cy)] = cost
        
        char_current = MAP_GRID[cy][cx]

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            
            if boundary_active:
                if (cy == 1 and ny == 2) or (cy == 2 and ny == 1):
                    if 22 <= cx <= 32: continue
                if (cy == 2 and ny == 3) or (cy == 3 and ny == 2):
                    if 15 <= cx <= 18: continue
                if cy == 3 and ny == 3:
                    if (cx == 18 and nx == 19) or (cx == 19 and nx == 18): continue
                    
            if char_current == 'E' and (dx != 0 or dy != 1):
                continue  
            if char_current == 'x' and (dx != 0 or dy != -1):
                continue  

            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                char_next = MAP_GRID[ny][nx]
                
                if char_next in allowed_chars or (nx == target_x and ny == target_y):
                    step_cost = 1
                    
                    if char_current == 'R' and char_next == 'R':
                        allowed_dirs = get_road_dirs(cx, cy)
                        if (dx, dy) not in allowed_dirs:
                            step_cost = 1000  
                            
                    if char_current == 'M':
                        if dx == 1: step_cost += 100  
                        if dy == -1: step_cost += 100 
                            
                    if (nx, ny) in obstacles:
                        step_cost += 2000 
                        
                    new_cost = cost + step_cost
                    if (nx, ny) not in visited or new_cost < visited.get((nx, ny), float('inf')):
                        h = abs(nx - target_x) + abs(ny - target_y)
                        heapq.heappush(queue, (new_cost + h, next(counter), new_cost, nx, ny, path + ((nx, ny),)))
    return tuple()

# =========================================================
# CAR CLASS
# =========================================================
class Car:
    def __init__(self, x, y, lane, car_id, intent):
        self.id = car_id
        self.lane = lane 
        self.dx = -1 
        
        self.x = x
        self.y = y
        self.real_x = x * CELL_SIZE
        self.real_y = y * CELL_SIZE
        
        self.is_disabled = (random.random() < 0.01)
        self.color = random.choice(COLORS_CAR)
        self.intent = intent 
        
        self.state = "HIGHWAY"
        self.target_slot = None
        self.dest_x = 0
        self.dest_y = 0
        self.path = []
        self.target_entrance_x = random.choice([24, 25, 26]) 
        
        self.highway_speed_kmh = random.uniform(40.0, 55.0) 
        self.parking_speed_kmh = random.uniform(15.0, 25.0)
        self.actual_speed_kmh = 0.0 
        self.move_accumulator = 0.0
        
        self.park_timer = 0.0
        self.maneuver_timer = 0.0
        self.gate_delay = 0.0
        self.block_timer = 0 

    def free_slot(self):
        if self.target_slot in SLOT_REGISTRY and SLOT_REGISTRY[self.target_slot] == self.id:
            original_tile = MAP_GRID[self.target_slot[1]][self.target_slot[0]]
            SLOT_REGISTRY[self.target_slot] = f"{original_tile}_FREE"

    def allocate_slot(self):
        if self.intent == "DROP_OFF":
            empty_slots = [c for c, state in SLOT_REGISTRY.items() if state == 'D_FREE']
        else:
            if self.is_disabled:
                empty_slots = [c for c, state in SLOT_REGISTRY.items() if state == '+_FREE']
                if not empty_slots: 
                    empty_slots = [c for c, state in SLOT_REGISTRY.items() if state == 'S_FREE']
            else:
                empty_slots = [c for c, state in SLOT_REGISTRY.items() if state == 'S_FREE']

        if not empty_slots: return False

        empty_slots.sort(key=lambda pos: math.hypot(pos[0] - 25, pos[1] - 31) + random.uniform(0, 5.0))
        chosen = empty_slots[0]

        SLOT_REGISTRY[chosen] = self.id
        self.target_slot = chosen
        return True

    def update_smooth_position(self, dt):
        target_px = self.x * CELL_SIZE
        target_py = self.y * CELL_SIZE
        diff_x = target_px - self.real_x
        diff_y = target_py - self.real_y

        smoothing_factor = min(1.0, 0.40 * (dt / (1.0/FPS) if dt > 0 else 1))
        
        self.real_x += diff_x * smoothing_factor
        self.real_y += diff_y * smoothing_factor

        if abs(diff_x) < 0.1: self.real_x = target_px
        if abs(diff_y) < 0.1: self.real_y = target_py

# =========================================================
# DRAWING SYSTEM
# =========================================================
def draw_map(surface, cars, font, boundary_active=False):
    surface.fill((20, 20, 20))
    for y, row in enumerate(MAP_GRID):
        for x, tile in enumerate(row):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, COLORS.get(tile, (0, 0, 0)), rect)
            
            if tile == 'S':
                pygame.draw.rect(surface, (80, 80, 40), rect, 1)
            elif tile == 'D':
                pygame.draw.rect(surface, (100, 50, 120), rect, 1)
                text_surf = font.render('D', True, (200, 150, 220))
                surface.blit(text_surf, (rect.x + 4, rect.y))
            elif tile == '+':
                pygame.draw.rect(surface, (41, 128, 185), rect, 1)
                text_surf = font.render('+', True, (150, 200, 230))
                surface.blit(text_surf, (rect.x + 5, rect.y))

    for x_dash in range(0, GRID_WIDTH * CELL_SIZE, 30):
        pygame.draw.line(surface, (255, 255, 255), (x_dash, 2 * CELL_SIZE), (x_dash + 15, 2 * CELL_SIZE), 2)

    if boundary_active:
        px_start = 22 * CELL_SIZE
        px_end = 33 * CELL_SIZE
        py = 2 * CELL_SIZE
        pygame.draw.line(surface, (230, 126, 34), (px_start, py), (px_end, py), 6)
        for cx in range(px_start, px_end, 20):
            pygame.draw.circle(surface, (255, 255, 255), (cx, py), 3)
            pygame.draw.circle(surface, (211, 84, 0), (cx, py), 2)
            
        L_sx = 15 * CELL_SIZE
        L_ex = 19 * CELL_SIZE
        L_y1 = 3 * CELL_SIZE
        L_y2 = 4 * CELL_SIZE
        
        pygame.draw.line(surface, (230, 126, 34), (L_sx, L_y1), (L_ex, L_y1), 6)
        pygame.draw.line(surface, (230, 126, 34), (L_ex, L_y1), (L_ex, L_y2), 6)
        
        for cx in range(L_sx, L_ex + 1, 20):
            pygame.draw.circle(surface, (255, 255, 255), (cx, L_y1), 3)
            pygame.draw.circle(surface, (211, 84, 0), (cx, L_y1), 2)
        pygame.draw.circle(surface, (255, 255, 255), (L_ex, L_y2), 3)
        pygame.draw.circle(surface, (211, 84, 0), (L_ex, L_y2), 2)

    for gx, gy in GATE_CELLS:
        rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        car_waiting = any(c.x == gx and c.y == gy and c.gate_delay > 0 for c in cars)
        pygame.draw.rect(surface, (50, 50, 50), (rect.left, rect.centery - 4, 6, 8))
        if car_waiting:
            pygame.draw.line(surface, (46, 204, 113), (rect.left + 4, rect.centery), (rect.right, rect.top), 4)
        else:
            pygame.draw.line(surface, (231, 76, 60), (rect.left + 4, rect.centery), (rect.right, rect.centery), 4)

def draw_ui(surface, font, title_font, cars, time_in_hours, sim_mode, total_slots, occ_slots, lam_current, is_paused, time_scale, sliders, avg_main_speed):
    ui_rect = pygame.Rect(GRID_WIDTH * CELL_SIZE, 0, UI_WIDTH, WINDOW_HEIGHT)
    pygame.draw.rect(surface, (30, 35, 45), ui_rect)
    pygame.draw.line(surface, (100, 100, 100), (GRID_WIDTH * CELL_SIZE, 0), (GRID_WIDTH * CELL_SIZE, WINDOW_HEIGHT), 2)
    
    x_offset = GRID_WIDTH * CELL_SIZE + 20
    h = int(time_in_hours) % 24
    m = int((time_in_hours * 60) % 60)
    
    title = title_font.render("SIMULASI PARKIR KA BANDUNG", True, (241, 196, 15))
    surface.blit(title, (x_offset, 25))
    clock_surf = title_font.render(f"JAM: {h:02d}:{m:02d}", True, (255, 255, 255))
    surface.blit(clock_surf, (x_offset, 60))
    scale_surf = font.render(f"Scale: {time_scale:.0f}x Real Time", True, (46, 204, 113))
    surface.blit(scale_surf, (x_offset, 85))
    
    if is_paused:
        stat_surf = font.render("[PAUSED]", True, (241, 196, 15))
    else:
        color_stat = (231, 76, 60) if sim_mode == "WEEKEND" else (52, 152, 219)
        stat_surf = font.render(f"[{sim_mode}]", True, color_stat)
    surface.blit(stat_surf, (x_offset + 120, 65))

    y = 120
    metrics = [
        ("Spatial Scale", "1 Grid = 5m x 5m"),
        ("Main Road Avg Speed", f"{avg_main_speed:.1f} km/h"),
        ("Total Slots", f"{total_slots} Slots"), 
        ("Slot Filled", f"{occ_slots} Slots"),
        ("Available Slots", f"{total_slots - occ_slots} Slots"),
        ("Parking Occupancy", f"{(occ_slots/total_slots)*100 if total_slots else 0:.1f} %"),
        ("Active Cars", f"{len(cars)} Units"),
        ("Current Lambda (Real)", f"{lam_current:.2f} / min")
    ]
    
    for label, val in metrics:
        if label:
            lbl_surf = font.render(label, True, (180, 190, 200))
            val_surf = font.render(val, True, (255, 255, 255))
            surface.blit(lbl_surf, (x_offset, y))
            surface.blit(val_surf, (x_offset + 220, y))
        y += 25

    y += 5
    pygame.draw.line(surface, (100, 100, 100), (x_offset, y), (x_offset + UI_WIDTH - 40, y), 1)
    y += 5
    
    legend = [
        ((241, 196, 15), "Parking Slots"),
        ((41, 128, 185), "For Dissabilities"),
        ((155, 89, 182), "Dropzone"),
        ((39, 174, 96), "Entrance / Exit")
    ]
    for color, text in legend:
        pygame.draw.circle(surface, color, (x_offset + 10, y + 8), 5)
        txt_surf = font.render(text, True, (200, 200, 200))
        surface.blit(txt_surf, (x_offset + 30, y))
        y += 25
        
    y += 5
    pygame.draw.line(surface, (100, 100, 100), (x_offset, y), (x_offset + UI_WIDTH - 40, y), 1)

    for slider in sliders:
        slider.draw(surface, font)

# =========================================================
# MAIN LOOP
# =========================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    pygame.display.set_caption("Optimized Realistic One-Way Parking Simulation")
    clock = pygame.time.Clock()
    
    font = pygame.font.SysFont("Segoe UI", 14, bold=True)
    title_font = pygame.font.SysFont("Segoe UI", 18, bold=True)
    
    cars = []
    car_id_pool = 0
    frame_count = 0
    
    time_in_hours = 0.0 
    next_spawn_time_hours = 0.0 
    
    running = True
    sim_mode = "NORMAL DAY"
    is_paused = False
    boundary_active = False

    csv_filename = "simulation_log.csv"
    with open(csv_filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Time_Hours', 'Lambda_Real', 'Occupied_Slots', 'Total_Slots', 
            'Avg_Main_Speed', 'Gate_Delay_Cars', 
            'Intent_DropOff', 'Intent_Short', 'Intent_Long', 'Intent_DriveBy'
        ])
    last_log_time = 0.0
    intent_counts = {'DROP_OFF': 0, 'SHORT_VISIT': 0, 'LONG_VISIT': 0, 'DRIVE_BY': 0}

    btn_y1 = WINDOW_HEIGHT - 60
    x_offset = GRID_WIDTH * CELL_SIZE + 15

    btn_normal = Button(x_offset, btn_y1, 120, 35, "NORMAL DAY", (46, 204, 113), (39, 174, 96))
    btn_weekend = Button(x_offset + 135, btn_y1, 100, 35, "WEEKEND", (231, 76, 60), (192, 57, 43))
    btn_pause = Button(x_offset + 250, btn_y1, 95, 35, "PAUSE", (52, 152, 219), (41, 128, 185))
    btn_boundary = Button(x_offset + 359, btn_y1, 150, 35, "BOUNDARY: OFF", (230, 126, 34), (211, 84, 0))

    slider_width = 300
    slider_start_y = 458
    
    slider_arrival = Slider(x_offset + 10, slider_start_y, slider_width, 0.0, 5.0, 1.0, "Arrival Rate Scale", "{:.1f}x")
    slider_gate = Slider(x_offset + 10, slider_start_y + 45, slider_width, 0.0, 100.0, 50.0, "Gate Latency", "{:.0f}%")
    slider_impatience = Slider(x_offset + 10, slider_start_y + 90, slider_width, 0.0, 100.0, 20.0, "Impatience Factor", "{:.0f}%")
    slider_dwell = Slider(x_offset + 10, slider_start_y + 135, slider_width, 0.5, 3.0, 1.0, "Dwell Time Scale", "{:.1f}x")
    slider_timescale = Slider(x_offset + 10, slider_start_y + 180, slider_width, 100.0, 720.0, 120.0, "Time Scale (1 Day Duration)", "{:.0f}x")
    
    sliders = [slider_arrival, slider_gate, slider_impatience, slider_dwell, slider_timescale]

    def reset_sim():
        cars.clear()
        for k in SLOT_REGISTRY:
            original_tile = MAP_GRID[k[1]][k[0]]
            SLOT_REGISTRY[k] = f"{original_tile}_FREE"
        return 0.0, 0, 0.0 

    while running:
        raw_dt = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
                
            if btn_normal.is_clicked(event, mouse_pos):
                sim_mode = "NORMAL DAY"
                is_paused = False
                btn_pause.text = "PAUSE"
                time_in_hours, car_id_pool, next_spawn_time_hours = reset_sim()
                intent_counts = {'DROP_OFF': 0, 'SHORT_VISIT': 0, 'LONG_VISIT': 0, 'DRIVE_BY': 0}
                
            if btn_weekend.is_clicked(event, mouse_pos):
                sim_mode = "WEEKEND"
                is_paused = False
                btn_pause.text = "PAUSE"
                time_in_hours, car_id_pool, next_spawn_time_hours = reset_sim()
                intent_counts = {'DROP_OFF': 0, 'SHORT_VISIT': 0, 'LONG_VISIT': 0, 'DRIVE_BY': 0}
                
            if btn_pause.is_clicked(event, mouse_pos):
                is_paused = not is_paused
                btn_pause.text = "RESUME" if is_paused else "PAUSE"

            if btn_boundary.is_clicked(event, mouse_pos):
                boundary_active = not boundary_active
                if boundary_active:
                    btn_boundary.text = "BOUNDARY: ON"
                    btn_boundary.color = (211, 84, 0)
                else:
                    btn_boundary.text = "BOUNDARY: OFF"
                    btn_boundary.color = (230, 126, 34)

            for slider in sliders:
                slider.handle_event(event, mouse_pos)

        current_hour_int = int(time_in_hours) % 24
        
        if sim_mode == "WEEKEND":
            base_lam = LAMBDA_WEEKEND.get(current_hour_int, 1.0)
        else:
            base_lam = LAMBDA_NORMAL.get(current_hour_int, 1.0)

        lam_real = base_lam * slider_arrival.val
        time_scale_multiplier = slider_timescale.val
        in_game_dt = raw_dt * time_scale_multiplier if not is_paused else 0.0

        if not is_paused:
            time_in_hours += in_game_dt / 3600.0
            if time_in_hours >= 24.0: 
                time_in_hours -= 24.0 
                next_spawn_time_hours -= 24.0  # [FIX 1: 24-HOUR WRAP AROUND]
            frame_count += 1
            
            # =================================================
            # EXPONENTIAL INTER-ARRIVAL SPAWNER 
            # =================================================
            if lam_real > 0:
                while time_in_hours >= next_spawn_time_hours:
                    intent_val = random.random()
                    has_empty_slots = any(state in ['S_FREE', 'D_FREE', '+_FREE'] for state in SLOT_REGISTRY.values())
                    
                    train_peak_hours = [4, 5, 6, 7, 8, 11, 12, 16, 17, 18, 21, 22]
                    if current_hour_int in train_peak_hours:
                        # [FIX 2: STATION BOUND PROBABILITY ADJUSTED]
                        station_bound_prob = 0.40 if sim_mode == "NORMAL DAY" else 0.85
                    else:
                        station_bound_prob = 0.15 if sim_mode == "NORMAL DAY" else 0.45
                        
                    wants_to_park = random.random() < station_bound_prob
                    
                    if wants_to_park and has_empty_slots:
                        lane = random.choices([0, 1, 2, 3], weights=[0.05, 0.15, 0.30, 0.50])[0]
                        # [FIX 3: REALISTIC INTENT WEIGHTS FOR A TRAIN STATION]
                        if intent_val < 0.75: intent = "DROP_OFF"
                        elif intent_val < 0.95: intent = "SHORT_VISIT"
                        else: intent = "LONG_VISIT"
                    else:
                        intent = "DRIVE_BY" 
                        lane = random.choices([0, 1, 2, 3], weights=[0.50, 0.30, 0.15, 0.05])[0]
                    
                    spawn_x = GRID_WIDTH - 1 
                    is_clear = not any(c.x == spawn_x and c.y == lane for c in cars)
                    
                    if is_clear:
                        cars.append(Car(spawn_x, lane, lane, car_id_pool, intent))
                        car_id_pool += 1
                        intent_counts[intent] += 1  
                        
                        inter_arrival_minutes = np.random.exponential(1.0 / lam_real)
                        next_spawn_time_hours += (inter_arrival_minutes / 60.0)
                    else:
                        break 
            else:
                next_spawn_time_hours = time_in_hours + (1.0 / 60.0)

            # =================================================
            # TIMER UPDATE
            # =================================================
            for car in cars:
                if car.state == "MANEUVERING":
                    car.maneuver_timer -= in_game_dt
                    if car.maneuver_timer <= 0:
                        car.state = "PARKED"
                        duration_multiplier = 1.8 if sim_mode == "WEEKEND" else 1.0
                        
                        if car.intent == "DROP_OFF":
                            base_park_time = random.uniform(2.0, 5.0) * duration_multiplier * 60.0 
                        elif car.intent == "SHORT_VISIT":
                            base_park_time = random.uniform(0.25, 1.5) * duration_multiplier * 3600.0 
                        else:
                            base_park_time = random.uniform(2.0, 4.0) * duration_multiplier * 3600.0 
                            
                        car.park_timer = max(60.0, base_park_time * slider_dwell.val)

                elif car.state == "PARKED":
                    car.park_timer -= in_game_dt
                    if car.park_timer <= 0:
                        car.state = "NAVIGATING_OUT"
                        
                        # [FIX UTAMA: ATURAN EXIT GATE]
                        # Jalur Paling Kiri (x <= 17) -> Exit Paling Kiri (17)
                        # Jalur Kedua (x > 17) -> Exit Kedua (18)
                        if car.x <= 17:
                            exit_x = 17
                        else:
                            exit_x = 18 
                            
                        car.dest_x, car.dest_y = exit_x, 4
                        
                        bfs_path = list(find_path(car.x, car.y, car.dest_x, car.dest_y, frozenset(['R', 'x', 'G', 'E']), frozenset(), boundary_active))
                        
                        if bfs_path:
                            if boundary_active:
                                join_lane = 3 
                            else:
                                join_lane = random.choices([1, 2, 3], weights=[0.10, 0.25, 0.65])[0]
                                
                            path_out = [(exit_x, 3)]
                            if join_lane == 1:
                                path_out.extend([(exit_x, 2), (exit_x, 1)])
                            elif join_lane == 2:
                                path_out.append((exit_x, 2))
                            
                            car.path = bfs_path + path_out
                        else:
                            car.park_timer = 60.0 
                            car.state = "PARKED"

            # =================================================
            # MOVEMENT PLANNING & GRIDLOCK RESOLUTION 
            # =================================================
            occupied_cells = {(c.x, c.y): c for c in cars}
            future_occupied = set() 
            planned_moves = {}
            
            patience_threshold = max(15, 200 - (slider_impatience.val / 100.0) * 185)

            for car in cars:
                if car.state in ["PARKED", "MANEUVERING"] or car.gate_delay > 0:
                    if car.gate_delay > 0: car.gate_delay -= in_game_dt
                    future_occupied.add((car.x, car.y))
                    car.actual_speed_kmh = 0.0
                    continue

                current_speed_kmh = car.highway_speed_kmh if car.state in ["HIGHWAY", "LEAVING_HIGHWAY"] else car.parking_speed_kmh
                
                nx, ny = car.x, car.y
                if car.path:
                    px, py = car.path[0]
                else:
                    px, py = car.x - 1, car.y

                if car.state == "HIGHWAY" and car.intent != "DRIVE_BY" and car.target_entrance_x <= car.x <= car.target_entrance_x + 3:
                    current_speed_kmh = min(current_speed_kmh, 20.0) 
                
                if (nx, ny) in GATE_CELLS or (px, py) in GATE_CELLS:
                    current_speed_kmh = min(current_speed_kmh, 10.0) 
                elif car.state == "ENTERING" and car.y < 10:
                    current_speed_kmh = min(current_speed_kmh, 15.0) 
                elif car.state in ["NAVIGATING_OUT", "LEAVING_HIGHWAY"] and car.y < 6:
                    current_speed_kmh = min(current_speed_kmh, 15.0) 
                
                speed_ms = current_speed_kmh / 3.6
                grids_per_sec_ingame = speed_ms / GRID_SIZE_M
                dynamic_physics_scale = slider_timescale.val / 6.0 
                visual_speed = grids_per_sec_ingame * dynamic_physics_scale
                car.move_accumulator += raw_dt * visual_speed * 1.5 

                if car.move_accumulator >= 1.0:
                    if car.path:
                        if (px, py) in occupied_cells and occupied_cells[(px, py)] != car:
                            car.block_timer += 1
                            if car.state in ["HIGHWAY", "ENTERING"] and car.block_timer > patience_threshold:
                                if car.y <= 3: 
                                    car.intent = "DRIVE_BY"
                                    if car.target_slot: car.free_slot()
                                    car.target_slot = None
                                    car.path = []
                                    car.state = "HIGHWAY"
                                    car.block_timer = 0
                                    nx = car.x - 1
                            elif car.block_timer > 20 and frame_count % 10 == 0 and car.y > 4:
                                
                                # [FIX 3: CEGAH RECALCULATE DETOUR/MEMUTAR]
                                # Jika mobil di jalur Exit (y <= 12), MATIKAN Recalculate!
                                # Biarkan mereka ngantri dan di-push otomatis oleh Failsafe Tembus Pandang.
                                if car.state == "NAVIGATING_OUT" and car.y <= 12:
                                    pass 
                                elif car.state == "ENTERING" and car.y <= 8:
                                    pass
                                else:
                                    obs = frozenset([(px, py)])
                                    
                                    # [FIX 1: HARAM OFF-ROAD KE SLOT PARKIR]
                                    # Jangan pernah masukkan S, D, + supaya mobil tidak numpuk di parkiran
                                    if car.state == "NAVIGATING_OUT":
                                        allowed = frozenset(['R', 'E', 'x'])
                                    else:
                                        allowed = frozenset(['R', 'E'])
                                        
                                    new_path = list(find_path(car.x, car.y, car.dest_x, car.dest_y, allowed, obs, boundary_active))
                                    
                                    if new_path and new_path != car.path:
                                        if car.state == "NAVIGATING_OUT":
                                            join_lane = 3 if boundary_active else random.choices([1, 2, 3], weights=[0.10, 0.25, 0.65])[0]
                                            path_out = [(car.dest_x, 3)]
                                            if join_lane == 1:
                                                path_out.extend([(car.dest_x, 2), (car.dest_x, 1)])
                                            elif join_lane == 2:
                                                path_out.append((car.dest_x, 2))
                                            new_path.extend(path_out)
                                        car.path = new_path
                                        # [FIX 2: BIARKAN TIMER FAILSAFE NAIK]
                                        # car.block_timer = 0 dihapus di sini agar timer bisa sampai angka 45
                                        
                            # [FAILSAFE BISA JALAN]
                            # Jika mobil terkunci macet lebih dari 45 frame, paksa tembus maju
                            if car.block_timer > 45:
                                nx, ny = px, py
                                
                        elif (px, py) in future_occupied:
                            car.block_timer += 1
                            if car.block_timer > 45:
                                nx, ny = px, py
                        else:
                            nx, ny = px, py
                            car.block_timer = 0
                    else: 
                        if car.state in ["HIGHWAY", "LEAVING_HIGHWAY", "DRIVE_BY"]:
                            if car.state == "LEAVING_HIGHWAY":
                                nx = car.x - 1
                            elif car.state == "HIGHWAY" and car.intent != "DRIVE_BY" and car.x == car.target_entrance_x:
                                if boundary_active and car.y < 2:
                                    car.intent = "DRIVE_BY"
                                    nx = car.x - 1
                                else:
                                    if car.allocate_slot():
                                        car.state = "ENTERING"
                                        car.dest_x, car.dest_y = car.target_slot
                                        
                                        path_down = [(car.x, y_step) for y_step in range(car.y + 1, 10)]
                                        
                                        bfs_path = list(find_path(car.x, 9, car.dest_x, car.dest_y, frozenset(['R', 'E']), frozenset(), boundary_active))
                                        
                                        if bfs_path:
                                            car.path = path_down + bfs_path
                                        else:
                                            car.free_slot()
                                            car.intent = "DRIVE_BY"
                                            nx = car.x - 1 
                                    else:
                                        if random.uniform(0, 100) < slider_impatience.val:
                                            car.intent = "DRIVE_BY"
                                        nx = car.x - 1
                            else:
                                if boundary_active and car.y == 3 and 15 <= car.x <= 22:
                                    nx = car.x - 1
                                    ny = 2 
                                elif car.intent != "DRIVE_BY":
                                    can_shift_down = car.y < 3
                                    if can_shift_down and boundary_active:
                                        if car.y == 1 and 22 <= car.x <= 32:
                                            can_shift_down = False
                                            
                                    if can_shift_down and random.random() < 0.15:
                                        nx = car.x
                                        ny = car.y + 1
                                    else:
                                        nx = car.x - 1
                                else:
                                    if car.y > 1 and random.random() < 0.10:
                                        nx = car.x
                                        ny = car.y - 1
                                    else:
                                        nx = car.x - 1
                        elif car.state == "ENTERING":
                            if car.y < 4:
                                nx, ny = car.x, car.y + 1
                            else:
                                nx, ny = car.x, car.y 
                        elif car.state == "NAVIGATING_OUT":
                            if car.y > 3:
                                nx, ny = car.x, car.y - 1
                            else:
                                car.state = "LEAVING_HIGHWAY"
                                nx = car.x - 1

                if (nx, ny) not in future_occupied:
                    future_occupied.add((nx, ny))
                    planned_moves[car.id] = (nx, ny)
                    car.actual_speed_kmh = current_speed_kmh
                    car.block_timer = 0
                else:
                    car.block_timer += 1
                    if car.block_timer > 45:
                        future_occupied.add((nx, ny))
                        planned_moves[car.id] = (nx, ny)
                        car.actual_speed_kmh = current_speed_kmh
                        car.block_timer = 0
                    else:
                        future_occupied.add((car.x, car.y)) 
                        if car.move_accumulator > 1.0: car.move_accumulator = 1.0 
                        car.actual_speed_kmh = 0.0

            # =================================================
            # APPLY MOVES & STATE TRANSITIONS
            # =================================================
            for car in cars:
                if car.id in planned_moves:
                    nx, ny = planned_moves[car.id]
                    
                    if (nx, ny) != (car.x, car.y):
                        car.move_accumulator -= 1.0 
                        if car.path and (nx, ny) == car.path[0]:
                            car.path.pop(0)
                            
                            if car.state == "NAVIGATING_OUT" and car.y <= 3:
                                car.free_slot()
                                car.state = "LEAVING_HIGHWAY"
                                car.path = []
                                car.block_timer = 0
                            elif not car.path:
                                if car.state == "ENTERING":
                                    car.state = "MANEUVERING"
                                    car.maneuver_timer = random.uniform(30.0, 120.0) 
                                elif car.state == "NAVIGATING_OUT":
                                    car.free_slot()
                                    car.state = "LEAVING_HIGHWAY"
                                    car.move_accumulator = 0.0

                        occupied_cells.pop((car.x, car.y), None)
                        
                        old_pos = (car.x, car.y)
                        car.x, car.y = nx, ny
                        occupied_cells[(car.x, car.y)] = car
                        
                        if (car.x, car.y) in GATE_CELLS and old_pos not in GATE_CELLS and car.gate_delay <= 0:
                            latency_multiplier = slider_gate.val / 100.0
                            car.gate_delay = latency_multiplier * random.uniform(10.0, 40.0) 

            for c in cars:
                if c.x < -1: 
                    c.free_slot()
            cars = [c for c in cars if c.x >= -1]

            # =========================================================
            # PENYIMPANAN DATA UNTUK GRAFIK
            # =========================================================
            if not is_paused and (time_in_hours - last_log_time) >= (5.0 / 60.0):
                last_log_time = time_in_hours
                gate_delay_cars = sum(1 for c in cars if c.gate_delay > 0)
                
                tot_s = len(SLOT_REGISTRY)
                occ_s = sum(1 for v in SLOT_REGISTRY.values() if v not in ['S_FREE', 'D_FREE', '+_FREE'])
                m_road_cars = [c for c in cars if c.y <= 3 and c.state in ["HIGHWAY", "LEAVING_HIGHWAY"]]
                avg_spd = sum(c.actual_speed_kmh for c in m_road_cars) / len(m_road_cars) if m_road_cars else 0.0
                
                with open(csv_filename, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        round(time_in_hours, 3), 
                        round(lam_real, 2), 
                        occ_s, 
                        tot_s, 
                        round(avg_spd, 2), 
                        gate_delay_cars,
                        intent_counts.get('DROP_OFF', 0), 
                        intent_counts.get('SHORT_VISIT', 0),
                        intent_counts.get('LONG_VISIT', 0), 
                        intent_counts.get('DRIVE_BY', 0)
                    ])

        # =================================================
        # DRAWING
        # =================================================
        screen.fill((0, 0, 0))
        draw_map(screen, cars, font, boundary_active)

        blink = (frame_count // 10) % 2 == 0

        for car in cars:
            if not is_paused:
                car.update_smooth_position(raw_dt)
                
            car_rect = pygame.Rect(car.real_x + 2, car.real_y + 2, CELL_SIZE - 4, CELL_SIZE - 4)
            pygame.draw.rect(screen, car.color, car_rect, border_radius=4)

            if car.state == "ENTERING":
                pygame.draw.circle(screen, (52, 152, 219), car_rect.center, 3)
            elif car.state == "MANEUVERING":
                if blink or is_paused: pygame.draw.circle(screen, (241, 196, 15), car_rect.center, 3)
            elif car.state == "PARKED":
                if car.intent == "DROP_OFF": pygame.draw.circle(screen, (155, 89, 182), car_rect.center, 3)
                elif car.intent == "SHORT_VISIT": pygame.draw.circle(screen, (230, 126, 34), car_rect.center, 3)
                else: pygame.draw.circle(screen, (255, 255, 255), car_rect.center, 3) 
            elif car.state == "NAVIGATING_OUT":
                pygame.draw.circle(screen, (231, 76, 60), car_rect.center, 3)
                
            if car.is_disabled and car.state not in ["MANEUVERING"]:
                pygame.draw.line(screen, (255, 255, 255), (car_rect.centerx-2, car_rect.centery), (car_rect.centerx+2, car_rect.centery), 2)
                pygame.draw.line(screen, (255, 255, 255), (car_rect.centerx, car_rect.centery-2), (car_rect.centerx, car_rect.centery+2), 2)

        total_slots = len(SLOT_REGISTRY)
        occ_slots = sum(1 for v in SLOT_REGISTRY.values() if v not in ['S_FREE', 'D_FREE', '+_FREE'])
        
        main_road_cars = [c for c in cars if c.y <= 3 and c.state in ["HIGHWAY", "LEAVING_HIGHWAY"]]
        if main_road_cars:
            avg_main_speed = sum(c.actual_speed_kmh for c in main_road_cars) / len(main_road_cars)
        else:
            avg_main_speed = 0.0
            
        draw_ui(screen, font, title_font, cars, time_in_hours, sim_mode, total_slots, occ_slots, lam_real, is_paused, slider_timescale.val, sliders, avg_main_speed)
        
        btn_normal.draw(screen, font, mouse_pos)
        btn_weekend.draw(screen, font, mouse_pos)
        btn_pause.draw(screen, font, mouse_pos)
        btn_boundary.draw(screen, font, mouse_pos)

        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()