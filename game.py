(
    globimport = lambda name: (
        module := __import__(name),
        globals().update({
            name: getattr(module, name)
            for name in dir(module)
            if not name.startswith("_")
        })
    )
    globimport("pyray"),
    globimport("itertools"),
    window_w := 680,
    window_h := 420,
    player := {"x": 200, "y": 200, "w": 10, "h": 20},
    entity1 := {"x": 50, "y": 50, "w": 50, "h": 50},
    entity2 := {"x": 150, "y": 220, "w": 70, "h": 50},
    entities := [entity1, entity2],
    set_target_fps(60),
    init_window(window_w, window_h, "game"),
    "".join(it.takewhile(
        lambda _ : not window_should_close(),
        ((  
            # INPUT 
            
            player.__setitem__("y", player["y"] - 1)
                if is_key_down(rl.KeyboardKey.KEY_UP) else None,

            player.__setitem__("y", player["y"] + 1)
                if is_key_down(rl.KeyboardKey.KEY_DOWN) else None,
            
            player.__setitem__("x", player["x"] - 1)
                if is_key_down(rl.KeyboardKey.KEY_LEFT) else None,
            
            player.__setitem__("x", player["x"] + 1)
                if is_key_down(rl.KeyboardKey.KEY_RIGHT) else None,
            
            # UPDATE

            # RENDER
            begin_drawing(),
            clear_background(rl.BLACK),
            [rl.draw_rectangle(
                entity["x"],
                entity["y"],
                entity["w"],
                entity["h"],
                BLUE,
            ) for entity in entities],
            draw_rectangle(
                player["x"],
                player["y"],
                player["w"],
                player["h"],
                RED,
            ),
            end_drawing(),
            ""
        ) for _ in cycle([1]))
    )),
)
