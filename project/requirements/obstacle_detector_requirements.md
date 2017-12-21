Based on:
> Hane, C., Sattler, T., & Pollefeys, M. (2015). Obstacle detection for self-driving cars using only monocular cameras and wheel odometry. In 2015 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS) (pp. 5101–5108). IEEE. https://doi.org/10.1109/IROS.2015.7354095

# Interfaces
See [../3-5.5 Item definition.md]() Item definition 5.4.3 a)

# Non functional requirements
## od_NFR1
Uses sonar, camera and motion of the car to detect objects in front of the car.

# Functional requirements
## od_FR1
The system can detect objects every 0.1 ms

## od_FR2
When an object is detected it should be send to the _ACC_System_.

## od_FR2.1
The speed and distance should be send for every detected object.

## od_FR2.2
When calculating the speed of an object it is assumed that the yaw of the car does not change.

## od_FR2.3
When multiple objects are detected at the same time the objects must be send ordered by proximity. (closest first)

## od_FR3
Every object that is detected gets an unique ID.

## od_FR4
When the system is sure an object has left from the front of the car. That is it either is to far to detect or not on collision course with the car anymore regarding the current movement of the car. It will be send that the object has disappeared.

## od_FR5
When an object has disappeared the ID can be used again.
