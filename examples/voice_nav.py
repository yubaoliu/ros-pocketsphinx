#!/usr/bin/python
import rospy

from geometry_msgs.msg import Twist
from std_msgs.msg import String
from math import copysign
from sound_play.libsoundplay import SoundClient

class VoiceNav(object):
    """Class to handle turtlebot simulation control using voice"""
    def __init__(self): 

        self.max_speed = rospy.get_param("max_speed", 0.4)
        self.max_angular_speed = rospy.get_param("max_angular_speed", 1.5)
        self.speed = rospy.get_param("start_speed", 0.2)
        self.angular_speed = rospy.get_param("start_angular_speed", 0.5)
        self.linear_increment = rospy.get_param("linear_increment", 0.05)
        self.angular_increment = rospy.get_param("angular_increment", 0.4)
        self.paused = False
        # Default values for turtlebot_simulator
        # self.speed = 0.2
        # Intializing message type
        self.cmd_vel = Twist()

        # initialize node
        rospy.init_node("voice_nav")
        rospy.on_shutdown(self.shutdown)

             # We don't have to run the script very fast
        self.rate = rospy.get_param("rate", 5)
        r = rospy.Rate(self.rate)

        # Init Soud playback
                  
        # Set the default TTS voice to use  
        self.voice = rospy.get_param("~voice", "voice_don_diphone")  
          
        # Set the wave file path if used  
        # self.wavepath = rospy.get_param("~wavepath", script_path + "/../sounds")  
          
        self.soundhandle =SoundClient()
        # Wait a moment to let the client connect to the  
        # sound_play server  
        rospy.sleep(1)
        # Make sure any lingering sound_play processes are stopped.  
        self.soundhandle.stopAll() 

        # Initializing publisher with buffer size of 10 messages
        self.cmd_vel_pub = rospy.Publisher("~cmd_vel", Twist, queue_size=10) #mobile_base/commands/velocity

        # Subscribe to kws output, /kws_data
        rospy.Subscriber("grammar_data", String, self.parse_asr_result)

        # A mapping from keywords or phrases to commands
        self.keywords_to_command = {'stop': ['stop', 'stop stop', 'shut down', 'turn off', 'help me'],
                                    'slower': ['slow down'],
                                    'faster': ['speed up'],
                                    'forward': ['go forward', 'go ahead', 'go straight', 'move forward', 'forward'],
                                    'backward': ['go back', 'move backward'],
                                    'rotate left': ['rotate left'],
                                    'rotate right': ['rotate right'],
                                    'turn left': ['turn left'],
                                    'turn right': ['turn right'],
                                    'quarter': ['quarter speed'],
                                    'half': ['half speed', 'slow down', 'speed down'],
                                    'full': ['full speed', 'hurry up', 'speed up'],
                                    'pause': ['pause speech'],
                                    'continue': ['continue speech']}
        rospy.loginfo("Ready to receive voice commands")

        # Announce that we are ready for input  
        # self.soundhandle.playWave(self.wavepath + "/R2D2a.wav")  
        rospy.sleep(1)  
        self.soundhandle.say("Ready", self.voice)  
        rospy.loginfo("Say one of the navigation commands...")  
  
                    
        while not rospy.is_shutdown():
            self.cmd_vel_pub.publish(self.cmd_vel)
            r.sleep()
        # rospy.spin()


    def get_command(self, data):
        # Attempt to match the recognized word or phrase to the 
        # keywords_to_command dictionary and return the appropriate
        # command
        for (command, keywords) in self.keywords_to_command.iteritems():
            for word in keywords:
                if data.find(word) > -1:
                    return command
        

    def parse_asr_result(self, msg):
        rospy.loginfo("Command: " + str(msg.data))
        # Get the motion command from the recognized phrase
        command = self.get_command(msg.data.lower())
        
        if command != None:
            self.soundhandle.say(str(command), self.voice)  

        # Log the command to the screen
        rospy.loginfo("Command: " + str(command))
        
        # If the user has asked to pause/continue voice control,
        # set the flag accordingly 
        if command == 'pause':
            self.paused = True
        elif command == 'continue':
            self.paused = False
        
        # If voice control is paused, simply return without
        # performing any action
        if self.paused:
            return       
        
        # The list of if-then statements should be fairly
        # self-explanatory
        if command == 'forward':    
            self.cmd_vel.linear.x = self.speed
            self.cmd_vel.angular.z = 0
            
        elif command == 'rotate left':
            self.cmd_vel.linear.x = 0
            self.cmd_vel.angular.z = self.angular_speed
                
        elif command == 'rotate right':  
            self.cmd_vel.linear.x = 0      
            self.cmd_vel.angular.z = -self.angular_speed
            
        elif command == 'turn left':
            if self.cmd_vel.linear.x != 0:
                self.cmd_vel.angular.z += self.angular_increment
            else:        
                self.cmd_vel.angular.z = self.angular_speed
                
        elif command == 'turn right':    
            if self.cmd_vel.linear.x != 0:
                self.cmd_vel.angular.z -= self.angular_increment
            else:        
                self.cmd_vel.angular.z = -self.angular_speed
                
        elif command == 'backward':
            self.cmd_vel.linear.x = -self.speed
            self.cmd_vel.angular.z = 0
            
        elif command == 'stop': 
            # Stop the robot!  Publish a Twist message consisting of all zeros.         
            self.cmd_vel = Twist()
        
        elif command == 'faster':
            self.speed += self.linear_increment
            self.angular_speed += self.angular_increment
            if self.cmd_vel.linear.x != 0:
                self.cmd_vel.linear.x += copysign(self.linear_increment, self.cmd_vel.linear.x)
            if self.cmd_vel.angular.z != 0:
                self.cmd_vel.angular.z += copysign(self.angular_increment, self.cmd_vel.angular.z)
            
        elif command == 'slower':
            self.speed -= self.linear_increment
            self.angular_speed -= self.angular_increment
            if self.cmd_vel.linear.x != 0:
                self.cmd_vel.linear.x -= copysign(self.linear_increment, self.cmd_vel.linear.x)
            if self.cmd_vel.angular.z != 0:
                self.cmd_vel.angular.z -= copysign(self.angular_increment, self.cmd_vel.angular.z)
                
        elif command in ['quarter', 'half', 'full']:
            if command == 'quarter':
                self.speed = copysign(self.max_speed / 4, self.speed)
        
            elif command == 'half':
                self.speed = copysign(self.max_speed / 2, self.speed)
            
            elif command == 'full':
                self.speed = copysign(self.max_speed, self.speed)
            
            if self.cmd_vel.linear.x != 0:
                self.cmd_vel.linear.x = copysign(self.speed, self.cmd_vel.linear.x)

            if self.cmd_vel.angular.z != 0:
                self.cmd_vel.angular.z = copysign(self.angular_speed, self.cmd_vel.angular.z)
                
        else:
            return

        self.cmd_vel.linear.x = min(self.max_speed, max(-self.max_speed, self.cmd_vel.linear.x))
        self.cmd_vel.angular.z = min(self.max_angular_speed, max(-self.max_angular_speed, self.cmd_vel.angular.z))


    def shutdown(self):
        """
        command executed after Ctrl+C is pressed
        """
        rospy.loginfo("Stop ASRControl")
        self.cmd_vel_pub.publish(Twist())
        rospy.sleep(1)


if __name__ == "__main__":
    VoiceNav()
