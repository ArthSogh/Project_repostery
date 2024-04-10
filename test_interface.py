from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.config import Config
import cv2
import numpy as np
from adafruit_servokit import ServoKit
from time import sleep

Config.set('graphics', 'fullscreen', 'true')
kit=ServoKit(channels=16)


class CameraWidget(Image):
    def __init__(self, **kwargs):
        super(CameraWidget, self).__init__(**kwargs)
        self.capture = cv2.VideoCapture(0)  # Assurez-vous que l'indice de votre caméra est correct
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        Clock.schedule_interval(self.update, 1.0 / 30)

    def update(self, *args):
        ret, frame = self.capture.read()
        if ret:
            
            # Rotation de la frame de 90 degrés
            (h, w) = frame.shape[:2]  # obtenir les dimensions de l'image
            center = (w // 2, h // 2)  # trouver le centre de l'image

            # Calculer la matrice de rotation pour tourner l'image de 90 degrés autour du centre sans échelle
            M = cv2.getRotationMatrix2D(center, 90, 1.0)

            # Appliquer la rotation
            frame = cv2.warpAffine(frame, M, (w, h))
            # Convertir l'image BGR en HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Définir la plage de couleur rouge dans HSV
            lower_red = np.array([0, 120, 120])
            upper_red = np.array([10, 255, 255])
            mask1 = cv2.inRange(hsv, lower_red, upper_red)

            lower_red = np.array([170, 120, 120])
            upper_red = np.array([180, 255, 255])
            mask2 = cv2.inRange(hsv, lower_red, upper_red)

            # Combinaison des deux masques pour obtenir le masque final de la couleur rouge
            mask = mask1 + mask2

            # Trouver les contours dans le masque
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                # Trouver le plus grand contour en fonction de l'aire et calculer son centre
                largest_contour = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    # Dessiner un cercle au centre du contour
                    cv2.circle(frame, (cX, cY), 5, (255, 255, 255), -1)  # Rayon augmenté pour plus de visibilité

            # Affichage de l'image avec le point central de la tache rouge
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tostring()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.texture = texture

    def on_stop(self):
        self.capture.release()

class RobotInterfaceApp(App):
    def build(self):
        main_layout = BoxLayout(orientation='horizontal')

        ia_actions_layout = GridLayout(cols=2, spacing=10, padding=10, size_hint=(0.3, 1))
        actions = [
            "Administrer", "Nettoyer plaie",
            "Saluer", "Scanner", "Détection d'objet", "Exploration"
        ]
        for action in actions:
            btn = Button(text=action)
            btn.bind(on_press=self.execute_ia_action)
            ia_actions_layout.add_widget(btn)

        manual_controls_layout = BoxLayout(orientation='vertical', size_hint=(0.7, 1))
        slider_layout = GridLayout(cols=2, spacing=10, padding=10, size_hint=(1, 0.3))
        for i in range(6):
            slider = Slider(min=0, max=180, value=45, orientation='horizontal')
            slider_value_label = Label(text=f"{slider.value}°")
            slider.bind(value=lambda instance, value, lbl=slider_value_label, index=i: self.update_servo_angle(instance, value, lbl, index))
            slider_layout.add_widget(slider)
            slider_layout.add_widget(slider_value_label)
        manual_controls_layout.add_widget(slider_layout)

        self.camera_widget = CameraWidget(size_hint=(1, 0.7))  # Assuming this is defined
        manual_controls_layout.add_widget(self.camera_widget)

        main_layout.add_widget(ia_actions_layout)
        main_layout.add_widget(manual_controls_layout)

        return main_layout

    def execute_ia_action(self, instance):
        print(f"Executing IA action: {instance.text}")
        if instance.text == "Saluer":
            sleep(3)
            L_saluer = [(0,84),(1,110),(2,45),(3,66),(4,86),(5,117)]
            for i in L_saluer:
                if i[0] == 1 or i[0] == 2:
                    kit.servo[i[0]].set_pulse_width_range(min_pulse = 500, max_pulse = 1750)
                else:
                    kit.servo[i[0]].set_pulse_width_range(min_pulse = 500, max_pulse = 2500)
                kit.servo[i[0]].angle_position = i[1]
            print(L_saluer)
                        
        if instance.text == "Exploration":
            sleep(2)
            kit.servo[0].angle_position = 45
            sleep(1)
            kit.servo[4].angle_position = 81
            sleep(1)
            kit.servo[3].angle_position = 30
            sleep(1)
            kit.servo[1].angle_position = 50
            kit.servo[2].angle_position = 45
            sleep(1)
            kit.servo[1].angle_position = 33
            kit.servo[2].angle_position = 36
            sleep(1)
            kit.servo[1].angle_position = 10
            sleep(5)
            kit.servo[5].angle_position = 10
                        
        if instance.text == "Détection d'objet":
            sleep(2)
            kit.servo[0].angle_position = 0
            kit.servo[4].angle_position = 81
            kit.servo[5].angle_position = 70
            kit.servo[3].angle_position = 30
            kit.servo[1].angle_position = 50
            kit.servo[2].angle_position = 45
            kit.servo[1].angle_position = 33
            kit.servo[2].angle_position = 36
            sleep(1)
            kit.servo[1].angle_position = 20
            sleep(5)
            kit.servo[5].angle_position = 170
            
        if instance.text == "Administrer":
            sleep(1)
            kit.servo[1].angle_position = 75
            kit.servo[5].angle_position = 20
            sleep(1)
            kit.servo[3].angle_position = 20
            kit.servo[5].angle_position = 160
            sleep(1)
            kit.servo[1].angle_position = 120
            kit.servo[3].angle_position = 44
            sleep(2)
            kit.servo[0].angle_position = 140
            kit.servo[4].angle_position = 117
            kit.servo[1].angle_position = 99
            kit.servo[2].angle_position = 72
            kit.servo[1].angle_position = 65
            sleep(5)
            
        if instance.text == "Nettoyer plaie":
            sleep(3)
            kit.servo[3].angle_position = 32
            sleep(2)
            kit.servo[1].angle_position = 84
            sleep(2)
            kit.servo[5].angle_ = 40
            
            

                        
    def update_servo_angle(self, instance, value, lbl, index):
        lbl.text = f"{int(value)}°"
        # Assuming each slider corresponds to a servo (e.g., 0 to 4). Adjust the index as needed.
        servo_index = index  # Update this if you have a specific mapping of sliders to servos
        kit.servo[servo_index].angle = int(value)


if __name__ == '__main__':
    RobotInterfaceApp().run()

