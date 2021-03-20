# This is the web apps for finding the airport connection
# from the airport and route database
#
# data obtained from
#
# Written by Shing Chi Leung at 8 March 2021


import streamlit as st
import pandas as pd
import numpy as np

from math import asin, atan, atan2, cos, pi, sin, sqrt

@st.cache
def load_data():

    df_airport = pd.read_csv("airports.dat.txt", names=["ID", "Name", "City", "Country", "IATA", 
                                                        "ICAO", "Latitude", "Longtitude", "Altitude", 
                                                        "Timezone", "DST Daylight",  "Tz database", "Type", "Source"])


    #print("Header of the file: \n{}\n".format(df_airport.head(5)))
    #print("Columns: {}".format(df_airport.columns))

    #num_airports = df_airport.shape[0]
    #print("Number of airports = {}".format(num_airports))
    #print("Country list: \n{}\n".format(df_airport["Country"].unique()))

    df_routes = pd.read_csv("routes.dat.txt", names=["Airline", "Airline ID", "Source", "Source ID", "Dest", 
                                                    "Dest ID", "Codeshare", "Stops", "Equipment"])

    # clean the data file
    df_routes["Source ID"] = df_routes["Source ID"].apply(remove_nan)   
    df_routes["Dest ID"] = df_routes["Dest ID"].apply(remove_nan)

    #print("Header of the file: \n{}\n".format(df_routes.head(10)))
    #print("Columns: {}".format(df_routes.columns))
    #num_routes = df_routes.shape[0]

    return df_airport, df_routes

def remove_nan(x):
    if str(x).isdigit():
        return int(x)
    else:
        return 0

def find_distance(coord1, coord2):

    # Earth radius
    radius = 6.371e3

    # translate to radian
    lat1 = coord1[0] * pi / 180
    lat2 = coord2[0] * pi / 180

    # translate to radian
    lon1 = coord1[1] * pi / 180
    lon2 = coord2[1] * pi / 180

    # Haversine Frmula
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # distance in km
    distance = radius * c  

    return distance

# defbug: test distance 
#distance = find_distance((df_airport.iloc[0]["Latitude"], df_airport.iloc[0]["Longtitude"]),
#                        (df_airport.iloc[1]["Latitude"], df_airport.iloc[1]["Longtitude"]))
#print(distance)

def get_airport_ID(df_airport, airport_name):
    return int(df_airport[df_airport["Name"] == airport_name]["ID"])

def get_airport_name(df_airport, airport_id):
    return list(df_airport[df_airport["ID"] == airport_id]["Name"])[0]

def get_airport_coord(df_airport, airport_id):
    df_temp = df_airport[df_airport["ID"] == airport_id]
    return (float(df_temp["Latitude"]), float(df_temp["Longtitude"]))

def find_direct_flight(df_airport, df_routes, source_name, dest_name):
    source_id = get_airport_ID(df_airport, source_name)
    dest_id = get_airport_ID(df_airport, dest_name)
    #print("Target id1, id2", source_id, dest_id)

    #route_list = df_routes[(df_routes["Source ID"] == source_id) & (df_routes["Dest ID"] == dest_id)]

    coord1 = get_airport_coord(df_airport, source_id)
    coord2 = get_airport_coord(df_airport, dest_id)
    distance = round(find_distance(coord1, coord2), 2)

    df_output = pd.DataFrame(data={"Source":[source_name], "Destination":[dest_name], "Distance": [distance]})
    df_coord = pd.DataFrame(data={"lat":[coord1[0], coord2[0]], "lon":[coord1[1], coord2[1]]})
    #print(route_list)
    return df_output, df_coord

def find_indirect_single_transfer(df_airport, df_routes, source_name, dest_name, transition=1):
    source_id = get_airport_ID(df_airport, source_name)
    dest_id = get_airport_ID(df_airport, dest_name)
    #print("Target id1, id2", source_id, dest_id)

    route_list1 = df_routes[df_routes["Source ID"] == source_id]
    route_list2 = df_routes[df_routes["Dest ID"] == dest_id]
    #print(route_list1, route_list2)
    #print(route_list1["Dest ID"].unique(), route_list2["Source ID"].unique())

    # filter the candidate list to speed up the search
    # we just need to do on one side to do a perfect match
    transfer_id2 = route_list2["Source ID"].unique()
    route_list1 = route_list1[route_list1["Dest ID"].isin(transfer_id2)]
    #print(route_list1["Dest ID"].unique(), route_list2["Source ID"].unique())

    transfer_id_list = route_list1["Dest ID"].unique()

    #transfer_id1 = route_list1["Dest ID"].unique()
    #route_list2 = route_list2[route_list2["Source ID"].isin(transfer_id1)]

    #print(route_list1)

    # compute the detailed list of transfer and the distance
    itinary = []
    coord1 = get_airport_coord(df_airport, source_id)
    coord3 = get_airport_coord(df_airport, dest_id)
    for transfer_id in transfer_id_list:
        transfer_name = get_airport_name(df_airport, transfer_id)
        coord2 = get_airport_coord(df_airport, transfer_id)
        distance = round(find_distance(coord1, coord2) + find_distance(coord2, coord3), 2)
        itinary.append((source_id, source_name, transfer_id, transfer_name, dest_id, dest_name, distance))

    itinary = np.array(sorted(itinary, key=lambda x:x[6]))
    #print(itinary.shape)

    x = len(itinary)
    if x > 0 and x < 30:
        df_output = pd.DataFrame(data={"Source":itinary[:,1], "Transfer 1":itinary[:,3], "Destination":itinary[:,5], "Distance":itinary[:,6]})
    elif x == 0:
        df_output = pd.DataFrame()
    else:
        df_output = pd.DataFrame(data={"Source":itinary[:30,1], "Transfer 1":itinary[:30,3], "Destination":itinary[:30,5], "Distance":itinary[:30,6]})

    df_coord = pd.DataFrame(data={"lat":[coord1[0], coord3[0]], "lon":[coord1[1], coord3[1]]})

    #print(itinary[:10])
    return df_output, df_coord

@st.cache
def get_country_list(df_airport):
    return list(df_airport["Country"].unique())

@st.cache
def get_airport_list(df_airport, country):
    return list(df_airport[df_airport["Country"] == country]["Name"])

@st.cache
def get_airport_id_list(df_airport):
    return df_airport["ID"].unique()

def find_indirect_double_transfer(df_airport, df_routes, source_name, dest_name, transition=1):
    source_id = get_airport_ID(df_airport, source_name)
    dest_id = get_airport_ID(df_airport, dest_name)
    #print("Target id1, id2", source_id, dest_id)

    route_list1 = df_routes[df_routes["Source ID"] == source_id]
    route_list3 = df_routes[df_routes["Dest ID"] == dest_id]
    #print(route_list1, route_list3)

    # filter the candidate list to speed up the search
    # we just need to do on one side to do a perfect match
    transfer1_list = route_list1["Dest ID"].unique()
    transfer2_list = route_list3["Source ID"].unique()

    route_list_tran = df_routes[df_routes["Source ID"].isin(transfer1_list) & df_routes["Dest ID"].isin(transfer2_list)]
    #print("1st transfer shape: {}".format(route_list1.shape))

    transfer1_list = route_list_tran["Source ID"].unique()
    transfer2_list = route_list_tran["Dest ID"].unique()
    
    # compute the detailed list of transfer and the distance
    
    airport_ID_list = get_airport_id_list(df_airport)

    itinary = []
    coord1 = get_airport_coord(df_airport, source_id)
    coord4 = get_airport_coord(df_airport, dest_id)
    for transfer1_id in transfer1_list:
        for transfer2_id in transfer2_list:
            
            # skip the route choice when the airport data is missing
            if transfer1_id not in airport_ID_list or transfer2_id not in airport_ID_list: 
                continue
            
            transfer1_name = get_airport_name(df_airport, transfer1_id)
            transfer2_name = get_airport_name(df_airport, transfer2_id)
            coord2 = get_airport_coord(df_airport, transfer1_id)
            coord3 = get_airport_coord(df_airport, transfer2_id)
            distance = round(find_distance(coord1, coord2) + find_distance(coord2, coord3) + find_distance(coord3, coord4), 2)
            itinary.append((source_id, source_name, transfer1_id, transfer1_name, transfer2_id, transfer2_name, dest_id, dest_name, distance))

    itinary = np.array(sorted(itinary, key=lambda x:x[8]))

    x = len(itinary)
    if x > 0 and x < 30:
        df_output = pd.DataFrame(data={"Source":itinary[:,1], "Transfer 1":itinary[:,3], 
            "Transfer 2":itinary[:,5], "Destination":itinary[:,7], "Distance":itinary[:,8]})
    elif x == 0:
        df_output = pd.DataFrame()
    else:
        df_output = pd.DataFrame(data={"Source":itinary[:30,1], "Transfer 1":itinary[:30,3], 
            "Transfer 2":itinary[:30,5], "Destination":itinary[:30,7], "Distance":itinary[:30,8]})

    return df_output

def main():
    st.header("Airport Connection Finder")
    st.write("This app helps you find the airport connection where a flight is available. "
            "Choose your source and destination, and the transfer option. "
            "The app will find the shortest transition path for you.")
    st.write("Written by Shing Chi Leung at 8 March 2021.")

    df_airport, df_routes = load_data()
    country_list = get_country_list(df_airport)

    st.sidebar.header("Options")
    source_country = st.sidebar.selectbox("Choose source country", country_list, index=0)
    source_airport = st.sidebar.selectbox("Choose source airport", get_airport_list(df_airport, source_country), index=0)

    dest_country = st.sidebar.selectbox("Choose destination country", country_list, index=0)
    dest_airport = st.sidebar.selectbox("Choose destination airport", get_airport_list(df_airport, dest_country), index=0)

    use_direct_flight = st.sidebar.checkbox("Direct flight")
    use_one_transfer = st.sidebar.checkbox("With one transfer")
    use_two_transfer = st.sidebar.checkbox("With two transfer")

    show_map = st.sidebar.checkbox("Show map")

    if use_direct_flight: 
        itinary, coord0 = find_direct_flight(df_airport, df_routes, source_airport, dest_airport)
        st.subheader("Connection by direct flight")
        if len(itinary) != 0:
            st.write(itinary)
        else:
            st.write("No direct flight available")

    if use_one_transfer:
        itinary, coord1 = find_indirect_single_transfer(df_airport, df_routes, source_airport, dest_airport)
        st.subheader("Connection by single transfer")
        if len(itinary) != 0:
            st.write(itinary)
        else:
            st.write("No single transfer available")

    if use_two_transfer:
        itinary = find_indirect_double_transfer(df_airport, df_routes, source_airport, dest_airport)
        st.subheader("Connection by double transfer")
        if len(itinary) != 0:
            st.write(itinary)
        else:
            st.write("No double transfer available")

    if show_map:

        df_coord = pd.DataFrame(columns=["lat", "lon"])
        if use_direct_flight:
            df_coord = pd.concat([df_coord, coord0])
        if use_one_transfer:
            df_coord = pd.concat([df_coord, coord1])

        print(df_coord)
        st.map(data=df_coord, zoom=0)
        

    st.sidebar.title("Info")
    st.sidebar.info("A short apps for finding airport connection with existing flights. "
                "Written by Shing Chi Leung at 8 March 2021. ")


if __name__=="__main__":
    main()