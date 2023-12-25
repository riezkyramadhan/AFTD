import cv2
import numpy as np
import math
import time

from Adafruit_AMG88xx import Adafruit_AMG88xx
from scipy.interpolate import griddata
from colour import Color

# Low range of the sensor (this will be blue on the screen)
MINTEMP = 26

# High range of the sensor (this will be red on the screen)
MAXTEMP = 40

# How many color values we can have
COLORDEPTH = 1024

# Initialize the sensor
sensorR = Adafruit_AMG88xx(busnum=0)
sensorL = Adafruit_AMG88xx(busnum=1)

points = [(math.floor(ix / 8), (ix % 8)) for ix in range(0, 64)]
grid_x, grid_y = np.mgrid[0:7:32j, 0:7:32j]

# Sensor is an 8x8 grid so let's do a square
height = 240
width = 240

# The list of colors we can choose from
blue = Color("indigo")
colors = list(blue.range_to(Color("red"), COLORDEPTH))

# Create the array of colors
colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]

displayPixelWidth = width / 30
displayPixelHeight = height / 30

# Create an OpenCV window
#cv2.namedWindow("AMG88xx Heatmap", cv2.WINDOW_NORMAL)
#cv2.resizeWindow("AMG88xx Heatmap", width, height)

# Some utility functions
def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def AMG():
    # Let the sensor initialize
    time.sleep(.1)
    
    while True:
        # Read the pixels
        pixels = sensorR.readPixels()
        pixels = [map(p, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1) for p in pixels]
        
        # Perform interpolation
        bicubic = griddata(points, pixels, (grid_x, grid_y), method='cubic')
        
        # Create an empty image
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Draw everything
        for ix, row in enumerate(bicubic):
            for jx, pixel in enumerate(row):
                color = colors[constrain(int(pixel), 0, COLORDEPTH - 1)]
                image[int(displayPixelHeight * ix):int(displayPixelHeight * (ix + 1)),
                      int(displayPixelWidth * jx):int(displayPixelWidth * (jx + 1))] = color
        
        avg_temp = np.mean(sensorR.readPixels())
        print(f'Temperature: {avg_temp:.2f}°C')
        
        # Display the image
        #cv2.imshow("AMG88xx Heatmap", image)
        
        # Check for the 'q' key press to exit the program
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Close OpenCV window and cleanup
    cv2.destroyAllWindows()

