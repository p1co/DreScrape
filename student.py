__author__ = 'pico'
from datetime import datetime

class Student( ):
    def __init__( self, name=["default"], cache="", tdTags="", worksheet="" ):
        self.name = name
        self.studHours = 0
        self.studMins = 0
        self.studSecs = 0
        self.avgWPM = 0
        self.substandardWork = []
        self.cache = cache
        self.tdTags = tdTags
        self.worksheet = worksheet

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
        cell_list = self.worksheet.range( 'A' + str( rowStart ) + ':Z' + str( rowStart ) )

        for item, cell in zip( studentList, cell_list ):
            cell.value = item

        self.worksheet.update_cells( cell_list )

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
        if 0 <= self.percentage( int( day[2].split( ' ' )[0] ), self.avgWPM ) <= 30:
            kidSubWork.append( day )
            dateList.pop( dateList.index( day ) )