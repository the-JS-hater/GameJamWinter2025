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
    globimport("heapq"),
    random := __import__("random"),

    # GUI constants

    window_w := 1920,
    window_h := 1080,
    healthbar_w := 180,
    healthbar_h := 15,
    dead_msg_font_size := 50,
    score_font_size := 15,
    lore_font_size := 50,

    # Init Raylib
    
    set_target_fps(60),
    set_trace_log_level(7), 
    init_window(window_w, window_h, "game"),
    
    # Textures
    player_texture := load_texture("resources/Player.png"),
    robot_texture := load_texture("resources/Robot.png"),
    pistol_texture := load_texture("resources/Pistol.png"),
    shotgun_texture := load_texture("resources/Shotgun.png"),
    assault_rifle_texture := load_texture("resources/MachineGun.png"),
    spam_texture := load_texture("resources/Spam.png"),
    wall_texture := load_texture("resources/SimpleWood.png"),
    floor_texture := load_texture("resources/StoneWall.png"),
    duck_head_texture := load_texture("resources/DuckHead.png"),
    duck_body_texture := load_texture("resources/DuckBody.png"),
        
    # Resizing the corpse textures
    duck_head_image := load_image_from_texture(duck_head_texture),
    duck_body_image := load_image_from_texture(duck_body_texture),
    image_resize_nn(duck_head_image, 32 * 5, 32 * 5),
    image_resize_nn(duck_body_image, 64 * 5, 32 * 5),
    duck_head_texture := load_texture_from_image(duck_head_image),
    duck_body_texture := load_texture_from_image(duck_body_image),

    # Classes
    classdef := lambda name, fields: (ty := type(name, (), {
        "__init__": lambda self, **vals: [setattr(self, n, vals[n]) for n in fields][0],
        "update": lambda self, **vals: [setattr(self, n, v) for n, v in vals.items() if n in fields],
        "copy_with": lambda self, **vals: ty(**{ n: vals[n] if n in vals else getattr(self, n) for n in fields }),
    })),

    Player := classdef("Player", ["x", "y", "dx", "dy", "w", "h", "weapon", "ammo", "health", "damage_cooldown", "weapon_cooldown"]),
    Robot := classdef("Robot", ["x", "y", "dx", "dy", "w", "h"]),
    Bullet := classdef("Bullet", ["x", "y", "dx", "dy"]),
    Wall := classdef("Wall", ["x", "y", "w", "h"]),
    WeaponPickup := classdef("WeaponPickup", ["x", "y", "w", "h", "weapon", "ammo"]),
    HealthPickup := classdef("HealthPickup", ["x", "y", "w", "h", "health"]),

    # HELPER FUNCTIONS
    
    has_collision := lambda a, b: not any([
        a.x + a.w <= b.x,
        b.x + b.w <= a.x,
        a.y + a.h <= b.y,
        b.y + b.h <= a.y,
    ]),

    has_world_collision := lambda obj: any(
        has_collision(obj, Wall(
            x = x * grid_scale_w, 
            y = y * grid_scale_h, 
            w = grid_scale_w, 
            h = grid_scale_h))
        for x in range(len(map[0]))
            for y in range(len(map)) 
                if map[y][x] != 0
    ),

    update_cooldowns := lambda player: (
        player.update(
            weapon_cooldown = max(0, player.weapon_cooldown - 1),
            damage_cooldown = max(0, player.damage_cooldown - 1),
        )
    ),

    fire_pistol := lambda x, y, dx, dy : (
        bullets.append(Bullet(
            x = x,
            y = y,
            dx = dx,
            dy = dy,
        ))
    ),

    fire_shotgun := lambda x, y, dx, dy : [
        bullets.append(Bullet(
            x = x,
            y = y,
            dx = dx + random.gauss(0, 1) * shotgun_spread,
            dy = dy + random.gauss(0, 1) * shotgun_spread,
        ))
        for _ in range(shotgun_bullets)
    ],

    spawn_robot := lambda: (
        robots.append(next(filter(
            lambda robot: not has_world_collision(robot)
                and hypot(robot.x - player.x, robot.y - player.y) > 300.0,
            (
                Robot(
                    x = random.randint(0, window_w - 32),
                    y = random.randint(0, window_h - 32),
                    w = 32,
                    h = 64,
                    dx = 0,
                    dy = 0,
                ) for _ in cycle([1])
            ),
        )))
    ) if len(robots) < robot_cap else None,

    spawn_weapon := lambda: (
        weapon_pickups.append(next(filter(
            lambda pickup: not has_world_collision(pickup),
            (
                (lambda weapon: WeaponPickup(
                    x = random.randint(0, window_w - 32),
                    y = random.randint(0, window_h - 32),
                    weapon = weapon,
                    ammo = weapon_ammos[weapon],
                    w = 32,
                    h = 32,
                ))(random.choice(["shotgun", "assault_rifle"]))
                for _ in cycle([1])
            ),
        )))
    ) if len(weapon_pickups) < 3 else None,

    spawn_health := lambda: (
        health_pickups.append(next(filter(
            lambda pickup: not has_world_collision(pickup),
            (
                HealthPickup(
                    x = random.randint(0, window_w - 32),
                    y = random.randint(0, window_h - 32),
                    health = 0.4,
                    w = 32,
                    h = 32,
                )
                for _ in cycle([1])
            ),
        )))
    ) if len(health_pickups) < 1 else None,
    
    map_dist_to := lambda x, y: (
        dist_to := [[10**10] * grid_size_w for _ in range(grid_size_h)],
        queue := [(0, x, y)],

        list(takewhile(
            lambda _: len(queue) > 0,
            ((
                p := heappop(queue),
                (
                    dist_to[p[2]].__setitem__(p[1], p[0]),
                    [
                        heappush(queue, (p[0] + dc, p[1] + dx, p[2] + dy))
                        for dx, dy, dc in [
                            (0, 1, 1.0), (0, -1, 1.0), (1, 0, 1.0), (-1, 0, 1.0),
                            (1, 1, 1.4), (1, -1, 1.4), (-1, 1, 1.4), (-1, -1, 1.4),
                        ]
                    ],
                )
                if 0 <= p[1] < grid_size_w
                    and 0 <= p[2] < grid_size_h
                    and not map[p[2]][p[1]]
                    and dist_to[p[2]][p[1]] == 10**10
                else None
            ) for _ in cycle([1]))
        )),
    )[0],

    # Game constants

    bullet_speed := 20,
    robot_speed := 1.8,
    player_speed := 2.8,
    damage_cooldown_rate := 60,

    # Game state

    game_state := "start_screen",
    
    map := [
        list(map(int, l.replace("\n", "")))
        for l in
        open("testMap.txt", 'r').readlines()
    ],

    grid_size_w := len(map[0]),
    grid_size_h := len(map),
    grid_scale_w := window_w / grid_size_w,
    grid_scale_h := window_h / grid_size_h,

    weapons := {"pistol": fire_pistol, "assault_rifle": fire_pistol, "shotgun": fire_shotgun},
    weapon_cooldowns := {"pistol": 45, "shotgun": 45, "assault_rifle": 10},
    weapon_ammos := {"pistol": float("inf"), "shotgun": 12, "assault_rifle": 40},
    
    shotgun_bullets := 6,
    shotgun_spread := 0.25,

    player := Player(
        x = 960, y = 540, 
        dx = 0, dy = 1, 
        w = 32, h = 32, 
        weapon = "pistol",
        ammo = float('inf'),
        health = 1.0,
        damage_cooldown = 0,
        weapon_cooldown = 0,
    ),

    robots := [],
    bullets := [],
    weapon_pickups := [],
    health_pickups := [],
    robot_cap := 3,
    score := 0,
    
    # Reset Game state
    reset_game := lambda : globals().update( 
        game_state = "running",
        player = Player(
            x = 960, y = 540, 
            dx = 0, dy = 1, 
            w = 32, h = 32, 
            weapon = "pistol",
            ammo = float('inf'),
            health = 1.0,
            damage_cooldown = 0,
            weapon_cooldown = 0,
        ),

        robots = [],
        bullets = [],
        weapon_pickups = [],
        health_pickups = [],
        robot_cap = 3,
        score = 0,
    ),

    reduce(lambda _, a : None, takewhile(
        lambda _ : not window_should_close(),
        ((
            # INPUT & UPDATE
            
            globals().update(robot_cap = robot_cap + 1 / 60 / 4),
            
            moved_player := player.copy_with(
                x = player.x
                    - (player_speed if is_key_down(KeyboardKey.KEY_LEFT) else 0)
                    + (player_speed if is_key_down(KeyboardKey.KEY_RIGHT) else 0),
                y = player.y
                    - (player_speed if is_key_down(KeyboardKey.KEY_UP) else 0)
                    + (player_speed if is_key_down(KeyboardKey.KEY_DOWN) else 0),
            ),

            moved_player.update(
                dx = moved_player.x - player.x,
                dy = moved_player.y - player.y,
            ),

            # Move player

            player.update(
                x = moved_player.x,
                y = moved_player.y,
                dx = moved_player.dx,
                dy = moved_player.dy,
            )
                if (moved_player.dx != 0 or moved_player.dy != 0)
                and not has_world_collision(moved_player)
            else None,
            
            # Update cooldowns
            update_cooldowns(player),
            
            # Player collides with robot
            player.update(
                health = player.health - 0.2,
                damage_cooldown = damage_cooldown_rate,
            ) if
                player.damage_cooldown == 0
                and any(
                    has_collision(player, robot) 
                for robot in robots) else None,
            

            # Fire weapon
            (
                weapons[player.weapon](
                    player.x + player.w / 2,
                    player.y + player.h / 4,
                    player.dx / hypot(player.dx, player.dy),
                    player.dy / hypot(player.dx, player.dy),
                ),
                player.update(
                    ammo = player.ammo - 1 if player.ammo > 1 else float("inf"),
                    weapon = player.weapon if player.ammo > 1 else "pistol",
                ),
                player.update(
                    weapon_cooldown = weapon_cooldowns[player.weapon]
                ),
            )
                if is_key_down(KeyboardKey.KEY_SPACE) 
                    and player.weapon_cooldown == 0
                else None,
    
            # Update bullets
            globals().update(bullets = [
                b.copy_with(
                    x = b.x + bullet_speed * b.dx,
                    y = b.y + bullet_speed * b.dy,
                )
                for b in bullets
                if 0 <= b.x <= window_w and 0 <= b.y <= window_h
            ]),
            bullet_world_coll := lambda b: (
                tx := int(b.x / grid_scale_h),
                ty := int(b.y / grid_scale_w),
                0 <= tx < grid_size_w and 0 <= ty < grid_size_h and map[ty][tx] != 0
            )[-1],
            globals().update(bullets = [
                b for b in bullets if not bullet_world_coll(b)
            ]),

            # Update robots
            ptx := int((player.x + player.w / 2) / grid_scale_w),
            pty := int((player.y + player.h / 2) / grid_scale_h),
            dist_to_player := map_dist_to(ptx, pty),
            globals().update(
                robots = [(
                    tx := int((r.x + r.w / 2) / grid_scale_w),
                    ty := int((r.y + r.h * 3 / 4) / grid_scale_h),
                    (
                        target := min(
                            [(tx - 1, ty), (tx + 1, ty), (tx, ty - 1), (tx, ty + 1)],
                            key = lambda p: (
                                dist_to_player[p[1]][p[0]]
                                if 0 <= p[0] < grid_size_w and 0 <= p[1] < grid_size_h
                                else 10**10
                            ),
                        ),
                        dx := (target[0] + 0.5) * grid_scale_w - (r.x + r.w / 2),
                        dy := (target[1] + 0.5) * grid_scale_h - (r.y + r.h * 3 / 4),
                    ) if (ptx, pty) != (tx, ty) else (
                        dx := player.x - r.x,
                        dy := player.y - r.y,
                    ),
                    dist := max(hypot(dx, dy), 0.01),
                    r.copy_with(
                        x = r.x + dx / dist * robot_speed,
                        y = r.y + dy / dist * robot_speed,
                        dx = dx,
                        dy = dy,
                    )
                )[-1] for r in robots],
            ),

            # Kill robots with bullets
            nr_of_robots := len(robots),
            bullet_collision := lambda robot, bullet: (
                robot.x <= bullet.x <= robot.x + robot.w
                and robot.y <= bullet.y <= robot.y + robot.h
            ),
            used_bullets := set(),
            globals().update(
                robots = [
                    r for r in robots if not any((
                        coll := bullet_collision(r, b),
                        coll and used_bullets.add(b),
                    )[0] for b in bullets)],
                bullets = [b for b in bullets if b not in used_bullets],
            ),
            score := score + (nr_of_robots - len(robots)), 

            # Pick up weapons and health
            globals().update(
                weapon_pickups = [
                    p for p in weapon_pickups if not (
                        coll := has_collision(player, p),
                        player.update(weapon = p.weapon, ammo = p.ammo)
                            if coll else None
                    )[0]
                ],
                health_pickups = [
                    p for p in health_pickups if not (
                        coll := has_collision(player, p),
                        player.update(health = min(1, player.health + p.health))
                            if coll else None
                    )[0]
                ],
            ),

            spawn_weapon(),
            spawn_health(),
            spawn_robot(),

            # RENDER
            begin_drawing(),
            clear_background(BLACK),
            [[draw_texture(
                wall_texture if map[y][x]
                else floor_texture,
                int(x * grid_scale_w),
                int(y * grid_scale_h),
                WHITE,
            ) for x in range(grid_size_w)] 
                for y in range(grid_size_h)],
            [draw_texture_rec(
                robot_texture,
                (64, 0, 32, 64) if robot.dx < -abs(robot.dy)
                else (32, 0, 32, 64) if robot.dx > abs(robot.dy) 
                else (96, 0, 32, 64) if robot.dy < 0
                else (0, 0, 32, 64),
                (int(robot.x), int(robot.y)),
                WHITE
            ) for robot in robots],
            [draw_circle(
                int(bullet.x),
                int(bullet.y),
                int(2.0),
                YELLOW,
            ) for bullet in bullets],
            [(draw_circle(
                pickup.x + 16,
                pickup.y + 16,
                18,
                YELLOW,
            ),draw_texture(
                shotgun_texture if pickup.weapon == "shotgun"
                else assault_rifle_texture,
                pickup.x,
                pickup.y,
                WHITE
            )) for pickup in weapon_pickups],
            [draw_texture(
                spam_texture,
                pickup.x,
                pickup.y,
                WHITE
            ) for pickup in health_pickups],
            draw_texture_rec(
                player_texture,
                (0, 0, 32, 64) if player.dx < 0
                else (96, 0, 32, 64) if player.dx > 0 
                else (32, 0, 32, 64) if player.dy < 0
                else (64, 0, 32, 64),
                (player.x, player.y - 32),
                WHITE if player.damage_cooldown == 0
                else RED
            ),
            draw_rectangle(
                int(0 + window_w * 0.8), 
                int(0 + window_h * 0.02),
                int(player.health * healthbar_w),
                healthbar_h,
                RED,
            ),
            draw_text(
                f"SCORE: {score}", 
                int(0.1 * window_w), 
                int(0.02 * window_h),
                score_font_size,
                WHITE 
            ),
            draw_text(
                f"AMMO: {player.ammo}", 
                int(0.3 * window_w), 
                int(0.02 * window_h),
                score_font_size,
                WHITE 
            ),
            end_drawing(),

            # Game over

            (game_state := "game_over") 
            if player.health <= 0 else None,

        ) if game_state == "running" else (
            (game_state := "start_screen") 
            if is_key_down(KeyboardKey.KEY_R) 
            else None,
            begin_drawing(),
            clear_background(BLACK),
            end_msg := f"You have the DEAD. You are died :c\nRobots killed {score}\nPress R to die again :D",
            msg_width := measure_text(end_msg, dead_msg_font_size),
            draw_texture(
                duck_head_texture,
                int(window_w * 0.045),
                int(window_h * 0.70),
                WHITE
            ),
            draw_texture(
                duck_body_texture,
                int(window_w * 0.05 + 200),
                int(window_h * 0.76),
                WHITE
            ),
            draw_text(
                end_msg, 
                int(window_w / 2 - msg_width / 2), 
                int(window_h / 2),
                dead_msg_font_size,
                RED
            ),
            end_drawing(),
        ) if game_state == "game_over" else
            (
            (reset_game()) 
            if is_key_down(KeyboardKey.KEY_ENTER) 
            else None,
            lore_msg := "In the not-actually-very-dystopian future of some \nyears ahead, you are the Donald Duck(tm). You are on the \nrun from robotic Disney(tm) lawyer-otons2000:s trying to \nsue the game developers (and murder you), aswell as \nwalking, not talking, LLM robots that want to \nstable-diffuse your assets to death.\nDue to lack of graphical assets, these two types of robots are \nvisually (and gameplay wise due to lack of programming) \nindistinguishable.\nThankfully Donald Duck(tm) is a God fearing, \nrepublican voting, true American(tm), and is thus \nrac- i mean ARMED TO THE THEETH.\nGood Luck!\n\nPress Enter to start",
            msg_width := measure_text(lore_msg, lore_font_size),
            begin_drawing(),
            clear_background(BLACK),
            draw_text(
                lore_msg, 
                int(window_w / 2 - msg_width / 2), 
                int(window_h * 0.1),
                lore_font_size,
                RED
            ),
            end_drawing(),
        ) if game_state == "start_screen" else None
        for _ in cycle([1]))
    )),
)
