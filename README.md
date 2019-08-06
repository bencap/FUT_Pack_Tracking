## FIFA Ultimate Team Pack Tracking GUI

This project allows a user to visualize the players gathered and sold within the FIFA marketplace. The GUI makes it simple for a user to add, edit, and sell players gathered from packs. The GUI also contains useful statistical outputs that tell a user how they are performing on an overall and per-pack basis. These statistical outputs update natively when a user subsets data, allowing for more granular output and strategic planning.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software and how to install them

```
Python3+
MSSQL Server 2016 or Newer
NumPy, MatPlotLib, TKinter, pyodbc, and pandas
```

### Installing and Running

A step by step series of examples that tell you how to get a development env running

Download and install MS SQL Server 2016 or newer onto your machine from [this webpage](https://www.microsoft.com/en-us/sql-server/sql-server-downloads). I use the developer edition to run this application on my machine. Then, using the SQL Server Management Studio (SSMS), enter the server name and connect to it.

To create a database and table to store our data, right click on the databases menu and select ```new database``` in the object explorer at left. Name this database ```player_packs``` and create it, leaving all other options as default. This database should then appear within the database menu. Expand the database entry, and right click on ```Tables```. Then select ```new -> table```. An entry pane should appear, allowing you to enter column names. The necessary columns should be entered as shown below, in that order and with the same settings.

```
| id         | int       | not null | primary key |
| pack_id    | int       | not null | na          |
| pack_price | int       | not null | na          |
| pack_type  | nchar(10) | not null | na          |
| name       | nchar(24) | not null | na          |
| type       | nchar(10) | not null | na          |
| bid        | int       | not null | na          |
| bin        | int       | not null | na          |
| sold       | int       | null     | na          |
```

Once these columns are entered with the appropriate settings, create the database with the name ```dbo.pack_tracking```.

It will also be necessary to update line 102 of the source code to reflect your database connection name

After these steps are taken, run the GUI with 

```
python pack_tracking.py
```

Within the GUI, the general workflow is to open a pack, enter the number of items you will list, enter the pack type, contents and list prices, and any modifiers; then confirm the pack to add it to the database and have it appear within the GUI. Additional buttons and list boxes allow the user to edit, confirm a transfer, and delete records. The list boxes allow for filtration based on the pack id or the quality of the pack. A stats frame at right displays the total expenditures, total profits, net profits, and the average profit per pack of the user.

## Built With

* [Python3](https://www.python.org/) - Used for all Project Scripts
* [MSSQL Server](https://www.microsoft.com/en-us/sql-server/sql-server-2019#Install) - Database for Pack Data
* [SQL Management Studio](https://docs.microsoft.com/en-us/sql/ssms/sql-server-management-studio-ssms?view=sql-server-2017) - Managing and Creating Necessary Databases
* Various Open Source Python Distributions

## Authors

* **Ben Capodanno** - *Initial work* - [bencap](https://github.com/bencap)

See also the list of [contributors](https://github.com/bencap/nba-vis/contributors) who participated in this project.
" 
