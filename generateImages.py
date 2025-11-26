import numpy as np
from PIL import Image
import os


THRESHOLD = 150 #Value between 0 and 255 which is the boundary between black and white 

def generateImages(frontCopperPath, backCopperPath, outlinePath, outputPath = os.path.expanduser('~/Downloads')):
    outlineImg = Image.open(outlinePath).convert('RGB')
    outlineArr = np.array(outlineImg)
    print(outlineArr)
    #makes output directory if it does not exist
    if not os.path.isdir(outputPath):
         print("output path does not exist")

    #generates the first outline to be cut
    topLeftCorner, bottomRightCorner = findBoardBoundaries(outlineArr)
    padding = generateFirstCut(outlineArr.shape[1], outlineArr.shape[0], topLeftCorner, bottomRightCorner,outputPath, boundaryOffset=32)

    #resized
    frontCopper = Image.open(frontCopperPath).convert('RGB')
    resizeImg(frontCopper, padding, os.path.join(outputPath, 'front-copper.png'))
    
    #flips the back traces and outline since the copper with be flipped in the mill
    #after milling the top layer
    backCopper = Image.open(backCopperPath)
    resizeImg(backCopper.transpose(Image.FLIP_LEFT_RIGHT), padding, os.path.join(outputPath, 'back-copper.png'))

    resizeImg(outlineImg.transpose(Image.FLIP_LEFT_RIGHT), padding, os.path.join(outputPath, 'back-outline.png'))









"""
generateFirstCut
    - generates the a 1000 DPI png for the cut out of the first side of the board with the tabs 
    given the boundary for the original pcb
    params:
        - imgWidth (int): width of the original image
        - imgHeight (int): height of the original image 
        - topLeftCorner ([int,int]): position of the top left corner of the bounding box of the board
        - bottomLeftCorner ([int,int]): position of the bottom left corner of the bounding box of the board
        - endMillDiameter (int): diameter of the endmill in mil (default is 31 mil for a 1/32 in endmill, which is 31.25 mil)
        - boundaryOffset (int): how many mils you want of buffer around the original board 
    return:
        - padding around the image (padding measured same as in css)


"""

def generateFirstCut(imgWidth, imgHeight, topLeftCorner, bottomRightCorner,outputPath, endMillDiameter = 31, boundaryOffset = 0):
    totalImagePadding = 2 * (boundaryOffset+endMillDiameter) #make sure there is enough
    finalImageWidth = imgWidth + totalImagePadding
    finalImageHeight = imgHeight + totalImagePadding
    
    innerBoxTopX, innerBoxTopY = topLeftCorner[0] - boundaryOffset + totalImagePadding//2, topLeftCorner[1] - boundaryOffset + totalImagePadding//2
    innerBoxBottomX, innerBoxBottomY = bottomRightCorner[0] + boundaryOffset + totalImagePadding//2, bottomRightCorner[1] + boundaryOffset + totalImagePadding//2

    imgArr = [[ [0,0,0] for _ in range(finalImageWidth)] for _ in range(finalImageHeight)]
    boardInnerWidth = innerBoxBottomX - innerBoxTopX 
    boardInnerHeight = innerBoxBottomY - innerBoxTopY
    
    #generates inner white square of outlien
    for i in range(innerBoxTopY, innerBoxBottomY + 1):
        for j in range(innerBoxTopX, innerBoxBottomX + 1):
                imgArr[i][j] = [255,255,255]

    boardPegWidth = boardInnerWidth - round(boardInnerWidth/2)
    topBoardPegStart = innerBoxBottomX - boardPegWidth
    bottomBoardPegStart = innerBoxTopX + boardPegWidth

    #generates top and bottom pegs
    for i in range(endMillDiameter):
        for j in range(boardPegWidth - i + 1):
             imgArr[innerBoxTopY - i][topBoardPegStart + j + i] = [255,255,255]
             imgArr[innerBoxBottomY + i][bottomBoardPegStart - j - i] = [255,255,255]

    boardPegHeight = boardInnerHeight - round(boardInnerHeight / 2)
    topBoardPegStart = innerBoxTopY + boardPegHeight
    bottomBoardPegStart = innerBoxBottomY - boardPegHeight

    #generates left and right pegs 
    for i in range(endMillDiameter):
         for j in range(boardPegHeight - i  + 1):
              imgArr[topBoardPegStart - j - i][innerBoxBottomX + i] = [255,255,255]
              imgArr[bottomBoardPegStart + j + i][innerBoxTopX - i] = [255,255,255]

    #generates corners connecting the pegs
    for i in range(endMillDiameter):
        for j in range(endMillDiameter):
             imgArr[innerBoxTopY - i][innerBoxBottomX + j - i] = [255,255,255]
             imgArr[innerBoxBottomY + i][innerBoxTopX - j + i ] = [255,255,255]
             
         
    npArr = np.array(imgArr, dtype=np.uint8)
    img = Image.fromarray(npArr, 'RGB')
    img.save(os.path.join(outputPath, 'front-outline.png'), dpi=(1000,1000))
    print(f'saved image: front-outline.png')
    return totalImagePadding//2


"""
    findBoardBoundaries: 
        - takes in a numpy array representing the rgb image of a board outline from gerber2img and returns the
        top left corner and bottom right corner of the bounding box of the board 
        params:
            imgArr [int, int]: numpy array of final outline of the border
            threshold (int): threshold value for cutoff between black and white
"""
def findBoardBoundaries(imgArr, threshold = 150):
    intensity = imgArr.sum(axis = 2)
    thresholdedArr = (intensity >= threshold).astype(int)
    maxColumnPixels = thresholdedArr.max(axis=0)
    columnWhitePixelIndices = np.indices(maxColumnPixels.shape)[0][maxColumnPixels == 1]
    boundingBoxLeft = columnWhitePixelIndices.min()
    boundingBoxRight = columnWhitePixelIndices.max()

    maxRowPixels = thresholdedArr.max(axis = 1)
    rowWhitePixelIndices = np.indices(maxRowPixels.shape)[0][maxRowPixels == 1]
    boundingBoxTop = rowWhitePixelIndices.min()
    boundingBoxBottom = rowWhitePixelIndices.max()

    return (boundingBoxLeft, boundingBoxTop), (boundingBoxRight, boundingBoxBottom)

"""
    resizeImg:
    - takes in an original image and saves a new image with the appropriate padding of black pixels around it
    params:
        - img: PIL rgb image object
        - padding (int): number of pixels of padding around original image
        - filename (string): new filename for final image to be saved to  
"""
def resizeImg(img, padding, filename):
    imgArr = np.array(img)
    print(imgArr)
    imgHeight,imgWidth  = imgArr.shape[0], imgArr.shape[1]
    if imgArr.shape[2] == 4:
         imgArr = imgArr[:, :, :3]
    print(imgHeight,imgWidth, imgArr.shape[2])
    resizedImg = np.zeros([imgHeight + padding * 2, imgWidth +padding * 2, 3], dtype= np.uint8)
    resizedImg[padding: padding + imgHeight, padding: padding + imgWidth] = imgArr
    img = Image.fromarray(resizedImg, 'RGB')
    print(f'saved image: {filename}')
    img.save(filename, dpi=(1000,1000))

    
