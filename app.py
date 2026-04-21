"""
Copyright (c) 2018-2026 Mat Booth.

This file is part of the Settlers of EMF app for the Tildagon
(see https://github.com/mbooth101/emf-settlers).

License: MIT
"""

import math
import os
import random
import sys

import app
from system.eventbus import eventbus
from system.patterndisplay.events import *
from system.scheduler.events import *
from events.input import ButtonDownEvent, ButtonUpEvent, BUTTON_TYPES

TITLE_IMG = "/apps/mbooth101_emf_settlers/title.png"
if os.getcwd() != "/":
    TITLE_IMG = os.getcwd() + TITLE_IMG

# Radians between points on a hexagon
HEX_INTERVAL = (math.pi * 2) / 6

# Kinds of resource
SHEEP = {'kind':0, 'col': (0xd4, 0xe1, 0x57)}
WHEAT = {'kind':1, 'col': (0xff, 0xc1, 0x07)}
WOOD = {'kind':2, 'col': (0x99, 0x33, 0x00)}
BRICK = {'kind':3, 'col': (0xff, 0x00, 0x00)}
ORE = {'kind':4, 'col': (0x75, 0x75, 0x75)}
DESERT = {'kind':5, 'col': (0xff, 0xee, 0x55)}  # Not really a resource
RESOURCE_KINDS = [ SHEEP, WHEAT, WOOD, BRICK, ORE ]


def html_to_rgb(html):
    if html[0] == '#':
        html = html[1:]
    r = int(html[0:2], 16) / 255
    g = int(html[2:4], 16) / 255
    b = int(html[4:6], 16) / 255
    return (r, g, b)


class Scene:

    def update(self, delta):
        """Updates the state of the current scene"""
        pass

    def draw(self, ctx):
        """Renders the current scene to the screen"""
        pass

    def handle_button_pressed(self, button):
        """Called when a button is pressed"""
        pass

    def handle_button_released(self, button):
        """Called when a button is released"""
        pass


class Menu(Scene):

    # Menu text colours
    enabled_fg = (0.8, 0.8, 0.8)
    disabled_fg = (0.4, 0.4, 0.4)
    selected_fg = (0.01, 0.01, 0.01)

    # Thickness of the ring around the edge of the sceen that we can use
    # to render the menu
    width = 25

    def __init__(self, options, callback):
        self.message = []
        self.options = options
        self.callback = callback
        self.selection = -1

    def set_message(self, message):
        """Set the message or question to display for the menu"""
        # The ctx library does not handle strings with newlines well so
        # lets split up the lines and we'll draw each line individually
        # TODO: Fix centred text containing newlines in uctx
        if not message:
            self.message = []
        else:
            self.message = message.splitlines()

    def set_disabled(self, indices):
        """Set disabled flag on options corresponding to the given list of indices"""
        if isinstance(indices, list):
            for idx in indices:
                self.options[idx]['disabled'] = True

    def get_disabled(self):
        """Return list of indices of options that have the disabled flag set"""
        return [idx for idx, option in enumerate(self.options) if Menu.is_option_disabled(option)]

    @staticmethod
    def is_option_disabled(opt):
        return opt['disabled'] if 'disabled' in opt else False

    def update(self, delta):
        pass

    def draw(self, ctx):
        ctx.save()

        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE

        # Render the background
        self.draw_background(ctx)

        # Define clip space so subsequent ops don't overwrite the title card
        # or message, the menu options will be drawn in the outside perimeter
        ctx.begin_path()
        ctx.rectangle(-120, -120, 240, 240)
        ctx.arc(0, 0, 120 - Menu.width, 0, math.pi * 2, True)
        ctx.close_path().clip()

        # Render the options
        for idx, option in enumerate(self.options):
            self.draw_option(ctx, option, idx == self.selection)

        ctx.restore()

    def draw_background(self, ctx):
        # Render message or title card if no message, either way we should
        # cover the whole screen to avoid seeing the system menu
        if self.message:
            ctx.font_size = 30
            ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()
            ctx.rgb(*Menu.enabled_fg)
            # Calculate offset to centre multi-line messages vertically
            if len(self.message) % 2 == 1:
                line_offset = ((len(self.message) - 1) / 2) * ctx.font_size
            else:
                line_offset = (len(self.message) / 2) * ctx.font_size - 0.5 * ctx.font_size
            # Message consists of a list of lines, because uctx doesn't treat
            # newlines well for centred text
            # TODO: Fix centred text containing newlines in uctx
            for idx, line in enumerate(self.message):
                ctx.move_to(0, idx * ctx.font_size - line_offset).text(line)
        else:
            # XXX: Avoid drawing images in the simulator due to bug
            # https://github.com/emfcamp/badge-2024-software/issues/269
            if sys.implementation.name == "micropython":
                ctx.image(TITLE_IMG, -120, -120, 240, 240)
            else:
                ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()

    def draw_option(self, ctx, option, selected):
        ctx.save()
        ctx.font_size = 18

        # Size of the arc in radians needed to highlight all of the text
        # Angle in radians is arc length over circle radius
        arc_extent = ctx.text_width(option['name']) / 120

        # Margin in radians used to centre the arc within the hex interval
        # associated with the botton position
        margin = (HEX_INTERVAL - arc_extent) / 2

        # Ordinal position of the button for the current option
        pos = ord(option['btn']) - 65

        # Render the selection highlight as a sector of a circle that is
        # truncated by the clip mask
        if selected:
            ctx.save()
            ctx.rgb(*Menu.enabled_fg)
            # Offset the position by -2 for drawing the arc because the vector
            # in the direction of zero radians points right instead of up and
            # we consider the "A" button to be at position 0
            ctx.rotate((pos - 2) * HEX_INTERVAL)
            # Draw the highlight arc
            ctx.begin_path()
            ctx.move_to(0, 0).arc(0, 0, 120, margin, HEX_INTERVAL - margin, False)
            ctx.close_path().fill()
            # Give the highlight rounded ends by adding a circle to each end
            # of the highlight arc
            end_radius = Menu.width / 2
            arc_start_x = math.cos(margin) * (120 - end_radius)
            arc_start_y = math.sin(margin) * (120 - end_radius)
            ctx.arc(arc_start_x, arc_start_y, end_radius, 0, math.pi * 2, False).fill()
            arc_end_x = math.cos(HEX_INTERVAL - margin) * (120 - end_radius)
            arc_end_y = math.sin(HEX_INTERVAL - margin) * (120 - end_radius)
            ctx.arc(arc_end_x, arc_end_y, end_radius, 0, math.pi * 2, False).fill()
            ctx.restore()

        # Choose foreground colour
        if Menu.is_option_disabled(option):
            ctx.rgb(*Menu.disabled_fg)
        else:
            if selected:
                ctx.rgb(*Menu.selected_fg)
            else:
                ctx.rgb(*Menu.enabled_fg)

        # Render the indicator arrow
        ctx.rotate(pos * HEX_INTERVAL).translate(0, -115)
        ctx.begin_path()
        ctx.move_to(0, -5).line_to(-10, 0).line_to(10, 0)
        ctx.close_path().fill()

        # Render option text, rotating by 180 degrees for the lower buttons
        if pos in [2,3,4]:
            ctx.rotate(math.pi).move_to(0, -10).text(option['name'])
        else:
            ctx.move_to(0, 10).text(option['name'])

        ctx.restore()

    def handle_button_pressed(self, button):
        for idx, opt in enumerate(self.options):
            if opt['btn'] == button and not Menu.is_option_disabled(opt):
                self.selection = idx

    def handle_button_released(self, button):
        if (self.callback and self.selection >= 0):
            self.callback(self.selection)
        self.selection = -1


class MainMenu(Menu):
    EXIT = 0
    NEW_GAME = 1
    CONTINUE = 2

    def __init__(self, callback):
        options = [
            {'btn': "F", 'name': "Exit"},
            {'btn': "E", 'name': "New Game"},
            {'btn': "C", 'name': "Continue Game"},
            ]
        super().__init__(options, callback)


class NumPlayersMenu(Menu):
    BACK = 0
    # No further constants, the chosen option index is the number of players

    def __init__(self, callback):
        options = [
            {'btn': "F", 'name': "Back"},
            {'btn': "A", 'name': "1 Player"},
            {'btn': "B", 'name': "2 Players"},
            {'btn': "C", 'name': "3 Players"},
            {'btn': "D", 'name': "4 Players"},
            ]
        super().__init__(options, callback)


class PlayerColourMenu(Menu):
    BACK = 0

    def __init__(self, callback):
        options = [
            {'btn': "F", 'name': "Back"},
            {'btn': "A", 'name': "Red", 'col': html_to_rgb("#FF1540")},
            {'btn': "B", 'name': "Blue", 'col': html_to_rgb("#15B5FF")},
            {'btn': "C", 'name': "Purple", 'col': html_to_rgb("#D415FF")},
            {'btn': "D", 'name': "Orange", 'col': html_to_rgb("#FF5F15")},
            ]
        super().__init__(options, callback)

    def set_message_for_player(self, num):
        self.set_message(f"Player {num},\nchoose your\ncolour:")


class Hex:
    """Hexes are the games tiles. They have a resource kind, correspond to the value
    of a roll of two D6 and may or may not contain the robber."""

    # Screen coords are x,y values that locate pixels on the physical display:
    #
    #       -120
    #         ↓
    # -120 →  0  → 120
    #         ↓
    #        120
    #
    # Hex coords are x,y,z values that locate the relative positions of hexagons:
    #
    #          0,1,-1
    # -1,1,0 ↖  ↑    ↗ 1,0,-1
    #          0,0,0
    # -1,0,1 ↙  ↓    ↘ 1,-1,0
    #          0,-1,1
    #
    # Converting between the two systems can be done by multiplying the x and y
    # coordinates against a matrix. When converting to hex coords, the z value
    # can be computed from the new x and y values because x + y + z must always
    # equal zero.
    #
    # This is the matrix used to convert from hex coords to screen coords
    matrix = [3.0 * 0.5, 0.0, math.sqrt(3.0) * 0.5, math.sqrt(3.0)]

    # Size in pixels of the hex, from the centre point to each corner
    size = 22

    # Hex coord translations for how to get to the neighbouring hexes
    directions = {
        0: [-1, 1, 0],  # South West
        1: [0, 1, -1],  # South
        2: [1, 0, -1],  # South East
        3: [1, -1, 0],  # North East
        4: [0, -1, 1],  # North
        5: [-1, 0, 1],  # North West
        }

    def __init__(self, coords, resource, number, robber):
        """Create a new hex at the given hex coordinates, of the given kind of resource"""
        # Validate coords
        assert len(coords) == 3, 'Invalid number of hexagon coordinates'
        assert coords[0] + coords[1] + coords[2] == 0, 'Invalid hexagon coordinate values'
        self.coords = coords

        # The kind of resource hosted by this hex
        self.resource = resource

        # The dice roll required to win this resource
        self.number = number

        # Whether this hex contains the robber
        self.robber = robber

        # Whether this hex should be highlighted
        self.highlight = False

        # Compute the screen coordinates of the centre of the hex
        x = self.coords[0]
        y = self.coords[1]
        self.centre = [
            (Hex.matrix[0] * x + Hex.matrix[1] * y) * Hex.size,
            (Hex.matrix[2] * x + Hex.matrix[3] * y) * Hex.size,
        ]

        # Generate the list of screen coordinates for each of the corners of the hex
        self.nodes = []
        for i in range(0, 6):
            angle = 2.0 * math.pi * (0 - i) / 6
            offset = [Hex.size * math.cos(angle), Hex.size * math.sin(angle)]
            self.nodes.append([int(self.centre[0] + offset[0]), int(self.centre[1] + offset[1])])

        # Generate the list of pairs of screen coordinates for each of the sides of the hex
        self.edges = []
        for i in range(0, 6):
            node1 = self.nodes[i]
            if i < 5:
                node2 = self.nodes[i + 1]
            else:
                node2 = self.nodes[0]
            if node1[0] <= node2[0]:
                self.edges.append([node1, node2])
            else:
                self.edges.append([node2, node1])

    def set_highlight(self, highlight):
        if self.highlight != highlight:
            self.highlight = highlight

    @staticmethod
    def get_neighbouring_hex_coords(coords, direction):
        return [a + b for a, b in zip(coords, Hex.directions[direction])]

    def draw(self, ctx):
        # Draw hexagon
        ctx.rgb(*self.resource['col'])
        ctx.begin_path()
        ctx.move_to(*self.nodes[0])
        for node in self.nodes[1:]:
            ctx.line_to(*node)
        ctx.close_path()
        ctx.fill()

        # Draw label
        if self.highlight:
            ctx.rgb(255, 255, 255)
        else:
            ctx.rgb(0, 0, 0)
        ctx.text_align = ctx.CENTER
        if self.robber:
            ctx.font_size = 20
            ctx.move_to(self.centre[0], self.centre[1] + 7).text("Rob")
        else:
            ctx.font_size = 30
            if self.resource != DESERT:
                ctx.move_to(self.centre[0], self.centre[1] + 10).text("{}".format(self.number['roll']))

class Game(Scene):

    def update(self, delta):
        pass

    def draw(self, ctx):
        ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()

class Settlers(app.App):

    # Game states
    MAIN_MENU = 1
    NUM_PLAYERS_MENU = 2
    PLAYER_COLOUR_MENU = 3
    GAME = 4

    def __init__(self):
        self.exit = False

        self.game = None
        self.scene = None

        self.num_players = 0
        self.players = []

        # State machine tracking
        self.state_prev = None
        self.state = None
        self.state_next = Settlers.MAIN_MENU

        # Tracked button state
        self.buttons = {}

        # Register for synchronous button events, there's too much input lag
        # if we did this asynchronously
        eventbus.on(ButtonDownEvent, self._button_down, self)
        eventbus.on(ButtonUpEvent, self._button_up, self)

        # Register for app stack events
        eventbus.on_async(RequestForegroundPushEvent, self._resume, self)
        eventbus.on_async(RequestForegroundPopEvent, self._pause, self)
        eventbus.emit(PatternDisable())

    def main_menu_cb(self, choice):
        if choice == MainMenu.EXIT:
            self.exit = True
        if choice == MainMenu.NEW_GAME:
            self.state_next = Settlers.NUM_PLAYERS_MENU

    def num_players_menu_cb(self, choice):
        if choice == NumPlayersMenu.BACK:
            self.state_next = Settlers.MAIN_MENU
        else:
            self.num_players = choice
            self.state_next = Settlers.PLAYER_COLOUR_MENU

    def player_colour_menu_cb(self, choice):
        if choice == PlayerColourMenu.BACK:
            self.state_next = Settlers.NUM_PLAYERS_MENU
        else:
            self.players.append({})
            if len(self.players) < self.num_players:
                # If we've not yet selected colours for all the players,
                # disable the one that was just chosen, update the menu
                # message, and round again
                disabled = self.scene.get_disabled()
                disabled.append(choice)
                self.scene.set_disabled(disabled)
                self.scene.set_message_for_player(len(self.players) + 1)
                self.state_next = Settlers.PLAYER_COLOUR_MENU
            else:
                self.state_next = Settlers.GAME

    def _button_down(self, event: ButtonDownEvent):
        button = event.button.name
        # Send pressed event to current active scene only if the button was
        # not already down (i.e. avoid repeat events for a held button)
        if button not in self.buttons or not self.buttons[button]:
            self.buttons[button] = True
            self.scene.handle_button_pressed(button)

    def _button_up(self, event: ButtonUpEvent):
        button = event.button.name
        # Send released event to current active scene only if the button was
        # previously pressed
        if button in self.buttons and self.buttons[button]:
            self.buttons[button] = False
            self.scene.handle_button_released(button)

    async def _resume(self, event: RequestForegroundPushEvent):
        # Disable firmware led pattern when foregrounded
        eventbus.emit(PatternDisable())

    async def _pause(self, event: RequestForegroundPopEvent):
        # Renable firmware led pattern when backgrounded
        eventbus.emit(PatternEnable())

    def enter_state(self):
        self.state_prev = self.state
        self.state = self.state_next
        self.state_next = None

        # Just exit early if the requested state is the same as the previous
        if self.state == self.state_prev:
            return

        # Load the scene associated with the new state
        if self.state == Settlers.MAIN_MENU:
            self.scene = MainMenu(self.main_menu_cb)
            # TODO Enable continue if game in progress
            self.scene.set_disabled([MainMenu.CONTINUE])
        if self.state == Settlers.NUM_PLAYERS_MENU:
            self.scene = NumPlayersMenu(self.num_players_menu_cb)
        if self.state == Settlers.PLAYER_COLOUR_MENU:
            self.scene = PlayerColourMenu(self.player_colour_menu_cb)
        if self.state == Settlers.GAME:
            self.scene = Game()

    def update(self, delta):
        if self.exit:
            self.exit = False
            self.minimise()

        if self.state_next:
            self.enter_state()

        self.scene.update(delta)
        return True

    def draw(self, ctx):
        self.scene.draw(ctx)

__app_export__ = Settlers
