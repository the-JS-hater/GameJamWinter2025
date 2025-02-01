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
    wall_texture := load_texture("resources/StoneWall.png"),

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

    fire_shotgun := lambda x, y, dx, dy : (
        bullets.append(Bullet(
            x = x,
            y = y,
            dx = dx,
            dy = dy,
        )),
        bullets.append(Bullet(
            x = x,
            y = y,
            dx = dx - dy * 0.2,
            dy = dy + dx * 0.2,
        )),
        bullets.append(Bullet(
            x = x,
            y = y,
            dx = dx + dy * 0.2,
            dy = dy - dx * 0.2,
        ))
    ),

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
                    health = 0.2,
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

    bullet_speed := 8,
    robot_speed := 1.1,
    player_speed := 2.1,
    damage_cooldown_rate := 60,

    # Game state

    game_state := "running",
    
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
    weapon_cooldowns := {"pistol": 60, "shotgun": 90, "assault_rifle": 10},
    weapon_ammos := {"pistol": float("inf"), "shotgun": 5, "assault_rifle": 30},
    
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

    reduce(lambda _, a : None, takewhile(
        lambda _ : not window_should_close(),
        ((
            # INPUT & UPDATE
            
            globals().update(robot_cap = robot_cap + 1 / 60 / 10),
            
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
                    player.dx,
                    player.dy,
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
            globals().update(
                robots = [r for r in robots if not any(bullet_collision(r, b) for b in bullets)],
                bullets = [b for b in bullets if not any(bullet_collision(r, b) for r in robots)],
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
                wall_texture,
                int(x * grid_scale_w),
                int(y * grid_scale_h),
                WHITE,
            ) for x in range(grid_size_w)
                if map[y][x]] 
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
            [draw_texture(
                shotgun_texture if pickup.weapon == "shotgun"
                else assault_rifle_texture,
                pickup.x,
                pickup.y,
                WHITE
            ) for pickup in weapon_pickups],
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
            begin_drawing(),
            clear_background(BLACK),
                end_msg := f"You have the DEAD. You are died :(\nRobots killed {score}",
            msg_width := measure_text(end_msg, dead_msg_font_size),
            draw_text(
                end_msg, 
                int(window_w / 2 - msg_width / 2), 
                int(window_h / 2),
                dead_msg_font_size,
                RED
            ),
            end_drawing(),
        )
        for _ in cycle([1]))
    )),
)
