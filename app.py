"""
Copyright (c) 2018-2026 Mat Booth.

This file is part of the Settlers of EMF app for the Tildagon
(see https://github.com/mbooth101/emf-settlers).

License: MIT
"""

import math
import os
import random

import app
from system.eventbus import eventbus
from system.patterndisplay.events import PatternEnable, PatternDisable
from system.scheduler.events import RequestForegroundPushEvent, RequestForegroundPopEvent
from events.input import ButtonDownEvent, ButtonUpEvent

TITLE_IMG = "/apps/mbooth101_emf_settlers/title.png"
if os.getcwd() != "/":
    TITLE_IMG = os.getcwd() + TITLE_IMG

# Radians in a full circle
TAU = math.pi * 2

# Radians between points on a hexagon
HEX_INTERVAL = TAU / 6


def html_to_rgb(html):
    """Utility function to convert a HTML-style hex colour code into an RGB tuple."""
    if html[0] == '#':
        html = html[1:]
    r = int(html[0:2], 16) / 255
    g = int(html[2:4], 16) / 255
    b = int(html[4:6], 16) / 255
    return (r, g, b)


class Scene:
    """A base class than contains the collection of game objects that will be
    rendered together in a single distinct scene."""

    def update(self, delta):
        """Updates the state of the current scene"""

    def draw(self, ctx):
        """Renders the current scene to the screen"""

    def handle_button_pressed(self, button):
        """Called when a button is pressed"""

    def handle_button_released(self, button):
        """Called when a button is released"""


class Menu(Scene):
    """An abstract menu scene that renders its options around the outside of the
    screen, one menu option can be assigned to each Tildagon button."""

    # Default menu item colours
    background = (0, 0, 0)
    highlight = (0.8, 0.8, 0.8)
    enabled_fg = (0.8, 0.8, 0.8)
    disabled_fg = (0.4, 0.4, 0.4)
    highlight_fg = (0.01, 0.01, 0.01)

    # Thickness of the ring around the edge of the sceen that we can use
    # to render the menu
    width = 25

    # Back is always first option
    BACK = 0

    def __init__(self, options, callback):
        self.message = []
        self.options = options
        self.callback = callback
        self.menu_selection = -1
        self.menu_highlight = -1

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
        if (self.callback and self.menu_selection >= 0):
            self.callback(self.menu_selection)
            self.menu_selection = -1
            self.menu_highlight = -1

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
        ctx.arc(0, 0, 120 - Menu.width, 0, TAU, True)
        ctx.close_path().clip()

        # Render the options
        for idx, option in enumerate(self.options):
            self.draw_option(ctx, option, idx == self.menu_highlight)

        ctx.restore()

    def draw_background(self, ctx):
        # Render message or title card if no message, either way we should
        # cover the whole screen to avoid seeing the system menu
        if self.message:
            ctx.font_size = 30
            ctx.rgb(*Menu.background).rectangle(-120, -120, 240, 240).fill()
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
            ctx.image(TITLE_IMG, -120, -120, 240, 240)

    def draw_option(self, ctx, option, highlight):
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
        if not Menu.is_option_disabled(option):
            ctx.save()
            if highlight:
                ctx.rgb(*Menu.highlight)
            else:
                if 'col' in option:
                    ctx.rgb(*option['col'])
                else:
                    ctx.rgb(*Menu.background)
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
            ctx.arc(arc_start_x, arc_start_y, end_radius, 0, TAU, False).fill()
            arc_end_x = math.cos(HEX_INTERVAL - margin) * (120 - end_radius)
            arc_end_y = math.sin(HEX_INTERVAL - margin) * (120 - end_radius)
            ctx.arc(arc_end_x, arc_end_y, end_radius, 0, TAU, False).fill()
            ctx.restore()

        # Choose foreground colour
        if Menu.is_option_disabled(option):
            ctx.rgb(*Menu.disabled_fg)
        else:
            if highlight:
                ctx.rgb(*Menu.highlight_fg)
            else:
                if 'col' in option:
                    # Just needs to contrast with the overridden bg colour
                    ctx.rgb(0, 0, 0)
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
                self.menu_highlight = idx

    def handle_button_released(self, button):
        for idx, opt in enumerate(self.options):
            if opt['btn'] == button and self.menu_highlight == idx:
                self.menu_selection = idx


class MainMenu(Menu):
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

    def __init__(self, callback):
        options = [
            {'btn': "F", 'name': "Back"},
            {'btn': "A", 'name': "  Red  ", 'col': html_to_rgb('#FF1540')},
            {'btn': "B", 'name': " Blue ", 'col': html_to_rgb('#15B5FF')},
            {'btn': "C", 'name': "Purple", 'col': html_to_rgb('#D415FF')},
            {'btn': "D", 'name': "Orange", 'col': html_to_rgb('#FF5F15')},
            ]
        super().__init__(options, callback)
        self.set_message_for_player(1)

    def set_message_for_player(self, num):
        self.set_message(f"Player {num},\nchoose your\ncolour:")

    def get_colour_for_choice(self, choice):
        return self.options[choice]['col']


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
            angle = TAU * (0 - i) / 6
            off = [Hex.size * math.cos(angle), Hex.size * math.sin(angle)]
            self.nodes.append([round(self.centre[0] + off[0]), round(self.centre[1] + off[1])])

        # Generate the list of pairs of screen coordinates for each of the sides of the hex
        self.edges = []
        for i in range(0, 6):
            node1 = self.nodes[i]
            if i < 5:
                node2 = self.nodes[i + 1]
            else:
                node2 = self.nodes[0]
            if node1[0] <= node2[0]:
                self.edges.append((node1, node2))
            else:
                self.edges.append((node2, node1))

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
            ctx.rgb(1, 1, 1)
        else:
            ctx.rgb(0, 0, 0)
        if self.robber:
            ctx.font_size = round(Hex.size * 0.8)
            ctx.move_to(self.centre[0], self.centre[1]).text("Rob")
        else:
            ctx.font_size = Hex.size
            if self.resource != GameBoard.DESERT:
                ctx.move_to(self.centre[0], self.centre[1])
                ctx.text(f"{self.number['roll']}")


class Player:
    """The player's hand of resource cards and their score and what not."""

    def __init__(self, name, colour):
        """Create a player that will be represented on screen by the given colour."""
        self.name = name
        self.colour = colour


class Selectable:
    """Base class for selectable locations on the game board."""

    # Default colours
    highlight = (1, 1, 1)
    outline = (0.8, 0.8, 0.8)

    # Possible things this location may contain
    EMPTY = 0

    def __init__(self, data):
        # Screen coords that define the selectable object
        self.data = data

        # The list of hexes next to which this selectable object is adjacent
        self.hexes = []

        # What is built here and who owns it
        self.player = None
        self.contents = Selectable.EMPTY

        # Whether to draw selection indicator
        self.selected = False

        # Selection throb animation data
        self.accum = 0
        self.throb = 0
        self.speed = 1000 # ms

    def is_empty(self):
        return self.contents == Selectable.EMPTY

    def update(self, delta):
        if self.selected:
            self.accum = self.accum + delta
            if self.accum > self.speed:
                self.accum = self.accum - self.speed
            self.throb = math.sin((TAU / self.speed) * self.accum)
            # Keep throbbing within the range of 0 to 1
            self.throb = (self.throb + 1) * 0.5


class Settlement(Selectable):
    """A node at which it is possible to build a settlement."""

    # Possible things this location may contain, the values here are the number of
    # victory points that the building is worth to the player who built it
    TOWN = 1
    CITY = 2

    def build_town(self, player):
        assert self.is_empty(), 'Town can only be built in empty location'
        self.player = player
        self.contents = Settlement.TOWN

    def build_city(self, player):
        assert self.contents == Settlement.TOWN and self.player.name == player.name, 'City can only be built in place of one of your own towns'
        self.contents = Settlement.CITY

    def draw(self, ctx):
        ctx.save()
        if self.contents == Settlement.TOWN:
            ctx.rgb(*self.player.colour)
            ctx.arc(self.data[0], self.data[1], 4, 0, TAU, False).fill()
            ctx.rgb(*Selectable.outline)
            ctx.arc(self.data[0], self.data[1], 4, 0, TAU, False).stroke()
        elif self.contents == Settlement.CITY:
            ctx.rgb(*self.player.colour)
            ctx.rectangle(self.data[0] - 4, self.data[1] - 4, 8, 8).fill()
            ctx.rgb(*Selectable.outline)
            ctx.rectangle(self.data[0] - 4, self.data[1] - 4, 8, 8).stroke()
        if self.selected:
            ctx.rgb(*Selectable.highlight)
            ctx.arc(self.data[0], self.data[1], 5 + (4 * self.throb), 0, TAU, False).stroke()
        ctx.restore()


class Road(Selectable):
    """An edge along which it is possible to build a road."""

    # Possible things this location may contain
    ROAD = 1

    def build_road(self, player):
        assert self.is_empty(), 'Road can only be built in empty location'
        self.player = player
        self.contents = Road.ROAD

    def draw(self, ctx):
        ctx.save()
        x0, y0 = self.data[0]
        x1, y1 = self.data[1]
        # Calculate the normalised edge vector
        normalised = ((x0 - x1) / Hex.size, (y0 - y1) / Hex.size)
        # Translate to one end of the edge and then rotate by the angle that
        # the normalised vector points, any subsequent rectangles we draw will
        # overlap the edge described by x0,y0 -> x1,y1
        ctx.translate(x0, y0).rotate(math.pi - math.atan2(*normalised))
        if self.contents == Road.ROAD:
            ctx.rgb(*self.player.colour)
            ctx.rectangle(-3, 0, 6, Hex.size).fill()
            ctx.rgb(*Selectable.outline)
            ctx.rectangle(-3, 0, 6, Hex.size).stroke()
        if self.selected:
            ctx.rgb(*Selectable.highlight)
            ctx.rectangle(-3 - 4 * self.throb, 0, 6 + 8 * self.throb, Hex.size).stroke()
        ctx.restore()


class GameBoard(Menu):
    """A gameboard is made of hexes, roads, and settlements. It also contains
    the players."""

    # Kinds of resource
    SHEEP = {'kind':0, 'col': html_to_rgb('#228B22')}
    WHEAT = {'kind':1, 'col': html_to_rgb('#DAA520')}
    WOOD = {'kind':2, 'col': html_to_rgb('#993300')}
    BRICK = {'kind':3, 'col': html_to_rgb('#ff0000')}
    ORE = {'kind':4, 'col': html_to_rgb('#757575')}
    DESERT = {'kind':5, 'col': html_to_rgb('#ffee55')}  # Not really a resource
    RESOURCE_KINDS = [SHEEP, WHEAT, WOOD, BRICK, ORE]

    # List of resources (pre-randomised to combat the not-very random number
    # generator) that make up the hexes on the game board for 4 players
    resources = [ORE, SHEEP, WHEAT, ORE, ORE, WOOD, DESERT, BRICK, SHEEP, WOOD,
                 WHEAT, WOOD, WOOD, WHEAT, SHEEP, BRICK, SHEEP, BRICK, WHEAT]

    # Dice roll probabilities
    TWO = {'roll':2, 'prob':1}
    THREE = {'roll':3, 'prob':2}
    FOUR = {'roll':4, 'prob':3}
    FIVE = {'roll':5, 'prob':4}
    SIX = {'roll':6, 'prob':5}
    SEVEN = {'roll':7, 'prob':0}  # Most probable, but zero because desert
    EIGHT = {'roll':8, 'prob':5}
    NINE = {'roll':9, 'prob':4}
    TEN = {'roll':10, 'prob':3}
    ELEVEN = {'roll':11, 'prob':2}
    TWELVE = {'roll':12, 'prob':1}

    # Dice rolls for (these have a strict order) to be assigned to the resource
    # hexes for 4 player games
    numbers = [FIVE, TWO, SIX, THREE, EIGHT, TEN, NINE, TWELVE, ELEVEN, FOUR,
               EIGHT, TEN, NINE, FOUR, FIVE, SIX, THREE, ELEVEN]

    game_options = [
        {'btn': "F", 'name': "Back"},
        ]

    def __init__(self, callback, players):
        """Creates a new game board for the given list of players."""
        super().__init__(GameBoard.game_options, callback)

        self.players = players
        self.current_player = None

        # Two rings of hexes around the centre
        radius = 2

        # Choose a starting hex on the outermost ring of hexes
        choice = random.randrange(0, 6)
        coords = [0, 0, 0]
        for i in range(radius):
            coords = [a + b for a, b in zip(coords, Hex.directions[choice])]

        # Copy lists so we can edit them with impunity
        r_copy = GameBoard.resources.copy()
        n_copy = GameBoard.numbers.copy()

        # Create the board
        self.hexes = []
        while radius > 0:
            # From the starting hex, go radius hexes in each of the 6 directions
            for i in list(range((choice + 2) % 6, 6)) + list(range(0, (choice + 2) % 6)):
                for _ in range(radius):
                    # The resources are picked at random from the list
                    resource = r_copy.pop(random.randrange(0, len(r_copy)))
                    # But the dice roll numbers are picked in order, unless it's
                    # the desert in which case that is always 7
                    number = GameBoard.SEVEN
                    if resource['kind'] != 5:
                        number = n_copy.pop(0)
                    self.hexes.append(Hex(coords, resource, number, number['roll'] == 7))
                    coords = Hex.get_neighbouring_hex_coords(coords, i)

            # Go into the next ring of hexes (opposite direction of starting choice)
            coords = Hex.get_neighbouring_hex_coords(coords, (choice + 3) % 6)
            radius = radius - 1
        # The final, centre hex
        resource = r_copy.pop()
        number = GameBoard.SEVEN
        if resource['kind'] != 5:
            number = n_copy.pop(0)
        self.hexes.append(Hex(coords, resource, number, number['roll'] == 7))

        # Generate lists of unique valid locations for building settlements and roads
        self.roads = []
        self.settlements = []
        for h in self.hexes:
            for edge in h.edges:
                already_got = False
                for r in self.roads:
                    if r.data == edge:
                        already_got = True
                        r.hexes.append(h)
                if not already_got:
                    r = Road(edge)
                    r.hexes.append(h)
                    self.roads.append(r)
            for node in h.nodes:
                already_got = False
                for s in self.settlements:
                    if s.data == node:
                        already_got = True
                        s.hexes.append(h)
                if not already_got:
                    s = Settlement(node)
                    s.hexes.append(h)
                    self.settlements.append(s)

        # Generate player setup queue, this determines the order in which the
        # players place their initial settlements and roads. The order is
        # player 1 to player n, then player n to player 1. This gives the
        # first player first pick of the first settlement and road, and the
        # last player first pick of the second settlement and road
        self.psq = []
        self.psq += self.players
        self.players.reverse()
        self.psq += self.players
        self.players.reverse()

    def next_player(self):
        """Select the next current player."""
        if self.psq:
            # If player setup queue still has entries, pop the next player
            # off the queue
            self.current_player = self.psq.pop(0)
        else:
            # Otherwise select the player that comes after the current player
            # in the player list
            for idx, player in enumerate(self.players):
                if self.current_player == player:
                    self.current_player = self.players[(idx + 1) % len(self.players)]
           # TODO implement dice self.dice.reset()
            for h in self.hexes:
                h.set_highlight(False)

    def update(self, delta):
        super().update(delta)
        for r in self.roads:
            r.update(delta)
        for s in self.settlements:
            s.update(delta)

    def draw_background(self, ctx):
        ctx.save()

        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE

        ctx.rgb(0, 0, 0).rectangle(-120, -120, 240, 240).fill()
        for h in self.hexes:
            h.draw(ctx)
        for r in self.roads:
            r.draw(ctx)
        for s in self.settlements:
            s.draw(ctx)
        ctx.restore()


class Settlers(app.App):
    """Entry point, state machine that manages scene transitions, and user input management."""

    # Game scenes
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
        if choice == Menu.BACK:
            self.exit = True
        if choice == MainMenu.NEW_GAME:
            self.state_next = Settlers.NUM_PLAYERS_MENU
        if choice == MainMenu.CONTINUE:
            self.state_next = Settlers.GAME

    def num_players_menu_cb(self, choice):
        if choice == Menu.BACK:
            self.state_next = Settlers.MAIN_MENU
        else:
            self.num_players = choice
            self.state_next = Settlers.PLAYER_COLOUR_MENU

    def player_colour_menu_cb(self, choice):
        if choice == Menu.BACK:
            self.state_next = Settlers.NUM_PLAYERS_MENU
            self.players.clear()
        else:
            colour = self.scene.get_colour_for_choice(choice)
            player_num = len(self.players) + 1
            self.players.append(Player(f"Player {player_num}", colour))
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

    def game_menu_cb(self, choice):
        if choice == Menu.BACK:
            self.state_next = Settlers.MAIN_MENU

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
            if not self.game:
                self.scene.set_disabled([MainMenu.CONTINUE])
        if self.state == Settlers.NUM_PLAYERS_MENU:
            self.scene = NumPlayersMenu(self.num_players_menu_cb)
        if self.state == Settlers.PLAYER_COLOUR_MENU:
            self.scene = PlayerColourMenu(self.player_colour_menu_cb)
        if self.state == Settlers.GAME:
            if not self.game:
                self.game = GameBoard(self.game_menu_cb, self.players)
            self.scene = self.game

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


__app_export__ = Settlers # pylint: disable=invalid-name
