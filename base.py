import os
import sys
import math
import random
import pygame
from sys import exit

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Wake Up!")
clock = pygame.time.Clock()

if getattr(sys, 'frozen', False):
    script_dir = sys._MEIPASS
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))

font_path = os.path.join(script_dir, "PixelPurl.ttf")
font = pygame.font.Font(font_path, 20)
big_font = pygame.font.Font(font_path, 36)
title_font = pygame.font.Font(font_path, 48)
white = (255, 255, 255)
dark_gray = (40, 40, 40)
box_color = (235, 234, 222)

bg_path = os.path.join(script_dir, "bg.png")
if not os.path.exists(bg_path):
    bg_path = os.path.join(script_dir, "test bg.jpg")
bg_image = pygame.image.load(bg_path).convert()
bg_image = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

ball_path = os.path.join(script_dir, "sprites", "ball.png")
if os.path.exists(ball_path):
    ball_image = pygame.image.load(ball_path).convert_alpha()
    ball_image = pygame.transform.scale(ball_image, (40, 40))
else:
    ball_image = None

item_sprites = {}
def load_sprite(filenames, target_size=(44, 44)):
    if isinstance(filenames, str):
        filenames = [filenames]
    for filename in filenames:
        search_paths = [
            os.path.join(script_dir, "sprites", filename),
            os.path.join(script_dir, filename)
        ]
        for p in search_paths:
            if os.path.isfile(p):
                try:
                    surf = pygame.image.load(p).convert_alpha()
                    return pygame.transform.scale(surf, target_size)
                except pygame.error:
                    pass
    return None

cat_surf = load_sprite("cat.png", (44, 44))
if cat_surf:
    item_sprites["Cat"] = cat_surf

hamper_slot_surf = load_sprite(["hamper_side.png", "hamper.png"], (44, 44))
if hamper_slot_surf:
    item_sprites["Clothes Hamper"] = hamper_slot_surf

phone_slot_surf = load_sprite(["phone_big.png", "phone.png"], (44, 44))
if phone_slot_surf:
    item_sprites["Phone"] = phone_slot_surf

pinboard_slot_surf = load_sprite(["pinboard_front.png", "pinboard.png"], (44, 44))
if pinboard_slot_surf:
    item_sprites["Pin Board"] = pinboard_slot_surf

room_cat_idle = load_sprite("cat.png", (96, 96))
room_cat_angry = load_sprite("angry_cat.png", (96, 96)) or room_cat_idle
ROOM_CAT_POS = (560, 360)

room_hamper_1 = load_sprite(["hamper_top_1.png", "hamper_1_top.png", "hamper_side.png"], (96, 96))
room_hamper_2 = load_sprite(["hamper_top_2.png", "hamper_2_top.png"], (96, 96)) or room_hamper_1
ROOM_HAMPER_POS = (420, 395)

room_phone_1 = load_sprite(["phone_vibrate_1.png", "phone_1_vibrate.png", "phone_big.png", "phone.png"], (72, 72))
room_phone_2 = load_sprite(["phone_vibrate_2.png", "phone_2_vibrate.png"], (72, 72)) or room_phone_1
ROOM_PHONE_POS = (200, 310)

room_pinboard_1 = load_sprite(["pinboard_1.png", "pinboard_front.png", "pinboard.png"], (220, 220))
room_pinboard_2 = load_sprite(["pinboard_2.png"], (220, 220)) or room_pinboard_1
ROOM_PINBOARD_POS = (175, -20)

PLAYER_WAKE_POS = (230, 240)

def resolve_audio_path(filename):
    extensions = ["", ".wav", ".mp3", ".ogg"]
    search_dirs = [
        os.path.join(script_dir, "Audio", "Music"),
        os.path.join(script_dir, "Audio", "SFX"),
        os.path.join(script_dir, "Audio"),
        script_dir
    ]
    for directory in search_dirs:
        for ext in extensions:
            target = os.path.join(directory, filename + ext)
            if os.path.isfile(target):
                return target
    return None

current_track = None
def play_bgm(track_name, loop=True):
    global current_track
    path = resolve_audio_path(track_name)
    if path and path != current_track:
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.6)
            loop_count = -1 if loop else 0
            pygame.mixer.music.play(loop_count)
            current_track = path
        except pygame.error:
            pass

def load_sound(filename):
    path = resolve_audio_path(filename)
    if path:
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(0.85)
            return sound
        except pygame.error:
            return None
    return None

sfx_snap = load_sound("snap")
sfx_win = load_sound("win")
sfx_fail = load_sound("fail")
sfx_click = load_sound("click")

sfx_papers = load_sound("papers")
sfx_clothes = load_sound("clothes")
sfx_phone = load_sound("phone")
sfx_cat = load_sound("cat")
sfx_bounce = load_sound("bounce")

def play_item_sfx(item_name):
    if sfx_bounce:
        sfx_bounce.play()

    if item_name == "Pin Board":
        if sfx_papers:
            sfx_papers.play()
    elif item_name == "Clothes Hamper":
        if sfx_clothes:
            sfx_clothes.play()
    elif item_name == "Phone":
        if sfx_phone:
            sfx_phone.play()
    elif item_name == "Cat":
        if sfx_cat:
            sfx_cat.play()

def get_failure_message(seq):
    if seq[0] == "Cat":
        return "DISASTER! The ball rolled straight to the cat first! The cat casually batted it under the bed and went to sleep; you overslept completely!"
    elif seq.index("Phone") < seq.index("Clothes Hamper"):
        return "DISASTER! The ball hit the phone too early! The phone buzzed and fell under a pile of blankets; the ball got stuck and you stayed asleep!"
    elif seq.index("Clothes Hamper") > seq.index("Cat"):
        return "DISASTER! The cat intercepted the ball before the hamper could knock over! The chain stopped dead and you slept through your alarm!"
    elif seq[0] != "Pin Board":
        return "DISASTER! The ball bounced off course without the pin board to guide it! It ricocheted uselessly against the wall while you snoozed!"
    else:
        return "DISASTER! The ball took a bad bounce, lost momentum, and rolled to a stop; you're still fast asleep in bed!"

def draw_wrapped_text(surface, text, font_obj, color, center_x, center_y, max_width=680, line_spacing=6):
    words = text.split(" ")
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        w, _ = font_obj.size(test_line)
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    line_surfs = [font_obj.render(line, True, color) for line in lines]
    line_height = font_obj.get_linesize() + line_spacing
    total_height = len(line_surfs) * line_height - line_spacing
    start_y = center_y - (total_height // 2)

    for i, surf in enumerate(line_surfs):
        rect = surf.get_rect(center=(center_x, start_y + (i * line_height) + (surf.get_height() // 2)))
        surface.blit(surf, rect)

slots = [50, 250, 450, 650]
initial_slots = [0, 1, 2, 3]
random.shuffle(initial_slots)

items = [
    {"text": "Pin Board", "slot": initial_slots[0]},
    {"text": "Clothes Hamper", "slot": initial_slots[1]},
    {"text": "Phone", "slot": initial_slots[2]},
    {"text": "Cat", "slot": initial_slots[3]}
]

def scramble_items():
    new_slots = [0, 1, 2, 3]
    random.shuffle(new_slots)
    for i, item in enumerate(items):
        item["slot"] = new_slots[i]

dragging_index = None
offset_x = 0

game_state = "TITLE"
current_step = -1
step_duration = 1100
step_start_time = 0

paused_previous_state = "EDITING"
step_elapsed_before_pause = 0

winning_sequence = ["Pin Board", "Clothes Hamper", "Phone", "Cat"]
player_sequence = []
game_message = ""
last_played_step = -2

def play_step_music(step_idx):
    if 0 <= step_idx < len(player_sequence) and step_idx < len(winning_sequence):
        is_correct = (player_sequence[step_idx] == winning_sequence[step_idx])
        step_number = step_idx + 1
        track_name = f"wakeup_{step_number}_correct" if is_correct else f"wakeup_{step_number}_wrong"
        play_bgm(track_name, loop=False)

play_bgm("wakeup_title", loop=True)

confetti_particles = []
CONFETTI_COLORS = [
    (240, 90, 90),
    (60, 160, 240),
    (255, 210, 70),
    (90, 200, 140),
    (170, 120, 220)
]

def spawn_confetti(count=45):
    global confetti_particles
    confetti_particles = []
    for _ in range(count):
        confetti_particles.append({
            "x": random.uniform(80, SCREEN_WIDTH - 80),
            "y": random.uniform(-100, 30),
            "vx": random.uniform(-0.8, 0.8),
            "vy": random.uniform(1.8, 3.6),
            "w": random.randint(7, 11),
            "h": random.randint(4, 7),
            "color": random.choice(CONFETTI_COLORS),
            "sway_phase": random.uniform(0, math.pi * 2),
            "sway_speed": random.uniform(0.04, 0.08)
        })

start_button_rect = pygame.Rect(320, 310, 160, 48)
start_button_color = (60, 160, 240)
start_button_hover = (90, 180, 255)

tutorial_button_rect = pygame.Rect(320, 370, 160, 48)
tutorial_button_color = (130, 90, 210)
tutorial_button_hover = (155, 115, 235)

title_exit_rect = pygame.Rect(320, 430, 160, 48)
title_exit_color = (200, 60, 60)
title_exit_hover = (230, 80, 80)

pause_resume_rect = pygame.Rect(320, 210, 160, 48)
pause_resume_color = (60, 160, 240)
pause_resume_hover = (90, 180, 255)

pause_menu_rect = pygame.Rect(320, 270, 160, 48)
pause_menu_color = (80, 140, 180)
pause_menu_hover = (100, 165, 210)

pause_tut_rect = pygame.Rect(320, 330, 160, 48)
pause_tut_color = (130, 90, 210)
pause_tut_hover = (155, 115, 235)

pause_exit_rect = pygame.Rect(320, 390, 160, 48)
pause_exit_color = (200, 60, 60)
pause_exit_hover = (230, 80, 80)

tutorial_slides = [
    {
        "title": "MORNING DISASTER!",
        "body": "Your alarm clock triggered a wild chain reaction! Every object must bounce the ball in sequence to wake you up. Can you trigger the chain reaction and make it to class?"
    },
    {
        "title": "HOW TO PLAY",
        "body": "Drag and swap items along the bottom tray to rearrange the order of the ball's path. Once you are confident in your plan, hit GO to launch the ball."
    },
    {
        "title": "PAUSE & CONTROLS",
        "body": "Press SPACEBAR at any time during planning or playback to pause the game. You can resume, revisit this tutorial, jump to the title menu, or exit."
    },
    {
        "title": "HOW TO WIN",
        "body": "Every room item must pass the ball along without breaking the reaction. Experiment with different paths to guide the bounce and find the one combination that successfully wakes you up!"
    }
]
current_slide = 0

tut_prev_rect = pygame.Rect(180, 440, 110, 45)
tut_next_rect = pygame.Rect(510, 440, 110, 45)
tut_back_rect = pygame.Rect(30, 30, 90, 35)

go_button_rect = pygame.Rect(620, 270, 100, 50)
go_button_color = (50, 200, 50)
go_button_hover_color = (70, 230, 70)

reset_button_rect = pygame.Rect(350, 360, 100, 50)
reset_button_color = (200, 100, 50)
reset_button_hover_color = (230, 125, 75)

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    if dragging_index is not None:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEALL)
    elif game_state == "TITLE" and (start_button_rect.collidepoint(mouse_pos) or tutorial_button_rect.collidepoint(mouse_pos) or title_exit_rect.collidepoint(mouse_pos)):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    elif game_state == "PAUSED" and (pause_resume_rect.collidepoint(mouse_pos) or pause_menu_rect.collidepoint(mouse_pos) or pause_tut_rect.collidepoint(mouse_pos) or pause_exit_rect.collidepoint(mouse_pos)):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    elif game_state == "TUTORIAL" and (tut_prev_rect.collidepoint(mouse_pos) or tut_next_rect.collidepoint(mouse_pos) or tut_back_rect.collidepoint(mouse_pos)):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    elif game_state == "EDITING" and go_button_rect.collidepoint(mouse_pos):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    elif game_state == "RESULT" and reset_button_rect.collidepoint(mouse_pos):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    elif game_state == "EDITING" and any(pygame.Rect(slots[item["slot"]], 510, 100, 70).collidepoint(mouse_pos) for item in items):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    target_slot = None
    if game_state == "EDITING" and dragging_index is not None:
        dragged_x = mouse_pos[0] + offset_x
        dragged_center = dragged_x + 50
        target_slot = min(range(len(slots)), key=lambda i: abs(slots[i] - dragged_center))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if game_state in ["EDITING", "PLAYING", "RESULT"]:
                    if sfx_click:
                        sfx_click.play()
                    paused_previous_state = game_state
                    if game_state == "PLAYING":
                        step_elapsed_before_pause = pygame.time.get_ticks() - step_start_time
                    pygame.mixer.music.pause()
                    game_state = "PAUSED"
                elif game_state == "PAUSED":
                    if sfx_click:
                        sfx_click.play()
                    pygame.mixer.music.unpause()
                    if paused_previous_state == "PLAYING":
                        step_start_time = pygame.time.get_ticks() - step_elapsed_before_pause
                    game_state = paused_previous_state

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if game_state == "TITLE":
                    if start_button_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        play_bgm("wakeup_base", loop=True)
                        game_state = "EDITING"
                    elif tutorial_button_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        current_slide = 0
                        play_bgm("wakeup_tutorial", loop=True)
                        game_state = "TUTORIAL"
                    elif title_exit_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        running = False

                elif game_state == "PAUSED":
                    if pause_resume_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        pygame.mixer.music.unpause()
                        if paused_previous_state == "PLAYING":
                            step_start_time = pygame.time.get_ticks() - step_elapsed_before_pause
                        game_state = paused_previous_state

                    elif pause_menu_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        confetti_particles.clear()
                        scramble_items()
                        game_state = "TITLE"
                        current_step = -1
                        game_message = ""
                        last_played_step = -2
                        play_bgm("wakeup_title", loop=True)

                    elif pause_tut_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        current_slide = 0
                        play_bgm("wakeup_tutorial", loop=True)
                        game_state = "TUTORIAL"

                    elif pause_exit_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        running = False

                elif game_state == "TUTORIAL":
                    if tut_back_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        play_bgm("wakeup_title", loop=True)
                        game_state = "TITLE"
                    elif tut_prev_rect.collidepoint(event.pos):
                        if current_slide > 0:
                            if sfx_click:
                                sfx_click.play()
                            current_slide -= 1
                    elif tut_next_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        if current_slide < len(tutorial_slides) - 1:
                            current_slide += 1
                        else:
                            play_bgm("wakeup_base", loop=True)
                            game_state = "EDITING"

                elif game_state == "EDITING" and go_button_rect.collidepoint(event.pos):
                    if sfx_click:
                        sfx_click.play()
                    sorted_items = sorted(items, key=lambda x: x["slot"])
                    player_sequence = [item["text"] for item in sorted_items]

                    # launches from go button towards first item
                    game_state = "PLAYING"
                    current_step = -1
                    step_start_time = pygame.time.get_ticks()
                    game_message = ""
                    last_played_step = -2

                elif game_state == "RESULT" and reset_button_rect.collidepoint(event.pos):
                    if sfx_click:
                        sfx_click.play()
                    confetti_particles.clear()
                    scramble_items()
                    play_bgm("wakeup_base", loop=True)
                    game_state = "EDITING"
                    game_message = ""
                    current_step = -1
                    last_played_step = -2

                elif game_state == "EDITING":
                    for i, item in enumerate(items):
                        box_x = slots[item["slot"]]
                        box_rect = pygame.Rect(box_x, 510, 100, 70)
                        if box_rect.collidepoint(event.pos):
                            dragging_index = i
                            offset_x = box_x - event.pos[0]
                            if sfx_click:
                                sfx_click.play()
                            break

        elif event.type == pygame.MOUSEBUTTONUP:
            if game_state == "EDITING" and event.button == 1 and dragging_index is not None:
                dragged_x = mouse_pos[0] + offset_x
                dragged_center = dragged_x + 50

                closest_slot = min(range(len(slots)), key=lambda i: abs(slots[i] - dragged_center))

                for i, item in enumerate(items):
                    if i != dragging_index and item["slot"] == closest_slot:
                        item["slot"] = items[dragging_index]["slot"]
                        break

                items[dragging_index]["slot"] = closest_slot
                dragging_index = None

                if sfx_snap:
                    sfx_snap.play()

    step_progress = 0.0
    max_steps = len(slots)

    if game_state == "PLAYING":
        now = pygame.time.get_ticks()
        step_elapsed = now - step_start_time

        if step_elapsed >= step_duration:
            step_start_time = now
            current_step += 1
            step_elapsed = 0

            # trigger sfx and music right on impact
            if 0 <= current_step < len(player_sequence):
                play_item_sfx(player_sequence[current_step])
                play_step_music(current_step)

            if current_step >= max_steps:
                game_state = "RESULT"
                if player_sequence == winning_sequence:
                    game_message = "SUCCESS! The ball bounced right into your hands and woke you up on time!"
                    spawn_confetti(45)
                    play_bgm("wakeup_credits", loop=True)
                    if sfx_win:
                        sfx_win.play()
                else:
                    confetti_particles.clear()
                    game_message = get_failure_message(player_sequence)
                    play_bgm("wakeup_allwrong", loop=True)
                    if sfx_fail:
                        sfx_fail.play()

        step_progress = min(1.0, max(0.0, step_elapsed / step_duration))

    if game_state == "TITLE":
        screen.blit(bg_image, (0, 0))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        title_surf = title_font.render("WAKE UP!", True, white)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 170))
        screen.blit(title_surf, title_rect)

        sub_surf = font.render("A Morning Routine Simulator", True, (210, 210, 210))
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 225))
        screen.blit(sub_surf, sub_rect)

        active_start_color = start_button_hover if start_button_rect.collidepoint(mouse_pos) else start_button_color
        pygame.draw.rect(screen, active_start_color, start_button_rect, border_radius=10)
        start_text = font.render("START", True, white)
        screen.blit(start_text, start_text.get_rect(center=start_button_rect.center))

        active_tut_color = tutorial_button_hover if tutorial_button_rect.collidepoint(mouse_pos) else tutorial_button_color
        pygame.draw.rect(screen, active_tut_color, tutorial_button_rect, border_radius=10)
        tut_btn_text = font.render("TUTORIAL", True, white)
        screen.blit(tut_btn_text, tut_btn_text.get_rect(center=tutorial_button_rect.center))

        active_exit_col = title_exit_hover if title_exit_rect.collidepoint(mouse_pos) else title_exit_color
        pygame.draw.rect(screen, active_exit_col, title_exit_rect, border_radius=10)
        exit_btn_text = font.render("EXIT", True, white)
        screen.blit(exit_btn_text, exit_btn_text.get_rect(center=title_exit_rect.center))

    elif game_state == "TUTORIAL":
        screen.blit(bg_image, (0, 0))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        back_col = (110, 110, 110) if tut_back_rect.collidepoint(mouse_pos) else (80, 80, 80)
        pygame.draw.rect(screen, back_col, tut_back_rect, border_radius=6)
        back_text = font.render("< TITLE", True, white)
        screen.blit(back_text, back_text.get_rect(center=tut_back_rect.center))

        card_rect = pygame.Rect(120, 90, 560, 420)
        pygame.draw.rect(screen, (32, 34, 42), card_rect, border_radius=14)
        pygame.draw.rect(screen, (100, 120, 150), card_rect, 2, border_radius=14)

        page_str = f"Slide {current_slide + 1} of {len(tutorial_slides)}"
        page_surf = font.render(page_str, True, (150, 160, 175))
        screen.blit(page_surf, page_surf.get_rect(center=(SCREEN_WIDTH // 2, 120)))

        slide_data = tutorial_slides[current_slide]
        slide_title = big_font.render(slide_data["title"], True, (255, 230, 80))
        screen.blit(slide_title, slide_title.get_rect(center=(SCREEN_WIDTH // 2, 165)))

        draw_wrapped_text(screen, slide_data["body"], font, white, SCREEN_WIDTH // 2, 275, max_width=480, line_spacing=8)

        if current_slide > 0:
            p_col = (100, 100, 110) if tut_prev_rect.collidepoint(mouse_pos) else (70, 70, 80)
            pygame.draw.rect(screen, p_col, tut_prev_rect, border_radius=8)
            p_text = font.render("PREV", True, white)
            screen.blit(p_text, p_text.get_rect(center=tut_prev_rect.center))

        is_last_slide = (current_slide == len(tutorial_slides) - 1)
        next_label = "PLAY!" if is_last_slide else "NEXT"
        next_base_col = (50, 180, 80) if is_last_slide else (60, 140, 230)
        next_hov_col = (70, 210, 100) if is_last_slide else (85, 165, 255)
        n_col = next_hov_col if tut_next_rect.collidepoint(mouse_pos) else next_base_col
        pygame.draw.rect(screen, n_col, tut_next_rect, border_radius=8)
        n_text = font.render(next_label, True, white)
        screen.blit(n_text, n_text.get_rect(center=tut_next_rect.center))

    elif game_state == "PAUSED":
        screen.blit(bg_image, (0, 0))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pause_title = big_font.render("GAME PAUSED", True, white)
        screen.blit(pause_title, pause_title.get_rect(center=(SCREEN_WIDTH // 2, 130)))

        pause_hint = font.render("press SPACE to resume", True, (170, 170, 170))
        screen.blit(pause_hint, pause_hint.get_rect(center=(SCREEN_WIDTH // 2, 165)))

        r_col = pause_resume_hover if pause_resume_rect.collidepoint(mouse_pos) else pause_resume_color
        pygame.draw.rect(screen, r_col, pause_resume_rect, border_radius=8)
        r_text = font.render("RESUME", True, white)
        screen.blit(r_text, r_text.get_rect(center=pause_resume_rect.center))

        m_col = pause_menu_hover if pause_menu_rect.collidepoint(mouse_pos) else pause_menu_color
        pygame.draw.rect(screen, m_col, pause_menu_rect, border_radius=8)
        m_text = font.render("MENU", True, white)
        screen.blit(m_text, m_text.get_rect(center=pause_menu_rect.center))

        t_col = pause_tut_hover if pause_tut_rect.collidepoint(mouse_pos) else pause_tut_color
        pygame.draw.rect(screen, t_col, pause_tut_rect, border_radius=8)
        t_text = font.render("TUTORIAL", True, white)
        screen.blit(t_text, t_text.get_rect(center=pause_tut_rect.center))

        e_col = pause_exit_hover if pause_exit_rect.collidepoint(mouse_pos) else pause_exit_color
        pygame.draw.rect(screen, e_col, pause_exit_rect, border_radius=8)
        e_text = font.render("EXIT", True, white)
        screen.blit(e_text, e_text.get_rect(center=pause_exit_rect.center))

    elif game_state == "RESULT":
        screen.fill(white)

        if confetti_particles:
            for p in confetti_particles:
                p["sway_phase"] += p["sway_speed"]
                p["x"] += p["vx"] + math.sin(p["sway_phase"]) * 0.9
                p["y"] += p["vy"]

                if p["y"] > SCREEN_HEIGHT + 15:
                    p["y"] = random.uniform(-40, -10)
                    p["x"] = random.uniform(80, SCREEN_WIDTH - 80)

                flutter_w = max(2, int(p["w"] * abs(math.cos(p["sway_phase"]))))
                pygame.draw.rect(screen, p["color"], (int(p["x"]), int(p["y"]), flutter_w, p["h"]), border_radius=1)

        if game_message != "":
            if "SUCCESS" in game_message:
                draw_wrapped_text(screen, game_message, big_font, (30, 150, 30), SCREEN_WIDTH // 2, 220, max_width=660)
            else:
                draw_wrapped_text(screen, game_message, big_font, (200, 30, 30), SCREEN_WIDTH // 2, 220, max_width=660)

        active_reset_color = reset_button_hover_color if reset_button_rect.collidepoint(mouse_pos) else reset_button_color
        pygame.draw.rect(screen, active_reset_color, reset_button_rect, border_radius=8)
        reset_text = font.render("RESET", True, white)
        reset_text_rect = reset_text.get_rect(center=reset_button_rect.center)
        screen.blit(reset_text, reset_text_rect)

    else:
        screen.blit(bg_image, (0, 0))

        active_target = player_sequence[current_step] if (game_state == "PLAYING" and 0 <= current_step < len(player_sequence)) else None
        is_reacting = (game_state == "PLAYING" and current_step >= 0 and step_progress < 0.40)

        if room_pinboard_1:
            pinboard_x, pinboard_y = ROOM_PINBOARD_POS
            pinboard_draw_surf = room_pinboard_1

            if is_reacting and active_target == "Pin Board":
                pinboard_draw_surf = room_pinboard_2 if int(step_progress * 12) % 2 == 1 else room_pinboard_1
                pinboard_y -= int(math.sin((step_progress / 0.40) * math.pi) * 8)

            screen.blit(pinboard_draw_surf, (pinboard_x, pinboard_y))

        if room_cat_idle:
            cat_x, cat_y = ROOM_CAT_POS
            cat_draw_surf = room_cat_idle

            is_cat_hit = (is_reacting and active_target == "Cat")
            if is_cat_hit:
                cat_draw_surf = room_cat_angry
                cat_y -= int(math.sin((step_progress / 0.40) * math.pi) * 12)
                cat_x += random.randint(-3, 3)
                cat_y += random.randint(-2, 2)

            screen.blit(cat_draw_surf, (cat_x, cat_y))

        if room_hamper_1:
            hamper_x, hamper_y = ROOM_HAMPER_POS
            hamper_draw_surf = room_hamper_1

            if is_reacting and active_target == "Clothes Hamper":
                hamper_draw_surf = room_hamper_2 if int(step_progress * 10) % 2 == 1 else room_hamper_1
                hamper_y -= int(math.sin((step_progress / 0.40) * math.pi) * 10)

            screen.blit(hamper_draw_surf, (hamper_x, hamper_y))

        if room_phone_1:
            phone_x, phone_y = ROOM_PHONE_POS
            phone_draw_surf = room_phone_1

            if is_reacting and active_target == "Phone":
                phone_draw_surf = room_phone_2 if int(step_progress * 14) % 2 == 1 else room_phone_1
                phone_x += random.randint(-3, 3)
                phone_y += random.randint(-2, 2)

            screen.blit(phone_draw_surf, (phone_x, phone_y))

        room_positions = {
            "Pin Board": (ROOM_PINBOARD_POS[0] + 110, ROOM_PINBOARD_POS[1] + 110),
            "Clothes Hamper": (ROOM_HAMPER_POS[0] + 48, ROOM_HAMPER_POS[1] + 48),
            "Phone": (ROOM_PHONE_POS[0] + 36, ROOM_PHONE_POS[1] + 36),
            "Cat": (ROOM_CAT_POS[0] + 48, ROOM_CAT_POS[1] + 48),
            "Player": PLAYER_WAKE_POS
        }

        # ball flight animation
        if game_state == "PLAYING":
            if current_step == -1 and len(player_sequence) > 0:
                start_pos = go_button_rect.center
                end_pos = room_positions.get(player_sequence[0], (400, 300))
                ball_x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * step_progress)
                base_y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * step_progress)
                gravity_arc = int(4 * step_progress * (1 - step_progress) * 85)
                ball_y = base_y - gravity_arc

                if ball_image:
                    screen.blit(ball_image, (ball_x - ball_image.get_width() // 2, ball_y - ball_image.get_height() // 2))
                else:
                    pygame.draw.circle(screen, (255, 255, 255), (ball_x, ball_y), 16)

            elif 0 <= current_step < len(player_sequence):
                start_pos = room_positions.get(player_sequence[current_step], (400, 300))

                if current_step < len(player_sequence) - 1:
                    next_item_name = player_sequence[current_step + 1]
                    end_pos = room_positions.get(next_item_name, (400, 300))
                else:
                    # at the last item (cat)
                    if player_sequence == winning_sequence:
                        end_pos = room_positions["Player"]
                    else:
                        end_pos = (start_pos[0] + 60, 520)

                ball_x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * step_progress)
                base_y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * step_progress)
                gravity_arc = int(4 * step_progress * (1 - step_progress) * 95)
                ball_y = base_y - gravity_arc

                if ball_image:
                    screen.blit(ball_image, (ball_x - ball_image.get_width() // 2, ball_y - ball_image.get_height() // 2))
                else:
                    pygame.draw.circle(screen, (255, 255, 255), (ball_x, ball_y), 16)

        if game_state == "EDITING":
            active_go_color = go_button_hover_color if go_button_rect.collidepoint(mouse_pos) else go_button_color
            pygame.draw.rect(screen, active_go_color, go_button_rect, border_radius=8)
            go_text = font.render("GO!", True, white)
            go_text_rect = go_text.get_rect(center=go_button_rect.center)
            screen.blit(go_text, go_text_rect)

        # connecting beam between tray slots
        if game_state == "PLAYING" and 0 <= current_step < len(slots) - 1:
            start_pt = (slots[current_step] + 100, 545)
            end_pt = (slots[current_step + 1], 545)
            pygame.draw.line(screen, (80, 80, 80), start_pt, end_pt, 3)

            beam_dist = end_pt[0] - start_pt[0]
            pulse_x = start_pt[0] + (beam_dist * step_progress)
            pygame.draw.circle(screen, (255, 235, 90), (int(pulse_x), 545), 6)
            pygame.draw.circle(screen, (255, 255, 255), (int(pulse_x), 545), 3)

        for i, slot_x in enumerate(slots):
            slot_rect = pygame.Rect(slot_x, 510, 100, 70)

            if game_state == "PLAYING" and i == current_step:
                pygame.draw.rect(screen, (255, 230, 80), slot_rect, border_radius=10)
                pygame.draw.rect(screen, (220, 190, 50), slot_rect, 2, border_radius=10)
            else:
                pygame.draw.rect(screen, box_color, slot_rect, 1, 10)

        for i, item in enumerate(items):
            if i == dragging_index:
                continue

            draw_x = slots[item["slot"]]
            draw_y = 510

            if is_reacting and active_target == item["text"]:
                bounce_offset = math.sin((step_progress / 0.40) * math.pi) * 8
                draw_y -= int(bounce_offset)

            rect = pygame.Rect(draw_x, draw_y, 100, 70)

            pygame.draw.rect(screen, box_color, rect, 0, 10)
            pygame.draw.rect(screen, (100, 100, 100), rect, 1, 10)

            if game_state == "EDITING" and dragging_index is None and rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (255, 230, 80), rect.inflate(6, 6), 3, 12)

            item_name = item["text"]
            if item_name in item_sprites:
                sprite_surf = item_sprites[item_name]
                sprite_rect = sprite_surf.get_rect(center=(rect.centerx, rect.centery - 8))
                screen.blit(sprite_surf, sprite_rect)

                label_surf = font.render(item_name, True, dark_gray)
                label_rect = label_surf.get_rect(center=(rect.centerx, rect.bottom - 13))
                screen.blit(label_surf, label_rect)
            else:
                text_surf = font.render(item_name, True, dark_gray)
                text_rect = text_surf.get_rect(center=rect.center)
                screen.blit(text_surf, text_rect)

        if dragging_index is not None and target_slot is not None:
            slot_x = slots[target_slot]
            slot_rect = pygame.Rect(slot_x, 510, 100, 70)
            pygame.draw.rect(screen, (0, 0, 0), slot_rect, 1, 10)

        if dragging_index is not None:
            item = items[dragging_index]
            draw_x = mouse_pos[0] + offset_x
            rect = pygame.Rect(draw_x, 510, 100, 70)

            pygame.draw.rect(screen, box_color, rect, 0, 10)
            pygame.draw.rect(screen, (100, 100, 100), rect, 1, 10)
            pygame.draw.rect(screen, (255, 230, 80), rect.inflate(6, 6), 3, 12)

            item_name = item["text"]
            if item_name in item_sprites:
                sprite_surf = item_sprites[item_name]
                sprite_rect = sprite_surf.get_rect(center=(rect.centerx, rect.centery - 8))
                screen.blit(sprite_surf, sprite_rect)

                label_surf = font.render(item_name, True, dark_gray)
                label_rect = label_surf.get_rect(center=(rect.centerx, rect.bottom - 13))
                screen.blit(label_surf, label_rect)
            else:
                text_surf = font.render(item_name, True, dark_gray)
                text_rect = text_surf.get_rect(center=rect.center)
                screen.blit(text_surf, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
exit()