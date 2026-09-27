import os
import sys
import math
import pygame
from sys import exit

pygame.mixer.pre_init(44100, -16, 2, 512)         # fixes latency[cite: 2]
pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("TXGJ 2026")
clock = pygame.time.Clock()

# handles paths for both development and pyinstaller builds[cite: 2]
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

bg_path = os.path.join(script_dir, "test bg.jpg")
bg_image = pygame.image.load(bg_path).convert()
bg_image = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# background music manager with fallbacks[cite: 2]
current_track = None
def play_bgm(filename):
    global current_track
    if filename == current_track:
        return
    path = os.path.join(script_dir, filename)
    if os.path.exists(path):
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        current_track = filename

# start title bgm[cite: 2]
if os.path.exists(os.path.join(script_dir, "title_theme.mp3")):
    play_bgm("title_theme.mp3")
else:
    play_bgm("wake_up.mp3")

# sound effects placeholders[cite: 2]
def load_sound(filename):
    path = os.path.join(script_dir, filename)
    if os.path.exists(path):
        sound = pygame.mixer.Sound(path)
        sound.set_volume(0.5)
        return sound
    return None

sfx_snap = load_sound("snap.wav")
sfx_win = load_sound("win.wav")
sfx_fail = load_sound("fail.wav")
sfx_click = load_sound("click.wav")

# step sounds[cite: 2]
sfx_steps = [
    load_sound("step_0.wav") or load_sound("step.wav"),
    load_sound("step_1.wav") or load_sound("step.wav"),
    load_sound("step_2.wav") or load_sound("step.wav"),
    load_sound("step_3.wav") or load_sound("step.wav")
]

# failure message generator[cite: 2]
def get_failure_message(seq):
    if seq[0] == "Lamp":
        return "DISASTER! You turned off the lamp first, stumbled in the pitch dark, and smashed the toaster!"
    elif seq.index("Shoes") < seq.index("Toothbrush"):
        return "DISASTER! You put muddy boots on first and slipped on toothpaste across the bathroom floor!"
    elif seq[-1] == "Toaster":
        return "DISASTER! You walked out the front door and left the toaster running—the kitchen is on fire!"
    elif seq.index("Toothbrush") > seq.index("Toaster"):
        return "DISASTER! You brushed your teeth immediately after eating scalding toast; total sensory overload!"
    else:
        return "DISASTER! The routine fell completely out of order and morning chaos took over!"

# text wrapping helper for multi-line messages[cite: 2]
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


# drag and drop mechanic[cite: 2]
slots = [50, 250, 450, 650]
items = [
    {"text": "Toaster", "slot": 0},
    {"text": "Toothbrush", "slot": 1},
    {"text": "Shoes", "slot": 2},
    {"text": "Lamp", "slot": 3}
]
dragging_index = None
offset_x = 0

# game state machine[cite: 2]
game_state = "TITLE"
current_step = 0
step_duration = 1200
step_start_time = 0

# stores previous state and elapsed time so pausing during playback stays accurate
paused_previous_state = "EDITING"
step_elapsed_before_pause = 0

# game logic[cite: 2]
winning_sequence = ["Toothbrush", "Toaster", "Shoes", "Lamp"]
game_message = ""

# title screen buttons
start_button_rect = pygame.Rect(320, 310, 160, 48)
start_button_color = (60, 160, 240)
start_button_hover = (90, 180, 255)

tutorial_button_rect = pygame.Rect(320, 370, 160, 48)
tutorial_button_color = (130, 90, 210)
tutorial_button_hover = (155, 115, 235)

title_exit_rect = pygame.Rect(320, 430, 160, 48)
title_exit_color = (200, 60, 60)
title_exit_hover = (230, 80, 80)

# pause menu buttons
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

# tutorial slides and controls
tutorial_slides = [
    {
        "title": "MORNING DISASTER!",
        "body": "Your alarm clock triggered a wild chain reaction! Every appliance in the apartment is set to trigger in sequence. Can you leave for class in one piece?"
    },
    {
        "title": "HOW TO PLAY",
        "body": "Drag and swap items along the bottom tray to rearrange the order of tasks. Once you are confident in your plan, hit GO to trigger the sequence."
    },
    {
        "title": "PAUSE & CONTROLS",
        "body": "Press SPACEBAR at any time during planning or playback to pause the game. You can resume, revisit this tutorial, jump to the title menu, or exit."
    },
    {
        "title": "HOW TO WIN",
        "body": "Order conflicts cause hilarious failures! Brush your teeth, toast your breakfast, put shoes on, and switch off the lamp on your way out."
    }
]
current_slide = 0

tut_prev_rect = pygame.Rect(180, 440, 110, 45)
tut_next_rect = pygame.Rect(510, 440, 110, 45)
tut_back_rect = pygame.Rect(30, 30, 90, 35)

# go button initialization[cite: 2]
go_button_rect = pygame.Rect(450, 45, 100, 50)
go_button_color = (50, 200, 50)
go_button_hover_color = (70, 230, 70)

# reset button initialization[cite: 2]
reset_button_rect = pygame.Rect(350, 360, 100, 50)
reset_button_color = (200, 100, 50)
reset_button_hover_color = (230, 125, 75)


running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    # cursor state updating[cite: 2]
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

    # target slot analyzing[cite: 2]
    target_slot = None
    if game_state == "EDITING" and dragging_index is not None:
        dragged_x = mouse_pos[0] + offset_x
        dragged_center = dragged_x + 50
        target_slot = min(range(len(slots)), key = lambda i: abs(slots[i] - dragged_center))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # toggle pause menu with spacebar from gameplay states
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
                    # unpauses back to where you were
                    if sfx_click:
                        sfx_click.play()
                    pygame.mixer.music.unpause()
                    if paused_previous_state == "PLAYING":
                        step_start_time = pygame.time.get_ticks() - step_elapsed_before_pause
                    game_state = paused_previous_state

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # title screen clicks
                if game_state == "TITLE":
                    if start_button_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        play_bgm("wake_up.mp3")
                        game_state = "EDITING"
                    elif tutorial_button_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        current_slide = 0
                        game_state = "TUTORIAL"
                    elif title_exit_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        running = False

                # pause menu clicks
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
                        # reset gameplay variables when returning to title
                        game_state = "TITLE"
                        current_step = 0
                        game_message = ""
                        if os.path.exists(os.path.join(script_dir, "title_theme.mp3")):
                            play_bgm("title_theme.mp3")
                        else:
                            play_bgm("wake_up.mp3")

                    elif pause_tut_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        current_slide = 0
                        game_state = "TUTORIAL"

                    elif pause_exit_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
                        running = False

                # tutorial navigation clicks
                elif game_state == "TUTORIAL":
                    if tut_back_rect.collidepoint(event.pos):
                        if sfx_click:
                            sfx_click.play()
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
                            play_bgm("wake_up.mp3")
                            game_state = "EDITING"

                # go button check[cite: 2]
                elif game_state == "EDITING" and go_button_rect.collidepoint(event.pos):
                    if sfx_click:
                        sfx_click.play()
                    sorted_items = sorted(items, key = lambda x: x["slot"])
                    player_sequence = [item["text"] for item in sorted_items]
                    print("Player's sequence: ", player_sequence)

                    game_state = "PLAYING"
                    current_step = 0
                    step_start_time = pygame.time.get_ticks()
                    game_message = ""

                    if sfx_steps[0]:
                        sfx_steps[0].play()

                # reset button check[cite: 2]
                elif game_state == "RESULT" and reset_button_rect.collidepoint(event.pos):
                    if sfx_click:
                        sfx_click.play()
                    game_state = "EDITING"
                    game_message = ""
                    current_step = 0

                # drag box check[cite: 2]
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

                closest_slot = min(range(len(slots)), key = lambda i: abs(slots[i] - dragged_center))

                for i, item in enumerate(items):
                    if i != dragging_index and item["slot"] == closest_slot:
                        item["slot"] = items[dragging_index]["slot"]
                        break

                items[dragging_index]["slot"] = closest_slot
                dragging_index = None

                if sfx_snap:
                    sfx_snap.play()

    # timing calculation for step transitions and animation progress
    step_progress = 0.0
    if game_state == "PLAYING":
        now = pygame.time.get_ticks()
        step_elapsed = now - step_start_time
        step_progress = min(1.0, max(0.0, step_elapsed / step_duration))

        if step_elapsed >= step_duration:
            step_start_time = now
            current_step += 1

            if current_step < len(slots):
                if sfx_steps[current_step]:
                    sfx_steps[current_step].play()

            if current_step >= len(slots):
                game_state = "RESULT"
                if player_sequence == winning_sequence:
                    game_message = "SUCCESS! You're ready for the day!"
                    if sfx_win:
                        sfx_win.play()
                else:
                    game_message = get_failure_message(player_sequence)
                    if sfx_fail:
                        sfx_fail.play()

    # --- rendering section ---
    if game_state == "TITLE":
        screen.blit(bg_image, (0, 0))

        # dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        title_surf = title_font.render("CHAIN REACTION", True, white)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 170))
        screen.blit(title_surf, title_rect)

        sub_surf = font.render("A Morning Routine Simulator", True, (210, 210, 210))
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 225))
        screen.blit(sub_surf, sub_rect)

        # start button
        active_start_color = start_button_hover if start_button_rect.collidepoint(mouse_pos) else start_button_color
        pygame.draw.rect(screen, active_start_color, start_button_rect, border_radius=10)
        start_text = font.render("START", True, white)
        screen.blit(start_text, start_text.get_rect(center=start_button_rect.center))

        # tutorial button
        active_tut_color = tutorial_button_hover if tutorial_button_rect.collidepoint(mouse_pos) else tutorial_button_color
        pygame.draw.rect(screen, active_tut_color, tutorial_button_rect, border_radius=10)
        tut_btn_text = font.render("TUTORIAL", True, white)
        screen.blit(tut_btn_text, tut_btn_text.get_rect(center=tutorial_button_rect.center))

        # exit button
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

        # dim overlay behind pause menu
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pause_title = big_font.render("GAME PAUSED", True, white)
        screen.blit(pause_title, pause_title.get_rect(center=(SCREEN_WIDTH // 2, 130)))

        pause_hint = font.render("press SPACE to resume", True, (170, 170, 170))
        screen.blit(pause_hint, pause_hint.get_rect(center=(SCREEN_WIDTH // 2, 165)))

        # resume button
        r_col = pause_resume_hover if pause_resume_rect.collidepoint(mouse_pos) else pause_resume_color
        pygame.draw.rect(screen, r_col, pause_resume_rect, border_radius=8)
        r_text = font.render("RESUME", True, white)
        screen.blit(r_text, r_text.get_rect(center=pause_resume_rect.center))

        # menu button
        m_col = pause_menu_hover if pause_menu_rect.collidepoint(mouse_pos) else pause_menu_color
        pygame.draw.rect(screen, m_col, pause_menu_rect, border_radius=8)
        m_text = font.render("MENU", True, white)
        screen.blit(m_text, m_text.get_rect(center=pause_menu_rect.center))

        # tutorial button
        t_col = pause_tut_hover if pause_tut_rect.collidepoint(mouse_pos) else pause_tut_color
        pygame.draw.rect(screen, t_col, pause_tut_rect, border_radius=8)
        t_text = font.render("TUTORIAL", True, white)
        screen.blit(t_text, t_text.get_rect(center=pause_tut_rect.center))

        # exit button
        e_col = pause_exit_hover if pause_exit_rect.collidepoint(mouse_pos) else pause_exit_color
        pygame.draw.rect(screen, e_col, pause_exit_rect, border_radius=8)
        e_text = font.render("EXIT", True, white)
        screen.blit(e_text, e_text.get_rect(center=pause_exit_rect.center))

    elif game_state == "RESULT":
        screen.fill(white)

        if game_message != "":
            if "SUCCESS" in game_message:
                msg_surf = big_font.render(game_message, True, (30, 150, 30))
                msg_rect = msg_surf.get_rect(center = (SCREEN_WIDTH // 2, 220))
                screen.blit(msg_surf, msg_rect)
            else:
                draw_wrapped_text(screen, game_message, big_font, (200, 30, 30), SCREEN_WIDTH // 2, 220, max_width=660)

        active_reset_color = reset_button_hover_color if reset_button_rect.collidepoint(mouse_pos) else reset_button_color
        pygame.draw.rect(screen, active_reset_color, reset_button_rect, border_radius = 8)
        reset_text = font.render("RESET", True, white)
        reset_text_rect = reset_text.get_rect(center = reset_button_rect.center)
        screen.blit(reset_text, reset_text_rect)

    else:
        screen.blit(bg_image, (0, 0))

        if game_state == "EDITING":
            active_go_color = go_button_hover_color if go_button_rect.collidepoint(mouse_pos) else go_button_color
            pygame.draw.rect(screen, active_go_color, go_button_rect, border_radius = 8)
            go_text = font.render("GO!", True, white)
            go_text_rect = go_text.get_rect(center = go_button_rect.center)
            screen.blit(go_text, go_text_rect)

        # animated energy beam connecting the active step to the next step
        if game_state == "PLAYING" and current_step < len(slots) - 1:
            start_pt = (slots[current_step] + 100, 545)
            end_pt = (slots[current_step + 1], 545)

            # base connection line
            pygame.draw.line(screen, (80, 80, 80), start_pt, end_pt, 3)

            # traveling energy pulse
            beam_dist = end_pt[0] - start_pt[0]
            pulse_x = start_pt[0] + (beam_dist * step_progress)
            pygame.draw.circle(screen, (255, 235, 90), (int(pulse_x), 545), 6)
            pygame.draw.circle(screen, (255, 255, 255), (int(pulse_x), 545), 3)

        for i, slot_x in enumerate(slots):
            slot_rect = pygame.Rect(slot_x, 510, 100, 70)

            # fills slot solid yellow when active so jumping box looks grounded
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

            # adds vertical pop when item is triggered
            if game_state == "PLAYING" and item["slot"] == current_step:
                bounce_offset = math.sin(step_progress * math.pi) * 14
                draw_y -= int(bounce_offset)

            rect = pygame.Rect(draw_x, draw_y, 100, 70)

            pygame.draw.rect(screen, box_color, rect, 1, 10)
            pygame.draw.rect(screen, (100, 100, 100), rect, 1, 10)

            if game_state == "EDITING" and dragging_index is None and rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (255, 230, 80), rect.inflate(6, 6), 3, 12)

            text_surf = font.render(item["text"], True, dark_gray)
            text_rect = text_surf.get_rect(center = rect.center)
            screen.blit(text_surf, text_rect)

        if dragging_index is not None and target_slot is not None:
            slot_x = slots[target_slot]
            slot_rect = pygame.Rect(slot_x, 510, 100, 70)
            pygame.draw.rect(screen, (0, 0, 0), slot_rect, 3, 10)

        if dragging_index is not None:
            item = items[dragging_index]
            draw_x = mouse_pos[0] + offset_x
            rect = pygame.Rect(draw_x, 510, 100, 70)

            pygame.draw.rect(screen, box_color, rect, 0, 10)
            pygame.draw.rect(screen, (100, 100, 100), rect, 1, 10)
            pygame.draw.rect(screen, (255, 230, 80), rect.inflate(6, 6), 3, 12)

            text_surf = font.render(item["text"], True, dark_gray)
            text_rect = text_surf.get_rect(center = rect.center)
            screen.blit(text_surf, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
exit()