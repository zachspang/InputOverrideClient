import os
import pygame
import serial
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

pygame.init()

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
    joysticks = {}

    # Instance id of the controller currently being read.
    selected_id = None

    # "next controller" button
    cycle_button_rect = pygame.Rect(10, 350, 200, 35)
    button_font = pygame.font.Font(None, 25)

    # Serial port that connects to the DSpico
    ser = serial.Serial()
    last_connect_attempt = -1000

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
        ids = sorted(joysticks.keys())
        if len(ids) < 2:
            return
        if selected_id in ids:
            selected_id = ids[(ids.index(selected_id) + 1) % len(ids)]
        else:
            selected_id = ids[0]
        print(f"Switched to joystick {selected_id}")

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

    # pygame xbox360 -> PAD_ALL_MASK https://twlsdk.randommeaninglesscharacters.com/docs/nitro/NitroSDK/pad/PAD_Read.html
    button_mapping = {
        0 : 1,
        1 : 0,
        2 : 11,
        3 : 10,
        4 : 9,
        5 : 8,
        6 : 2,
        7 : 3,
    }

    done = False
    while not done:
        # Searching for the port enumerates every COM port, so only try once a second
        if not ser.is_open and pygame.time.get_ticks() - last_connect_attempt >= 1000:
            last_connect_attempt = pygame.time.get_ticks()
            try:
                ser = serial.serial_for_url("hwgrep://CAFE:6000", timeout=1, write_timeout=0.25)
            except (serial.SerialException, OSError):
                ser = serial.Serial()

        # Event processing step.
        # Possible joystick events: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
        # JOYBUTTONUP, JOYHATMOTION, JOYDEVICEADDED, JOYDEVICEREMOVED
        try:
            events = pygame.event.get()
        except (SystemError, KeyError):
            events = []  # pygame's joystick map got out of sync, skip this frame

        for event in events:
            if event.type == pygame.QUIT:
                done = True

            # Handle hotplugging
            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                if joy.get_instance_id() not in joysticks:
                    joysticks[joy.get_instance_id()] = joy
                    print(f"Joystick {joy.get_instance_id()} connected")

            if event.type == pygame.JOYDEVICEREMOVED:
                joysticks.pop(event.instance_id, None)
                print(f"Joystick {event.instance_id} disconnected")
                send(4095)

            # Cycle controllers
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cycle_button_rect.collidepoint(event.pos):
                    cycle_controller()


        screen.fill((255, 255, 255))
        text_print.reset()

        # Make sure the selection is valid
        if joysticks and selected_id not in joysticks:
            selected_id = sorted(joysticks.keys())[0]
        elif not joysticks:
            selected_id = None

        # Draw the cycle button (greyed out unless 2+ controllers are connected)
        enabled = len(joysticks) > 1
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
        text_print.tprint(screen, "Controller state:")
        text_print.indent()

        # State of all the buttons, active low
        button_state = [1] * 12

        if selected_id is not None:
            joystick = joysticks[selected_id]

            ids = sorted(joysticks.keys())
            text_print.tprint(screen, f"Controller {ids.index(selected_id) + 1} of {len(ids)}")

            name = joystick.get_name()
            text_print.tprint(screen, f"Joystick name: {name}")
            text_print.indent()

            buttons = joystick.get_numbuttons()

            for i in range(buttons):
                button = joystick.get_button(i)
                if (i <= 7):
                    button_state[button_mapping[i]] = button ^ 1

            hats = joystick.get_numhats()
            if hats > 0:
                hat = joystick.get_hat(0)
                up,down,left,right = 0,0,0,0

                if hat[0] == -1:
                    left = 1
                elif hat[0] == 1:
                    right = 1

                if hat[1] == -1:
                    down = 1
                elif hat[1] == 1:
                    up = 1
                button_state[4] = right ^ 1
                button_state[5] = left ^ 1
                button_state[6] = up ^ 1
                button_state[7] = down ^ 1

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