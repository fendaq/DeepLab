import plot
import numpy as np
plot.draw_curve("./dummy.csv", "./dummy.png")

img = np.random.rand(480,640,20)
plot.draw_image(img, './dummy2.png', keys = ["%d"%i for i in range(20)])

