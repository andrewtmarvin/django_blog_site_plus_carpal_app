from django.shortcuts import render, redirect
import googlemaps, gmplot
from datetime import datetime
import smartcar
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Smartcar authorization
client = smartcar.AuthClient(
    client_id='',
    client_secret='',
    redirect_uri='',
    test_mode=True,
)

# Google Maps authorization
gmaps = googlemaps.Client(key='')


def index(request):

    # Renew Google Sheets token
    global smartcar_sheet
    global report_sheet
    sheets_scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    sheets_creds = ServiceAccountCredentials.from_json_keyfile_name('sheet_creds.json', scopes=sheets_scope)
    gc = gspread.authorize(sheets_creds)
    sht = gc.open_by_url(
        '')
    report_sheet = sht.get_worksheet(0)
    smartcar_sheet = sht.get_worksheet(1)


    list_of_lists = report_sheet.get_all_values()

    marks = []
    for row in list_of_lists[1:]:
        if row[3] == '' or row[4] == '':
            pass
        else:
            try:
                row[3] = float(row[3])
            except:
                pass
            try:
                row[4] = float(row[4])
            except:
                pass
            if row[0] == 'drunk':
                row_dic = {
                    'color': '#B22222',
                    'lat': row[3],
                    'lng': row[4],
                    'title': "License Plate: " + row[2],
                }
                marks.append(row_dic)
            elif row[0] == 'pothole':
                if row[5] == '':
                    row[5] = 'unknown'
                row_dic = {
                    'color': '#191970',
                    'lat': row[3],
                    'lng': row[4],
                    'title': "Pothole in lane: " + row[5]
                }
                marks.append(row_dic)
    mymap = gmplot.GoogleMapPlotter(marks[-1]['lat'], marks[-1]['lng'], 8, apikey='')

    for mark in marks:
        mymap.marker(lat=mark['lat'], lng=mark['lng'], color=mark['color'], title=mark['title'])
    mymap.draw("blog/templates/carpal/mymap.html")

    return render(request, 'carpal/index.html', {'all': list_of_lists[1:]})


def get_location():
    # Pulls from sheet
    access_token = smartcar_sheet.acell('A2').value
    response = smartcar.get_vehicle_ids(access_token)
    vid = response['vehicles'][0]
    vehicle = smartcar.Vehicle(vid, access_token)
    location = vehicle.location()
    pos = [location['data']['latitude'], location['data']['longitude']]
    return pos


def drunk(request):
    if request.method == 'POST':
        location = get_location()
        empty_row = len(report_sheet.col_values(1)) + 1
        report_sheet.update_cell(empty_row, 1, 'drunk')
        report_sheet.update_cell(empty_row, 2, str(datetime.now()))
        report_sheet.update_cell(empty_row, 3, '7HGY508')
        report_sheet.update_cell(empty_row, 4, location[0] + (int(request.POST['mod']) / 7000))
        report_sheet.update_cell(empty_row, 5, location[1] + (int(request.POST['mod']) / 7000))
        return redirect('/carpal/')

    if request.method == 'GET':
        return render(request, 'carpal/drunk.html')


def pothole(request):
    location = get_location()
    empty_row = len(report_sheet.col_values(1)) + 1
    report_sheet.update_cell(empty_row, 1, 'pothole')
    report_sheet.update_cell(empty_row, 2, str(datetime.now()))
    report_sheet.update_cell(empty_row, 4, location[0] + (int(request.POST['mod']) / 7000))
    report_sheet.update_cell(empty_row, 5, location[1] + (int(request.POST['mod']) / 7000))
    report_sheet.update_cell(empty_row, 6, request.POST['lane'])

    return redirect('/carpal/')


def get_sheet(request):
    values_list = report_sheet.row_values(1)

    return render(request, 'carpal/sheets.html', {'first_row': values_list})


def get_auth(request):
    auth_url = client.get_auth_url(vehicle_info={"make": "TESLA"})
    print(auth_url)
    link = auth_url
    return render(request, 'carpal/get-auth.html', {'auth_link': link})


def after_auth(request):
    if request.method == 'GET':
        auth_code = request.GET['code']
        access = client.exchange_code(auth_code)

        access_token = access['access_token']

        # Saves to sheet
        smartcar_sheet.update_acell('A2', access_token)

        response = smartcar.get_vehicle_ids(access_token)

        vid = response['vehicles'][0]

        vehicle = smartcar.Vehicle(vid, access_token)

        location = vehicle.location()

        latitude = location['data']['latitude']
        longitude = location['data']['longitude']

        mymap = gmplot.GoogleMapPlotter(latitude, longitude, 10)

        return render(request, 'carpal/after_auth.html', {'code': auth_code, 'lat': latitude, 'lon': longitude, 'mymap': mymap})

