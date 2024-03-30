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
kit = ServoKit(channels=16)


class CameraWidget(Image):
    def _init_(self, **kwargs):
        super(CameraWidget, self)._init_(**kwargs)
        self.capture = cv2.VideoCapture(0)  # Assurez-vous que l'indice de votre caméra est correct
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        Clock.schedule_interval(self.update, 1.0 / 30)

    def update(self, *args):
        ret, frame = self.capture.read()
        if ret:
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
            "Administrer médicament", "Nettoyer plaie", "Utiliser caméra",
            "Saluer", "Scanner l'environnement", "Mode veille",
            "Analyse audio", "Détection d'objet", "Suivi de cible", "Mode exploration"
        ]
        for action in actions:
            btn = Button(text=action)
            btn.bind(on_press=self.execute_ia_action)
            ia_actions_layout.add_widget(btn)

        manual_controls_layout = BoxLayout(orientation='vertical', size_hint=(0.7, 1))
        slider_layout = GridLayout(cols=2, spacing=10, padding=10, size_hint=(1, 0.3))
        for i in range(6):
            slider = Slider(min=0, max=180, value=0, orientation='horizontal')
            slider_value_label = Label(text=f"{slider.value}°")
            slider.bind(
                value=lambda instance, value, lbl=slider_value_label, index=i: self.update_servo_angle(instance, value,
                                                                                                       lbl, index))
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
            kit.servo[0].angle = 90
            kit.servo[1].angle = 67
            kit.servo[2].angle = 63
            kit.servo[3].angle = 90
            kit.servo[4].angle = 120
            kit.servo[5].angle = 160

    def update_servo_angle(self, instance, value, lbl, index):
        lbl.text = f"{int(value)}°"
        # Assuming each slider corresponds to a servo (e.g., 0 to 4). Adjust the index as needed.
        servo_index = index  # Update this if you have a specific mapping of sliders to servos
        kit.servo[servo_index].angle = int(value)


if _name_ == '_main_':
    RobotInterfaceApp().run()