from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.graphics.texture import Texture
from kivy.config import Config
from kivy.uix.image import Image
from kivy.properties import NumericProperty

from kivy.core.window import Window
import cv2
import numpy as np
import threading

from adafruit_servokit import ServoKit
from time import sleep

# Config.set('graphics', 'fullscreen', 'true')
Config.set('graphics', 'width', '1066')
Config.set('graphics', 'height', '768')

kit=ServoKit(channels=16)

class CameraThread(threading.Thread):

    def __init__(self):
        super(CameraThread, self).__init__()
        self.running = False
        print("Name of the current thread :", threading.current_thread().name)
        red_percentage = NumericProperty(0)

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(0)
        # Modifier la résolution de capture vidéo
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Largeur de la frame
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)  # Hauteur de la frame
        while self.running:
            ret, frame = cap.read()
            if ret:
                # Rotation de la frame de 90 degrés
                (h, w) = frame.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, 0, 1.0)
                frame = cv2.warpAffine(frame, M, (w, h))

                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                lower_red = np.array([0, 120, 120])
                upper_red = np.array([10, 255, 255])
                mask1 = cv2.inRange(hsv, lower_red, upper_red)

                lower_red = np.array([170, 120, 120])
                upper_red = np.array([180, 255, 255])
                mask2 = cv2.inRange(hsv, lower_red, upper_red)

                mask = mask1 + mask2

                contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    M = cv2.moments(largest_contour)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        cv2.circle(frame, (cX, cY), 5, (255, 255, 255), -1)

                        # Calcul du pourcentage de rouge dans le contour
                        contour_mask = np.zeros_like(mask)
                        cv2.drawContours(contour_mask, [largest_contour], 0, (255), -1)
                        red_pixels = np.sum(np.logical_and(contour_mask, mask))
                        contour_area = cv2.contourArea(largest_contour)
                        percentage_red = (red_pixels / contour_area) * 100
                        print("Pourcentage de rouge dans le contour: {:.2f}%".format(percentage_red))
                        self.red_percentage = percentage_red  # Met à jour la propriété NumericProperty

                        cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
                        if 70 <= self.red_percentage <= 100:
                            print("HEMORAGIEEEEEEE")

                buf1 = cv2.flip(frame, 0)
                buf = buf1.tobytes()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.texture = texture

                cv2.imshow("Camera Feed", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        cap.release()
        cv2.destroyAllWindows()

    def stop(self):
        self.running = False

    def show_popup(self):
        popup = Popup(title='Alerte',
                      content=Label(text='Le pourcentage de rouge est entre 70% et 100%.'),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

class RobotInterfaceApp(App):

    def __init__(self):
        super(RobotInterfaceApp, self).__init__()
        self.camera_thread = CameraThread()

    def build(self):
        # Window.clearcolor = (0.4,0.4,1,1)
        # Window.clearcolor = (1,1,1,1)
        main_layout = BoxLayout(orientation='vertical', padding=5, spacing=5)

        # Layout pour les boutons en haut de l'interface
        button_layout = BoxLayout(orientation='horizontal',
                                  # size_hint=(1, 0.5),
                                  height=70,
                                  padding=5, spacing=10
                                  )

        # Ajouter une image à la place du label "logo"
        image = Image(source='logo_tr.png', size_hint=(1, 4), height=100)
        main_layout.add_widget(image)

        # text = Label(text="logo")
        # main_layout.add_widget(text)


        actions = [
            "Administrer",
            "Nettoyer plaie",
            "Saluer",
            "Scanner",
            "Détection d'objet",
            "Exploration"]

        for action in actions:
            btn = Button(text=action,
                         background_normal='',
                         background_color=(48/255, 84/255, 150/255, 1),
                         size_hint=(0.5, 0.9),
                         pos_hint ={'x':1, 'y':.2}
                         )
            # btn.background_normal = icon
            btn.bind(on_press=self.on_button_press)
            button_layout.add_widget(btn)

            # Ajout du dessin du contour orange avec RoundedRectangle
            # with btn.canvas.before:
            #     Color(48 / 255, 84 / 255, 150 / 255, 1)  # Couleur orange
            #     RoundedRectangle(size=btn.size, pos=btn.pos, radius=[58])

        main_layout.add_widget(button_layout)

        # Layout pour les sliders et leurs numéros
        slider_layout = GridLayout(cols=2, spacing=10, padding=5, size_hint=(1, None), height=300)
        for i in range(6):
            # Slider
            slider = Slider(min=0, max=180,
                            value_track=True,
                            value_track_color =(48/255, 84/255, 150/255, 1),
                            value=45,
                            orientation='horizontal')

            # Label pour afficher le numéro du slider
            label = Label(markup=True,
                          text=f"[b]{i}[/b] - {slider.value}",
                          size_hint=(0.05, None),
                          height=30,
                          outline_color =(48/255, 84/255, 150/255, 1))

            slider_layout.add_widget(label)

            slider.bind(value=lambda instance,
                                     value,
                                     lbl=label,
                                     index=i: self.on_slider_change(instance, value, lbl, index))

            slider_layout.add_widget(slider)

        main_layout.add_widget(slider_layout)

        return main_layout

    def on_button_press(self, instance):
        if instance.text == "Administrer":
            L_saluer = [(0,82),(1,110),(2,45),(3,66),(4,86),(5,117)]
            for i in L_saluer:
                if i[0] == 1 or i[0] == 2:
                    kit.servo[i[0]].set_pulse_width_range(min_pulse = 500, max_pulse = 1750)
                else:
                    kit.servo[i[0]].set_pulse_width_range(min_pulse = 500, max_pulse = 2500)
                kit.servo[i[0]].angle_position = i[1]
            print(L_saluer)
            sleep(1)
            kit.servo[1].angle_position = 75
            kit.servo[5].angle_position = 20
            sleep(1)
            kit.servo[3].angle_position = 5
            kit.servo[2].angle_position = 10
            kit.servo[5].angle_position = 160
            sleep(1.5)
            kit.servo[1].angle_position = 120
            kit.servo[3].angle_position = 44
            sleep(2)
            kit.servo[0].angle_position = 140
            kit.servo[4].angle_position = 117
            kit.servo[1].angle_position = 99
            kit.servo[2].angle_position = 72
            kit.servo[1].angle_position = 60
            sleep(5)
            L_saluer = [(0,82),(1,110),(2,45),(3,66),(4,86),(5,117)]
            for i in L_saluer:
                if i[0] == 1 or i[0] == 2:
                    kit.servo[i[0]].set_pulse_width_range(min_pulse = 500, max_pulse = 1750)
                else:
                    kit.servo[i[0]].set_pulse_width_range(min_pulse = 500, max_pulse = 2500)
                kit.servo[i[0]].angle_position = i[1]
            print(L_saluer)
            self.show_administration_popup()
            #kit.servo[0].angle_position = 80
            sleep(1)
            kit.servo[3].angle_position = 16
            sleep(1)
            kit.servo[1].angle_position = 79
            sleep(1)
            kit.servo[3].angle_position = 45
            sleep(0.5)
            kit.servo[5].angle_position = 0

        if instance.text == "Scanner":
            L_saluer = [(0, 84), (1, 110), (2, 45), (3, 66), (4, 86), (5, 117)]
            for i in L_saluer:
                 if i[0] == 1 or i[0] == 2:
                     kit.servo[i[0]].set_pulse_width_range(min_pulse=500, max_pulse=1750)
                 else:
                     kit.servo[i[0]].set_pulse_width_range(min_pulse=500, max_pulse=2500)
                 kit.servo[i[0]].angle_position = i[1]
            print(L_saluer)
            kit.servo[0].angle_position = 157
            kit.servo[1].angle_position = 110
            kit.servo[2].angle_position = 20
            kit.servo[3].angle_position = 83
            sleep(1)
            kit.servo[0].angle_position = 175
            sleep(0.1)
            kit.servo[0].angle_position = 170
            sleep(0.1)
            kit.servo[0].angle_position = 165
            sleep(0.1)
            kit.servo[0].angle_position = 160
            sleep(0.1)
            kit.servo[0].angle_position = 155
            sleep(0.1)
            kit.servo[0].angle_position = 150
            sleep(0.1)
            kit.servo[0].angle_position = 145
            sleep(0.1)
            kit.servo[0].angle_position = 140
            sleep(0.1)
            kit.servo[0].angle_position = 135
            sleep(0.1)
            kit.servo[0].angle_position = 130
            sleep(1)
            kit.servo[0].angle_position = 175
            sleep(0.1)
            kit.servo[0].angle_position = 170
            sleep(0.1)
            kit.servo[0].angle_position = 165
            sleep(0.1)
            kit.servo[0].angle_position = 160
            sleep(0.1)
            kit.servo[0].angle_position = 155
            sleep(0.1)
            kit.servo[0].angle_position = 150
            sleep(0.1)
            kit.servo[0].angle_position = 145
            sleep(0.1)
            kit.servo[0].angle_position = 140
            sleep(0.1)
            kit.servo[0].angle_position = 135
            sleep(0.1)
            kit.servo[0].angle_position = 130
            sleep(1)
            kit.servo[0].angle_position = 175
            sleep(0.1)
            kit.servo[0].angle_position = 170
            sleep(0.1)
            kit.servo[0].angle_position = 165
            sleep(0.1)
            kit.servo[0].angle_position = 160
            sleep(0.1)
            kit.servo[0].angle_position = 155
            sleep(0.1)
            kit.servo[0].angle_position = 150
            sleep(0.1)
            kit.servo[0].angle_position = 145
            sleep(0.1)
            kit.servo[0].angle_position = 140
            sleep(0.1)
            kit.servo[0].angle_position = 135
            sleep(0.1)
            kit.servo[0].angle_position = 130
            L_saluer = [(0,82),(1,110),(2,45),(3,66),(4,86),(5,117)]
            for i in L_saluer:
                if i[0] == 1 or i[0] == 2:
                    kit.servo[i[0]].set_pulse_width_range(min_pulse = 500, max_pulse = 1750)
                else:
                    kit.servo[i[0]].set_pulse_width_range(min_pulse = 500, max_pulse = 2500)
                kit.servo[i[0]].angle_position = i[1]
            print(L_saluer)
            self.hemoragie_popup()

        if instance.text == "Saluer":
            sleep(3)
            L_saluer = [(0, 84), (1, 110), (2, 45), (3, 66), (4, 86), (5, 117)]
            for i in L_saluer:
                 if i[0] == 1 or i[0] == 2:
                     kit.servo[i[0]].set_pulse_width_range(min_pulse=500, max_pulse=1750)
                 else:
                     kit.servo[i[0]].set_pulse_width_range(min_pulse=500, max_pulse=2500)
                 kit.servo[i[0]].angle_position = i[1]
            print(L_saluer)

            valeur_des_angles = ((0, 84), (1, 110), (2, 45), (3, 66), (4, 86), (5, 117))


        if instance.text == "Exploration":
            self.show_exploration_popup()


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

        if instance.text == "Nettoyer plaie":
            sleep(3)
            kit.servo[3].angle_position = 32
            sleep(2)
            kit.servo[1].angle_position = 84
            sleep(2)
            kit.servo[5].angle_ = 40

        else:
            print(f"Button '{instance.text}' pressed")

    def show_administration_popup(self):
        popup = Popup(title='Administration Réalisée',
                      content=Label(text='Administration Réalisée'),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    def hemoragie_popup(self):
        content_text = "Hémorragie 60% ! SUIVRE INSTRUCTIONS !"
        content = Label(text=content_text, font_size=16, halign='center', valign='middle')

        instructions_button = Button(text="Instructions", size_hint=(1, 0.2))
        instructions_button.background_color = (1, 0, 0, 1)  # Couleur rouge vive

        popup_content = BoxLayout(orientation='vertical')
        popup_content.add_widget(content)
        popup_content.add_widget(instructions_button)

        popup = Popup(title='Alerte', title_color=(1, 0, 0, 1),  # Couleur rouge vive
                      content=popup_content,
                      size_hint=(None, None), size=(400, 200))

        instructions_button.bind(on_release=popup.dismiss)
        popup.open()


    def show_exploration_popup(self):
        # Fonction pour valider les entrées et fermer le popup
        def validate_inputs(instance):
            # Récupération des valeurs entrées
            x_value = x_input.text
            y_value = y_input.text
            z_value = z_input.text

            # Traiter les valeurs ici...

            # Fermer le popup
            popup.dismiss()

        # Création des widgets du popup
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text="Vous êtes sur le point d'utiliser la cinématique inverse."))
        content.add_widget(Label(text="Veuillez entrer les valeurs X, Y et Z:"))

        x_input = TextInput(multiline=False, hint_text="X")
        y_input = TextInput(multiline=False, hint_text="Y")
        z_input = TextInput(multiline=False, hint_text="Z")

        content.add_widget(x_input)
        content.add_widget(y_input)
        content.add_widget(z_input)

        # Bouton de validation
        validate_button = Button(text="Valider", size_hint=(1, 0.2))
        validate_button.bind(on_release=validate_inputs)
        content.add_widget(validate_button)

        # Création du popup
        popup = Popup(title='Exploration',
                      content=content,
                      size_hint=(None, None), size=(400, 250))

        # Afficher le popup
        popup.open()

    def on_slider_change(self, instance, value, lbl, index):
        print(f"Slider value changed: {value}")
        lbl.text = f"{int(value)}°"
        # Assuming each slider corresponds to a servo (e.g., 0 to 4). Adjust the index as needed.
        servo_index = index  # Update this if you have a specific mapping of sliders to servos
        kit.servo[servo_index].angle = int(value)


    def on_start(self):
        self.camera_thread.start()

    def on_stop(self):
        self.camera_thread.stop()



if __name__ == '__main__':
    RobotInterfaceApp().run()
