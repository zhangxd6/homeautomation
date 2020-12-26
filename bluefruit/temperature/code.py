import time
from adafruit_circuitplayground import cp
import displayio
import terminalio
from adafruit_gizmo import tft_gizmo
from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect
from adafruit_bitmap_font import bitmap_font

from adafruit_ble import BLERadio
from adafruit_ble_adafruit.adafruit_service import AdafruitServerAdvertisement
from adafruit_ble_adafruit.light_sensor_service import LightSensorService
from adafruit_ble_adafruit.temperature_service import TemperatureService


BACKGROUND_COLOR = 0x49523b  # Gray
TEXT_COLOR = 0xFF0000  # Red
BORDER_COLOR = 0xAAAAAA  # Light Gray
STATUS_COLOR = BORDER_COLOR

def wrap_in_tilegrid(open_file):
    odb = displayio.OnDiskBitmap(open_file)
    return displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter())

def make_background(width, height, color):
    color_bitmap = displayio.Bitmap(width, height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = color
 
    return displayio.TileGrid(color_bitmap,
                              pixel_shader=color_palette,
                              x=0, y=0)

def load_font(fontname, text):
    font = bitmap_font.load_font(fontname)
    font.load_glyphs(text.encode('utf-8'))
    return font

def make_label(text, x, y, color, max_glyphs=30, font=terminalio.FONT):
    if isinstance(font, str):
        font = load_font(font, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,?()")
    text_area = Label(font, text=text, color=color, max_glyphs=max_glyphs)
    text_area.x = x
    text_area.y = y
    return text_area
 
def set_label(label, value, max_length):
    text = "{}".format(value)
    if len(text) > max_length:
        text = text[:max_length-3] + "..."
    label.text = text
 
def set_status(label, action_text, player):
    label.text = "{} on {}".format(action_text, player)
    _, _, label_width, _ = label.bounding_box
    label.x = display.width - 10 - label_width

display = tft_gizmo.TFT_Gizmo()
group = displayio.Group(max_size=20)
display.show(group)

title_label = make_label("None", 12, 30, TEXT_COLOR, font="/fonts/Arial-Bold-18.bdf")
artist_label = make_label("None", 12, 70, TEXT_COLOR, font="/fonts/Arial-16.bdf")
album_label = make_label("None", 12, 184, TEXT_COLOR, font="/fonts/Arial-16.bdf")
status_label = make_label("None", 80, 220, STATUS_COLOR, font="/fonts/Arial-16.bdf")
group.append(make_background(240, 240, BACKGROUND_COLOR))
border = Rect(4, 4, 232, 200, outline=BORDER_COLOR, stroke=2)
group.append(title_label)
group.append(artist_label)
group.append(album_label)
group.append(status_label)
group.append(border)



light_svc = LightSensorService()
light_svc.measurement_period = 100
light_last_update = 0
 
temp_svc = TemperatureService()
temp_svc.measurement_period = 100
temp_last_update = 0
ble = BLERadio()
ble.name = "Garage"
adv = AdafruitServerAdvertisement()
adv.pid = 0x8046


while True:
    set_label(title_label, "Temp: {0:.2f} C".format(cp.temperature) , 18)
    set_label(album_label, "Temp: {0:.2f} F".format(cp.temperature * 1.8 + 32), 21)
    light="OFF"
    if cp.light>1:
        light="ON"
    set_label(artist_label,"Light: {}".format(light), 21)


    ble.start_advertising(adv)
    while not ble.connected:
        pass
    ble.stop_advertising()
    
    while ble.connected:
        now_msecs = time.monotonic_ns() // 1000000  # pylint: disable=no-member
    
        if now_msecs - temp_last_update >= temp_svc.measurement_period:
            temp_svc.temperature = cp.temperature
            temp_last_update = now_msecs
        if now_msecs - light_last_update >= light_svc.measurement_period:
            light_svc.light_level = cp.light
            light_last_update = now_msecs
        print("Temperature C:", cp.temperature)
        print("Temperature F:", cp.temperature * 1.8 + 32)
        print("Light:", cp.light)
        print("Sound level:", cp.sound_level)

        set_label(title_label, "Temp: {0:.2f} C".format(cp.temperature) , 18)
        set_label(album_label, "Temp: {0:.2f} F".format(cp.temperature * 1.8 + 32), 21)
        light="OFF"
        if cp.light>1:
            light="ON"
        set_label(artist_label,"Light: {}".format(light), 21)
        set_status(status_label,"Sound: {}".format(cp.sound_level), "db")
        # /time.sleep()
    # if cp.button_a:
    #     cp.pixels.fill((50, 0, 0))
    #     time.sleep(1)
    # if cp.
    #     cp.pixels.fill((50, 50, 50))
    #     time.sleep(1)
    
    # cp.pixels.fill((0, 0, 0))

