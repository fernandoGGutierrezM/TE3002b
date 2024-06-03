import rclpy
from rclpy.node import Node
import cv2
import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from std_msgs.msg import Float32

class lineFollower(Node):
    def __init__(self):
        super().__init__('line_node')

        self.valid_img = False
        self.bridge = CvBridge()

        self.sub = self.create_subscription(Image, '/video_source/raw', self.camera_callback, 10)
        self.pub = self.create_publisher(Float32, '/offset', 10)
        self.pubMean = self.create_publisher(Float32, '/meanSHT', 10)
        self.pubFilterMean = self.create_publisher(Float32, '/filterMean', 10)
        self.filteredImage = self.create_publisher(Image, '/procImage', 10)
        #self.pubCrop = self.create_publisher(Image, '/image_crop', 10)
        #self.pubMean = self.create_publisher(Float32, '/average', 10)
        self.get_logger().info('offset detector node start')
        #intialize the array to use the filtering
        self.lastMeans = [255, 255, 255, 255, 255]

        #initialize the array to store the means at every frame
        self.meanArr = []
        #Set point for the center of the image
        self.setPoint = 210
        self.meanVal = 0
        self.regressionCopy = 0

    def offset_calculator(self, frame):
        #image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        gray_flip_vertical = cv2.flip(frame, 1)
        gray_flip = cv2.flip(gray_flip_vertical, 0)

        #mask = np.zeros(gray_flip.shape[:2], dtype="uint8")
        #pts = [(640, 720), (490, 520), (840, 520), (1080, 720)]
        #cv2.fillPoly(mask, np.array([pts]), 255)
        #crop = cv2.bitwise_and(gray_flip, gray_flip, mask=mask)

        #initialize the array to store the means at every frame
        self.meanArr = []
        #Set point for the center of the image
        self.setPoint = 210
        self.meanVal = 0
        self.regressionCopy = 0

    def offset_calculator(self, frame):
        #image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        gray_flip_vertical = cv2.flip(frame, 1)
        gray_flip = cv2.flip(gray_flip_vertical, 0)

        #mask = np.zeros(gray_flip.shape[:2], dtype="uint8")
        #pts = [(640, 720), (490, 520), (840, 520), (1080, 720)]
        #cv2.fillPoly(mask, np.array([pts]), 255)
        #crop = cv2.bitwise_and(gray_flip, gray_flip, mask=mask)


        crop = gray_flip[480:720, 345:885]

        alow = crop.min()
        ahigh = crop.max()
        amax = 255
        amin = 0
        #255 10
        alpha = ((amax-amin)/(ahigh-alow))
        beta = amin - alow * alpha
        #print(crop.mean())

        correctBright = cv2.convertScaleAbs(crop, alpha=alpha, beta=beta)
#        image = cv2.cvtColor(correctBright, cv2.COLOR_RGB2BGR)

        gray_raw_image = cv2.cvtColor(correctBright, cv2.COLOR_BGR2GRAY)


        blurred = cv2.blur(gray_raw_image, (5, 7))

        ret, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        cv2.imshow("im", thresh)
        #crop = thresh[600:720, 450:950
        #self.filteredImage.publish(self.bridge.cv2_to_imgmsg(thresh, "bgr8"))

        #flipVertical = cv2.flip(crop, 1)
        #flipHorizontal = cv2.flip(flipVertical, 0)
                              # 50 200
        high_thresh = ret
        low_thresh = ret*0.1

        dst = cv2.Canny(thresh,float(low_thresh), float(high_thresh), None, 3)
        #dst = cv2.bitwise_and(dst, mask)
        cdst = cv2.cvtColor(dst, cv2.COLOR_GRAY2BGR)
        cdstP = np.copy(cdst)
        linesP = cv2.HoughLinesP(dst, 1, np.pi/180, 50, None, 50, 10)
        #np.pi/180
        arrayx1 = linesP[:,0,0]
        self.meanVal = np.mean(arrayx1)
        self.meanArr.append(self.meanVal)


        #cv2.imshow("Lines", dst)
        cv2.waitKey(1)

        #store the last five values
        self.lastMeans[4] = self.lastMeans[3]
        self.lastMeans[3] = self.lastMeans[2]
        self.lastMeans[2] = self.lastMeans[1]
        self.lastMeans[1] = self.lastMeans[0]
        self.lastMeans[0] = self.meanVal

        timeArr = list(range(0, len(self.lastMeans)))
        regression = np.poly1d(np.polyfit(timeArr, self.lastMeans, 1))
        self.regressionCopy = float(regression(2))

        #cv2.line(cdstP, (int(regression(2)), 0), (int(regression(2)), 400), (0,0,255), 3, cv2.LINE_AA)
        error = self.setPoint - float(regression(2))
        return error
    
    def camera_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            offset = self.offset_calculator(cv_image)
            self.pub.publish(Float32(data=offset))
            self.pubMean.publish(Float32(data=self.meanVal))
            self.pubFilterMean.publish(Float32(data=self.regressionCopy))
            #self.filteredImage.publish(self.bridge.cv2_to_imgmsg(self.blurred,>
            #self.filteredImage.publish(self.bridge.cv2_to_imgmsg(crop, "bgr8"))
            #self.img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            #self.valid_img = True
        except:
            self.get_logger().info('Failed to get an imageasallllllllls')

def main(args=None):
    rclpy.init(args=args)
    cv_linef = lineFollower()
    rclpy.spin(cv_linef)
    cv_linef.destroy_node()
    rclpy.shutdown()

if __name__=='__main__':
    main()