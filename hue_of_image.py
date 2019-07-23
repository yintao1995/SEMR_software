from PIL import Image
import matplotlib.pyplot as plt

# 功能：将RGB表示转换成HSV,从而求色相值
# 参数：r,g,b值
def rgb_to_hsv(r, g, b):
        maxRGB = max(r, g, b)
        minRGB = min(r, g, b)
        d = maxRGB - minRGB
        v = maxRGB
        if d == 0:
            return 0.0, 0.0, v
        s = d / maxRGB
        if maxRGB == r:      # 红色色相为0
            h = (g - b)/d*60 + 0
        elif maxRGB == g:  # 绿色色相为120
            h = (b - r)/d*60 + 120
        else:                          # 蓝色色相为240
            h = (r - g)/d*60 + 240
        if h < 0:
            h = h + 360
        return round(h, 2), s, v
# r, g, b = 255, 255, 0
# print(rgb_to_hsv(r, g, b))


# 功能：读取图片，求其平均色相值
# 参数：图片路径和名称（图片统一放在hue_image文件夹下）
def hue_of_image(path,*mybox):
    filename = path
    im = Image.open(filename)
    if mybox and len(mybox)==4:
        print(mybox)
        box=(mybox[0],mybox[1],mybox[0]+mybox[2],mybox[1]+mybox[3])
        im=im.crop(box) #CROP的参数是左上角坐标和左下角坐标！！！
    pix = im.load()
    width = im.size[0]
    height = im.size[1]
    sum_hue = 0
    hue_matrix = [[0 for i in range(width)] for i in range(height)]
    # 求图片对象位置的色相值矩阵
    for x in range(width):
        for y in range(height):
            r, g, b = pix[x, y][0:3]
            # 为什么有时候pix返回四个数？
            single_hue = rgb_to_hsv(r, g, b)[0]
            hue_matrix[y][x] = single_hue
            # 测试表明,pix[x,y]读取顺序为一列一列的读(第一个下标为列指标)
            # 因此此处的下标为[y][x],也是按列赋值(第一个下标为行指标)
            sum_hue += single_hue
    average_hue = round(sum_hue / (width * height), 2)
    print(average_hue)
    # filename = path.split('\\')[-1]  # 使用双斜杠而不是斜杠,因为斜杠有时会被当成转义字符
    # plt.title('hue image of '+filename
    # draw_image(hue_matrix)
    return average_hue, hue_matrix


# 功能：把矩阵转换成图片,按照值的大小映射颜色
# 参数：一个二维数值矩阵,此处为300x300的色相值矩阵
def draw_image(matrix):

    plt.figure("Hue image",figsize=(3,3),dpi=100)
    #根据需求设置分辨率,此处为(300*300像素)
    plt.imshow(matrix, cmap=plt.cm.rainbow, vmin=0, vmax=360)
    # vmin 和 vmax可根据实验数据的范围进行调节
    plt.colorbar()   #显示颜色条
    plt.axis('off')
    # plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.show()

#
# print(hue_of_image("C:/Users/yintao/Desktop/1.png",0,0,100,100)[0])
# draw_image(hue_of_image("C:/Users/yintao/Desktop/1.png",0,0,100,100)[1])
