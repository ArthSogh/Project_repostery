from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.graphics.texture import Texture
from kivy.config import Config
from kivy.uix.image import Image

from kivy.core.window import Window
import cv2
import numpy as np
import threading

# Config.set('graphics', 'fullscreen', 'true')
Config.set('graphics', 'width', '1066')
Config.set('graphics', 'height', '768')


class CameraThread(threading.Thread):
    def __init__(self):
        super(CameraThread, self).__init__()
        self.running = False
        print("Name of the current thread :", threading.current_thread().name)

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
        image = Image(source='arm_b.png', size_hint=(1, 1), height=100)
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
                         size_hint=(0.5, 0.5),
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
            # Label pour afficher le numéro du slider
            label = Label(markup=True,
                          text=f"[b]{i}[/b]",
                          size_hint=(0.05, None),
                          height=30,
                          outline_color =(48/255, 84/255, 150/255, 1))

            slider_layout.add_widget(label)

            # Slider
            slider = Slider(min=0, max=180,
                            value_track=True,
                            value_track_color =(48/255, 84/255, 150/255, 1),
                            value=45,
                            orientation='horizontal')

            slider.bind(value=self.on_slider_change)
            slider_layout.add_widget(slider)

        main_layout.add_widget(slider_layout)

        return main_layout

    def on_button_press(self, instance):
        print(f"Button '{instance.text}' pressed")

    def on_slider_change(self, instance, value):
        print(f"Slider value changed: {value}")

    def on_start(self):
        self.camera_thread.start()

    def on_stop(self):
        self.camera_thread.stop()


if __name__ == '__main__':
    RobotInterfaceApp().run()
