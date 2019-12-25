import RPi.GPIO as GPIO
import time
import numpy
import json
import queue
import threading
from firebase import firebase

firebase = firebase.FirebaseApplication("https://tourguide-d36af.firebaseio.com/", None)

GPIO.setmode(GPIO.BCM)
 
GPIO_TRIGGER = 15
GPIO_ECHO = 14
 
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

free_parking_place = int(firebase.get('Attractioninfo/5/parking/TG/0', None))
data = queue.Queue()

def distance_measure():
    GPIO.output(GPIO_TRIGGER, True)
 
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
  
    Start_time = time.time()
    Stop_time = time.time()
 
    while GPIO.input(GPIO_ECHO) == 0:
        Start_time = time.time()
 
    while GPIO.input(GPIO_ECHO) == 1:
        Stop_time = time.time()
 
    distance = ((Stop_time - Start_time) * 34300) / 2
    return distance

def sensor_check():

    global data
    global free_parking_place
    distance = 90
    amount = 0
    path = 'a'

    while True:

        distance_check = ["0","0"]
        i = j = 0
        
        while i < 2 :
            distance1 = distance_measure()
            print ("distance = %.1f cm" % distance1)
            time.sleep(0.2)
            # "102" is the distance between car and sensor
            if distance1 > distance :
                i = 0
                distance_check[i] = '0'
            else :
                distance_check[i] = distance1
                i += 1
                print("the car comes")

        distance_bool = numpy.array(distance_check)
        b = (distance_bool <= distance).all()
        b.astype(numpy.int)
        distance_check.clear()

        distance_check = ["0","0"]
        while j < 2:
            distance2 = distance_measure()
            print ("distance = %.1f cm" % distance2)
            time.sleep(0.2)
            # "102" is the distance between car and sensor
            if distance2 < distance:
                j = 0
                distance_check[j] = '0'
            else :
                distance_check[j] = distance2
                j += 1
                print("the car already passes")
        distance_bool = numpy.array(distance_check)
        c = (distance_bool >= distance).all()
        c.astype(numpy.int)
        distance_check.clear()

        log = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " distance_state1 =" + str(distance1) + " distance_state2 =" + str(distance2) + "free parking place = " + str(free_parking_place) + '\n'
        
        if b and c:
            data.put(-1)
            if free_parking_place > 0:
                print ("free parking place - 1")
                
                if amount > 10000:
                    path = 'w'
                    amount = 0
                else:
                    path = 'a'
                with open("underground_entrance_log.txt",path) as f:
                    f.write(log)
                amount +=1
            else:
                free_parking_place = 0
                print ("parking place is full")
                with open("underground_entrance_log.txt",path) as f:
                    f.write(log)

def upload_info():
    global data
    global free_parking_place
    while True:
        if data.empty() != True:
            check = 0
            while check == 0:
                try:
                    free_parking_place = int(firebase.get('Attractioninfo/5/parking/TG/0', None))
                    if free_parking_place > 0:
                        free_parking_place = data.get() + free_parking_place
                        firebase.put('Attractioninfo/5/parking/TG', "0", str(free_parking_place))
                        print("successfully upload data")
                        check = 1
                except:
                    with open("underground_entrance_log.txt",'a') as f:
                        f.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) )
                        f.write("data upload failed\n")
                    time.sleep(5)

if __name__ == '__main__':

    sensor = threading.Thread(target = sensor_check)
    upload = threading.Thread(target = upload_info)
    
    sensor.setDaemon(True)
    upload.setDaemon(True)

    sensor.start()
    upload.start()

    sensor.join(1)
    upload.join(1)

    while True:
        try:
            pass
        except KeyboardInterrupt:
            print("stop")
            GPIO.cleanup()
            exit()