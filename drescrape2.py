# written by pico
# testing github push

import requests
import bs4
import json
import gspread
from datetime import datetime
from oauth2client.client import SignedJwtAssertionCredentials

worksheetName = "moose"  # moose & typingweb_grades
uploadWhichGrade = "grade6"  # options: grade6 grade7 grade8

with open('creds.json') as data_file:
    data = json.load(data_file)

# datetime(year, month, day)
startDate = datetime( int( 2015 ), int( 10 ), int( 26 ) )
endDate = datetime( int( 2016 ), int( 1 ), int( 30 ) )

URL = data['url1']

print("Establishing session with typingweb.")
client = requests.session( )

# Retrieve the CSRF token first
client.get( URL )  # sets cookie
user_agent = { 'User-agent': 'Mozilla/5.0' }

print("  Sending login data.")
login_data = dict( username=data['user'], password=data['pass'], csrfmiddlewaretoken=data['csrftoken'], next='/' )
r = client.post( URL, data=login_data, headers=user_agent )

print("Establishing session with google api.")
json_key = json.load( open( data['json_key'] ) )
scope = ['https://spreadsheets.google.com/feeds']

print("  Settings creds.")
credentials = SignedJwtAssertionCredentials( json_key['client_email'], json_key['private_key'].encode( ), scope )

print("  Authorizing.")
gc = gspread.authorize( credentials )

print("  Opening spreadsheet.")
sh = gc.open( worksheetName )

# the currTime & whichGrade will be used to create unique worksheet names
currTime = datetime.now( ).strftime( '%Y-%m-%d %H:%M:%S' )

print("  Adding worksheet: " + str( uploadWhichGrade + "_" + currTime ))
worksheet = sh.add_worksheet( title=uploadWhichGrade + "_" + currTime, rows=len( data[uploadWhichGrade] ),
                              cols=26 )


class Student( ):
    def __init__( self, name=["default"], cache="", tdTags="" ):
        self.name = name
        self.studHours = 0
        self.studMins = 0
        self.studSecs = 0
        self.avgWPM = 0
        self.substandardWork = []
        self.cache = cache
        self.tdTags = tdTags

    def percentage( self, part, whole ):
        if part == 0:
            part = 1
        if whole == 0:
            whole = 1
        return int( 100 * float( part ) / float( whole ) )

    def calcWPM( self, date ):
        sum = 0
        for x in date:
            sum += int( x[2].split( ' ' )[0] )
        try:
            return int( sum / len( date ) ) if sum > 0 else 0
        except:
            print("something in calcWPM broke!! " + str( date ))

    def writeGoogle( self, rowStart, studentList, nameStudent ):
        # print("Current {} spreadsheet row: {}".format(nameStudent, rowStart))
        cell_list = worksheet.range( 'A' + str( rowStart ) + ':Z' + str( rowStart ) )

        for item, cell in zip( studentList, cell_list ):
            cell.value = item

        worksheet.update_cells( cell_list )

        return rowStart + 1

    # translate the date in the data to a format
    # used by datetime module
    def calcDateBasedOnDataEntries( self, day ):
        # because those typingweb idiots wrote 'Sept' instead of 'Sep'
        if day[0].split( ' ' )[0] == 'Sept.':
            return datetime( int( day[0].split( ' ' )[2] ), 9, int( day[0].split( ' ' )[1].split( ',' )[0] ) )
        else:
            return datetime.strptime( day[0], '%b. %d, %Y' )
            # assholes..

    # time spent
    def calcTimeSpent( self, day, studHours, studMins, studSecs ):
        if day[1].count( ':' ) > 1:  # If there was work > 1 hr
            studHours += int( day[1].split( ' ' )[0].split( ':' )[0] )
            # print("hours: " + day[1].split(' ')[0].split(':')[0])
            studMins += int( day[1].split( ' ' )[0].split( ':' )[1] )
            # print("mins: " + day[1].split(' ')[0].split(':')[1])
            studSecs += int( day[1].split( ' ' )[0].split( ':' )[2] )
            # print("secs: " + day[1].split(' ')[0].split(':')[2])
        else:  # If there was work < 1 hr
            studMins += int( day[1].split( ' ' )[0].split( ':' )[0] )
            # print("mins: " + day[1].split(' ')[0].split(':')[0])
            studSecs += int( day[1].split( ' ' )[0].split( ':' )[1] )
            # print("secs: " + day[1].split(' ')[0].split(':')[1])

        return studHours, studMins, studSecs

    # checks whether student did substandard work, if this is the case, the program
    # moves onto the next day and does not add the worked time to the counter
    def calcSubstandardWorkWPM( self, day, dateList, kidSubWork ):
        if 0 <= kid.percentage( int( day[2].split( ' ' )[0] ), kid.avgWPM ) <= 30:
            kidSubWork.append( day )
            dateList.pop( dateList.index( day ) )


# for generating worksheet in spreadsheet
rowStart = 1

useTheseStudents = []
for key, value in data.iteritems():
    if key == uploadWhichGrade:
        for item in value:
            useTheseStudents.append( item )

for student in useTheseStudents:
    r = client.get(data['url2'] + student + data['url3'])

    studentCache = bs4.BeautifulSoup( r.text, "html.parser" )
    #  studentCache = bs4.BeautifulSoup( open('test.html','r'), "html.parser" )
    tdTags = studentCache.find_all( 'td' )

    # saves student name
    studentName = studentCache.find_all( 'h1' )

    kid = Student( [studentName[0].text.split( ' ' )[0], studentName[0].text.split( ' ' )[1]],
                   studentCache,
                   tdTags )

    # this list will store a single attempt, time, WPM, and %
    lineData = []

    # this list will store all of the days in a list of lists format
    masterList = []

    # build the single attempt
    for line in kid.tdTags:
        if line.text.strip( ).isdigit( ):
            masterList.append( lineData )
            lineData = []
        else:
            lineData.append( line.text )

    # this section weeds out the days not between the specified date range
    dateList = []
    for day in masterList:
        date = kid.calcDateBasedOnDataEntries( day )

        if startDate <= date <= endDate:
            dateList.append( day )
        else:
            continue

    for day in dateList:
        if 0 <= int( day[3].split( '%' )[0] ) <= 20:  # Accuracy
            kid.substandardWork.append( day )
            dateList.pop( dateList.index( day ) )
            continue

    if len( dateList ) == 0:
        studentDir = [kid.name[0], kid.name[1], "No work during this period"]
        rowStart = kid.writeGoogle( rowStart, studentDir, studentName )
        continue

    try:
        kid.avgWPM = kid.calcWPM( dateList )
    except:
        print("calcWPM, getting the avgWPM, BROKE!!! :(   " + dateList)

    for day in dateList:
        kid.calcSubstandardWorkWPM( day, dateList, kid.substandardWork )

    # time spent
    for day in dateList:
        studHours, studMins, studSecs = kid.calcTimeSpent( day, kid.studHours, kid.studMins, kid.studSecs )

    # first name, last name, minutes, date range, wpm, class, substandard
    studentDir = [kid.name[0],
                  kid.name[1],
                  str( kid.studMins + (kid.studHours * 60) + int( kid.studSecs / 60 ) ),
                  str( startDate ).split( ' ' )[0] + " to " + str( endDate ).split( ' ' )[0],
                  str( kid.avgWPM ) + " WPM"]

    # if there are substandard work days, add to the student record those
    if len( kid.substandardWork ) != 0:
        studentDir.append( "Substandard days:" )
        for substandardDays in kid.substandardWork:
            myList = ', '.join( map( str, substandardDays ) )
            studentDir.append( myList )

    # f = open('dretest.txt','a+')
    # for thing in studentDir:
    #     f.write(str(thing) + " ")
    # f.write("\n")
    # f.close()
    rowStart = kid.writeGoogle( rowStart, studentDir, kid.name[0] + kid.name[1] )

print("Done processing grade {}.".format( uploadWhichGrade[-1] ))
