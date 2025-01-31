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
    window_w := 680,
    window_h := 420,
    
    # HELPER FUNCTIONS
    
    has_collision := (
        lambda a, b : not any([
            a['x'] + a['w'] <= b['x'],
            b['x'] + b['w'] <= a['x'],
            a['y'] + a['h'] <= b['y'],
            b['y'] + b['h'] <= a['y'],
            ])
    ),

    fire_pistol := (
        lambda x, y, dx, dy : bullets.append(
            {
                "x": x,
                "y": y,
                "dx": dx,
                "dy": dy,
            }
        ) 
    ),
    # Game constants
    bullet_speed := 8,
    
    # Game state
    weapons := {"pistol": fire_pistol},
    player := {"x": 200, "y": 180, "dx": 0, "dy": 1, "w": 10, "h": 20, "weapon": "pistol"},
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
                (moved_player["dx"] != 0 or moved_player["dy"] != 0) and
                not any(
                    has_collision(moved_player, entity)
                for entity in robots) else None,
            
            # Fire weapon
            weapons[player["weapon"]](
                player['x'],
                player['y'],
                player['dx'],
                player['dy'],
            )
                if is_key_down(KeyboardKey.KEY_SPACE) else None,
    
            # Update bullets
            globals().update(bullets = [
                {
                    'x': b['x'] + bullet_speed * b['dx'],
                    'y': b['y'] + bullet_speed * b['dy'],
                    'dx': b['dx'],
                    'dy': b['dy'],
                }
                for b in bullets
                if 0 <= b['x'] <= window_w and
                    0 <= b['y'] <= window_h
            ]),

            # RENDER
            begin_drawing(),
            clear_background(BLACK),
            [draw_rectangle(
                entity["x"],
                entity["y"],
                entity["w"],
                entity["h"],
                GREEN,
            ) for entity in robots],
            [draw_circle(
                bullet['x'],
                bullet['y'],
                2.0,
                YELLOW,
            ) for bullet in bullets],
            draw_rectangle(
                player["x"],
                player["y"],
                player["w"],
                player["h"],
                RED,
            ),
            end_drawing(),
        ) for _ in cycle([1]))
    )),
)
