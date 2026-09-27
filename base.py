import os
import sys
import pygame
from sys import exit

pygame.mixer.pre_init(44100, -16, 2, 512)         #fixes latency
pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("TXGJ 2026")
clock = pygame.time.Clock()

#paths
if getattr(sys, 'frozen', False):
    script_dir = sys._MEIPASS
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))

font_path = os.path.join(script_dir, "Pixel.otf")
font = pygame.font.Font(font_path, 20)
big_font = pygame.font.Font(font_path, 36)
white = (255, 255, 255)
dark_gray = (40, 40, 40)
box_color = (235, 234, 222)

bg_path = os.path.join(script_dir, "test bg.jpg")
bg_image = pygame.image.load(bg_path).convert()
bg_image = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

#background music
bgm_path = os.path.join(script_dir, "wake_up.mp3")  # Change filename to match your audio file
if os.path.exists(bgm_path):
    pygame.mixer.music.load(bgm_path)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

#sound effects placeholders
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

sfx_steps = [
    load_sound("step_0.wav") or load_sound("step.wav"),
    load_sound("step_1.wav") or load_sound("step.wav"),
    load_sound("step_2.wav") or load_sound("step.wav"),
    load_sound("step_3.wav") or load_sound("step.wav")
]

#failure message generator (placeholders until finalized)
def get_failure_message(seq):
    if seq[0] == "Lamp":
        return "DISASTER! You turned off the lamp first, stumbled in the pitch dark, and smashed the toaster!"
    elif seq.index("Shoes") < seq.index("Toothbrush"):
        return "DISASTER! You put muddy boots on first and slipped on toothpaste across the bathroom floor!"
    elif seq[-1] == "Toaster":
        return "DISASTER! You walked out the front door and left the toaster running—the kitchen is on fire!"
    elif seq.index("Toothbrush") > seq.index("Toaster"):
        return "DISASTER! You brushed your teeth immediately after eating scalding toast—total sensory overload!"
    else:
        return "DISASTER! The routine fell completely out of order and morning chaos took over!"

#text wrapping for multi-line messages
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

    #calculate total height to center all lines vertically
    line_surfs = [font_obj.render(line, True, color) for line in lines]
    line_height = font_obj.get_linesize() + line_spacing
    total_height = len(line_surfs) * line_height - line_spacing
    start_y = center_y - (total_height // 2)

    for i, surf in enumerate(line_surfs):
        rect = surf.get_rect(center=(center_x, start_y + (i * line_height) + (surf.get_height() // 2)))
        surface.blit(surf, rect)


#drag and drop mechanic
slots = [50, 250, 450, 650]
items = [
    {"text": "Toaster", "slot": 0},
    {"text": "Toothbrush", "slot": 1},
    {"text": "Shoes", "slot": 2},
    {"text": "Lamp", "slot": 3}
]
dragging_index = None
offset_x = 0

#game state
game_state = "EDITING"
current_step = 0
step_duration = 1600
step_start_time = 0

#game logic
winning_sequence = ["Toothbrush", "Toaster", "Shoes", "Lamp"]
game_message = ""

#go button initialization
go_button_rect = pygame.Rect(450, 45, 100, 50)
go_button_color = (50, 200, 50)
go_button_hover_color = (70, 230, 70)

#reset button initialization
reset_button_rect = pygame.Rect(350, 360, 100, 50)
reset_button_color = (200, 100, 50)
reset_button_hover_color = (230, 125, 75)


running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    #cursor state updating
    if dragging_index is not None:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEALL)
    elif game_state == "EDITING" and go_button_rect.collidepoint(mouse_pos):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    elif game_state == "RESULT" and reset_button_rect.collidepoint(mouse_pos):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    elif game_state == "EDITING" and any(pygame.Rect(slots[item["slot"]], 510, 100, 70).collidepoint(mouse_pos) for item in items):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    #target slot analyzing
    target_slot = None
    if game_state == "EDITING" and dragging_index is not None:
        dragged_x = mouse_pos[0] + offset_x
        dragged_center = dragged_x + 50
        target_slot = min(range(len(slots)), key = lambda i: abs(slots[i] - dragged_center))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                #go button check
                if game_state == "EDITING" and go_button_rect.collidepoint(event.pos):
                    if sfx_click:
                        sfx_click.play()
                    sorted_items = sorted(items, key = lambda x: x["slot"])
                    player_sequence = [item["text"] for item in sorted_items]
                    print("Player's sequence: ", player_sequence)

                    #start playback
                    game_state = "PLAYING"
                    current_step = 0
                    step_start_time = pygame.time.get_ticks()
                    game_message = ""

                    #play first step sound immediately on start
                    if sfx_steps[0]:
                        sfx_steps[0].play()

                #reset button check
                elif game_state == "RESULT" and reset_button_rect.collidepoint(event.pos):
                    if sfx_click:
                        sfx_click.play()
                    game_state = "EDITING"
                    game_message = ""
                    current_step = 0

                #drag box check
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

                #finding closest slot
                closest_slot = min(range(len(slots)), key = lambda i: abs(slots[i] - dragged_center))

                #box swap
                for i, item in enumerate(items):
                    if i != dragging_index and item["slot"] == closest_slot:
                        item["slot"] = items[dragging_index]["slot"]
                        break

                items[dragging_index]["slot"] = closest_slot
                dragging_index = None

                #play snap sound on drop
                if sfx_snap:
                    sfx_snap.play()

    if game_state == "PLAYING":
        now = pygame.time.get_ticks()

        #check time elapsed
        if now - step_start_time >= step_duration:
            step_start_time = now
            current_step += 1

            #play sound for the new step if we haven't reached the end
            if current_step < len(slots):
                if sfx_steps[current_step]:
                    sfx_steps[current_step].play()

            #after 4 steps
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

    #drawing end screen or gameplay
    if game_state == "RESULT":
        screen.fill(white)

        #win/lose message rendering
        if game_message != "":
            if "SUCCESS" in game_message:
                msg_surf = big_font.render(game_message, True, (30, 150, 30))
                msg_rect = msg_surf.get_rect(center = (SCREEN_WIDTH // 2, 220))
                screen.blit(msg_surf, msg_rect)
            else:
                # Wrapped failure message
                draw_wrapped_text(screen, game_message, big_font, (200, 30, 30), SCREEN_WIDTH // 2, 220, max_width=660)

        #drawing reset button
        active_reset_color = reset_button_hover_color if reset_button_rect.collidepoint(mouse_pos) else reset_button_color
        pygame.draw.rect(screen, active_reset_color, reset_button_rect, border_radius = 8)
        reset_text = font.render("RESET", True, white)
        reset_text_rect = reset_text.get_rect(center = reset_button_rect.center)
        screen.blit(reset_text, reset_text_rect)

    else:
        screen.blit(bg_image, (0, 0))

        #drawing go button
        if game_state == "EDITING":
            active_go_color = go_button_hover_color if go_button_rect.collidepoint(mouse_pos) else go_button_color
            pygame.draw.rect(screen, active_go_color, go_button_rect, border_radius = 8)
            go_text = font.render("GO!", True, white)
            go_text_rect = go_text.get_rect(center = go_button_rect.center)
            screen.blit(go_text, go_text_rect)

        #highlighting slots while playing
        for i, slot_x in enumerate(slots):
            slot_rect = pygame.Rect(slot_x, 510, 100, 70)
            pygame.draw.rect(screen, box_color, slot_rect, 1, 10)

            #highlight current step
            if game_state == "PLAYING" and i == current_step:
                highlight_rect = slot_rect.inflate(8, 8)
                pygame.draw.rect(screen, (255, 230, 80), highlight_rect, 4, 12)

        #drawing boxes
        for i, item in enumerate(items):
            if i == dragging_index:
                continue

            draw_x = slots[item["slot"]]
            rect = pygame.Rect(draw_x, 510, 100, 70)

            pygame.draw.rect(screen, box_color, rect, 1, 10)
            pygame.draw.rect(screen, (100, 100, 100), rect, 1, 10)

            #hover highlight for boxes
            if game_state == "EDITING" and dragging_index is None and rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (255, 230, 80), rect.inflate(6, 6), 3, 12)

            text_surf = font.render(item["text"], True, dark_gray)
            text_rect = text_surf.get_rect(center = rect.center)
            screen.blit(text_surf, text_rect)

        #drawing box highlight
        if dragging_index is not None and target_slot is not None:
            slot_x = slots[target_slot]
            slot_rect = pygame.Rect(slot_x, 510, 100, 70)
            pygame.draw.rect(screen, (0, 0, 0), slot_rect, 3, 10)

        #dragged box
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