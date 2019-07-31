""" stats.py

This file contains functions to calculate necessary statistical details from 
pandas dataframes

This file contains functions:
    * total_cost( data ) - returns the total cost of all packs
    * total_revenue( data ) - returns the total revenue from player sales
    * net_profit( data ) - returns the net profit of the player
    * test( data, assertions ) - tests the values returned by the functions above
    * main( ) - run test function

Created by Ben Capodanno on July 30th, 2019. Updated July 30th, 2019.
"""

import pandas as pd 
import numpy as np 

def total_cost( data ):
    """ returns the total of the pack cost column, excluding duplicates
    :param data: The data from which to calculate this value
    :type data: pandas DataFrame
    :returns: The total of the pack prices associated w/ unique pack IDs
    :rtype: Float
    """

    unique = data.drop_duplicates( "pack_id" )
    return unique["pack_price"].sum()

def total_revenue( data ):
    """ returns the total of the sold column
    :param data: The data from which to calculate this value
    :type data: pandas DataFrame
    :returns: The total from the sold column
    :rtype: Float
    """

    return data["sold"].sum()

def net_profit( data ):
    """ returns the sold column sum minus the costs of all packs
    :param data: The data from which to calculate this value
    :type data: pandas DataFrame
    :returns: sold - costs
    :rtype: Float
    """

    return total_revenue( data ) - total_cost( data )

def avg_profit( data ):
    """ returns the profit averaged over all packs in the set
    :param data: The data from which to calculate this value
    :type data: pandas DataFrame
    :returns: The average per pack profit
    :rtype: Float
    """

    return round( net_profit( data ) / len( data.drop_duplicates( "pack_id" ) ), 2 )

def test( data, assertions ):
    """ tests the stat gathering functions from this file
    :param data: The data to use in the test
    :type data: pandas DataFrame
    :param assertions: A dictionary of truth values that the functions should return
    :returns: None
    :rtype: None
    """

    func_ret = total_cost( data )
    true_val = assertions[ "total_cost" ]
    assert func_ret == true_val, "unexpected total %d, not %d" % ( func_ret, true_val )

    func_ret = total_revenue( data )
    true_val = assertions[ "total_revenue" ]
    assert func_ret == true_val, "unexpected total %d, not %d" % ( func_ret, true_val )

    func_ret = net_profit( data )
    true_val = assertions[ "net_profit" ]
    assert func_ret == true_val, "unexpected total %d, not %d" % ( func_ret, true_val )

    func_ret = avg_profit( data )
    true_val = assertions[ "avg_profit" ]
    assert func_ret == true_val, "unexpected total %d, not %d" % ( func_ret, true_val )

    print( "all values consistent" )

def main():
    """ runs the test function
    :returns: None
    :rtype: None
    """

    test_data = [ [1,353,"bronze","ben","player",150,300,None], 
                  [1,353,"bronze","emily","player",250,300,None],
                  [2,2400,"silver","hannah","player",150,300,300],
                  [3,300,"gold","tk","player",300,350,None],
                  [4,2500,"silver","chris","healing",150,300,None],
                  [6,750,"bronze r","cat","player",200,300,200],
                  [6,750,"bronze r","cat","player",800,1600,1600],
                  [6,750,"bronze r","emily","player",150,300,None],
                  [7,239,"bronze","o'day","player",150,300,150],
                  [8,400,"bronze","ben","player",150,300,None]
                ]

    data = pd.DataFrame( test_data, columns=['pack_id','pack_price','pack_type','name','type','bid','bin','sold'] )

    # calculated manually from test data
    assertions = { "total_cost": 6942, "total_revenue": 2250, "net_profit": -4692, "avg_profit": -670.29 }

    test( data, assertions )

if __name__ == "__main__":
    main()