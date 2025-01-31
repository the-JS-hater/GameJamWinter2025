(
    globimport := lambda name: (
        module := __import__(name),
        globals().update({
            name: getattr(module, name)
            for name in dir(module)
            if not name.startswith("_")
        })
    ),
    globimport("pyray"),
    globimport("itertools"),
    globimport("functools"),
    globimport("math"),

    # GUI constants
    window_w := 680,
    window_h := 420,
    healthbar_w := 120,
    healthbar_h := 25,
    
    # HELPER FUNCTIONS
    
    has_collision := lambda a, b: not any([
        a['x'] + a['w'] <= b['x'],
        b['x'] + b['w'] <= a['x'],
        a['y'] + a['h'] <= b['y'],
        b['y'] + b['h'] <= a['y'],
    ]),

    update_cooldowns := lambda player: (
        player.update(
            weapon_cooldown = max(0, player["weapon_cooldown"] - 1),
            damage_cooldown = max(0, player["damage_cooldown"] - 1),
        )
    ),

    fire_pistol := lambda x, y, dx, dy : (
        bullets.append({
            "x": x,
            "y": y,
            "dx": dx,
            "dy": dy,
        })
    ),
    # Game constants
    bullet_speed := 8,
    robot_speed := 0.5,

    # Game state
    weapons := {"pistol": fire_pistol},
    weapon_cooldowns := {"pistol": 60},

    player := {
        "x": 200, "y": 180, 
        "dx": 0, "dy": 1, 
        "w": 10, "h": 20, 
        "weapon": "pistol",
        "health": 1.0,
        "damage_cooldown": 0,
        "weapon_cooldown": 0,
    },

    robot1 := {"x": 50, "y": 50, "w": 10, "h": 20},
    robot2 := {"x": 150, "y": 220, "w": 10, "h": 20},
    robots := [robot1, robot2],
    bullets := [],
    
    set_target_fps(60),
    set_trace_log_level(7), 
    init_window(window_w, window_h, "game"),
    reduce(lambda _, a : None, takewhile(
        lambda _ : not window_should_close(),
        ((
            moved_player := player.copy(),

            # INPUT 
            # & UPDATE
            
            moved_player.__setitem__("y", player["y"] - 1)
                if is_key_down(KeyboardKey.KEY_UP) else None,

            moved_player.__setitem__("y", player["y"] + 1)
                if is_key_down(KeyboardKey.KEY_DOWN) else None,
            
            moved_player.__setitem__("x", player["x"] - 1)
                if is_key_down(KeyboardKey.KEY_LEFT) else None,
            
            moved_player.__setitem__("x", player["x"] + 1)
                if is_key_down(KeyboardKey.KEY_RIGHT) else None,
            
            moved_player.__setitem__("dx", moved_player["x"] - player["x"]),
            moved_player.__setitem__("dy", moved_player["y"] - player["y"]),
            

            # Move player
            player.update(moved_player) if 
                (moved_player["dx"] != 0 or moved_player["dy"] != 0) else None,
            
            #    and
            #    not any(
            #        has_collision(moved_player, entity)
            #    for entity in robots) else None,
            
            # player.update(
            #     damage_cooldown = player["damage_cooldown"] - 1
            # ) if player["damage_cooldown"] > 0 else None,

            # Update cooldowns
            update_cooldowns(player),
            
            # Player collides with robot
            player.update(
                health = player['health'] - 0.2,
                damage_cooldown = 120,
            ) if
                player["damage_cooldown"] == 0
                and any(
                    has_collision(player, robot) 
                for robot in robots) else None,
            

            # Fire weapon
            (
                weapons[player["weapon"]](
                    player['x'],
                    player['y'],
                    player['dx'],
                    player['dy'],
                ),
                player.update(
                    weapon_cooldown = weapon_cooldowns[player["weapon"]]
                )
            )
                if is_key_down(KeyboardKey.KEY_SPACE) 
                    and player["weapon_cooldown"] == 0
                else None,
    
            # Update bullets
            globals().update(bullets = [
                {
                    **b,
                    'x': b['x'] + bullet_speed * b['dx'],
                    'y': b['y'] + bullet_speed * b['dy'],
                }
                for b in bullets
                if 0 <= b['x'] <= window_w and 0 <= b['y'] <= window_h
            ]),

            # Update robots
            globals().update(
                robots = [(
                    dx := player["x"] - r["x"],
                    dy := player["y"] - r["y"],
                    dist := hypot(dx, dy),
                    {
                        **r,
                        "x": r["x"] + dx / dist * robot_speed,
                        "y": r["y"] + dy / dist * robot_speed,
                    }
                )[-1] for r in robots],
            ),

            # Kill robots with bullets
            bullet_collision := lambda robot, bullet: (
                robot["x"] <= bullet["x"] <= robot["x"] + robot["w"]
                and robot["y"] <= bullet["y"] <= robot["y"] + robot["h"]
            ),
            globals().update(
                robots = [r for r in robots if not any(bullet_collision(r, b) for b in bullets)],
                bullets = [b for b in bullets if not any(bullet_collision(r, b) for r in robots)],
            ),

            # RENDER
            begin_drawing(),
            clear_background(BLACK),
            [draw_rectangle(
                int(entity["x"]),
                int(entity["y"]),
                int(entity["w"]),
                int(entity["h"]),
                GREEN,
            ) for entity in robots],
            [draw_circle(
                int(bullet['x']),
                int(bullet['y']),
                int(2.0),
                YELLOW,
            ) for bullet in bullets],
            draw_rectangle(
                int(player["x"]),
                int(player["y"]),
                int(player["w"]),
                int(player["h"]),
                RED,
            ),
            draw_rectangle(
                int(0 + window_w * 0.1), 
                int(0 + window_h * 0.9),
                int(player["health"] * healthbar_w),
                healthbar_h,
                BLUE,
            ),
            end_drawing(),
        ) for _ in cycle([1]))
    )),
)
