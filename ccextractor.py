# Quick and dirty walk a directory and parse text files for common credit card numbers and dump them out
# console output gives a bit more specific information
#
# Sources cited inline where used
#
# Detective Robert Sirois/13025
# robertsirois@elpasoco.com
# El Paso County Sheriff's Office
# 27 East Vermijo Avenue, Colorado Springs, CO 80903

import argparse, re, os

# https://www.geeksforgeeks.org/luhn-algorithm/
def checkLuhn( cardNo ):
    nDigits = len( cardNo )
    nSum = 0
    isSecond = False

    for i in range( nDigits - 1, -1, -1 ):
        d = ord( cardNo[i] ) - ord( '0' )

        if ( isSecond == True ):
            d = d * 2

        # We add two digits to handle
        # cases that make two digits after
        # doubling
        nSum += d // 10
        nSum += d % 10

        isSecond = not isSecond

    return nSum % 10 == 0

validators = {
    'luhn': checkLuhn
}

# https://www.forensicfocus.com/news/using-keywords-with-magnet-axiom/
parsers = {
    'visa': {
        'regex': re.compile( r'''4[0-9]{12}(?:[0-9]{3})?''' )
        , 'validator': 'luhn'
    }
    , 'mc': {
        'regex': re.compile( r'''5[1-5][0-9]{14}''' )
        , 'validator': 'luhn'
    }
    , 'amex': {
        'regex': re.compile( r'''3[47][0-9]{13}''' )
        , 'validator': 'luhn'
    }
    , 'diners': {
        'regex': re.compile( r'''3(?:0[0-5]|[68][0-9])[0-9]{11}''' )
        , 'validator': 'luhn'
    }
    , 'discover': {
        'regex': re.compile( r'''6(?:011|5[0-9]{2})[0-9]{12}''' )
        , 'validator': 'luhn'
    }
    , 'jcb': {
        'regex': re.compile( r'''(?:2131|1800|35\d{3})\d{11}''' )
        , 'validator': 'luhn'
    }
}

class CCResult:
    def __init__( self, label, value, valid, filename, line, position ):
        self.label = label
        self.value = value
        self.valid = valid
        self.filename = filename
        self.line = line
        self.position = position

    def __repr__( self ):
        return '%s%s%s%s %s' % ( self.value.ljust( 20 ), self.label.ljust( 10 ), ( '  VALID' if self.valid else 'INVALID' ).ljust( 10 ), self.filename, str( self.line ) + ':' + str( self.position[0] ) + ',' + str( self.position[1] ) )

class CCExtractor:
    def __init__( self, filename, lines ):
        self.filename = filename
        self.lines = lines
        self.results = []

    def extract( self ):
        lineNum = 0

        for line in self.lines:
            lineNum += 1

            for label, parser in parsers.items():
                for match in parser['regex'].finditer( line ):
                    if match != '':
                        val = match.group()

                        self.results.append( CCResult(
                            label
                            , val
                            , validators[parser['validator']]( val )
                            , self.filename
                            , lineNum
                            , match.span()
                        ))

        for res in self.results:
            print( res )

    def getValues( self ):
        return map( lambda res: res.value, self.results )

extractors = []

# main program driver
if __name__ == '__main__':
    parser = argparse.ArgumentParser( description='Find credit card numbers in text files (recursively walks the directory given).' )
    parser.add_argument( 'path', help='Path to directory containing text files.', action='store' )
    parser.add_argument( '-o', '--output', help='Output text file name (creates a file with the path given).', type=argparse.FileType('w') )
    args = parser.parse_args()

    for root, dirs, files in os.walk( args.path, topdown=True ):
        for name in files:
            filePath = os.path.join( root, name )

            try:
                file = open( filePath, 'r' )
                extractor = CCExtractor( filePath, file.readlines() )
                extractor.extract()

                # hang onto the extractor instance for now
                # could change this later to make it a little more memory efficient
                # each extractor represents a file, which could be useful for a plugin
                extractors.append( extractor )
            except UnicodeDecodeError:
                print( 'Unable to decode file "%s" -- skipping.' % filePath )

    # this is where you would customize the output file
    if args.output:
        for extractor in extractors:
            for val in extractor.getValues():
                args.output.write( val )
                args.output.write( '\n' )

        args.output.close()

        print( 'CC numbers written to: %s' % args.output.name )
