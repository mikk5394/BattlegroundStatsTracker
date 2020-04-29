import tkinter as tk
import glob
from PIL import Image

class SelectHero:

    def __init__(self, master, images):
        self.master = master
        self.images = images
        self.frame = tk.Frame(master)
        self.frame.pack()

        # creating all the buttons (heroes) for the user to select, 34 total heroes, 10 on each line, 4 on the last
        btns = []

        r = 0
        c = 0
        for i in range(1, len(images)):
            btns.append(tk.Button(self.frame, image=images[i]).grid(row=r, column=c))
            c += 1
            if c == 10:                                          # start a new row when the row before exceeds 10 heroes
                c = 0
                r += 1



class mainWindow:
    pass


def main():
    root = tk.Tk()
    root.title('Battlegrounds stat tracking software')

    # saving all image portraits to a list
    path = r"C:\Users\Mikke\PycharmProjects\BattlegroundStats\BGpics"
    images = []
    for img_name in glob.glob(path + "/*.png"):
        img = tk.PhotoImage(file=img_name).subsample(3, 3)
        images.append(img)

    app = SelectHero(root, images)

    root.mainloop()


main()
