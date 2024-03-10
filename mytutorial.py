import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()

# 设置窗口说明文字
pygame.display.set_caption('NIHAO')
# 全局变量 背景色
WIDTH, HEIGHT = 1000, 800
FPS = 60
# 玩家人物的行动速度
PLAYER_VEL = 5
# 创建窗口
window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip(sprites):
    # 翻转图片，因为我们的素材都是向右的
    # flip_x为true则只在x方向翻转
    return [pygame.transform.flip(sprite, True, False)
            for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    # width height 是图片的宽高，我们这里已经知道是32x32,
    # 获取那个角色的素材路径
    path = join("assets", dir1, dir2)
    # 读取了所有文件，只有文件(isfile判断)
    # listdir应该是把path目录下的所有路径都列出来
    # 现在images里面都是各个图片的名称例如hit.png
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        # convert_alpha读取空白背景的图片，
        # print(image)
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            # SRCALPHA允许载入透明图片
            # 创建一个表面，来装从素材截取的一张张图片
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            # 这个矩形就是一个图片的大小，参数为xywh,起点xy就是左上角那个点，很容易理解
            rect = pygame.Rect(i * width, 0, width, height)
            # blit就是draw，sprite_sheet读取了那张素材，
            # 然后我们画再surface的(0,0)，只截取rect矩形里面框的图片
            surface.blit(sprite_sheet, (0, 0), rect)
            # 放大两倍，变成64x64
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            # 翻转，获取朝向两边的动画
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    # 选的是绿草的那个方块
    rect = pygame.Rect(96, 64, size, size)
    surface.blit(image, (0, 0), rect)
    # blit先切割，surface此时得到的结果还不是最后的方块，我们通过return surface能知道
    # 把切割下来的图片放大两倍之后，得到的才是那个草地方块
    # 我们做个实验，按照原本的位置进行切割,然后再放大，可以看到只有一点点放的了的一部分
    # 所以如果要放大两倍就得这样
    return pygame.transform.scale2x(surface)


# 使用这个Sprite更好处理碰撞事件
class Player(pygame.sprite.Sprite):
    COLOR = (100, 200, 200)
    GRAVITY = 1
    # 所有的素材库
    SPRITES = load_sprite_sheets("MainCharacters", "VirtualGuy", 32, 32, True)
    # 每多少帧改变图形
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        # 人物朝向默认为左
        self.direction = "left"
        self.animation_count = 0
        # 坠落时间，模拟现实重力,坠落时间越长则速度越快
        self.fall_count = 0
        self.sprite = None
        self.jump_count = 0
        self.hit_count = 0
        self.hit = False

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def being_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        # 因为除了fps之后会很小，所以我们最少下落+1个像素，所以就不会等很久才能感受到重力
        self.y_vel += min(0.5, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        # 为了后面的二段跳
        self.jump_count = 0

    def hit_head(self):
        self.fall_count = 0
        self.y_vel *= -1

    def update_sprite(self):
        # 默认使用站立的动画
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel > 0.6:
            sprite_sheet = "fall"
        elif self.y_vel < 0:
            sprite_sheet = "jump"
            if self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.x_vel != 0:
            sprite_sheet = "run"
        else:
            sprite_sheet = "idle"
        # 这里切记不能填 >0因为每时每刻都在算你的y的速度，所以一直大于0就会卡动画

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        # 得遍历这些图片以至于像在动一样
        sprites = self.SPRITES[sprite_sheet_name]

        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        # 有些动画可能大可能小，所以我们要调整其矩形(碰撞体积？)
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        # 使用mask能告诉我们动画哪些真的有像素哪些没有
        # 这样在后面碰撞检测的时候就是真的像素碰撞了而不是矩形碰撞了
        # 如果采用矩形碰撞则会其实没碰到但检测你碰撞了
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        # 面向哪个方向就加载那个方向的图片
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width, self.height = width, height
        self.name = name

    def draw(self, win, offset_x):
        # 为什么是减这个偏移值？
        # 因为你往右走偏移值为正，原先的方块就要往左移，就是减
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire_image = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire_image["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on_fire(self):
        self.animation_name = "on"

    def off_fire(self):
        self.animation_name = "off"

    def loop(self):
        # 得遍历这些图片以至于像在动一样
        sprites = self.fire_image[self.animation_name]

        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        # 有些动画可能大可能小，所以我们要调整其矩形(碰撞体积？)
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        # 使用mask能告诉我们动画哪些真的有像素哪些没有
        # 这样在后面碰撞检测的时候就是真的像素碰撞了而不是矩形碰撞了
        # 如果采用矩形碰撞则会其实没碰到但检测你碰撞了
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


# 返回装着一系列背景块的列表
def get_background(name):
    # join方法返回那个文件的路径，这个函数就是不断加入中间的文件，这里就是
    # assets/Background/ + name
    image = pygame.image.load(join('assets', "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []
    # WIDTH窗口大小除以背景块大小就知道我们需要多少个背景块来填充
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            # 当前正在加入的背景块的左上角的xy位置
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(my_window, background, bg_image, player, objects, offset_x):
    for tile in background:
        my_window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(my_window, offset_x)

    player.draw(my_window, offset_x)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            # 因为时刻有重力，dy总是大于0，所以会出现碰到一个方块就会到他上面
            if dy > 0:
                # 再往下走，在某个物体的上面发生碰撞
                player.rect.bottom = obj.rect.top
                # 着陆
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                # 撞到头
                player.hit_head()
            collided_objects.append(obj)

    # 返回碰撞到的物体，以便后面可以检测碰撞到特殊物体的行为(例如碰到火？)
    return collided_objects


def horizontal_collide(player, objects, dx):
    # 检查往dx方向走会不会碰撞
    player.move(dx, 0)
    player.update()
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_objects.append(obj)

    player.move(-dx, 0)
    player.update()
    return collided_objects


def handle_move(player, objects):
    # 处理键盘按键事件，左右移动
    keys = pygame.key.get_pressed()
    # 如果不重置这个为0的话，按下某一个方向的时候就会一直往那边走直到按下另一个键
    # 我们只想要一直按着某个方向就往那个方向走
    player.x_vel = 0
    # 如果往左右走会碰撞就不让他走
    # 这里设置速度乘2是为了解决向右走的一个小BUG，这样会导致与物体的间隔更宽了
    collide_left = horizontal_collide(player, objects, -PLAYER_VEL * 1.4)
    collide_right = horizontal_collide(player, objects, PLAYER_VEL * 1.4)
    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collision = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [*collide_left, *collide_right, *vertical_collision]
    for obj in to_check:
        if obj.name == "fire":
            player.being_hit()


def main(my_window):
    clock = pygame.time.Clock()
    background, bg_image = get_background('Pink.png')
    # 注意这里方块大小事原来的两倍因为返回的是原来图片的2倍大小
    block_size = 96
    player = Player(100, 500, 50, 50)
    # 不止填充这个屏幕，左边右边都有
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in
             range(-WIDTH // block_size, WIDTH * 2 // block_size)]
    # 把floor拆成一个个个体再放入objects
    myfire = Fire(300, HEIGHT - block_size - 64, 16, 32)
    myfire.on_fire()
    all_objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size), Block(0, HEIGHT - block_size * 3, block_size),
                   myfire]
    offset_x = 0
    scroll_area_width = 200

    run = True
    while run:
        # 确保60帧
        clock.tick(FPS)
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w and player.jump_count < 2:
                    player.jump()
        # loop才是真正移动
        player.loop(FPS)
        myfire.loop()
        handle_move(player, all_objects)
        draw(my_window, background, bg_image, player, all_objects, offset_x)

        # 判断往右走了多少需不需要移动屏幕
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel
    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
