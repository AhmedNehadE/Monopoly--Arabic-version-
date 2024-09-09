from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GL import *
import math
import random
import time
import easygui

MONOPOLY_PROPERTIES_BY_COLOR = {
    "brown": ["Syria", "El Khartoum"],
    "light blue": ["Beirut", "El Reyad", "Baghdad"],
    "pink": ["Beni Ghazi", "Adan", "Jeddah"],
    "orange": ["Casablanca", "Tunise", "Algerie"],
    "red": ["Alexandria", "Abu Dhabi", "Dubai"],
    "yellow": ["Yemen", "Aswan", "Ghaza"],
    "green": ["Al Ain", "Bahrain", "Oman"],
    "blue": ["Qatar", "Kuwait"],
    "utility": ["Electric Company", "Water Works"]
}

#dictionary contain all the rent prices for each color ("ANE")
MONOPOLY_RENT = {
    "brown": [
        [2, 4], [4, 8], [6, 12], [8, 16], [10, 20], [14, 28]
    ],
    "light blue": [
        [4, 8], [8, 16], [12, 24], [16, 32], [20, 40], [28, 56]
    ],
    "pink": [
        [6, 12], [12, 24], [18, 36], [24, 48], [30, 60], [42, 84]
    ],
    "orange": [
        [6, 12], [14, 28], [22, 44], [30, 60], [38, 76], [54, 108]
    ],
    "red": [
        [8, 16], [18, 36], [28, 56], [38, 76], [48, 96], [68, 136]
    ],
    "yellow": [
        [10, 20], [22, 44], [32, 64], [44, 88], [56, 112], [78, 156]
    ],
    "green": [
        [14, 28], [30, 60], [46, 92], [60, 120], [74, 148], [98, 196]
    ],
    "blue": [
        [22, 44], [50, 100], [70, 140], [90, 180], [110, 220], [150, 300]
    ],
    "utility": [
        [4, 10], [10, 20]
    ]
}



CC = ["Go","Syria","Community Chest","El Khartoum","Income Tax","Beirut","Chance","El Reyad","Baghdad",
                    "Jail","Beni Ghazi","Electric Company","Adan","Jeddah","Casablanca","Community Chest","Tunise",
                    "Algerie","Free Parking","Alexandria","Chance", "Abu Dhabi","Dubai","Yemen","Aswan","Water Works",
                   "Ghaza","Go To Jail","Al Ain","Bahrain","Community Chest","Oman","Chance","Qatar","Luxury Tax",
                   "Kuwait"]
li=0



#============= player class =============
class Player:
    STARTING_BALANCE = 1300

    #the constructor is used to __init__ialize all the player's properties
    def __init__(self, name, game_board , x_left ,  x_right ):
        self.name = name
        self.balance = Player.STARTING_BALANCE
        self.position = 0
        self.x_left = x_left
        self.x_right = x_right
        self.y_top = -0.9
        self.y_bottom = -0.95
        self.go_right =  self.go_up = self.go_left = self.go_down = False
        self.properties = []
        self.game_board = game_board
        self.in_jail = False
        self.get_out_of_jail_cards = []
        self.last_roll = None #used to calculate the rent paid when player stand on one of the companies
        self.num_companies = 0
        self.jail_turns = 0
        self.num_of_mortgaged =0

    def __str__(self):
        return self.name

    def pay(self, amount, to_player):
        self.balance -= amount
        if to_player is not None:
            to_player.receive(amount)

    def receive(self, amount):
        self.balance += amount

    def buy_property (self , property):
        self.add_property(property)
        self.pay(property.price , None)
        property.set_owner(self)

    def add_property(self, property):
        self.properties.append(property)
        if property.get_color() == "utility":
            self.num_companies += 1 # update num_companies for utility properties
        property.set_owner(self)

    def remove_property(self, property):
        self.properties.remove(property)
        if property.get_color() == "utility":
            self.num_companies -= 1 # update num_companies for utility properties
        property.remove_owner()

    def move(self, num_spaces):
        self.num_of_mortgaged = len([p for p in self.properties if p.is_mortgaged])
        self.position = (self.position + num_spaces) % 36
        self.last_roll = num_spaces

    def move_to(self, position):
        if self.position > position:
            self.receive(200)
        self.position = position

    def get_net_worth(self):
        return self.balance + sum([p.price for p in self.properties if not p.is_mortgaged])

    def can_afford(self, amount):
        return self.balance >= amount

    def has_get_out_of_jail_card(self):
        return len(self.get_out_of_jail_cards) > 0

    def use_get_out_of_jail_card(self):
        if self.has_get_out_of_jail_card():
            card = self.get_out_of_jail_cards.pop()
            self.game_board.return_get_out_of_jail_card(card)
            self.in_jail = False

    def go_to_jail(self):
        self.in_jail = True
        self.jail_turns = 2

    def in_jail_turns(self):
        self.jail_turns -= 1
        if(self.jail_turns == 0):
            self.leave_jail()
    def leave_jail(self):
        self.in_jail = False
        self.jail_turns = 0

    def get_balance(self):
        return self.balance

    def show_properties(self):
        prop=""
        i=1
        for p in self.properties:
            prop += str(i)+": "+p.name
            i+=1
            if p.is_mortgaged:
                prop += " (mortaged)\t"
            else:
                prop+="\t"
        return prop
    def show_unmortgaged_properties(self):
        prop = ""
        i = 1
        for p in self.properties:
            if not p.is_mortgaged:
                prop += str(i) + ": " + p.name + "  \t "
            i += 1
        return prop

    def show_mortgaged_properties(self):
        prop = ""
        i = 1
        for p in self.properties:
            if p.is_mortgaged:
                prop += str(i) + ": " + p.name + "  \t "
            i += 1
        return prop


class Property:
    MAX_HOUSES = 4
    MAX_HOTELS = 1

    def __init__(self, name, price, rent, position, color=None):
        self.name = name
        self.price = price
        self.rent = rent
        self.owner = None
        self.position = position
        self.color = color
        self.is_mortgaged = False
        self.mortgage_value = int(self.price / 2)
        self.num_houses = 0
        self.num_hotels = 0

    def __str__(self):
        return f"{self.name} (${self.price})"

    def is_owned(self):
        return self.owner is not None

    def get_rent(self):
        special_rent = self.get_special_rent()
        if self.is_owned() and not special_rent == 0:
            rent = self.rent + self.get_house_rent() + self.get_hotel_rent() + self.get_special_rent()
            if self.has_full_color_set():
                rent += self.rent # to double the rent if the owner has a full color set
            return rent
        else:
            return special_rent

    def set_owner(self, owner):
        self.owner = owner

    def remove_owner(self):
        self.owner = None

    def get_color(self):
        return self.color

    def mortgage(self):
        self.owner.num_of_mortgaged = len([p for p in self.owner.properties if p.is_mortgaged])
        if self.is_owned() and not self.is_mortgaged:
            self.is_mortgaged = True
            self.owner.receive(self.mortgage_value)

    def unmortgage(self):
        self.owner.num_of_mortgaged = len([p for p in self.owner.properties if p.is_mortgaged])
        if self.is_mortgaged and self.owner is not None:
            self.is_mortgaged = False
            self.owner.pay(int(self.mortgage_value*1.1) , None)
    def get_house_rent(self):
        return self.num_houses * self.rent

    def get_hotel_rent(self):
        return self.num_hotels * self.rent * 5

    def can_build_house(self):
        return self.is_owned() and self.num_houses < Property.MAX_HOUSES and self.num_hotels == 0 and self.has_full_color_set()

    def can_build_hotel(self):
        return self.is_owned() and self.num_houses == Property.MAX_HOUSES and self.num_hotels < Property.MAX_HOTELS and self.has_full_color_set()

    def build_house(self):
        if self.can_build_house():
            self.owner.pay(self.price / 2, None)
            self.num_houses += 1
            #self.update_rent()

    def build_hotel(self):
        if self.can_build_hotel():
            self.owner.pay(self.price / 2, None)
            self.num_houses = 0
            self.num_hotels = 1
            #self.update_rent()

    def has_full_color_set(self):
        if self.color is None:
            return True
        properties = self.owner.properties
        color_properties = [p for p in properties if p.color == self.color]
        return len(color_properties) == len(MONOPOLY_PROPERTIES_BY_COLOR[self.color])

    # def update_rent(self):
    #     self.rent = MONOPOLY_RENT[self.color][self.num_houses][self.num_hotels]

    def get_special_rent(self):
        if not self.is_owned():
            return 0
        if self.name == "Electric Company" or "Water Works":
            num_owned = len(
                [p for p in self.owner.properties if p.name == "Electric Company" or p.name == "Water Works"])
            return 4 * self.owner.last_roll if num_owned == 2 else 10 * self.owner.last_roll
        else:
            return 0

class Board:

    def __init__(self):
        self.spaces = []
        self.chance_places = [6, 20, 32]
        self.community_chest_places = [2, 15, 30]
        self.jail_position = 9
        self.income_tax_position = 4
        self.luxury_tax_position = 34
        self.acu_position = 27
        self.free_parking_position = 18
        self.get_out_of_jail_cards = []
        self.initialize_spaces()
        self.chance_deck = None
        self.community_chest_deck = None
        self.NUM_SPACES = 40

    def __len__(self):
        return self.NUM_SPACES

    def initialize_spaces(self):
        self.spaces = [Property("Go", 200, 0, 0),
                       Property("Syria", 60, 2, 1, "brown"),
                       Property("Community Chest", 0, 0, 2),
                       Property("El Khartoum", 60, 4, 3, "Brown"),
                       Property("Income Tax", 200, 0, 4),
                       Property("Beirut", 100, 6, 5, "light blue"),
                       Property("Chance", 0, 0, 6),
                       Property("El Reyad", 100, 6, 7, "light blue"),
                       Property("Baghdad", 120, 8, 8, "light blue"),
                       Property("Jail", 0, 0, 9),
                       Property("Beni Ghazi", 140, 10, 10, "pink"),
                       Property("Electric Company", 150, 0, 11, "utility"),
                       Property("Adan", 140, 10, 12, "pink"),
                       Property("Jeddah", 160, 12, 13, "pink"),
                       Property("Casablanca", 180, 14, 14, "orange"),
                       Property("Community Chest", 0, 0, 15),
                       Property("Tunise", 180, 14, 16, "orange"),
                       Property("Algerie", 200, 16, 17, "orange"),
                       Property("Free Parking", 0, 0, 18),
                       Property("Alexandria", 220, 18, 19, "red"),
                       Property("Chance", 0, 0, 20),
                       Property("Abu Dhabi", 220, 18, 21, "red"),
                       Property("Dubai", 240, 20, 22, "red"),
                       Property("Yemen", 260, 22, 23, "yellow"),
                       Property("Aswan", 260, 22, 24, "yellow"),
                       Property("Water Works", 150, 0, 25, "utility"),
                       Property("Ghaza", 280, 24, 26, "yellow"),
                       Property("ACU", 0, 0, 27),
                       Property("Al Ain", 300, 26, 28, "green"),
                       Property("Bahrain", 300, 26, 29, "green"),
                       Property("Community Chest", 0, 0, 30),
                       Property("Oman", 320, 28, 31, "green"),
                       Property("Chance", 0, 0, 32),
                       Property("Qatar", 350, 35, 33, "blue"),
                       Property("Luxury Tax", 100, 0, 34),
                       Property("Kuwait", 400, 50, 35, "blue")]

        self.jail_position = 9
        self.get_out_of_jail_cards = [GetOutOfJailCard() for _ in range(0, 4)]

    def get_space(self, position):
        return self.spaces[position]

    def get_jail_position(self):
        return self.jail_position

    def buy_get_out_of_jail_card(self):
        if len(self.get_out_of_jail_cards) > 0:
            return self.get_out_of_jail_cards.pop()
        else:
            return None

    def return_get_out_of_jail_card(self, card):
        self.get_out_of_jail_cards.append(card)

    def community_chest_card(self, player):
        card = self.community_chest_deck.draw_card()
        card.perform_action(player)
        if not isinstance(card, GetOutOfJailCard):
            self.community_chest_deck.used_cards.append(card)

    def chance_card(self, player):
        card = self.chance_deck.draw_card()
        card.perform_action(player)
        if not isinstance(card, GetOutOfJailCard):
            self.chance_deck.used_cards.append(card)

    def get_space_position(self, space_name):
        for i in range(len(self.spaces)):
            if self.spaces[i].name == space_name:
                return i
        return None

    def advance_to_property(self, player, property_name):
        current_position = player.position
        target_position = self.get_space_position(property_name)
        if target_position < current_position:
            player.receive(200)
        player.position = target_position

class Card:
    def __init__(self, text, action=None , value=0):
        self.text = text
        self.action = action
        self.value = value

    def __str__(self):
        return self.text

    def execute(self, player):
        if self.action is not None:
            self.action(player , self.value)

class Deck:
    def __init__(self, cards):
        self.cards = cards
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        card = self.cards.pop(0)
        self.cards.append(card)
        return card

class GetOutOfJailCard:
    def __init__(self):
        self.is_used = False

    def __str__(self):
        return "Get Out of Jail Free"

    def use(self):
        self.is_used = True


# ============ Global variable ==========
can_roll = True
go_right = go_up = go_left = go_down = False
n =0
my_board = Board()
my_board.initialize_spaces()
player1 = Player("Player1" , my_board , -0.96, -0.92)
player2 = Player("player2" , my_board , -0.90, -0.86)
p1_tm, p1_cities, p1_markets, p1_rests, p1_garage = player1.balance, len(player1.properties), 0, 0, 0
p2_tm, p2_cities, p2_markets, p2_rests, p2_garage = player2.balance, len(player2.properties), 0, 0, 0
City="Go"
player = True
current_player = player2

# =============== text ===========

index=0

def render_text(text, x, y):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ctypes.c_int(ord(ch)))

def DiplayInformation():
    global player
    if player == False:
       # Render Player One requirment text
        glColor3f(0.0, 0.0, 1.0)
        render_text("Player Two", 0.55, -0.71)
        render_text("Total Money: "+str(player2.balance), 0.55, -0.64)
        render_text("Cities: "+str(len(player2.properties)), 0.55, -0.77)
       # render_text("Markets: "+str(p2_markets), )
       # render_text("Rests: "+str(p2_rests), )
       # render_text("Garage: "+str(p2_garage), )
    elif player == True:
        # Render Player One requirment text
        glColor3f(1.0, 0, 0.0)
        render_text("Player One",  0.55, -0.71)
        render_text("Total Money: "+str(player1.balance), 0.55, -0.64)
        render_text("Cities: "+str(len(player1.properties)),0.55, -0.77)
        #render_text("Markets: "+str(p1_markets), 0.55, -0.64)
        #render_text("Rests: "+str(p1_rests), 0.55, -0.71)
        #render_text("Garage: "+str(p1_garage), 0.55, -0.77)

#=================== put image from ChatGpt Code ==================



# initialize PyOpenGL
# def draw_logo():
#         screen_width = glutGet(GLUT_SCREEN_WIDTH)
#         screen_height = glutGet(GLUT_SCREEN_HEIGHT)
#         x = (screen_width - 1920) // 2
#         y = (screen_height - 1080) // 2
#         image = Image.open("1.png")
#         image_data = image.tobytes("raw", "RGBX", 0, -1)
#         # create a texture and bind it to the image data
#         texture = glGenTextures(1)
#         glBindTexture(GL_TEXTURE_2D, texture)
#         glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
#         glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
#         glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
#         # set up OpenGL
#         glMatrixMode(GL_PROJECTION)
#         glLoadIdentity()
#         gluPerspective(45, (1920/1080), 0.1, 50.0)
#         glMatrixMode(GL_MODELVIEW)
#
#         # set the position of the image
#         x = (1920 - image.width) / 2
#         y = (1080 - image.height)/ 2
#
#         # draw the image
#         glTranslatef(x, y, -5.0)
#         glBindTexture(GL_TEXTURE_2D, texture)
#         glBegin(GL_QUADS)
#         glTexCoord2f(0.0, 0.0); glVertex3f(0.0, 0.0, 0.0)
#         glTexCoord2f(0.0, 1.0); glVertex3f(0.0, image.height, 0.0)
#         glTexCoord2f(1.0, 1.0); glVertex3f(image.width, image.height, 0.0)
#         glTexCoord2f(1.0, 0.0); glVertex3f(image.width, 0.0, 0.0)
#         glEnd()
#
#
#
#
#


# ============== Dice =============


def Cube(y_top, y_bottom, x_left, x_right):
    glColor3f(0.8, 0.8, 0.8)
    glBegin(GL_QUADS)
    glVertex2f(x_right, y_top)
    glVertex2f(x_right, y_bottom)
    glVertex2f(x_left, y_bottom)
    glVertex2f(x_left, y_top)
    glEnd()
    glColor3f(0.5, 0.5, 0.5)
    glBegin(GL_QUADS)
    glVertex2f(x_right, y_top)
    glVertex2f(x_right, y_bottom)
    glVertex2f(x_right+0.01, y_bottom+0.01)
    glVertex2f(x_right+0.01, y_top+0.01)
    glEnd()
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glVertex2f(x_right, y_top)
    glVertex2f(x_right+0.01, y_top+0.01)
    glVertex2f(x_left + 0.01, y_top+0.01)
    glVertex2f(x_left, y_top)
    glEnd()


def draw_point(x, y):
    glPointSize(5.0)  # set point size
    glBegin(GL_POINTS)
    glVertex2f(x, y)  # draw the point
    glEnd()


def point1_1():
    glColor3f(0, 0, 0)
    draw_point(-0.08625, -0.71)
    glutSwapBuffers()


def point1_2():
    glColor3f(0, 0, 0)
    draw_point(-0.079, -0.73)
    draw_point(-0.1025, -0.69)
    glutSwapBuffers()


def point1_3():
    glColor3f(0, 0, 0)
    draw_point(-0.07, -0.73)
    draw_point(-0.08625, -0.71)
    draw_point(-0.1025, -0.69)
    glutSwapBuffers()


def point1_4():
    glColor3f(0, 0, 0)
    draw_point(-0.07, -0.73)
    draw_point(-0.07, -0.69)
    draw_point(-0.1025, -0.73)
    draw_point(-0.1025, -0.69)
    glutSwapBuffers()


def point1_5():
    glColor3f(0, 0, 0)
    draw_point(-0.07, -0.73)
    draw_point(-0.07, -0.69)
    draw_point(-0.08625, -0.71)
    draw_point(-0.1025, -0.73)
    draw_point(-0.1025, -0.69)
    glutSwapBuffers()


def point1_6():
    glColor3f(0, 0, 0)
    draw_point(-0.07, -0.73)
    draw_point(-0.07, -0.71)
    draw_point(-0.07, -0.69)
    draw_point(-0.1025, -0.73)
    draw_point(-0.1025, -0.71)
    draw_point(-0.1025, -0.69)
    glutSwapBuffers()
# ======== player 2 dice point =================


def point2_1():
    glColor3f(0, 0, 0)
    draw_point(0.03375, -0.71)
    glutSwapBuffers()
# draw_point(0.03375, -0.71) mid


def point2_2():
    glColor3f(0, 0, 0)
    draw_point(0.01475, -0.73)
    draw_point(0.05375, -0.69)
    glutSwapBuffers()


def point2_3():
    glColor3f(0, 0, 0)
    draw_point(0.01475, -0.73)
    draw_point(0.03375, -0.71)
    draw_point(0.05375, -0.69)
    glutSwapBuffers()


def point2_4():
    glColor3f(0, 0, 0)
    draw_point(0.01475, -0.73)
    draw_point(0.01475, -0.69)
    draw_point(0.05375, -0.73)
    draw_point(0.05375, -0.69)
    glutSwapBuffers()


def point2_5():
    glColor3f(0, 0, 0)
    draw_point(0.01475, -0.73)
    draw_point(0.01475, -0.69)
    draw_point(0.03375, -0.71)
    draw_point(0.05375, -0.73)
    draw_point(0.05375, -0.69)
    glutSwapBuffers()


def point2_6():
    glColor3f(0, 0, 0)
    draw_point(0.01475, -0.73)
    draw_point(0.01475, -0.71)
    draw_point(0.01475, -0.69)
    draw_point(0.05375, -0.73)
    draw_point(0.05375, -0.71)
    draw_point(0.05375, -0.69)
    glutSwapBuffers()

def dice_loop():
        global player
        if player == True:
            for i in range(3):
                point1_1()
                time.sleep(0.09)
                draw_background()
                point1_2()
                draw_background()
                time.sleep(0.09)
                draw_background()
                point1_3()
                time.sleep(0.09)
                draw_background()
                point1_4()
                time.sleep(0.09)
                draw_background()
                point1_5()
                time.sleep(0.09)
                draw_background()
                point1_6()
                time.sleep(0.09)
                draw_background()
        elif player == False:
            for i in range(3):
                point2_1()
                time.sleep(0.09)
                draw_background()
                point2_2()
                draw_background()
                time.sleep(0.09)
                draw_background()
                point2_3()
                time.sleep(0.09)
                draw_background()
                point2_4()
                time.sleep(0.09)
                draw_background()
                point2_5()
                time.sleep(0.09)
                draw_background()
                point2_6()
                time.sleep(0.09)
                draw_background()



#========================================================


# def community_chest():
#     global selected
#     glColor3f(0.2, 0.2, 0.2)
#     word_list = ['HBD_take_50$','recieve_200$_from_bank', 'recive 100$ from another player']
#     index = [0, 1, 2]
#     selectd = random.choice(index)
#     j = word_list[selected]
#     easygui.msgbox(selected)
#     return selected


# def chance():
#     global selected
#     word_list = ['pay 100 $ for the bank', 'pay 100 $ for Another play', 'pay 50 $ for another player']
#     index =[0,1,2]
#     selectd = random.choice(index)
#     j = word_list[selected]
#     easygui.msgbox(selected)
#     return selected



def chance_square():
    glColor3f(251 / 256, 144 / 256, 32 / 256)
    glBegin(GL_QUADS)
    glVertex2f(-0.75, -0.4)
    glVertex2f(-0.5, -0.75)
    glVertex2f(-0.3, -0.5)
    glVertex2f(-0.55, -0.15)
    glEnd()


def community_chest_square():
    glColor3f(0.33, 0.79, 0.98)
    glBegin(GL_QUADS)
    glVertex2f(0.75, 0.4)
    glVertex2f(0.5, 0.75)
    glVertex2f(0.3, 0.5)
    glVertex2f(0.55, 0.15)
    glEnd()

def after_the_move():
    global my_board , p1 , player
    current_property = my_board.get_space(p1.position)
    if p1.position in my_board.chance_places:
        word_list = ['HBD_take_50$','recieve_200$_from_bank', 'recive 100$ from another player']
        random_select=random.randint(0,2)
        if random_select == 0:
            easygui.msgbox(word_list[0])
            p1.receive(50)
        elif random_select == 1:
            easygui.msgbox(word_list[1])
            p1.receive(200)
        elif random_select == 2:
            easygui.msgbox(word_list[2])
            if player:
                player2.pay(100, p1)
            else:
                player1.pay(100,player2)
    elif p1.position in my_board.community_chest_places :
        word_list = ['pay 100 $ for the bank', 'pay 100 $ for Another play', 'pay 50 $ for another player']
        random_select=random.randint(0,2)

        if random_select == 0:
            easygui.msgbox(word_list[0])
            p1.pay(100,None)
        elif random_select == 1:
            easygui.msgbox(word_list[1])
            if player:
                p1.pay(100, player2)
            else:
                player2.pay(100, player1)
        elif random_select == 2:
            easygui.msgbox(word_list[2])
            if player:
                p1.pay(50, player2)
            else:
                player2.pay(50, player1)

    elif p1.position == my_board.jail_position:
        p1.go_to_jail()
    elif p1.position == 0:
        pass
    elif p1.position == my_board.free_parking_position:
        pass
    elif p1.position == my_board.luxury_tax_position:
        p1.pay(100 , None)
    elif p1.position == my_board.income_tax_position:
        p1.pay(200 , None)
    elif p1.position == my_board.acu_position:
        if player:
            p1.pay(201 , player2)
        else:
            p1.pay(201,player1)
    elif current_property.is_owned() and current_property.owner != p1:
        p1.pay(current_property.get_rent(), current_property.owner)
    elif not current_property.is_owned() and p1.can_afford(current_property.price):
        result = easygui.buttonbox("If you want to buy this property", title="Unowned property", choices=["Buy", "Dont Buy"])
        # check which button was clicked
        if result == "Buy":
            p1.buy_property(current_property)
            DiplayInformation()
        else :
            pass
    else:
        pass


    # easygui.msgbox(p1.position, title="Unowned property")
    # p1.pay(100)
p1 = player1
def keyboard(key, x, y):
    global player , n,index , current_player , player1 , player2,p1 , can_roll
    if key == b'i':
        msg = "Press '1'  ==>  player one roll dice\n" \
              "Press '2'  ==>  player two roll dice\n" \
              "Press 'e'  ==>  end round\n" \
              "Press 'm'  ==>  mortage\n" \
              "Press 'n'  ==>  negotiate\n" \
              "Press 'p'  ==>  properties\n" \
              "Press 'r'  ==>  refresh scene\n" \
              "Press 'esc' ==> exit program "
        easygui.msgbox(msg, title="Instructions")

    if key == b'r':
        glutSwapBuffers()
    global player, my_board
    randomnum = 0
    if key == b'p':
        if player:
            easygui.msgbox("your properties \n" + player1.show_properties(), title="Player 1")
        elif not player:
            easygui.msgbox("your properties \n" + player2.show_properties(), title="Player 2")

    if key == b'1':

        if player and can_roll:
            p1=player1
            if p1.in_jail :
                response = easygui.buttonbox("Would you like to pay 50 to get out of jail?", title="Player 1", choices=["Yes", "No"])
                if response == "Yes":
                    p1.pay(50 , None)
                    p1.leave_jail()
                elif response == "No":
                    p1.in_jail_turns()
                    can_roll = False
            if not p1.in_jail:
                randomnum = random.randint(1, 6)
                p1.move(randomnum)

                dice_loop()
                if randomnum == 1:
                    point1_1()
                elif randomnum == 2:
                    point1_2()
                elif randomnum == 3:
                    point1_3()
                elif randomnum == 4:
                    point1_4()
                elif randomnum == 5:
                    point1_5()
                elif randomnum == 6:
                    point1_6()
                time.sleep(2)
                glClear(GL_COLOR_BUFFER_BIT)
                player_move(p1, randomnum)

                draw_background()
                glutSwapBuffers()
                glClear(GL_COLOR_BUFFER_BIT)

                after_the_move()
                player1 = p1
                can_roll = False
    elif key == b'2':
        if not player and can_roll:
            p1 = player2
            if p1.in_jail :
                response = easygui.buttonbox("Would you like to pay 50 to get out of jail?", title="Player 2", choices=["Yes", "No"])
                if response == "Yes":
                    p1.pay(50 , None)
                    p1.leave_jail()
                elif response == "No":
                    p1.in_jail_turns()
                    can_roll = False
            if not p1.in_jail:
                randomnum = random.randint(1, 6)
                p1.move(randomnum)

                dice_loop()
                if randomnum == 1:
                    point2_1()
                elif randomnum == 2:
                    point2_2()
                elif randomnum == 3:
                    point2_3()
                elif randomnum == 4:
                    point2_4()
                elif randomnum == 5:
                    point2_5()
                elif randomnum == 6:
                    point2_6()
                time.sleep(2)
                glClear(GL_COLOR_BUFFER_BIT)
                player_move(p1, randomnum)

                draw_background()
                glutSwapBuffers()
                glClear(GL_COLOR_BUFFER_BIT)
                after_the_move()
                player2 = p1
                can_roll = False

    elif key == b'\x1b':  # Escape key
        glutLeaveMainLoop()

    elif key == b'n':
        if player:
            prop_number = int(easygui.enterbox(player2.show_properties() + "\nchoose the property number", title="Player 1",default="1"))
            if prop_number <= len(player2.properties):
                offered_price = int(easygui.enterbox("Enter offered price", title="Player 1"))
                message = "Do you accept to give "+player2.properties[prop_number-1].name + " for "+str(offered_price)+"to the other player"
                response = easygui.buttonbox(message, title="Player 2", choices=["Accept", "Reject"])
                if response == "Accept":
                    player1.pay(offered_price,player2)
                    prop = player2.properties[prop_number-1]
                    prop.remove_owner()
                    prop.set_owner(player1)
                    player2.properties.pop(prop_number-1)
                    player1.add_property(prop)
                else:
                    pass
            else:
                easygui.msgbox("Invalid input", title = "Wrong input")

        elif not player:
            prop_number = int(easygui.enterbox(player1.show_properties() + "\nchoose the property number",title="Player 2"))
            if prop_number <= len(player1.properties):
                offered_price = int(easygui.enterbox("Enter offered price", title="Player 2"))
                message = "Do you accept to give " + player1.properties[prop_number - 1].name + " for " + str(
                    offered_price) + " to the other player"
                response = easygui.buttonbox(message, title="Player 1", choices=["Accept", "Reject"])
                if response == "Accept":
                    player2.pay(offered_price, player1)
                    prop = player1.properties[prop_number - 1]
                    prop.remove_owner()
                    prop.set_owner(player2)
                    player1.properties.pop(prop_number - 1)
                    player2.add_property(prop)
                else:
                    pass
            else:
                easygui.msgbox("Invalid input", title="Wrong input")
    elif key == b'm':
        if player:
            response = easygui.buttonbox("do you want to mortgage or unmortgage", title="Player 1", choices=["mortgage", "Unmortgage"])
            if response == "mortgage" and not len(player1.properties)-player1.num_of_mortgaged == 0:
                prop_number = int(easygui.enterbox(player1.show_unmortgaged_properties()+"\nchoose the property number you want to mortgage",title="Player 1"))
                if prop_number <= len(player1.properties):
                    prop = player1.properties[prop_number-1]
                    prop.mortgage()
                else:
                    easygui.msgbox("Invalid input", title = "Wrong input")
            elif response == "Unmortgage" and not player1.num_of_mortgaged == 0:
                prop_number = int(easygui.enterbox(player1.show_mortgaged_properties() + "\nchoose the property number you want to mortgage",title="Player 1"))
                if prop_number <= len(player1.properties):
                    prop = player1.properties[prop_number - 1]
                    if player1.can_afford(prop.mortgage_value * 1.1):
                        prop.unmortgage()
                    else :
                        easygui.msgbox("you haven't enough balance")
                else:
                    easygui.msgbox("Invalid input", title="Wrong input")
            else:
                pass
        elif not player:
            response = easygui.buttonbox("do you want to mortgage or unmortgage", title="Player 2",
                                         choices=["mortgage", "Unmortgage"])
            if response == "mortgage" and not len(player2.properties)-player2.num_of_mortgaged == 0:
                prop_number = int(easygui.enterbox(
                    player2.show_unmortgaged_properties() + "\nchoose the property number you want to mortgage",
                    title="Player 2"))
                if prop_number <= len(player2.properties):
                    prop = player2.properties[prop_number - 1]
                    prop.mortgage()
                else:
                    easygui.msgbox("Invalid input", title="Wrong input")
            elif response == "Unmortgage" and not player2.num_of_mortgaged == 0:
                prop_number = int(easygui.enterbox(
                    player2.show_mortgaged_properties() + "\nchoose the property number you want to mortgage",
                    title="Player 2"))
                if prop_number <= len(player2.properties):
                    prop = player2.properties[prop_number - 1]
                    if player2.can_afford(prop.mortgage_value * 1.1):
                        prop.unmortgage()
                    else:
                        easygui.msgbox("you haven't enough balance")
                else:
                    easygui.msgbox("Invalid input", title="Wrong input")
            else:
                pass
    elif key == b'e':
        if player:
            if p1.balance<0 and p1.get_net_worth()<=0:
                easygui.msgbox("Hard luck 😪")
                time.sleep(5)
                glutLeaveMainLoop()
            elif p1.balance<0 and not p1.get_net_worth()<=0:
                easygui.msgbox("can't end round with a negative balance , mortgage properties to play")
            else:
                player = False
                can_roll = True

        else:
            if p1.balance < 0 and p1.get_net_worth() <= 0:
                easygui.msgbox("Hard luck 😪")
                time.sleep(5)
                glutLeaveMainLoop()
            elif p1.balance < 0 and not p1.get_net_worth() <= 0:
                easygui.msgbox("can't end round with a negative balance , mortgage properties to play")
            else:
                player = True
                can_roll = True
    #glutSwapBuffers()
    glutPostRedisplay()
    current_player = player1

def draw_bordered_background(r, g, b, y_top, y_bottom, x_left, x_right):
    # Draw rectangle to the right of first quad
    glBegin(GL_QUADS)
    glColor3f(r, g, b)
    glVertex2f(x_right, y_top)
    glVertex2f(x_left, y_top)
    glVertex2f(x_left, y_bottom)
    glVertex2f(x_right, y_bottom)
    glEnd()
    # border of the first
    glBegin(GL_LINE_LOOP)
    glColor3f(0.0, 0.0, 0.0)
    glVertex2f(x_right, y_top)
    glVertex2f(x_left, y_top)
    glVertex2f(x_left, y_bottom)
    glVertex2f(x_right, y_bottom)
    glEnd()


def draw_rectangles_with_text():
    # Draw rectangles on the left side
    list1 = ['GO', 'Syria\n60', 'Community Chest', 'El Khartoum\n60',
             'Tax Income\npay 200', 'Beirut\n100', 'Chance', 'El Reyad\n100', 'Baghdad\n120']
    for i, j in zip(range(9), list1):
        glBegin(GL_QUADS)
        glColor3f(0.9, 0.9, 0.7)
        glVertex2f(-1, -0.8 + 0.2 * i)
        glVertex2f(-0.8, -0.8 + 0.2 * i)
        glVertex2f(-0.8, -1 + 0.2 * i)
        glVertex2f(-1, -1 + 0.2 * i)
        glEnd()

        # Draw the word from list1 inside the quad
        glColor3f(0.2, 0.2, 0.2)
        glRasterPos2f(-0.99, -0.9 + 0.2 * i)
        glutBitmapString(GLUT_BITMAP_HELVETICA_18, j.encode())

    # Draw rectangles on the right side
    list2 = ['eygpt', 'Ghaza\n280', 'Water works\n150', 'Aswan\n260',
             'Yemen\n260', 'Dubai\n240', 'Abu Dhabi\n220', 'Chance', 'Alexandria\n220']
    for i, j in zip(range(9), list2):
        glBegin(GL_QUADS)
        glColor3f(0.9, 0.9, 0.7)
        glVertex2f(0.8, -0.8 + 0.2 * i)
        glVertex2f(1, -0.8 + 0.2 * i)
        glVertex2f(1, -1 + 0.2 * i)
        glVertex2f(0.8, -1 + 0.2 * i)
        glEnd()

        # Draw the word from list2 inside the quad
        glColor3f(0.2, 0.2, 0.2)
        glRasterPos2f(0.85, -0.9 + 0.2 * i)
        glutBitmapString(GLUT_BITMAP_HELVETICA_18, j.encode())

    # Draw rectangles on the top side
    list3 = ['Beni Ghazi\n140', 'Electric comp.\n150', 'Adan\n140', 'Jeddah\n160',
             'Casablanca\n180', 'Community \nchest', 'Tunis\n180', ' Algerie\n200', 'Free Parking']
    for i, j in zip(range(9), list3):
        glBegin(GL_QUADS)
        glColor3f(0.9, 0.9, 0.7)
        glVertex2f(-0.8 + 0.2 * i, 0.8)
        glVertex2f(-0.6 + 0.2 * i, 0.8)
        glVertex2f(-0.6 + 0.2 * i, 1)
        glVertex2f(-0.8 + 0.2 * i, 1)
        glEnd()

        # Draw the word from list3 inside the quad
        glColor3f(0.2, 0.2, 0.2)
        glRasterPos2f(-0.75 + 0.2 * i, 0.95)
        glutBitmapString(GLUT_BITMAP_HELVETICA_18, j.encode())

    # Draw rectangles on the bottom side
    list4 = ['Kuwait\n400', 'Luxury Tax\npay 100', 'Qatar\n350', 'Chance', 'Oman\n320',
             'Community \nChest', 'Bahrain\n300', 'Al Ain\n300', '']
    for i, j in zip(range(9), list4):
        glBegin(GL_QUADS)
        glColor3f(0.9, 0.9, 0.7)
        glVertex2f(-0.8 + 0.2 * i, -1)
        glVertex2f(-0.6 + 0.2 * i, -1)
        glVertex2f(-0.6 + 0.2 * i, -0.8)
        glVertex2f(-0.8 + 0.2 * i, -0.8)
        glEnd()

        # Draw the word from list4 inside the quad
        glColor3f(0.2, 0.2, 0.2)
        glRasterPos2f(-0.75 + 0.2 * i, -0.95)
        glutBitmapString(GLUT_BITMAP_HELVETICA_18, j.encode())
    glBegin(GL_QUADS)
    glColor3f(0.9, 0.9, 0.7)
    glVertex2f(-1, 0.8)
    glVertex2f(-0.8, 0.8)
    glVertex2f(-0.8, 1)
    glVertex2f(-1, 1)
    glEnd()
    glColor3f(0.2, 0.2, 0.2)
    glRasterPos2f(-0.95, 0.95)
    glutBitmapString(GLUT_BITMAP_HELVETICA_18, "Jail".encode())
    glRasterPos2f(0.81, -0.85)
    glutBitmapString(GLUT_BITMAP_HELVETICA_18, "Ahram Canadian\nUniversity\npay 201".encode())
    # Draw black borders around rectangles
    glLineWidth(2.0)
    glColor3f(0, 0, 0)
    for i in range(9):
        glBegin(GL_LINE_LOOP)
        glVertex2f(-1, -0.8 + 0.2 * i)
        glVertex2f(-0.8, -0.8 + 0.2 * i)
        glVertex2f(-0.8, -1 + 0.2 * i)
        glVertex2f(-1, -1 + 0.2 * i)
        glEnd()

    for i in range(9):
        glBegin(GL_LINE_LOOP)
        glVertex2f(0.8, -0.8 + 0.2 * i)
        glVertex2f(1, -0.8 + 0.2 * i)
        glVertex2f(1, -1 + 0.2 * i)
        glVertex2f(0.8, -1 + 0.2 * i)
        glEnd()

    for i in range(9):
        glBegin(GL_LINE_LOOP)
        glVertex2f(-0.8 + 0.2 * i, 0.8)
        glVertex2f(-0.6 + 0.2 * i, 0.8)
        glVertex2f(-0.6 + 0.2 * i, 1)
        glVertex2f(-0.8 + 0.2 * i, 1)
        glEnd()

    for i in range(9):
        glBegin(GL_LINE_LOOP)
        glVertex2f(-0.8 + 0.2 * i, -1)
        glVertex2f(-0.6 + 0.2 * i, -1)
        glVertex2f(-0.6 + 0.2 * i, -0.8)
        glVertex2f(-0.8 + 0.2 * i, -0.8)
        glEnd()

#=============Movement====================
def draw_player_piece(y_top, y_bottom, x_right, x_left):

    glBegin(GL_TRIANGLES)
    glVertex2f((x_left +  x_right) / 2, y_top)
    glVertex2f( x_left,  y_bottom)
    glVertex2f( x_right,  y_bottom)
    glEnd()

def draw_players():
    global player1 , player2
    glColor3f(1, 0, 0)
    draw_player_piece(player1.y_top, player1.y_bottom, player1.x_right, player1.x_left)
    glColor3f(0, 0, 1)
    draw_player_piece(player2.y_top, player2.y_bottom, player2.x_right, player2.x_left)


def player_move(pll,rn):
    global n
    current_player = pll
    for i in range (rn):
        if current_player.go_up and not current_player.y_top > 0.8:
            current_player.y_top += 0.2
            current_player.y_bottom += 0.2
        elif current_player.go_down and not current_player.y_bottom < -0.8:
            current_player.y_top -= 0.2
            current_player.y_bottom -= 0.2
        elif current_player.go_right and not current_player.x_right > 0.8:
            current_player.x_right += 0.2
            current_player.x_left += 0.2
        elif current_player.go_down and not current_player.x_left < -0.8:
            current_player.x_right -= 0.2
            current_player.x_left -= 0.2
        elif current_player.x_left < -0.8 and current_player.y_top > 0.8:
            current_player.x_right += 0.2
            current_player.x_left += 0.2
            current_player.go_up = current_player.go_left = current_player.go_down = False
            current_player.go_right = True
        elif current_player.x_left > 0.8 and current_player.y_top > 0.8:
            current_player.y_top -= 0.2
            current_player.y_bottom -= 0.2
            current_player.go_right = current_player.go_left = current_player.go_up = False
            current_player.go_down = True
        elif current_player.x_left > 0.8 and current_player.y_top < -0.8:
            current_player.x_right -= 0.2
            current_player.x_left -= 0.2
            current_player.go_right = current_player.go_up = current_player.go_down = False
            current_player.go_left = True
        elif current_player.x_left < -0.8 and current_player.y_top < -0.8:
            current_player.y_top += 0.2
            current_player.y_bottom += 0.2
            current_player.go_right = current_player.go_left = current_player.go_down = False
            current_player.go_up = True
            current_player.balance+=200

def draw_small_rectangle():
    # brown properties
    draw_bordered_background(150 / 256, 84 / 256, 54 / 256, -0.6, -0.8, -0.84, -0.8)
    draw_bordered_background(150 / 256, 84 / 256, 54 / 256, -0.2, -0.4, -0.84, -0.8)
    # sky blue properties
    draw_bordered_background(171 / 256, 224 / 256, 249 / 256, 0.2, 0, -0.84, -0.8)
    draw_bordered_background(171 / 256, 224 / 256, 249 / 256, 0.6, 0.4, -0.84, -0.8)
    draw_bordered_background(171 / 256, 224 / 256, 249 / 256, 0.8, 0.6, -0.84, -0.8)
    # pink properties
    draw_bordered_background(217 / 256, 59 / 256, 151 / 256, 0.84, 0.8, -0.8, -0.6)
    draw_bordered_background(217 / 256, 59 / 256, 151 / 256, 0.84, 0.8, -0.4, -0.2)
    draw_bordered_background(217 / 256, 59 / 256, 151 / 256, 0.84, 0.8, -0.2, 0)
    # orange properties
    draw_bordered_background(246 / 256, 149 / 256, 29 / 256, 0.84, 0.8, 0, 0.2)
    draw_bordered_background(246 / 256, 149 / 256,
                             29 / 256, 0.84, 0.8, 0.4, 0.6)
    draw_bordered_background(246 / 256, 149 / 256,
                             29 / 256, 0.84, 0.8, 0.6, 0.8)
    # red properties
    draw_bordered_background(
        236 / 256, 27 / 256, 36 / 256, 0.8, 0.6, 0.8, 0.84)
    draw_bordered_background(
        236 / 256, 27 / 256, 36 / 256, 0.4, 0.2, 0.8, 0.84)
    draw_bordered_background(236 / 256, 27 / 256, 36 / 256, 0.2, 0, 0.8, 0.84)
    # yellow properties
    draw_bordered_background(254 / 256, 241 / 256, 0, 0, -0.2, 0.8, 0.84)
    draw_bordered_background(254 / 256, 241 / 256, 0, -0.2, -0.4, 0.8, 0.84)
    draw_bordered_background(254 / 256, 241 / 256, 0, -0.6, -0.8, 0.8, 0.84)
    # green properties
    draw_bordered_background(31 / 256, 177 / 256, 89 /
                             256, -0.8, -0.84, 0.6, 0.8)
    draw_bordered_background(31 / 256, 177 / 256, 89 /
                             256, -0.8, -0.84, 0.4, 0.6)
    draw_bordered_background(
        31 / 256, 177 / 256, 89 / 256, -0.8, -0.84, 0, 0.2)
    # Blue properties
    draw_bordered_background(1 / 256, 114 / 256, 187 /
                             256, -0.8, -0.84, -0.4, -0.2)
    draw_bordered_background(1 / 256, 114 / 256, 187 /
                             256, -0.8, -0.84, -0.8, -0.6)

    # Jail
    draw_bordered_background(246 / 256, 149 / 256,
                             29 / 256, 0.95, 0.8, -0.95, -0.8)
    # inner white square
    glBegin(GL_QUADS)
    glColor3f(1, 1, 1)
    glVertex2f(-0.875, 0.95)
    glVertex2f(-0.95, 0.875)
    glVertex2f(-0.875, 0.8)
    glVertex2f(-0.8, 0.875)
    glEnd()
    glBegin(GL_LINES)
    glColor3f(0, 0, 0)
    glVertex2f(-0.9125, 0.9125)
    glVertex2f(-0.8375, 0.8375)
    glVertex2f(-0.89375, 0.93125)
    glVertex2f(-0.81875, 0.85625)
    glVertex2f(-0.93125, 0.89375)
    glVertex2f(-0.85625, 0.81875)
    glEnd()


def draw_background():

    glClearColor(229 / 255, 229 / 255, 178 / 255, 0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    DiplayInformation()
    draw_rectangles_with_text()
    draw_small_rectangle()
    Cube(-0.65, -0.77, 0, 0.07)
    Cube(-0.65, -0.77, -0.12, -0.05)
    chance_square()
    community_chest_square()
    draw_players()
    #glutSwapBuffers()
def main():

    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutCreateWindow(b"Colored Background with Rectangles")
    glutFullScreen()
    glutDisplayFunc(draw_background)
    glutInitWindowSize(700, 800)
    glutKeyboardFunc(keyboard)
    glutSwapBuffers()
    glutMainLoop()


if __name__ == "__main__":

    main()