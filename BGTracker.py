import sys
import tkinter as tk
import glob
from PIL import Image, ImageTk
import sqlite3
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os.path

# global variable where all the images are stored so they can be accessed when a window gets relaunched
images = []
hero_names = []

# setting up connection with sqlite db
connect = sqlite3.connect('BGTracking.db')
c = connect.cursor()
c.execute('CREATE TABLE IF NOT EXISTS stats (hero_id INTEGER, Placement INTEGER, Rating INTEGER)')


class SelectHero:

    def __init__(self, master):
        self.master = master
        self.master.resizable(False, False)
        self.frame = tk.Frame(master)
        self.frame.pack()

        # creating all the buttons (heroes) for the user to select, 34 total heroes, 9 on each line, 7 on the last
        btns = []

        r = 0
        c = 0

        for i in range(0, len(images)):
            btns.append(tk.Button(self.frame, text=i, image=images[i],
                                  command=lambda p=i: self.hero_selected_window(p)).grid(row=r, column=c))
            c += 1
            if c == 9:  # start a new row before the current row exceeds 9 heroes
                c = 0
                r += 1

        # additional options for the player
        stats = tk.Button(self.frame, text="Rating Graph", command=lambda: self.see_stats()).grid(row=3, column=7,
                                                                                                  pady=(0, 0))
        hero_stats = tk.Button(self.frame, text="Hero Stats", command=lambda: self.see_hero_stats()).grid(row=3,
                                                                                                          column=8,
                                                                                                          pady=(0, 0))

        # have to handle the resizing first that comes with importing the pictures onto the buttons, else it wont work
        center(self.master)

    def hero_selected_window(self, hero_id):
        hero_window = tk.Toplevel(self.master)
        hs = HeroSelectedWindow(hero_window, hero_id)
        center(hero_window)

    def see_stats(self):
        stat_window = tk.Toplevel(self.master)
        sw = SeeStats(stat_window)
        center(stat_window)

    def see_hero_stats(self):
        hero_stat_window = tk.Toplevel(self.master)
        hsw = HeroStats(hero_stat_window)
        center(hero_stat_window)


class HeroSelectedWindow:
    def __init__(self, master, hero_id):
        self.master = master
        self.master.title("Logging")
        self.master.resizable(False, False)
        self.frame = tk.Frame(self.master)
        self.frame.pack()

        # storing the background image
        path = os.path.dirname(os.path.abspath(__file__))
        bg = Image.open(path + r"\background.png")
        w, h = bg.size
        # crops the background
        left = (w / 4)
        right = (3 * w / 4)
        upper = (h / 4)
        lower = (3 * h / 4)

        bg = bg.crop([left, upper, right, lower])
        bg = bg.resize((int(w / 2), int(h / 2)), Image.ANTIALIAS)
        image = ImageTk.PhotoImage(bg)
        image.image = image  # keeping a reference to it doesn't get garbage collected
        bgImage = tk.Label(self.frame, image=image).grid()

        clicked = tk.IntVar()

        hero = tk.Label(self.frame, image=images[hero_id]).grid(row=0, column=0, pady=(0, 300))

        placement = tk.Label(self.frame, text="Placement", width=8).grid(row=0, column=0, pady=(15, 0), padx=(0, 125))
        choices = tk.OptionMenu(self.frame, clicked, 1, 2, 3, 4, 5, 6, 7, 8).grid(row=0, column=0, pady=(15, 0),
                                                                                  padx=(118, 0))

        ratingText = tk.Label(self.frame, text="Rating", width=8).grid(row=0, column=0, pady=(100, 0), padx=(0, 125))

        # Restricts the user from typing anything else in but numbers using validatecommand
        vcmd = (self.frame.register(self.check_if_number))
        rating = tk.Entry(self.frame, validate='all', validatecommand=(vcmd, '%P'), width=15)
        rating.grid(row=0, column=0, pady=(100, 0), padx=(75, 0))

        submitButton = tk.Button(self.frame, text='Submit', width=12,
                                 command=lambda: self.submit(hero_id, clicked, rating)).grid(row=0, column=0,
                                                                                             pady=(400, 0))

    def check_if_number(self, P):
        return P.isdigit()

    def submit(self, hero_id, clicked, rating):
        c.execute(f'INSERT INTO stats(hero_id, Placement, Rating) VALUES ({hero_id},{clicked.get()},{rating.get()})')
        connect.commit()
        self.master.destroy()


class SeeStats:

    def __init__(self, master):
        self.master = master
        self.master.title('Rating graph')
        self.master.resizable(False, False)
        self.frame = tk.Frame(self.master)
        self.frame.config(bg='white')
        self.frame.pack()

        f = Figure(figsize=(7, 7), dpi=100)
        a = f.add_subplot(111)

        # retrieving data from sqlite to plot into a graph
        c.execute("SELECT Rating FROM stats")
        rows = c.fetchall()

        # shows the user an empty graph if there's no data to display
        if len(rows) != 0:
            first_rating = str(rows[0])
            current_rating = str(rows[-1])
            difference = int(current_rating[1:-2]) - int(first_rating[1:-2])

            if difference > 0:
                difference = "+" + str(difference)

            # retrieving placement data to get average
            c.execute("SELECT Placement FROM stats")
            rows2 = c.fetchall()
            average = sum(pair[0] for pair in rows2) / len(rows2)

            # getting all 1st placements
            c.execute(f"SELECT Placement FROM stats where Placement = 1")
            rows_1st = c.fetchall()

            label = tk.Label(self.frame, text="Number of games played: " + str(len(rows))
                                              + "\n Number of 1st places: " + str(len(rows_1st))
                                              + "\n Average placement: " + str(round(average, 2))
                                              + "\n\n First recorded rating: " + first_rating[1:-2]
                                              + "\n Current rating: " + current_rating[1:-2]
                                              + "\n Difference: " + str(difference),
                             bg='white', font=("44")).grid(pady=(15, 0))

            # spaghetti way to make the x axis display the correct number of games played - list starts at 0 but I need
            # the x axis to start at 1. Duplicating the first index and inserting it in front of it - then setting to
            # graph to start at 1, ignoring the 0th index.

            filler = (rows[0])
            rows.insert(0, filler)

            a.plot(rows)
            a.margins(0)
            a.set_xlim(xmin=1)
        else:
            a.plot(0)

        a.grid()

        canvas = FigureCanvasTkAgg(f, self.frame)
        canvas.get_tk_widget().grid()


class HeroStats:

    def __init__(self, master):
        self.master = master
        self.master.title('Hero Stats')
        self.frame = tk.Frame(master)
        self.frame.pack()

        # retrieving data from sqlite to plot into a graph

        f = Figure(figsize=(15, 8), dpi=100)
        a = f.add_subplot(111)
        a.set_ylabel("Average placement")
        a.set_xticks([i for i in range(0, 34)])

        hero_data = []
        hero_number_of_games = []

        # each pic in the list represents one hero, aka it has the total number of unique heroes
        for hero_id in range(0, len(images)):
            c.execute(f"SELECT * FROM stats WHERE hero_id = {hero_id}")
            rows = c.fetchall()
            # storing number of games with each hero to find the average placement for each hero
            number_of_games = 0
            placement = 0

            # placements are stored in the second column in the database so they get saved in index 1 in the tuble (a tuple reprensting one row - aka one game)
            for row in rows:
                placement += row[1]
                number_of_games += 1

            if number_of_games == 0:
                hero_data.append(0)
            else:
                average_placement = (placement / number_of_games)
                # heroes comes in sorted order so no need to store the id with the placement
                hero_data.append(average_placement)

            # need to store number of games played for each hero
            hero_number_of_games.append(number_of_games)

        # have to merge hero name + number of games together to display on the x-axis

        merged = [(hero_names[i], hero_number_of_games[i]) for i in range(0, len(hero_names))]
        formatted_merge = []
        for x in merged:
            formatted_merge.append(x[0] + "-" + str(x[1]))

        a.set_xticklabels(formatted_merge, rotation=45, horizontalalignment='right')

        for i, v in enumerate(hero_data):
            rounded_v = float("{:.2f}".format(v))
            if v > 0:
                a.text(i-0.4, v+0.1, str(rounded_v), color='blue', fontweight='bold')

        bar_chart = a.bar([i for i in range(0, 34)], hero_data, 0.8)

        canvas = FigureCanvasTkAgg(f, self.master)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


def center(win):
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()


def main():
    root = tk.Tk()
    root.title('Battlegrounds Tracking')

    # changing directory to the place where the script is being executed - can locate the pictures this way
    os.chdir(sys.path[0])
    path = os.path.dirname(os.path.abspath(__file__)) + r"\BGpics"

    # saving all image portraits to a list
    for img_name in glob.glob(path + "/*.png"):

        hero = img_name.split(path, 1)[1]
        if hero[1:-4] == "LK":
            hero_names.append(hero[1:-4].upper())
        else:
            hero_names.append(hero[1:-4].capitalize())

        img = Image.open(img_name)
        w, h = img.size
        # crops the pictures, removing background and border
        left = (w / 4)
        right = (3 * w / 4)
        upper = (h / 4)
        lower = (3 * h / 4)

        img = img.crop([left, upper, right, lower])
        img = img.resize((int(w / 4), int(h / 4)), Image.ANTIALIAS)  # resize the picture to make the buttons smaller
        image = ImageTk.PhotoImage(img)

        images.append(image)

    app = SelectHero(root)

    root.mainloop()


if __name__ == '__main__':
    main()
    connect.close()
