from ursina import *
import random
import math
import json
import os
import time

MAX_PLAYERS = 10
WORLD_SIZE = 60
SAVE_FILE = "submarine_save.json"


def build_ship_templates():
    templates = []

    for i in range(1, 43):
        hp = random.randint(70, 120)
        templates.append({
            "id": f"SUB-{i:02d}",
            "name": f"U-{i:02d}",
            "kind": "submarine",
            "hp": hp,
            "max_hp": hp,
            "speed": random.randint(1, 2),
            "damage": random.randint(10, 22),
            "color": color.azure,
            "price": 5000,
        })

    for i in range(1, 9):
        hp = random.randint(120, 190)
        templates.append({
            "id": f"DEST-{i:02d}",
            "name": f"Z-{i:02d}",
            "kind": "destroyer",
            "hp": hp,
            "max_hp": hp,
            "speed": random.randint(2, 3),
            "damage": random.randint(15, 32),
            "color": color.orange,
            "price": 8000,
        })

    return templates


SHIP_TEMPLATES = build_ship_templates()


class Boat(Entity):
    def __init__(self, name, template, is_player=False, position=(0, 0, 0), player_data=None):
        self.name = name
        self.template = template
        self.kind = template["kind"]
        self.hp = template["hp"]
        self.max_hp = template["max_hp"]
        self.speed = template["speed"]
        self.damage = template["damage"]
        self.is_player = is_player
        self.color = template["color"]
        self.alive = True
        self.next_fire = 0
        self.player_data = player_data
        self.uranium = 0

        if self.kind == "submarine":
            model_shape = "cube"
            scale_x = 2.0
            scale_y = 0.8
            scale_z = 1.2
        else:
            model_shape = "cube"
            scale_x = 2.4
            scale_y = 1.0
            scale_z = 1.6

        super().__init__(
            parent=scene,
            model=model_shape,
            color=self.color,
            position=position,
            scale=(scale_x, scale_y, scale_z),
        )

        self.hp_bg = Entity(
            parent=self,
            model='quad',
            color=color.black66,
            scale=(2.4, 0.25, 1),
            position=(0, 1.8, 0),
        )

        self.hp_fill = Entity(
            parent=self,
            model='quad',
            color=color.lime,
            scale=(2.1, 0.15, 1),
            position=(0, 1.8, 0),
        )

        self.uranium_bg = Entity(
            parent=self,
            model='quad',
            color=color.black66,
            scale=(2.4, 0.2, 1),
            position=(0, 1.45, 0),
        )

        self.uranium_fill = Entity(
            parent=self,
            model='quad',
            color=color.yellow,
            scale=(0.1, 0.12, 1),
            position=(0, 1.45, 0),
        )

        self.label = Text(
            text=self.name,
            parent=self,
            origin=(0, 0),
            position=(0, 2.4, 0),
            scale=1.0,
            color=color.white,
        )

        self.ring = Entity(
            parent=self,
            model='circle',
            color=color.rgba(255, 255, 255, 80),
            scale=(0.7, 0.7, 1),
            position=(0, -0.7, 0),
        )

    def update_hp_bar(self):
        if not self.alive:
            return
        ratio = max(0, self.hp / self.max_hp)
        self.hp_fill.scale_x = 2.1 * ratio
        self.hp_fill.x = -1.05 + (2.1 * ratio / 2)

    def update_uranium_bar(self):
        if not self.alive:
            return
        ratio = max(0, self.uranium / 100.0)
        self.uranium_fill.scale_x = 2.1 * ratio
        self.uranium_fill.x = -1.05 + (2.1 * ratio / 2)

    def take_damage(self, damage):
        self.hp -= damage
        self.uranium = min(100, self.uranium + (damage / self.max_hp) * 50)

        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.visible = False
            self.label.text = "GESUNKEN"
            self.label.color = color.red

    def update(self):
        if not self.alive:
            return

        self.update_hp_bar()
        self.update_uranium_bar()
        self.rotation_y += 20 * time.dt

        if self.is_player:
            self.control_player()
        else:
            self.control_bot()

        self.x = clamp(self.x, -WORLD_SIZE / 2, WORLD_SIZE / 2)
        self.z = clamp(self.z, -WORLD_SIZE / 2, WORLD_SIZE / 2)
        self.y = 0.8 + math.sin(time.time() * 2 + self.x) * 0.3

        if time.time() > self.next_fire:
            self.fire_at_nearest()

    def control_player(self):
        speed = self.speed * 3.5

        if held_keys['w']:
            self.z += speed * time.dt
        if held_keys['s']:
            self.z -= speed * time.dt
        if held_keys['a']:
            self.x -= speed * time.dt
        if held_keys['d']:
            self.x += speed * time.dt

        if held_keys['space']:
            self.try_fire()

    def control_bot(self):
        if random.random() < 0.02:
            self.direction = Vec3(
                random.uniform(-1, 1),
                0,
                random.uniform(-1, 1),
            ).normalized()

        if hasattr(self, 'direction'):
            self.x += self.direction.x * self.speed * 2.5 * time.dt
            self.z += self.direction.z * self.speed * 2.5 * time.dt

        if abs(self.x) > WORLD_SIZE / 2 - 5 or abs(self.z) > WORLD_SIZE / 2 - 5:
            self.direction *= -1

    def try_fire(self):
        self.fire_at_nearest()

    def fire_at_nearest(self):
        if time.time() < self.next_fire:
            return

        nearest = None
        nearest_dist = 9999

        for boat in boats:
            if boat is self or not boat.alive:
                continue

            d = distance(self.position, boat.position)
            if d < nearest_dist:
                nearest_dist = d
                nearest = boat

        if nearest and nearest_dist < 12:
            nearest.take_damage(self.damage)
            if not nearest.alive and self.is_player and self.player_data:
                self.player_data["water_coins"] += 3000
            self.next_fire = time.time() + 0.8


class Shop:
    def __init__(self, player_data):
        self.player_data = player_data
        self.panel = None

    def show(self):
        if self.panel:
            destroy(self.panel)
        self.create_shop_ui()

    def hide(self):
        if self.panel:
            destroy(self.panel)
            self.panel = None

    def create_shop_ui(self):
        self.panel = Panel(
            size=(0.6, 0.8),
            position=(-0.7, 0.1),
            color=color.rgba(20, 20, 40, 200),
            border=2,
            border_color=color.cyan,
        )

        Text(
            text="SHOP",
            parent=self.panel,
            position=(0, 0.35),
            scale=1.5,
            color=color.cyan,
        )

        Text(
            text=f"Wasser-Kronen: {self.player_data['water_coins']}",
            parent=self.panel,
            position=(0, 0.28),
            scale=1.0,
            color=color.lime,
        )

        Text(
            text=f"U-Boote: {self.player_data['submarines']} | Zerstörer: {self.player_data['destroyers']}",
            parent=self.panel,
            position=(0, 0.20),
            scale=0.9,
            color=color.white,
        )

        Button(
            text="U-Boot kaufen\n5.000 Kronen",
            parent=self.panel,
            position=(0, 0.05),
            scale=(0.4, 0.08),
            color=color.blue,
            on_click=self.buy_submarine,
        )

        Button(
            text="Zerstörer kaufen\n8.000 Kronen",
            parent=self.panel,
            position=(0, -0.08),
            scale=(0.4, 0.08),
            color=color.orange,
            on_click=self.buy_destroyer,
        )

        Button(
            text="Schließen",
            parent=self.panel,
            position=(0, -0.20),
            scale=(0.4, 0.08),
            color=color.red,
            on_click=self.hide,
        )

    def buy_submarine(self):
        if self.player_data["water_coins"] >= 5000:
            self.player_data["water_coins"] -= 5000
            self.player_data["submarines"] += 1
            print(f"U-Boot gekauft! Neue Anzahl: {self.player_data['submarines']}")
        else:
            print("Nicht genügend Wasser-Kronen!")
        self.create_shop_ui()

    def buy_destroyer(self):
        if self.player_data["water_coins"] >= 8000:
            self.player_data["water_coins"] -= 8000
            self.player_data["destroyers"] += 1
            print(f"Zerstörer gekauft! Neue Anzahl: {self.player_data['destroyers']}")
        else:
            print("Nicht genügend Wasser-Kronen!")
        self.create_shop_ui()


class PauseMenu:
    def __init__(self, game):
        self.game = game
        self.panel = None

    def show(self):
        self.game.paused = True
        self.create_pause_ui()

    def hide(self):
        self.game.paused = False
        if self.panel:
            destroy(self.panel)
            self.panel = None

    def create_pause_ui(self):
        if self.panel:
            destroy(self.panel)

        self.panel = Panel(
            size=(0.5, 0.6),
            position=(0, 0),
            color=color.rgba(20, 20, 40, 220),
            border=3,
            border_color=color.cyan,
        )

        Text(
            text="PAUSIERT",
            parent=self.panel,
            position=(0, 0.25),
            scale=2.0,
            color=color.cyan,
        )

        Button(
            text="Weiterspielen",
            parent=self.panel,
            position=(0, 0.10),
            scale=(0.35, 0.08),
            color=color.green,
            on_click=self.hide,
        )

        Button(
            text="Shop (X)",
            parent=self.panel,
            position=(0, 0.00),
            scale=(0.35, 0.08),
            color=color.blue,
            on_click=self.open_shop,
        )

        Button(
            text="Server Liste",
            parent=self.panel,
            position=(0, -0.10),
            scale=(0.35, 0.08),
            color=color.orange,
            on_click=self.show_servers,
        )

        Button(
            text="Beenden",
            parent=self.panel,
            position=(0, -0.20),
            scale=(0.35, 0.08),
            color=color.red,
            on_click=self.quit_game,
        )

    def open_shop(self):
        self.hide()
        self.game.shop.show()

    def show_servers(self):
        self.hide()
        self.game.show_server_list()

    def quit_game(self):
        self.game.save_game()
        application.quit()


class ServerBrowser:
    def __init__(self, game):
        self.game = game
        self.panel = None
        self.servers = [
            {"name": "Server 1 - Europa", "ip": "127.0.0.1", "port": 5000, "players": 7},
            {"name": "Server 2 - Amerika", "ip": "127.0.0.1", "port": 5001, "players": 5},
            {"name": "Server 3 - Asien", "ip": "127.0.0.1", "port": 5002, "players": 9},
            {"name": "Server 4 - Ozeanien", "ip": "127.0.0.1", "port": 5003, "players": 3},
        ]

    def show(self):
        self.create_browser_ui()

    def hide(self):
        if self.panel:
            destroy(self.panel)
            self.panel = None

    def create_browser_ui(self):
        if self.panel:
            destroy(self.panel)

        self.panel = Panel(
            size=(0.8, 0.9),
            position=(0, 0),
            color=color.rgba(20, 20, 40, 220),
            border=3,
            border_color=color.cyan,
        )

        Text(
            text="SERVER LISTE",
            parent=self.panel,
            position=(0, 0.40),
            scale=1.8,
            color=color.cyan,
        )

        y_pos = 0.30
        for server in self.servers:
            Text(
                text=f"{server['name']} | Spieler: {server['players']}/10",
                parent=self.panel,
                position=(0, y_pos),
                scale=0.9,
                color=color.white,
            )
            Button(
                text="Beitreten",
                parent=self.panel,
                position=(0.25, y_pos - 0.05),
                scale=(0.20, 0.06),
                color=color.green,
                on_click=lambda s=server: self.join_server(s),
            )
            y_pos -= 0.12

        Button(
            text="Zurück",
            parent=self.panel,
            position=(0, -0.40),
            scale=(0.3, 0.08),
            color=color.red,
            on_click=self.back_to_game,
        )

    def join_server(self, server):
        print(f"Verbinde zu: {server['name']} ({server['ip']}:{server['port']})")
        self.hide()
        self.game.pause_menu.show()

    def back_to_game(self):
        self.hide()
        self.game.pause_menu.show()


class Game:
    def __init__(self):
        self.boats = []
        self.player_data = self.load_game()
        self.shop = Shop(self.player_data)
        self.pause_menu = PauseMenu(self)
        self.server_browser = ServerBrowser(self)
        self.paused = False

        self.water = Entity(
            parent=scene,
            model='plane',
            texture='white_cube',
            scale=(WORLD_SIZE, 1, WORLD_SIZE),
            color=color.rgba(25, 80, 150, 180),
            position=(0, 0, 0),
        )

        self.sky = Sky(color=color.rgb(20, 40, 70))
        camera.position = (0, 18, -35)
        camera.rotation_x = 25

        self.spawn_player_fleet()
        self.fill_with_bots()

        self.hud_text = Text(
            text="",
            position=(-0.95, 0.45),
            scale=0.9,
            origin=(-1, 1),
            color=color.white,
        )

        DirectionalLight(y=2, z=2, rotation=(45, -45, 0))

    def load_game(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                return data
        return {
            "water_coins": 15000,
            "submarines": 2,
            "destroyers": 1,
        }

    def save_game(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump(self.player_data, f, indent=2)
        print("[GAME] Spiel gespeichert!")

    def spawn_player_fleet(self):
        for i in range(self.player_data["submarines"]):
            template = next(t for t in SHIP_TEMPLATES if t["kind"] == "submarine")
            x = -8 + i * 4
            boat = Boat(
                f"Spieler-U-Boot {i+1}",
                template,
                is_player=True,
                position=(x, 0.8, 5),
                player_data=self.player_data,
            )
            boat.speed = 5
            self.boats.append(boat)

        for i in range(self.player_data["destroyers"]):
            template = next(t for t in SHIP_TEMPLATES if t["kind"] == "destroyer")
            x = -4 + i * 8
            boat = Boat(
                f"Spieler-Zerstörer {i+1}",
                template,
                is_player=True,
                position=(x, 0.8, 8),
                player_data=self.player_data,
            )
            boat.speed = 5
            self.boats.append(boat)

    def fill_with_bots(self):
        while len(self.boats) < MAX_PLAYERS:
            template = random.choice(SHIP_TEMPLATES)
            name = f"BOT-{len(self.boats)}"
            x = random.uniform(-WORLD_SIZE / 2 + 5, WORLD_SIZE / 2 - 5)
            z = random.uniform(-WORLD_SIZE / 2 + 5, WORLD_SIZE / 2 - 5)
            bot = Boat(name, template, is_player=False, position=(x, 0.8, z))
            bot.direction = Vec3(random.uniform(-1, 1), 0, random.uniform(-1, 1)).normalized()
            bot.speed = template["speed"] * 2
            self.boats.append(bot)

    def update(self):
        if self.paused:
            return

        if self.boats:
            player = self.boats[0]
            if player.alive:
                camera.position = lerp(camera.position, Vec3(player.x, 18, player.z - 30), 0.05)
                camera.look_at(player.position + Vec3(0, 2, 0))

        player_count = sum(1 for b in self.boats if b.alive and b.is_player)
        alive_boats = sum(1 for b in self.boats if b.alive)

        self.hud_text.text = f"""WASSER-KRONEN: {self.player_data['water_coins']}

Deine Schiffe: {player_count}
Gegner online: {alive_boats - player_count}

Steuerung:
W/A/S/D - Bewegen
LEERTASTE - Schießen
X - Shop
ESC - Pausieren
C - Speichern
"""

        if player_count == 0:
            self.respawn_all_player_ships()

        if alive_boats < MAX_PLAYERS:
            self.fill_with_bots()

    def respawn_all_player_ships(self):
        for boat in self.boats:
            if boat.is_player:
                template = next(t for t in SHIP_TEMPLATES if t["id"] == boat.template["id"])
                boat.alive = True
                boat.visible = True
                boat.hp = template["max_hp"]
                boat.uranium = 0
                boat.position = Vec3(random.uniform(-5, 5), 0.8, random.uniform(3, 10))
                boat.label.text = boat.name
                boat.label.color = color.white

    def show_server_list(self):
        self.server_browser.show()


app = Ursina(borderless=False, fullscreen=False)

boats = []
game = Game()
boats = game.boats


def input(key):
    if key == 'escape':
        if game.pause_menu.panel is not None and game.pause_menu.panel.enabled:
            game.pause_menu.hide()
        else:
            game.pause_menu.show()
    elif key == 'x':
        if not game.pause_menu.panel:
            game.shop.show()
    elif key == 'c':
        game.save_game()


def update():
    game.update()
    for b in boats:
        b.update()


app.run()
