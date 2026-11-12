import errno
import os
import sys
import pygame
from pygame._sdl2 import controller
import serial

os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
os.environ["SDL_JOYSTICK_RAWINPUT"] = "0"

pygame.init()
controller.init()

class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 25)

    def tprint(self, screen, text):
        text_bitmap = self.font.render(text, True, (0, 0, 0))
        screen.blit(text_bitmap, (self.x, self.y))
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10


def main():
    screen = pygame.display.set_mode((500, 400))
    pygame.display.set_caption("DSpico InputOverride")

    # Used to manage how fast the screen updates.
    clock = pygame.time.Clock()
    text_print = TextPrint()
    controllers = {}

    # Instance id of the controller currently being read.
    selected_id = None

    # "next controller" button
    cycle_button_rect = pygame.Rect(10, 350, 200, 35)
    button_font = pygame.font.Font(None, 25)

    # Serial port that connects to the DSpico
    ser = serial.Serial()
    last_connect_attempt = -1000
    # Set on Linux when the port exists but the user isn't allowed to open it
    permission_denied = False

    def send(value):
        nonlocal ser
        if not ser.is_open:
            return
        try:
            ser.write(value.to_bytes(2, byteorder="little"))
        except (serial.SerialException, OSError) as e:
            print(f"DSpico disconnected: {e}")
            try:
                ser.close()
            except (serial.SerialException, OSError):
                pass
            ser = serial.Serial()

    def cycle_controller():
        nonlocal selected_id
        ids = sorted(controllers.keys())
        if len(ids) < 2:
            return
        if selected_id in ids:
            selected_id = ids[(ids.index(selected_id) + 1) % len(ids)]
        else:
            selected_id = ids[0]
        print(f"Switched to controller {selected_id}")

    button_names = {
        0 : "A",
        1 : "B",
        2 : "Select",
        3 : "Start",
        4 : "Dpad right",
        5 : "Dpad left",
        6 : "Dpad up",
        7 : "Dpad down",
        8 : "R",
        9 : "L",
        10: "X",
        11: "Y"
    }

    # pygame controller -> PAD_ALL_MASK https://twlsdk.randommeaninglesscharacters.com/docs/nitro/NitroSDK/pad/PAD_Read.html
    button_mapping = {
        pygame.CONTROLLER_BUTTON_A            : 1,
        pygame.CONTROLLER_BUTTON_B            : 0,
        pygame.CONTROLLER_BUTTON_X            : 11,
        pygame.CONTROLLER_BUTTON_Y            : 10,
        pygame.CONTROLLER_BUTTON_LEFTSHOULDER : 9,
        pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: 8,
        pygame.CONTROLLER_BUTTON_BACK         : 2,
        pygame.CONTROLLER_BUTTON_START        : 3,
        pygame.CONTROLLER_BUTTON_DPAD_RIGHT   : 4,
        pygame.CONTROLLER_BUTTON_DPAD_LEFT    : 5,
        pygame.CONTROLLER_BUTTON_DPAD_UP      : 6,
        pygame.CONTROLLER_BUTTON_DPAD_DOWN    : 7,
    }

    done = False
    while not done:
        # Searching for the port enumerates every COM port, so only try once a second
        if not ser.is_open and pygame.time.get_ticks() - last_connect_attempt >= 1000:
            last_connect_attempt = pygame.time.get_ticks()
            try:
                ser = serial.serial_for_url("hwgrep://CAFE:6000", timeout=1, write_timeout=0.25)
                permission_denied = False
            except (serial.SerialException, OSError) as e:
                permission_denied = sys.platform.startswith("linux") and e.errno == errno.EACCES
                ser = serial.Serial()

        # Event processing step.
        # Possible controller events: CONTROLLERAXISMOTION, CONTROLLERBUTTONDOWN,
        # CONTROLLERBUTTONUP, CONTROLLERDEVICEADDED, CONTROLLERDEVICEREMOVED
        try:
            events = pygame.event.get()
        except (SystemError, KeyError):
            events = []  # pygame's joystick map got out of sync, skip this frame

        for event in events:
            if event.type == pygame.QUIT:
                done = True

            # Handle hotplugging
            if event.type == pygame.CONTROLLERDEVICEADDED:
                ctrl = controller.Controller(event.device_index)
                instance_id = ctrl.as_joystick().get_instance_id()
                if instance_id not in controllers:
                    controllers[instance_id] = ctrl
                    print(f"Controller {instance_id} connected")

            if event.type == pygame.CONTROLLERDEVICEREMOVED:
                controllers.pop(event.instance_id, None)
                print(f"Controller {event.instance_id} disconnected")
                send(4095)

            # Cycle controllers
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cycle_button_rect.collidepoint(event.pos):
                    cycle_controller()

        screen.fill((255, 255, 255))
        text_print.reset()

        # Make sure the selection is valid
        if controllers and selected_id not in controllers:
            selected_id = sorted(controllers.keys())[0]
        elif not controllers:
            selected_id = None

        # Draw the cycle button (greyed out unless 2+ controllers are connected)
        enabled = len(controllers) > 1
        mouse_over = cycle_button_rect.collidepoint(pygame.mouse.get_pos())
        if not enabled:
            fill = (220, 220, 220)
        elif mouse_over:
            fill = (170, 200, 240)
        else:
            fill = (200, 220, 250)
        pygame.draw.rect(screen, fill, cycle_button_rect, border_radius=6)
        pygame.draw.rect(screen, (0, 0, 0), cycle_button_rect, 2, border_radius=6)
        label = button_font.render("Next controller", True, (0, 0, 0) if enabled else (140, 140, 140))
        screen.blit(label, label.get_rect(center=cycle_button_rect.center))

        text_print.tprint(screen, f"DSpico connected: {ser.is_open}")
        if permission_denied:
            text_print.tprint(screen, "Permission denied opening the DSpico. Run:")
            text_print.tprint(screen, "  sudo usermod -aG dialout $USER")
            text_print.tprint(screen, "then log out and back in.")
        text_print.tprint(screen, "Controller state:")
        text_print.indent()

        # State of all the buttons, active low
        button_state = [1] * 12

        if selected_id is not None:
            ctrl = controllers[selected_id]

            ids = sorted(controllers.keys())
            text_print.tprint(screen, f"Controller {ids.index(selected_id) + 1} of {len(ids)}")

            text_print.tprint(screen, f"Controller name: {ctrl.name}")
            text_print.indent()

            for sdl_button, ds_bit in button_mapping.items():
                button_state[ds_bit] = int(ctrl.get_button(sdl_button)) ^ 1

            for i in range(len(button_state)):
                text_print.tprint(screen, f"{button_names[i]} value: {button_state[i] ^ 1}")

            # Convert button_state to int
            big_endian_bits = button_state[::-1]
            button_state_value = int("".join(str(bit) for bit in big_endian_bits), 2)
            hex_value = hex(button_state_value)
            text_print.tprint(screen, f"Button state: {hex_value}")

            send(button_state_value)

        else:
            text_print.tprint(screen, "No controller connected")

        # Update the screen
        pygame.display.flip()

        # Limit to 60 frames per second.
        clock.tick(60)

    # Release all buttons
    send(4095)
    if ser.is_open:
        ser.close()


if __name__ == "__main__":
    main()

    pygame.quit()