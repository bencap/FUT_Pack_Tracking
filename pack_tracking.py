""" pack_tracking.py

This file contains classes w/ methods to build the TKinter GUI responsible for
tracking FIFA pack purchases

This file contains classes:
    * DisplayApp - Class for creating the main GUI
    * NumberListing_Dialog - Class for creating dialog box for user to enter the # of sales from a pack
    * Listing_Dialog - Class for getting details of the players being listed
    * Selling_Dialog - Class for getting details of how much a player was sold for
    * ScrolledWindow - Class for creating a scrollable window

This file contains methods:
    Global Methods:
        * string_validator( string, search ) - returns true if a string has no invalid characters

    Members of Class DisplayApp:
        * __init___( self, width, height ) - builds the initial view of the GUI
        * db_connect( self, driver, server, database, trust ) - connects the display app to a MSSQL database
        * test_connection( self ) - prints the currently connected database to the cmd line
        * loadData( self ) - Loads the data into a pandas DF from a MSSQL table
        * buildMenus( self ) - builds the menu ribbon of the GUI
        * buildStatsFrame( self ) - builds the monetary stats frame at the top of the main frame
        * buildPlayerFrame( self ) - builds the main display frame for displaying player sale records
        * buildControls( self ) - builds the control frame at the right of the GUI window
        * createButtons( self ) - Creates the buttons the user uses to control the GUI
        * createListBoxes( self ) - Creates the list boxes the user uses to control the GUI
        * packBox( self, event ) - Handles user selection of pack box members
        * costBox( self, event ) - Handles user selection of cost box members
        * handleReset( self ) - Resets the player frame to display all data
        * setBindings( self ) - Sets all keyboard, mouse, and tkinter bindings
        * handleNewPack( self ) - Controls flow for pack opening
        * postData( self ) - Posts data into a new record in the MSSQL table and displays it
        * handleSale( self ) - Controls flow for sale data entry
        * postSale( self, id, price ) - Alters MSSQL table to add the sale price
        * handleWrite( self, columns, rows, pack_id, reload, update ) - Controls flow for data writing
        * writePlayers( self, data ) - Writes the data to the frame
        * handleStats( self, data ) - Controls flow for profit calculations
        * calcStats( self, data ) - Calculates the statistics for display
        * writeStats( self, stats ) - Displays the stats calculated in the stats window
        * handleDelete( self ) - Controls flow for deleting a row entry
        * postDelete( self, id ) - Posts and commits the delete request to the sql database
        * handleQuit( self, event ) - handles closing of the GUI
        * main( self ) - creates the main loop for the GUI

    Members of Class NumberListing_Dialog:
        * body( self, master) - creates the widgets for the dialog box
        * buttonbox( self ) - creates the ok and cancel buttons for the dialog box
        * ok( self, event ) - flow for user clicking ok
        * cancel( self, event, cancelled ) - flow for user clicking cancel (and for closing the window)
        * validate( self ) - validates user entered data
        * apply( self ) - changes tk types to built-ins for returning
        * getResult( self ) - returns the user entered data
        * userCancelled( self ) - returns whether the user cancelled the window 

    Members of Class Listing_Dialog:
        * body( self, master ) - override body from NumberListing_Dialog
        * ok( self ) - override ok from NumberListing_Dialog
        * validate( self ) - override validate from NumberListing_Dialog
        * apply( self ) - override apply from NumberListing_Dialog
        * getResult_qs - gets the quick sell result
        * getResult_pack - gets the type of pack result
        * getResult_reward - gets whether the pack was a reward

    Members of Class Selling_Dialog:
        * body( self, master ) - override body from NumberListing_Dialog
        * ok( self ) - override ok from NumberListing_Dialog
        * validate( self ) - override validate from NumberListing_Dialog 
        * apply( self ) - override apply from NumberListing_Dialog
        * getResult_sale( self ) - gets the price the item was sold for

    Members of Class ScrolledWindow:
        * _bound_to_mousewheel( self, event ) - binds the mousewheel to scroll action on window entry
        * _unbound_to_mousewheel( self, event ) - unbinds the mousewheel to scroll action on window exit
        * _on_mousewheel( self, event ) - Moves the items w/in the window on scroll action
        * _configure_window( self, event ) - Configures the window on resize events

Created by Ben Capodanno on July 23rd, 2019. Updated July 31st, 2019.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import numpy as np
import pandas as pd
import random
import pyodbc
import re
import stats

# change as necessary for database
# this program expects a SQL Table with column names and types...
#
# id (primary key)      pack_id     pack_type     pack_price     player      type       bid    bin  sold
#       int               int       nchar(10)         int       nchar(24)  nchar(10)    int    int  int

DRIVER = "{SQL Server}"
SERVER = "DESKTOP-5R7EE8O\\SQLEXPRESS"
DATABASE = "player_packs"
TABLE = "dbo.pack_tracking"


class DisplayApp:
    """ An extendable GUI system with multiple control and display frame, and scrollable main frame

        __init__( self, width, height )
        width - width of root window (encompasses all frames)
        height - height of root window
    """

    def __init__(self, width, height):

        # app wide constants
        self.COLUMNS = [
            "id",
            "pack_id",
            "pack_price",
            "pack_type",
            "name",
            "type",
            "bid",
            "bin",
            "sold",
        ]
        self.PACKS = {
            "bronze": 400,
            "bronze r": 750,
            "silver": 2500,
            "silver r": 3750,
            "gold": 5000,
            "gold r": 7500,
        }
        self.TYPES = [
            "player",
            "healing",
            "fitness",
            "contract",
            "kit",
            "stadia",
            "badge",
            "manager",
            "coach",
        ]

        # create a tk object, which is the root window
        self.root = tk.Tk()

        # create the server connection and get all columns
        self.cursor = self.db_connect(DRIVER, SERVER, DATABASE)

        # width and height of the window
        self.initDx = width
        self.initDy = height

        # set up the geometry for the window
        self.root.geometry("%dx%d+50+30" % (self.initDx, self.initDy))

        # set the title of the window
        self.root.title("Viewing Axes")

        # set the maximum size of the window for resizing
        self.root.maxsize(1440, 820)

        # bring the window to the front
        self.root.lift()

        # load the data
        self.loadData()

        # setup the menus
        self.buildMenus()

        # build the controls
        self.buildControls()

        # build the objects on the Canvas
        self.buildPlayerFrame()
        self.buildStatsFrame()

        # set up the key bindings
        self.setBindings()

        # set up system wide tracking variables
        try:
            self.curr_pack_id = self.data["pack_id"].unique().max() + 1
            self.curr_id = self.data.index.unique().max() + 1
            self.curr_pack_displaying = None
        except ValueError:
            self.curr_pack_id = 1
            self.curr_id = 1

    def db_connect(self, driver, server, database, trust="yes"):
        """ connects to the database, sets a connection object
        :param driver: the driver name of the sql server
        :type driver: String
        :param server: the name of the sql server
        :type server: String
        :param database: the name of the sql database
        :type database: String
        :param trust: whether to trust the connection
        :type trust: String
        :returns: the cursor object for db interaction
        :rtype: pyodbc cursor
        """

        self.conn = pyodbc.connect(
            driver=driver, server=server, database=database, Trusted_Connection=trust
        )

        return self.conn.cursor()

    def test_connection(self):
        """ prints the database to ensure it is connected
        :returns: None
        :rtype: None
        """

        self.cursor.execute("SELECT * FROM " + TABLE)

        for row in self.cursor:
            print(row)

    def loadData(self):
        """ loads the data from MSSQL server into a pandas DataFrame
        :returns: None
        :rtype: None
        """

        query = "SELECT * FROM " + TABLE
        self.cursor.execute(query)

        # convert iterator to a list and then make a data frame from this list, stripping off all whitespace
        records = pd.DataFrame.from_records(list(self.cursor), columns=self.COLUMNS)
        self.data = records.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        self.data.set_index("id", inplace=True)
        self.curr_index = self.data.index

        return

    def buildMenus(self):
        """ builds the ribbon menu
        :returns: None
        :rtype: None
        """

        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        self.menulist = []

        # create a file menu
        filemenu = tk.Menu(self.menu)
        self.menu.add_cascade(label="File", menu=filemenu)
        self.menulist.append(filemenu)

        # menu text and functions for the elements
        menutext = [["Quit", "Test DB"]]
        menucmd = [[self.handleQuit, self.test_connection]]

        # build the menu elements and callbacks
        for i in range(len(self.menulist)):
            for j in range(len(menutext[i])):
                if menutext[i][j] != "-":
                    self.menulist[i].add_command(
                        label=menutext[i][j], command=menucmd[i][j]
                    )
                else:
                    self.menulist[i].add_separator()

    def buildStatsFrame(self):
        """ builds the basis of what will become the player display frame
        :returns: None
        :rtype: None
        """

        # create a status area that is capable of displaying current point
        self.statsArea = tk.Frame(self.bigframe, width=48)
        self.statsArea.pack(side=tk.RIGHT, padx=2, pady=4, fill=tk.Y)

        # create a sepaarator line for the status area
        sep = tk.Frame(self.root, height=self.initDy, width=2, bd=1, relief=tk.SUNKEN)
        sep.pack(side=tk.RIGHT, padx=2, pady=2, fill=tk.Y)

        self.handleStats(self.data)

        return

    def buildPlayerFrame(self, write=True):
        """ builds the basis of what will become the player display frame
        :param write: (Default True) Whether to write the current data stored onto the frame
        :type write: Boolean
        :returns: None
        :rtype: None
        """

        # create the frame for display
        self.canvas = ScrolledWindow(
            self.root, width=self.initDx - 100, height=self.initDy
        )
        self.canvas.pack(side=tk.RIGHT)

        # write data using all columns if write is true
        if write:
            self.handleWrite(self.COLUMNS, self.curr_index, update_stats=False)

        return

    def clearPlayerFrame(self):
        """ clears the player frame so it can be redrawn with other information
        :returns: None
        :rtype: None
        """

        # loops through children of the scroll window and destroys them, allowing new labels to be drawn
        for widget in self.canvas.scrollwindow.winfo_children():
            widget.destroy()

        return

    def buildControls(self):
        """ builds the control frame at right of the GUI
        :returns: None
        :rtype: None
        """

        # make a big control frame at right
        self.bigframe = tk.Frame(self.root)
        self.bigframe.pack(side=tk.RIGHT, padx=2, pady=2, fill=tk.Y)

        # TODO: find out where this separator goes and why I only get one separator at right
        sep = tk.Frame(self.root, height=self.initDy, width=2, bd=1, relief=tk.SUNKEN)
        sep.pack(side=tk.RIGHT, padx=2, pady=2, fill=tk.Y)

        # make other cntl frames
        self.cntlframe = tk.Frame(self.bigframe)
        self.cntlframe.pack(side=tk.RIGHT, padx=2, pady=2, fill=tk.Y)

        self.createButtons()
        self.createListBoxes()

        return

    def setBindings(self):
        """ sets all bindings for the GUI
        :returns: None
        :rtype: None
        """

        self.pkBox.bind("<FocusOut>", lambda e: self.pkBox.selection_clear(0, "end"))
        self.cstBox.bind("<FocusOut>", lambda e: self.cstBox.selection_clear(0, "end"))
        self.cstBox.bind("<<ListboxSelect>>", self.costBox)
        self.pkBox.bind("<<ListboxSelect>>", self.packBox)

    def createButtons(self):
        # make buttons for control frame, enabling user open, sell, and delete
        # add new buttons here
        self.buttons = []
        self.buttons.append(
            (
                "clear filters",
                tk.Button(
                    self.cntlframe,
                    text="Clear all Filters",
                    command=self.handleReset,
                    width=12,
                ),
            )
        )
        self.buttons.append(
            (
                "open pack",
                tk.Button(
                    self.cntlframe,
                    text="Open New Pack",
                    command=self.handleNewPack,
                    width=12,
                ),
            )
        )
        self.buttons.append(
            (
                "enter sale",
                tk.Button(
                    self.cntlframe,
                    text="Enter Player Sale",
                    command=self.handleSale,
                    width=12,
                ),
            )
        )
        self.buttons.append(
            (
                "delete record",
                tk.Button(
                    self.cntlframe,
                    text="Delete Records",
                    command=self.handleDelete,
                    width=12,
                ),
            )
        )

        # add these buttons to frame
        for bNum in range(len(self.buttons)):
            self.buttons[bNum][1].pack(side=tk.TOP)

        return

    def createListBoxes(self):
        """ creates the list boxes that allow for data subsetting
        :returns: None
        :rtype: None
        """

        xLabel = tk.Label(self.cntlframe, text="Individual Packs")
        self.pkBox = tk.Listbox(self.cntlframe, height=16, width=16, exportselection=0)

        # attach lambda to pkBox that allows for checking what entries are in listbox
        self.pkBox.__contains__ = lambda str: str in self.pkBox.get(0, "end")

        for record in self.data["pack_id"].unique():
            self.pkBox.insert("end", record)

        yLabel = tk.Label(self.cntlframe, text="Pack Types")
        self.cstBox = tk.Listbox(self.cntlframe, height=6, width=16, exportselection=0)

        # same lambda as above but for cost box
        self.cstBox.__contains__ = lambda str: str in self.cstBox.get(0, "end")

        for record in self.data["pack_type"].unique():
            self.cstBox.insert("end", record)

        # draw and label the list boxes
        self.listboxes = [self.pkBox, self.cstBox]
        labels = [xLabel, yLabel]
        for t in range(len(self.listboxes)):
            labels[t].pack(side=tk.TOP, pady=2)
            self.listboxes[t].pack(side=tk.TOP, pady=0)

        return

    def packBox(self, event):
        """ main method for handling listbox of pack subsetting
        :param event: The tkinter event that spawned this call
        :type event: TKinter event
        :returns: None
        :rtype: None
        """

        # this gets the indices matching the current selection and sets the current index to those rows
        curselection = self.data["pack_id"].unique()[self.pkBox.curselection()[0]]
        self.curr_index = self.data[self.data["pack_id"] == curselection].index

        self.handleWrite(self.COLUMNS, self.curr_index, reload=False, update=True)

        return

    def costBox(self, event):
        """ main method for handling listbox of cost subsetting
        :param event: The tkinter event that spawned this call
        :type event: TKinter event
        :returns: None
        :rtype: None
        """

        # this gets the indices matching the current selection and sets the current index to those rows
        curselection = self.data["pack_type"].unique()[self.cstBox.curselection()[0]]
        self.curr_index = self.data[
            self.data["pack_type"].str.match(str(curselection))
        ].index

        self.handleWrite(self.COLUMNS, self.curr_index, reload=False, update=True)

        return

    def handleReset(self):
        """ method for handling view reset
        :returns: None
        :rtype: None
        """

        self.clearPlayerFrame()
        self.loadData()
        self.handleWrite(self.COLUMNS, self.curr_index, reload=True)
        self.canvas.scrollwindow.focus_set()  # this isnt strictly necessary, but clears selections from the listboxes

    def handleNewPack(self):
        """ main method for handling pack opening
        :returns: None
        :rtype: None
        """

        # gets the number of items to list
        num_listing = NumberListing_Dialog(self, "Items to List")
        if num_listing.userCancelled():
            return

        # gets the bulk of the data, including name, type, bid, and bin
        # of form [ [name, type, bid, bin], [name, type, bid, bin], [...] ]
        to_add = Listing_Dialog(self, int(num_listing.getResult()), "Items to List")
        if to_add.userCancelled():
            return

        # whether the pack is a reward pack and had cost of 0
        # this will enable more accurate profit and loss statistics in stats frame
        pack_type = to_add.getResult_pack()
        if to_add.getResult_reward():
            pack_price = 0
        else:
            pack_price = self.PACKS[pack_type]

        self.postData(to_add.getResult(), to_add.getResult_qs(), pack_type, pack_price)

        # we have to load data here even though we have that reload argument b/c otherwise the write
        # function doesn't get the index for the new data
        self.loadData()
        self.handleWrite(self.COLUMNS, self.data.index, reload=False)

        return

    def postData(self, data, qs_price, pack_type, pack_price):
        """ posts data gathered into the mssql database connected currently
        :param data: The 'meat' of the data to post
        :type data: List( List( String, String, Integer, Integer ) )
        :param qs_price: The quick sell price of the pack being posted
        :type qs_price: Integer
        :param pack_type: The type of pack the data was gotten from
        :type pack_type: String
        :param pack_price: The cost of the pack (This is a field as it may have been a free pack)
        :type pack_price: Integer
        :returns: None
        :rtype: None
        """

        for row in data:
            query = (
                "INSERT INTO "
                + TABLE
                + "(id,pack_id,pack_price,pack_type,name,type,bid,bin) VALUES (?,?,?,?,?,?,?,?)"
            )

            self.cursor.execute(
                query,
                (
                    int(self.curr_id),
                    int(self.curr_pack_id),
                    pack_price - qs_price,
                    pack_type,
                    row[0],
                    row[1],
                    int(row[2]),
                    int(row[3]),
                ),
            )
            self.curr_id += 1

        self.pkBox.insert("end", self.curr_pack_id)
        # make sure pack types do not duplicate w/in the listbox
        if not self.cstBox.__contains__(pack_type):
            self.cstBox.insert("end", pack_type)
        self.curr_pack_id += 1
        self.conn.commit()

        return

    def handleSale(self):
        """ main method for handling a completed player sale
        :returns: None
        :rtype: None
        """

        selling = Selling_Dialog(self, "Sale Completed")

        if selling.userCancelled():
            return

        id_loc = int(selling.getResult())

        self.postSale(id_loc, selling.getResult_sale())
        self.handleWrite(self.COLUMNS, self.data.index, reload=True, update=True)

    def postSale(self, id, sale_price):
        """ updates the sale price of a low in the database
        :param id: the primary key of the row to update
        :type id: Integer
        :param sale_price: The sale price to store in the database
        :type sale_price: Integer
        :returns: None
        :rtype: None
        """

        query = "UPDATE " + TABLE + " SET " + "sold = (?) WHERE id = (?)"
        self.cursor.execute(query, (sale_price, id))
        self.conn.commit()

        return

    def handleWrite(self, columns, rows, reload=True, update=False, update_stats=True):
        """ main method for handling player writing
        :param columns: The columns on which to subset the data
        :type columns: List of Strings
        :param pack_id: (Default None) The id number of the pack on which to subset this data
        :type pack_id: Integer or None
        :param reload: (Default True) Whether to reload the data
        :type reload: Boolean
        :param update: (Default False) Whether this call should update where the players are displayed.
                       This makes deleting and redrawing the player frame necessary
        :type update: Boolean
        :param update_stats: (Default True) Whether to update the stats frame on redraw
        :type update_stats: Boolean
        :returns: None
        :rtype: None
        """

        # if we reload the data, we assume that we display all of it because the rows passed would
        # not contain the reloaded rows, but if update, we dont need to do this since it'll just get
        # destroyed later
        if reload:
            self.loadData()
            if not update:
                self.writePlayers(self.data.loc[rows][columns[1:]], update_stats)
                return

        # updating the frame just creates an empty canvas to write.
        # if you are calling update=True you should be subsetting or changing the data displayed in some way
        if update:
            self.clearPlayerFrame()

        self.writePlayers(self.data.loc[rows][columns[1:]], update_stats)

        return

    def writePlayers(self, data, update_stats):
        """ writes the player data to the main tk Frame
        :param data: the data being written to the frame
        :type data: pandas DataFrame
        :returns: None
        rtype: None
        """

        # creates the header row of the table
        lab = tk.Label(self.canvas.scrollwindow, text="id")
        lab.config(font=(8), anchor="center", width=9)
        lab.grid(row=0, column=0, padx=(7, 0))
        for col in enumerate(data):
            lab = tk.Label(self.canvas.scrollwindow, text=col[1])
            lab.config(font=(8), anchor="center", width=9)
            lab.grid(row=0, column=col[0] + 1, padx=(7, 0))

        # grids and displays player data
        for rdx, row in data.iterrows():
            lab = tk.Label(self.canvas.scrollwindow, text=rdx)
            lab.config(font=(6))
            lab.grid(row=rdx + 1, column=0, padx=(3, 0))
            for col in enumerate(data):
                lab = tk.Label(self.canvas.scrollwindow, text=row[col[1]])
                lab.config(font=(6))
                if col[1] == "player":
                    lab.config(width=8)
                lab.grid(row=rdx + 1, column=col[0] + 1, padx=(3, 0))

        # update stats pane each time records are written
        # this keeps the stats pane consistent w/ all filters applied and any new players added
        if update_stats:
            self.handleStats(data)

        return

    def handleStats(self, data):
        """ main method for handling overall profit statistics
        :param data: A pandas DF containing the data to calc stats on
        :type data: Pandas DataFrame
        :returns: None
        :rtype: None
        """

        stats = self.calcStats(data)
        self.writeStats(stats)

        return

    def calcStats(self, data):
        """ calculates the statistics to be displayed in the stats frame
        :param data: A pandas DF containing the data to calc stats on
        :type data: Pandas DataFrame
        :returns: A dictionary containing the stats and their names
        :rtype: Dictionary
        """

        gross_spend = "(" + str(stats.total_cost(data)) + ")"
        gross_revenue = str(stats.total_revenue(data))

        net_profit = stats.net_profit(data)
        if net_profit < 0:
            net_profit = "(" + str(net_profit).strip("-") + ")"
        else:
            net_profit = str(net_profit)

        avg_profit = stats.avg_profit(data)
        if avg_profit < 0:
            avg_profit = "(" + str(avg_profit).strip("-") + ")"
        else:
            avg_profit = str(avg_profit)

        pack_stats = {
            "Gross Expenses": gross_spend,
            "Gross Revenue": gross_revenue,
            "Net Profit": net_profit,
            "Profit per Pack": avg_profit,
        }

        return pack_stats

    def writeStats(self, pack_stats):
        """ writes the statistics returned by the calcStats function to the stats pane
        :param stats: A tuple of the different stats to be displayed
        :type: Tuple of type ( TODO )
        :returns: None
        :rtype: None
        """

        for idx, key in enumerate(pack_stats):
            alt = idx * 3
            lab = tk.Label(self.statsArea, text=key)
            lab.config(font=(8), anchor="center", width=18)
            lab.grid(row=alt, column=0)

            lab = tk.Label(self.statsArea, text=pack_stats[key])
            if pack_stats[key][0] == "(":
                lab.config(font=(8), anchor="center", width=18, foreground="red")
            elif pack_stats[key] == "0.0":
                lab.config(font=(8), anchor="center", width=18)
            else:
                lab.config(font=(8), anchor="center", width=18, foreground="green")
            lab.grid(row=alt + 1, column=0)

            lab = tk.Label(self.statsArea, text=" ")
            lab.grid(row=alt + 2, column=0)

    def handleDelete(self):
        """ main method for handling player record deletion
        :param self: This GUI class
        :type self: DisplayApp
        :returns: None
        :rtype: None
        """
        deleteing = Delete_Dialog(self, "Sale Completed")

        if deleteing.userCancelled():
            return

        id_loc = int(deleteing.getResult())

        self.postDeletion(id_loc)
        self.loadData()
        self.handleWrite(self.COLUMNS, self.curr_index, reload=False, update=True)

    def postDeletion(self, id):
        """ deletes a row from the table
        :param loc:
        :type loc:
        :returns:
        :rtype:
        """

        query = "DELETE FROM " + TABLE + " WHERE id = (?)"
        self.cursor.execute(query, id)
        self.conn.commit()

        return

    def handleQuit(self, event=None):
        """ closes the GUI
        :param self: This GUI class
        :type self: DisplayApp
        :param event: The event which prompted the quit message. 
        :type event: Optional Argument, allows for multiple closing strategies with singular method
        :returns: None
        :rtype: None
        """

        self.root.destroy()
        return

    def main(self):
        """ runs the gui and ensures loop until quit
        :param self: This GUI class
        :type self: DisplayApp
        :returns: None
        :rtype: None
        """

        self.root.mainloop()
        return


class NumberListing_Dialog(tk.Toplevel):
    def __init__(self, parent, title=None):

        tk.Toplevel.__init__(self)

        if title:
            self.title(title)

        self.parent = parent
        self.cancelled = None

        body = tk.Frame(self)
        self.result = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry(
            "+%d+%d"
            % (parent.root.winfo_rootx() + 100, parent.root.winfo_rooty() + 100)
        )

        self.wait_window(self)

    def body(self, master):
        """ creates the widgets for the dialog box
        :param master: The frame to place widgets into
        :type master: tk Frame
        :returns: The result from the widget
        :rtype: StrVar
        """

        result = tk.StringVar()
        l = tk.Label(self, text="Enter the Number of Items to List from this Pack")
        l.pack()
        entry = tk.Entry(self, textvariable=result)
        entry.pack()
        entry.focus()

        return result

    def buttonbox(self):
        """ constructs the button box for the dialob window
        :returns: None
        :rtype: None
        """

        box = tk.Frame(self)

        w = tk.Button(box, text="OK", width=10, command=self.ok, default="active")
        w.pack(side="left", padx=5, pady=5)
        w = tk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side="left", padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def ok(self, event=None):
        """ handles actions for the click of the ok button
        :returns: None
        :rtype: None
        """

        if not self.validate():
            tk.messagebox.showerror("Error", "Please enter a positive integer")
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()
        self.cancel(cancelled=False)

    def cancel(self, event=None, cancelled=True):
        """ handles dialog box destruction
        :param event: Handle box click and esc cancellations
        :type event: tk event or None
        :param cancelled: Defines whether the user cancelled or box closed naturally
        :type cancelled: Boolean
        :returns: None
        :rtype: None
        """

        self.cancelled = cancelled

        self.parent.root.focus_set()
        self.destroy()

    def validate(self):
        """ validates the information entered into the dialog box
        :returns: A exit value related to the error or 1 if data is valid
        :rtype: Integer
        """

        val = self.result.get()
        try:
            if int(val) > 0:
                return True
            else:
                return False
        except ValueError:
            return False

    def apply(self):
        """ alters types from tk xxxVar to builtins
        :returns: None
        :rtype: None
        """
        self.result = self.result.get()

    def getResult(self):
        """ gets main data result
        :returns: The main listbox data
        :rtype: List( String )
        """

        return self.result

    def userCancelled(self):
        """ gets whether the window close was a user action
        :returns: Whether the user cancelled the window
        :rtype: Boolean
        """

        return self.cancelled


class Listing_Dialog(NumberListing_Dialog):
    def __init__(self, parent, rows, title=None):

        tk.Toplevel.__init__(self)

        if title:
            self.title(title)

        self.parent = parent
        self.rows = rows
        self.columns = ["player", "item type", "start bid", "bin price"]
        self.cancelled = None

        body = tk.Frame(self)
        self.pack_type, self.result, self.qs, self.free = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry(
            "+%d+%d"
            % (parent.root.winfo_rootx() + 100, parent.root.winfo_rooty() + 100)
        )

        self.wait_window(self)

    def body(self, master):
        """ creates the widgets for the dialog box (Override)
        :param master: The frame to place widgets into
        :type master: tk Frame
        :returns: The results from the widgets
        :rtype: Tuple of types (StrVar, List( StrVar ), StrVar, IntVar )
        """

        result = []

        # pack type entry set up
        pack_type = tk.StringVar()
        pack_type.set("bronze")
        tk.Label(master, text="    Select Pack Type:").grid(row=0, column=0)
        tk.OptionMenu(master, pack_type, *self.parent.PACKS).grid(row=0, column=1)
        free = tk.IntVar()
        free.set(0)
        check = tk.Checkbutton(
            master, text="Free Pack?", onvalue=1, offvalue=0, variable=free
        )
        check.grid(row=0, column=2)
        check.focus()

        # give some separation between pack type entry and item entry
        tk.Label(master, text="").grid(row=self.rows + 5, column=0)

        # list out headers for entry set
        for header in enumerate(self.columns):
            tk.Label(master, text=header[1]).grid(row=3, column=header[0])

        # give as many entry spaces as rows specified from first dialog
        for i in range(self.rows):

            # player entry field
            w = tk.StringVar()
            tk.Entry(master, textvariable=w).grid(row=i + 4, column=0)

            # item type
            x = tk.StringVar()
            x.set("player")  # option menu will default to player
            tk.OptionMenu(master, x, *self.parent.TYPES).grid(row=i + 4, column=1)

            # initial bid
            y = tk.StringVar()
            y.set(150)
            tk.Entry(master, textvariable=y).grid(row=i + 4, column=2)

            # initial bin
            z = tk.StringVar()
            z.set(200)
            tk.Entry(master, textvariable=z).grid(row=i + 4, column=3)

            # each sublist in the result variable is one row of data ordered as
            # [ item name, item type, item initial bid price, item buy it now price ]
            result.append([w, x, y, z])

        qs_val = tk.StringVar()
        qs_val.set(23)

        # give some separation between quick sell entry and item entry
        tk.Label(master, text="").grid(row=self.rows + 5, column=0)

        # quick sell entry set up
        tk.Label(master, text="Enter Quick Sell Value:").grid(
            row=self.rows + 6, column=0
        )
        tk.Entry(master, textvariable=qs_val).grid(row=self.rows + 6, column=1)

        return pack_type, result, qs_val, free

    def ok(self, event=None):
        """ handles actions for the click of the ok button (Override)
        :returns: None
        :rtype: None
        """

        validation = self.validate()

        # handle different error codes. note errors cannot happen from option menus b/c of default values:
        # 0 -> characters other than A-z, '
        # -1 -> empty player name box
        # -2 -> int less than 150 in bid price
        # -3 -> int less than 200 in bin price
        # -4 -> player name greater than 24 characters (would clash later w/ database storage)
        # -5 -> int less than 0 for quick sell price
        # -6 -> one of bid, bin, or qs not an integer

        if validation == 0:
            tk.messagebox.showerror(
                "Error", "Please enter only valid characters in the player name box"
            )
            return
        elif validation == -1:
            tk.messagebox.showerror(
                "Error", "Please enter a name in the player name box"
            )
            return
        elif validation == -2:
            tk.messagebox.showerror(
                "Error",
                "Please enter an integer greater than or equal to 150 for the initial bid",
            )
            return
        elif validation == -3:
            tk.messagebox.showerror(
                "Error",
                "Please enter an integer greater than or equal to 200 for the initial bin",
            )
            return
        elif validation == -4:
            tk.messagebox.showerror(
                "Error", "Please keep names under 24 characters in length"
            )
            return
        elif validation == -5:
            tk.messagebox.showerror(
                "Error", "Please enter a positive integer for the quick sell price"
            )
            return
        elif validation == -6:
            tk.messagebox.showerror(
                "Error",
                "Please enter... \n"
                + "- An integer greater than or equal to 150 for the initial bid \n"
                + "- An integer greater than or equal to 200 for the initial bin \n"
                + "- An integer greater than or equal to 0 for the quick sell price",
            )
            return
        elif validation == -7:
            tk.messagebox.showerror(
                "Error", "Initial Bid price must be lower than initial BIN price"
            )
            return
        else:
            # applies the results and closes the dialog
            self.withdraw()
            self.update_idletasks()

            self.apply()
            self.cancel(cancelled=False)

    def validate(self):
        """ validates the information entered into the dialog box (Override)
        :returns: A exit value related to the error or 1 if data is valid
        :rtype: Integer
        """

        rows = self.result
        qs = self.qs.get()
        try:
            for row in rows:
                if not string_validator(row[0].get()):
                    return 0
                if row[0].get() is "":
                    return -1
                if int(row[2].get()) < 150:
                    return -2
                if int(row[3].get()) < 200:
                    return -3
                if int(row[2].get()) > int(row[3].get()):
                    return -7
                if len(row[0].get()) > 24:
                    return -4
                if int(qs) < 0:
                    return -5
        except ValueError:
            return -6

        return 1

    def apply(self):
        """ alters types from tk xxxVar to builtins (Override)
        :returns: None
        :rtype: None
        """

        self.pack_type = self.pack_type.get()
        self.qs = int(self.qs.get())

        self.free = self.free.get()
        if self.free == 0:
            self.free = False
        else:
            self.free = True

        result = []
        for record in self.result:
            row = []
            for item in record:
                row.append(item.get())
            result.append(row)

        self.result = result

        return

    def getResult_qs(self):
        """ gets the quick sell result
        :returns: The pack quicksell price
        :rtype: Integer
        """

        return self.qs

    def getResult_pack(self):
        """ gets the pack type result
        :returns: The pack type selected
        :rtype: String
        """

        return self.pack_type

    def getResult_reward(self):
        """ gets whether the pack was a reward pack
        :returns: If the pack was free, return true
        :rtype: Boolean
        """

        return self.free


class Selling_Dialog(NumberListing_Dialog):
    def __init__(self, parent, title=None):

        tk.Toplevel.__init__(self)

        if title:
            self.title(title)

        self.parent = parent
        self.cancelled = None

        body = tk.Frame(self)
        self.result, self.value = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry(
            "+%d+%d"
            % (parent.root.winfo_rootx() + 100, parent.root.winfo_rooty() + 100)
        )

        self.wait_window(self)

    def body(self, master):
        """ creates the widgets for the dialog box (Override)
        :param master: The frame to place widgets into
        :type master: tk Frame
        :returns: The results from the widgets
        :rtype: Tuple of types (StrVar, List( StrVar ), StrVar, IntVar )
        """

        # id/name type entry set up
        search = tk.StringVar()
        tk.Label(master, text="Enter player name or row ID:").grid(row=0, column=0)
        entry = tk.Entry(master, textvariable=search)
        entry.grid(row=0, column=1)
        entry.focus()

        value = tk.StringVar()
        tk.Label(master, text="Enter amount player sold for:").grid(row=1, column=0)
        tk.Entry(master, textvariable=value).grid(row=1, column=1)

        return search, value

    def ok(self, event=None):
        """ handles actions for the click of the ok button (Override)
        :returns: None
        :rtype: None
        """

        validation = self.validate()

        # handle different error codes. note errors cannot happen from option menus b/c of default values:
        # 0 -> characters other than A-z, '
        # -1 -> empty player name box
        # -2 -> int less than 150 in bid price
        # -3 -> int less than 200 in bin price
        # -4 -> player name greater than 24 characters (would clash later w/ database storage)
        # -5 -> int less than 0 for quick sell price
        # -6 -> one of bid, bin, or qs not an integer
        # -7 -> the player name entered appears in multiple rows

        if validation == 0:
            tk.messagebox.showerror("Error", "Please enter only valid characters")
            return
        elif validation == -1:
            tk.messagebox.showerror("Error", "Please do not leave entries blank")
            return
        elif validation == -2:
            tk.messagebox.showerror(
                "Error",
                "Please enter a valid ID, valid IDs are a positive integer\n"
                + "between 0 and "
                + str(self.parent.curr_id - 1),
            )
            return
        elif validation == -3:
            tk.messagebox.showerror(
                "Error", "Please enter a player name currently within the data table"
            )
            return
        elif validation == -4:
            tk.messagebox.showerror(
                "Error", "Please keep names under 24 characters in length"
            )
            return
        elif validation == -5 or validation == -6:
            tk.messagebox.showerror("Error", "Sale price must be a positive integer")
            return
        elif validation == -7:
            mults = self.parent.data[
                self.parent.data["name"].str.match(self.result.get())
            ].index
            display_str = "Player name appears in multiple rows. Please choose an index shown below instead of naming the player\n"
            for idx in mults:
                display_str += str(idx + 1) + "  "
            tk.messagebox.showerror("Error", display_str)
            return
        else:
            # applies the results and closes the dialog
            self.withdraw()
            self.update_idletasks()

            self.apply()
            self.cancel(cancelled=False)

    def validate(self):
        """ validates the information entered into the dialog box (Override)
        :returns: A exit value related to the error or 1 if data is valid
        :rtype: Integer
        """

        search = self.result.get()
        price = self.value.get()

        try:
            search = int(search)
            if search >= self.parent.curr_id or search < 0:
                return -2
        except ValueError:
            if not string_validator(search):
                return 0
            if search is "":
                return -1
            if len(search) > 24:
                return -4
            # player name entered is not in the dataframe
            if not self.parent.data["name"].str.contains(search).any():
                return -3
            # player name appears multiple times in the dataframe
            if (
                len(
                    self.parent.data[
                        self.parent.data["name"].str.match(self.result.get())
                    ].index
                )
                > 1
            ):
                return -7

        try:
            if not string_validator(price):
                return 0
            if price is "":
                return -1
            price = int(price)
            if price < 0:
                return -5
        except ValueError:
            return -6

        return 1

    def apply(self):
        """ alters types from tk xxxVar to builtins (Override)
        :returns: None
        :rtype: None
        """

        try:
            self.result = int(self.result.get())
        except:
            self.result = self.parent.data[
                self.parent.data["name"].str.match(self.result.get())
            ].index
            self.result = self.result[0] + 1

        self.value = int(self.value.get())

        return

    def getResult_sale(self):
        """ gets whether the pack was a reward pack
        :returns: If the pack was free, return true
        :rtype: Boolean
        """

        return self.value


class Delete_Dialog(Selling_Dialog):
    def __init__(self, parent, title=None):

        tk.Toplevel.__init__(self)

        if title:
            self.title(title)

        self.parent = parent
        self.cancelled = None

        body = tk.Frame(self)
        body.pack(padx=5, pady=5)
        self.result = self.body(body)
        self.buttonbox()

        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry(
            "+%d+%d"
            % (parent.root.winfo_rootx() + 100, parent.root.winfo_rooty() + 100)
        )

        self.wait_window(self)

    def body(self, master):
        """ creates the widgets for the dialog box (Override)
        :param master: The frame to place widgets into
        :type master: tk Frame
        :returns: The results from the widgets
        :rtype: Tuple of types (StrVar, List( StrVar ), StrVar, IntVar )
        """

        # id/name type entry set up
        search = tk.StringVar()
        tk.Label(master, text="Enter player name or row ID:").grid(row=0, column=0)
        entry = tk.Entry(master, textvariable=search)
        entry.grid(row=0, column=1)
        entry.focus()

        return search

    def validate(self):
        """ validates the information entered into the dialog box (Override)
        :returns: A exit value related to the error or 1 if data is valid
        :rtype: Integer
        """

        search = self.result.get()

        try:
            search = int(search)
            if search >= self.parent.curr_id or search < 0:
                return -2
        except ValueError:
            if not string_validator(search):
                return 0
            if search is "":
                return -1
            if len(search) > 24:
                return -4
            # player name entered is not in the dataframe
            if not self.parent.data["name"].str.contains(search).any():
                return -3
            # player name appears multiple times in the dataframe
            if (
                len(
                    self.parent.data[
                        self.parent.data["name"].str.match(self.result.get())
                    ].index
                )
                > 1
            ):
                return -7

        return 1

    def apply(self):
        """ alters types from tk xxxVar to builtins (Override)
        :returns: None
        :rtype: None
        """

        try:
            self.result = int(self.result.get())
        except:
            self.result = self.parent.data[
                self.parent.data["name"].str.match(self.result.get())
            ].index
            self.result = self.result[0] + 1

        return

class ScrolledWindow(tk.Frame):
    """
    1. Master widget gets scrollbars and a canvas. Scrollbars are connected 
    to canvas scrollregion.

    2. self.scrollwindow is created and inserted into canvas

    Usage Guideline:
    Assign any widgets as children of <ScrolledWindow instance>.scrollwindow
    to get them inserted into canvas

    __init__(self, parent, canv_w = 400, canv_h = 400, *args, **kwargs)
    Parent = master of scrolled window
    canv_w - width of canvas
    canv_h - height of canvas

    """

    def __init__(self, parent, canv_w=400, canv_h=400, *args, **kwargs):
        """ Initializes and displays a scrolled window
        :param parent: master of scrolled window
        :type parent: tkinter Frame or Window object
        :param canv_w: width of canvas
        :type canv_w: Integer
        :param canv_h: height of canvas
        :type canv_h: Integer
        :returns: None
        :rtype: None
       """
        super().__init__(parent, *args, **kwargs)

        self.parent = parent

        # creating a scrollbar
        self.yscrlbr = ttk.Scrollbar(self.parent)
        self.yscrlbr.pack(side=tk.RIGHT, padx=2, pady=2, fill=tk.Y)

        # creating a canvas
        self.canv = tk.Canvas(self.parent)
        self.canv.config(relief="flat", width=10, heigh=10, bd=2)

        # placing a canvas into frame
        self.canv.pack(side=tk.RIGHT, padx=2, pady=2, fill=tk.Y)

        # accociating scrollbar commands to canvas scroling
        self.yscrlbr.config(command=self.canv.yview)

        # creating a frame to inserto to canvas
        self.scrollwindow = ttk.Frame(self.parent)

        self.canv.create_window(0, 0, window=self.scrollwindow, anchor="nw")

        self.canv.config(yscrollcommand=self.yscrlbr.set, scrollregion=(0, 0, 100, 100))

        self.yscrlbr.lift(self.scrollwindow)
        self.scrollwindow.bind("<Configure>", self._configure_window)
        self.scrollwindow.bind("<Enter>", self._bound_to_mousewheel)
        self.scrollwindow.bind("<Leave>", self._unbound_to_mousewheel)

        return

    def _bound_to_mousewheel(self, event):
        self.canv.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canv.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canv.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _configure_window(self, event):
        # update the scrollbars to match the size of the inner frame
        size = (self.scrollwindow.winfo_reqwidth(), self.scrollwindow.winfo_reqheight())
        self.canv.config(scrollregion="0 0 %s %s" % size)
        if self.scrollwindow.winfo_reqwidth() != self.canv.winfo_width():
            # update the canvas's width to fit the inner frame
            self.canv.config(width=self.scrollwindow.winfo_reqwidth())
        if self.scrollwindow.winfo_reqheight() != self.canv.winfo_height():
            # update the canvas's width to fit the inner frame
            self.canv.config(height=self.scrollwindow.winfo_reqheight())


def string_validator(string, search=re.compile(r"[^A-z0-9.\']").search):
    """ checks a string for valid characters
    :param string: a string to check
    :type string: String
    :param search: The characters which are valid - default is A-z and '
    :type search: Regex Pattern object
    :returns: True if only the characters in search are in the string, otherwise returns False
    :rtype: Boolean
    """
    return not bool(search(string))


if __name__ == "__main__":
    dapp = DisplayApp(1440, 1280)
    dapp.main()
