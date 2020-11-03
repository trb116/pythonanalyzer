#!/usr/bin/python

###################################################
### THE VALUES BELOW CAN BE EDITED AS NEEDED ######
###################################################

kFontInstanceFileName = "font.ufo"
kInstancesDataFileName = "instances"

###################################################

__copyright__ = __license__ =  """
Copyright (c) 2014 Adobe Systems Incorporated. All rights reserved.
 
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"), 
to deal in the Software without restriction, including without limitation 
the rights to use, copy, modify, merge, publish, distribute, sublicense, 
and/or sell copies of the Software, and to permit persons to whom the 
Software is furnished to do so, subject to the following conditions:
 
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
DEALINGS IN THE SOFTWARE.
"""

__usage__ = """
UFOInstanceGenerator v2.1 - Dec 02 2014

python UFOInstanceGenerator.py -h
python UFOInstanceGenerator.py [<input_folder_path>] [-o <output_folder_path>] [-kern] [-mark] [-min <integer>] [...]

"""

__help__ = __usage__ + """
GENERAL OPTIONS
-h	Print help
-u	Print usage
-d	Print documentation
-o	Output folder path
-v	Enable verbose mode

MAIN OPTIONS
-kern	Generate 'kern' feature
-mark	Generate 'mark' feature
-hint	Autohint the font instances
-flat	Flatten the glyphs (i.e. remove overlaps)
-nufo	Do not save the UFO instance files

KERN FEATURE OPTIONS
-min	Minimum kern value (inclusive). Default is 3 units
-wtr	Write trimmed pairs
-wsb	Write subtables

MARK FEATURE OPTIONS
-mkmk	Write mark-to-mark lookups
-clas	Write mark classes in separate file
-indi	Format the output for Indian scripts
-trtg	Trim casing tags on anchor names

"""

__doc__ = """
This script will generate a set of UFO instances from a series of main design fonts.
The main designs must be compatible. For each instance, in addition to creating a UFO 
font file, the script can also write 'kern', 'mark' and 'mkmk' feature files. These 
files will be saved in the same folder as the UFO font instance.

For information about how the "kern.fea" file is created, please read the documentation 
in the WriteFeaturesKernFDK.py module.

For information about how the "mark/mkmk.fea" files are created, please read the 
documentation in the WriteFeaturesMarkFDK.py module.

The UFO font files are written to a sub-directory path <selected_folder>/<face_name>, 
where the face name is derived by taking the part of the font's PostScript name after the 
hyphen, or "Regular" if there is no hyphen (e.g. if the font's PostScript name is 
MyFont-BoldItalic, the folder will be named "BoldItalic")

This script depends on info provided by an external simple text file named "instances".
The data supplied in this file, is used for specifying the instance's values, and for 
providing the font names used in the UFO's fontinfo.plist file. The "instances" file 
must be located in the same folder as the UFO main files. Each line specifies one 
instance, as a record of tab-delimited fields. The first 6 fields are always, in order:

  FamilyName : This is the Preferred Family name.
  FontName   : This is the PostScript name.
  FullName   : This is the Preferred Full name.
  Weight     : This is the Weight name.
  Coords     : This is a single value, or a sequence of comma-separated integer values.
			   Each integer value corresponds to an axis.
  IsBold     : This must be either 1 (True) or 0 (False). This will be translated into
			   Postscript FontDict ForceBold field. The recommended value is 0 for all the
			   instances.
  Mains    : Optional. This is for using intermediate mains in a linear interpolation,
			   The mains are specified as a tuple of file names (see example below).



  Examples:
	# Two mains, one axis
	MyFontStd<tab>MyFontStd-Bold<tab>MyFont Std Bold<tab>Bold<tab>650<tab>1
	MyFontStd<tab>MyFontStd-Regular<tab>MyFont Std Regular<tab>Regular<tab>350<tab>0	

	# Three mains, one axis (interpolation with intermediate main)
	MyFontPro<tab>MyFontPro-Light<tab>MyFontPro Light<tab>Light <tab>(408)<tab>0<tab>("MyFontPro_0.ufo", "MyFontPro_1.ufo")
	MyFontPro<tab>MyFontPro-Regular<tab>MyFontPro<tab>Regular<tab>(41)<tab>0<tab>("MyFontPro_1.ufo", "MyFontPro_2.ufo")
	MyFontPro<tab>MyFontPro-Semibold<tab>MyFontPro Semibold<tab>Semibold<tab>(367)<tab>0<tab>("MyFontPro_1.ufo", "MyFontPro_2.ufo")


(All empty lines and all the lines that start with the number sign (#) are ignored.)


[NOT IMPLEMENTED]    If only these six fields are used, then there is no need for a header line.
[NOT IMPLEMENTED]    However, if any additional fields are used, then the file must contain a line
[NOT IMPLEMENTED]    starting with "#KEYS:", and continuing with tab-delimited field names. Two of
[NOT IMPLEMENTED]    the additional fields allowed are:
[NOT IMPLEMENTED]    
[NOT IMPLEMENTED]      ExceptionSuffixes : A list of suffixes, used to identify MM exception glyphs. An
[NOT IMPLEMENTED]      MM exception glyph is one which is designed for use in only one instance, and is
[NOT IMPLEMENTED]      used by replacing every occurence of the glyphs that match the MM exception
[NOT IMPLEMENTED]      glyph's base name. The MM exception glyph is used in no other instance. This
[NOT IMPLEMENTED]      allows the developer to fix problems with just a few glyphs in each instance.
[NOT IMPLEMENTED]      For example, in the record for HypatiaSansPro-Black the 'instances' file
[NOT IMPLEMENTED]      specifies an ExceptionSuffix suffix list which contains the suffix "-black", and
[NOT IMPLEMENTED]      there is an MM exception glyph named "a-black", then the glyph "a" will be
[NOT IMPLEMENTED]      replaced by the glyph "a-black", and all composite glyphs that use "a" will be
[NOT IMPLEMENTED]      updated to use the contours from "a-black" instead.
[NOT IMPLEMENTED]      
[NOT IMPLEMENTED]      ExtraGlyphs : A list of working glyph names, to be omitted from the instances.
[NOT IMPLEMENTED]      This may be a complete glyph name, or a wild-card pattern. A pattern may take two
[NOT IMPLEMENTED]      forms: "*<suffix>", which will match any glyph ending with that suffix, or a
[NOT IMPLEMENTED]      regular expression which must match entire glyph names. The pattern must begin
[NOT IMPLEMENTED]      with "^" and end with "$". You do not need to include glyph names which match
[NOT IMPLEMENTED]      an MM Exception glyph suffix: such glyphs will not be written to any instance.
[NOT IMPLEMENTED]    
[NOT IMPLEMENTED]      Example:
[NOT IMPLEMENTED]    	#KEYS:FamilyName<tab>FontName<tab>FullName<tab>Weight<tab>Coords<tab>IsBold<tab>ExceptionSuffixes<tab>ExtraGlyphs
[NOT IMPLEMENTED]    	MyFontPro<tab>MyFontPro-ExtraLight<tab>MyFont Pro ExtraLight<tab>ExtraLight<tab>0<tab>0<tab><tab>["*-black","*-aux"]
[NOT IMPLEMENTED]    	MyFontPro<tab>MyFontPro-Black<tab>MyFont Pro Black<tab>Black<tab>1000<tab>0<tab>["-black"]<tab>["*-aux"]
[NOT IMPLEMENTED]    
[NOT IMPLEMENTED]    
[NOT IMPLEMENTED]    The other additional field names are assumed to be the names for Postscript FontDict
[NOT IMPLEMENTED]    keys, such as: BlueScale, BlueShift, BlueFuzz, BlueValues, OtherBlues, FamilyBlues, FamilyOtherBlues, StdHW, StdVW, StemSnapH, StemSnapV
[NOT IMPLEMENTED]    
[NOT IMPLEMENTED]      Example:
[NOT IMPLEMENTED]    	#KEYS:FamilyName<tab>FontName<tab>FullName<tab>Weight<tab>Coords<tab>IsBold<tab>BlueFuzz<tab>BlueScale<tab>BlueValues
[NOT IMPLEMENTED]    	MyFontPro<tab><MyFontPro-Regular<tab>MyFont Pro Regular<tab>Regular<tab>160,451<tab>0<tab>0<tab>0.0479583<tab>[-18 0 395 410 439 453 596 608 615 633 672 678]
[NOT IMPLEMENTED]    	MyFontPro<tab><MyFontPro-Bold<tab>MyFont Pro Bold<tab>Bold<tab>1000,451<tab>1<tab>0<tab>0.0479583<tab>[-18 0 400 414 439 453 584 596 603 621 653 664]


==================================================
Versions:
v1.0   - Mar 10 2013 - Initial release
v1.0.1 - Mar 13 2013 - Added shebang
v2.0   - Sep 05 2013 - Removed the step of handling Type 1 files; UFO is now the default font format.
                       Added the option to not save the fonts.
                       Removed the dependencies on 'ufo2fdk' and 'defcon' now that the FDK tools support the UFO format natively.
v2.0.1 - Apr 22 2014 - Added Unicode values to glyphs in interpolated instances.
v2.1   - Dec 02 2014 - Added the possibility to use intermediate mains.

"""

import os, sys, time, copy, re, math, shutil
from subprocess import Popen, PIPE
from robofab.world import NewFont, OpenFont
from robofab.objects import objectsBase

fdkExtrasDir = os.path.dirname(os.path.abspath(__file__))
pyScriptsDir = os.path.dirname(fdkExtrasDir)
pyModulesDir = os.path.join(os.path.dirname(pyScriptsDir), "python-modules")

if pyModulesDir not in sys.path:
	sys.path.append(pyModulesDir)

try:
	import WriteFeaturesKernFDK, WriteFeaturesMarkFDK
except ImportError:
	print >> sys.stderr, "ERROR: Failed to find the FDK Python modules."
	print "\nCurrent directory:\n\t", os.path.abspath(os.getcwd())
	print "\nCurrent list of search paths for modules:\n\t",
	print "\n\t".join(sys.path)
	print
	raise


kFieldsKey         = "#KEYS:"
kFamilyName        = "FamilyName"
kFontName          = "FontName"
kFullName          = "FullName"
kWeight            = "Weight"
kCoordsKey         = "Coords"
kIsBoldKey         = "IsBold" # This is changed to kForceBold in the instanceDict when reading in the instance file.
kForceBold         = "ForceBold"
kIsItalicKey       = "IsItalic"
kExceptionSuffixes = "ExceptionSuffixes"
kExtraGlyphs       = "ExtraGlyphs"
kMains           = "Mains"

kFixedFieldKeys = {
		# field index: key name
		0:kFamilyName,
		1:kFontName,
		2:kFullName,
		3:kWeight,
		4:kCoordsKey,
		5:kIsBoldKey,
		}

kNumFixedFields = len(kFixedFieldKeys)

kBlueScale        = "BlueScale"
kBlueShift        = "BlueShift"
kBlueFuzz         = "BlueFuzz"
kBlueValues       = "BlueValues"
kOtherBlues       = "OtherBlues"
kFamilyBlues      = "FamilyBlues"
kFamilyOtherBlues = "FamilyOtherBlues"
kStdHW            = "StdHW"
kStdVW            = "StdVW"
kStemSnapH        = "StemSnapH"
kStemSnapV        = "StemSnapV"

kHintingKeys        = [kBlueScale, kBlueShift, kBlueFuzz, kBlueValues, kOtherBlues, kFamilyBlues, kFamilyOtherBlues, kStdHW, kStdVW, kStemSnapH, kStemSnapV]
kAlignmentZonesKeys = [kBlueValues, kOtherBlues, kFamilyBlues, kFamilyOtherBlues]
kTopAlignZonesKeys  = [kBlueValues, kFamilyBlues]
kMaxTopZonesSize    = 14 # 7 zones
kBotAlignZonesKeys  = [kOtherBlues, kFamilyOtherBlues]
kMaxBotZonesSize    = 10 # 5 zones
kStdStemsKeys       = [kStdHW, kStdVW]
kMaxStdStemsSize    = 1
kStemSnapKeys       = [kStemSnapH, kStemSnapV]
kMaxStemSnapSize    = 12 # including StdStem


def validateArrayValues(arrayList, valuesMustBePositive):
	for i in range(len(arrayList)):
		try:
			arrayList[i] = eval(arrayList[i])
		except (NameError, SyntaxError):
			return
		if valuesMustBePositive:
			if arrayList[i] < 0:
				return
	return arrayList


def readInstanceFile(instancesFilePath):
	f = open(instancesFilePath, "rt")
	data = f.read()
	f.close()
	
	lines = data.splitlines()
	
	i = 0
	parseError = 0
	keyDict = copy.copy(kFixedFieldKeys)
	numKeys = kNumFixedFields
	numLines = len(lines)
	instancesList = []
	
	for i in range(numLines):
		line = lines[i]
		
		# Skip over blank lines
		line2 = line.strip()
		if not line2:
			continue

		# Get rid of all comments. If we find a key definition comment line, parse it.
		commentIndex = line.find('#')
		if commentIndex >= 0:
			if line.startswith(kFieldsKey):
				if instancesList:
					print >> sys.stderr, "ERROR: Header line (%s) must preceed a data line." % kFieldsKey
					raise
				# parse the line with the field names.
				line = line[len(kFieldsKey):]
				line = line.strip()
				keys = line.split('\t')
				keys = map(lambda name: name.strip(), keys)
				numKeys = len(keys)
				k = kNumFixedFields
				while k < numKeys:
					keyDict[k] = keys[k]
					k +=1
				continue
			else:
				line = line[:commentIndex]
				continue

		# Must be a data line.
		fields = line.split('\t')
		fields = map(lambda datum: datum.strip(), fields)
		numFields = len(fields)
		if (numFields != numKeys):
			print >> sys.stderr, "ERROR: In line %s, the number of fields %s does not match the number of key names %s (FamilyName, FontName, FullName, Weight, Coords, IsBold)." % (i+1, numFields, numKeys)
			parseError = 1
			continue
		
		instanceDict= {}
		#Build a dict from key to value. Some kinds of values needs special processing.
		for k in range(numFields):
			key = keyDict[k]
			field = fields[k]
			if not field:
				continue
			if field in ["Default", "None", "FontBBox"]:
				# FontBBox is no longer supported - I calculate the real
				# instance fontBBox from the glyph metrics instead,
				continue
			if key == kFontName:
				value = field
			if key == kMains:
				value = eval(field)
			elif key in [kExtraGlyphs, kExceptionSuffixes]:
				value = eval(field)
			elif key in [kIsBoldKey, kIsItalicKey, kCoordsKey]:
				try:
					value = eval(field) # this works for all three fields.
					
					if key == kIsBoldKey: # need to convert to Type 1 field key.
						instanceDict[key] = value
						# add kForceBold key.
						key = kForceBold
						if value == 1:
							value = "true"
						else:
							value = "false"
					elif key == kIsItalicKey:
						if value == 1:
							value = "true"
						else:
							value = "false"
					elif key == kCoordsKey:
						if type(value) == type(0):
							value = (value,)
				except (NameError, SyntaxError):
					print >> sys.stderr, "ERROR: In line %s, the %s field has an invalid value." % (i+1, key)
					parseError = 1
					continue

			elif field[0] in ["[","{"]: # it is a Type 1 array value. Turn it into a list and verify that there's an even number of values for the alignment zones
				value = field[1:-1].split() # Remove the begin and end brackets/braces, and make a list
				
				if key in kAlignmentZonesKeys:
					if len(value) % 2 != 0:
						print >> sys.stderr, "ERROR: In line %s, the %s field does not have an even number of values." % (i+1, key)
						parseError = 1
						continue
				
				if key in kTopAlignZonesKeys: # The Type 1 spec only allows 7 top zones (7 pairs of values)
					if len(value) > kMaxTopZonesSize:
						print >> sys.stderr, "ERROR: In line %s, the %s field has more than %d values." % (i+1, key, kMaxTopZonesSize)
						parseError = 1
						continue
					else:
						newArray = validateArrayValues(value, False) # False = values do NOT have to be all positive
						if newArray:
							value = newArray
						else:
							print >> sys.stderr, "ERROR: In line %s, the %s field contains invalid values." % (i+1, key)
							parseError = 1
							continue
					currentArray = value[:] # make copy, not reference
					value.sort()
					if currentArray != value:
						print "WARNING: In line %s, the values in the %s field were sorted in ascending order." % (i+1, key)
				
				if key in kBotAlignZonesKeys: # The Type 1 spec only allows 5 top zones (5 pairs of values)
					if len(value) > kMaxBotZonesSize:
						print >> sys.stderr, "ERROR: In line %s, the %s field has more than %d values." % (i+1, key, kMaxBotZonesSize)
						parseError = 1
						continue
					else:
						newArray = validateArrayValues(value, False) # False = values do NOT have to be all positive
						if newArray:
							value = newArray
						else:
							print >> sys.stderr, "ERROR: In line %s, the %s field contains invalid values." % (i+1, key)
							parseError = 1
							continue
					currentArray = value[:] # make copy, not reference
					value.sort()
					if currentArray != value:
						print "WARNING: In line %s, the values in the %s field were sorted in ascending order." % (i+1, key)
				
				if key in kStdStemsKeys:
					if len(value) > kMaxStdStemsSize:
						print >> sys.stderr, "ERROR: In line %s, the %s field can only have %d value." % (i+1, key, kMaxStdStemsSize)
						parseError = 1
						continue
					else:
						newArray = validateArrayValues(value, True) # True = all values must be positive
						if newArray:
							value = newArray
						else:
							print >> sys.stderr, "ERROR: In line %s, the %s field has an invalid value." % (i+1, key)
							parseError = 1
							continue
				
				if key in kStemSnapKeys: # The Type 1 spec only allows 12 stem widths, including 1 standard stem
					if len(value) > kMaxStemSnapSize:
						print >> sys.stderr, "ERROR: In line %s, the %s field has more than %d values." % (i+1, key, kMaxStemSnapSize)
						parseError = 1
						continue
					else:
						newArray = validateArrayValues(value, True) # True = all values must be positive
						if newArray:
							value = newArray
						else:
							print >> sys.stderr, "ERROR: In line %s, the %s field contains invalid values." % (i+1, key)
							parseError = 1
							continue
					currentArray = value[:] # make copy, not reference
					value.sort()
					if currentArray != value:
						print "WARNING: In line %s, the values in the %s field were sorted in ascending order." % (i+1, key)
			else:
				# either a single number or a string.
				if re.match(r"^[-.\d]+$", field):
					value = field #it is a Type 1 number. Pass as is, as a string.
				else:
					value = field
			
			instanceDict[key] = value
				
		if (kStdHW in instanceDict and kStemSnapH not in instanceDict) or (kStdHW not in instanceDict and kStemSnapH in instanceDict):
			print >> sys.stderr, "ERROR: In line %s, either the %s value or the %s values are missing or were invalid." % (i+1, kStdHW, kStemSnapH)
			parseError = 1
		elif (kStdHW in instanceDict and kStemSnapH in instanceDict): # cannot be just 'else' because it will generate a 'KeyError' when these hinting parameters are not provided in the 'instances' file
			if instanceDict[kStemSnapH][0] != instanceDict[kStdHW][0]:
				print >> sys.stderr, "ERROR: In line %s, the first value in %s must be the same as the %s value." % (i+1, kStemSnapH, kStdHW)
				parseError = 1

		if (kStdVW in instanceDict and kStemSnapV not in instanceDict) or (kStdVW not in instanceDict and kStemSnapV in instanceDict):
			print >> sys.stderr, "ERROR: In line %s, either the %s value or the %s values are missing or were invalid." % (i+1, kStdVW, kStemSnapV)
			parseError = 1
		elif (kStdVW in instanceDict and kStemSnapV in instanceDict): # cannot be just 'else' because it will generate a 'KeyError' when these hinting parameters are not provided in the 'instances' file
			if instanceDict[kStemSnapV][0] != instanceDict[kStdVW][0]:
				print >> sys.stderr, "ERROR: In line %s, the first value in %s must be the same as the %s value." % (i+1, kStemSnapV, kStdVW)
				parseError = 1
		
		instancesList.append(instanceDict)
		
	if parseError or len(instancesList) == 0:
		raise
		
	return instancesList
	

def makeFaceFolder(root, folder):
	facePath = os.path.join(root, folder)
	if not os.path.exists(facePath):
		os.makedirs(facePath)
	return facePath


def makeInstance(counter, ufoMains, instanceInfo, outputDirPath, options):

	if len(ufoMains) == 2:
		'Linear interpolation with 2 mains'
		pass
	else:
		'Linear interpolation with intermediate mains'
		ufoMains = [main for main in ufoMains if os.path.basename(main.path) in instanceInfo.get(kMains)]

	try:
		faceName = instanceInfo[kFontName].split('-')[1]
	except IndexError:
		faceName = 'Regular'

	print
	print "%s (%d/%d)" % (faceName, counter[0], counter[1])
	
	# Calculate the value of the interpolation factor
	# XXX It's currently assuming a 0-1000 axis
	interpolationFactor = instanceInfo[kCoordsKey][0]/1000.000

	glyphOrder = ufoMains[0].lib["public.glyphOrder"]
	
	# aGlyph.isCompatible(otherGlyph, report=True)
# 	for glyphName in glyphOrder:
# 		ufoMains[0][glyphName].isCompatible(ufoMains[1][glyphName], True)
	
	ufoInstance = NewFont()
	
	# Interpolate the mains
	# Documentation: http://www.robofab.org/howto/interpolate.html
	# aFont.interpolate(factor, minFont, maxFont, suppressError=True, analyzeOnly=False)
	# aFont.interpolate() interpolates:
	#	- positions of components
	#	- anchors
	#	- ascender
	#	- descender
	#	- glyph widths for the whole font
	ufoInstance.interpolate(interpolationFactor, ufoMains[0], ufoMains[1])
	
	# Round all the point coordinates to whole integer numbers
	ufoInstance.round()

	# Interpolate the kerning
	# Documentation: http://www.robofab.org/objects/kerning.html
	# f.kerning.interpolate(sourceDictOne, sourceDictTwo, value, clearExisting=True)
	if len(ufoMains[0].kerning):
		ufoInstance.kerning.interpolate(ufoMains[0].kerning, ufoMains[1].kerning, interpolationFactor)
		ufoInstance.kerning.round(1) # convert the interpolated values to integers
	
	for glyphName in glyphOrder:
		ufoInstance[glyphName].unicode = ufoMains[0][glyphName].unicode

		if len(ufoMains[0][glyphName]) != len(ufoInstance[glyphName]):
			print "\tWARNING: Interpolation failed in glyph %s" % glyphName

	styleName = instanceInfo[kFullName].replace(instanceInfo[kFamilyName], '').strip()
	ufoInstance.info.styleName = styleName

	ufoInstance.info.familyName = instanceInfo[kFamilyName]
	ufoInstance.info.postscriptFontName = instanceInfo[kFontName]
	ufoInstance.info.postscriptFullName = instanceInfo[kFullName]
	ufoInstance.info.postscriptWeightName = instanceInfo[kWeight]
	ufoInstance.info.postscriptForceBold = True if instanceInfo[kIsBoldKey] else False
	
	ufoInstance.lib = ufoMains[0].lib
	ufoInstance.groups = ufoMains[0].groups
	
	ufoInstance.info.copyright = ufoMains[0].info.copyright
	ufoInstance.info.trademark = ufoMains[0].info.trademark
	ufoInstance.info.unitsPerEm = ufoMains[0].info.unitsPerEm
	ufoInstance.info.versionMajor = ufoMains[0].info.versionMajor
	ufoInstance.info.versionMinor = ufoMains[0].info.versionMinor
	ufoInstance.info.postscriptIsFixedPitch = ufoMains[0].info.postscriptIsFixedPitch
	
	# ascender
	if ufoMains[0].info.ascender and ufoMains[1].info.ascender:
		ufoInstance.info.ascender = int(round(objectsBase._interpolate(ufoMains[0].info.ascender, ufoMains[1].info.ascender, interpolationFactor)))
	# descender
	if ufoMains[0].info.descender and ufoMains[1].info.descender:
		ufoInstance.info.descender = int(round(objectsBase._interpolate(ufoMains[0].info.descender, ufoMains[1].info.descender, interpolationFactor)))
	# capHeight
	if ufoMains[0].info.capHeight and ufoMains[1].info.capHeight:
		ufoInstance.info.capHeight = int(round(objectsBase._interpolate(ufoMains[0].info.capHeight, ufoMains[1].info.capHeight, interpolationFactor)))
	# xHeight
	if ufoMains[0].info.xHeight and ufoMains[1].info.xHeight:
		ufoInstance.info.xHeight = int(round(objectsBase._interpolate(ufoMains[0].info.xHeight, ufoMains[1].info.xHeight, interpolationFactor)))
	# italicAngle
	if (ufoMains[0].info.italicAngle != None) and (ufoMains[1].info.italicAngle != None):
		ufoInstance.info.italicAngle = int(round(objectsBase._interpolate(ufoMains[0].info.italicAngle, ufoMains[1].info.italicAngle, interpolationFactor)))
	# postscriptUnderlinePosition
	if ufoMains[0].info.postscriptUnderlinePosition and ufoMains[1].info.postscriptUnderlinePosition:
		ufoInstance.info.postscriptUnderlinePosition = int(round(objectsBase._interpolate(ufoMains[0].info.postscriptUnderlinePosition, ufoMains[1].info.postscriptUnderlinePosition, interpolationFactor)))
	# postscriptUnderlineThickness
	if ufoMains[0].info.postscriptUnderlineThickness and ufoMains[1].info.postscriptUnderlineThickness:
		ufoInstance.info.postscriptUnderlineThickness = int(round(objectsBase._interpolate(ufoMains[0].info.postscriptUnderlineThickness, ufoMains[1].info.postscriptUnderlineThickness, interpolationFactor)))
	# postscriptBlueFuzz
	if (ufoMains[0].info.postscriptBlueFuzz != None) and (ufoMains[1].info.postscriptBlueFuzz != None):
		ufoInstance.info.postscriptBlueFuzz = int(round(objectsBase._interpolate(ufoMains[0].info.postscriptBlueFuzz, ufoMains[1].info.postscriptBlueFuzz, interpolationFactor)))
	# postscriptBlueScale
	if ufoMains[0].info.postscriptBlueScale and ufoMains[1].info.postscriptBlueScale:
		ufoInstance.info.postscriptBlueScale = objectsBase._interpolate(ufoMains[0].info.postscriptBlueScale, ufoMains[1].info.postscriptBlueScale, interpolationFactor)
	# postscriptBlueShift
	if ufoMains[0].info.postscriptBlueShift and ufoMains[1].info.postscriptBlueShift:
		ufoInstance.info.postscriptBlueShift = int(round(objectsBase._interpolate(ufoMains[0].info.postscriptBlueShift, ufoMains[1].info.postscriptBlueShift, interpolationFactor)))

	# postscriptBlueValues
	if len(ufoMains[0].info.postscriptBlueValues) == len(ufoMains[1].info.postscriptBlueValues):
		ufoMains[0].info.postscriptBlueValues.sort()
		ufoMains[1].info.postscriptBlueValues.sort()
		tempArray = []
		for i in range(len(ufoMains[0].info.postscriptBlueValues)):
			tempArray.append(int(round(objectsBase._interpolate(ufoMains[0].info.postscriptBlueValues[i], ufoMains[1].info.postscriptBlueValues[i], interpolationFactor))))
		ufoInstance.info.postscriptBlueValues = tempArray
	# postscriptOtherBlues
	if len(ufoMains[0].info.postscriptOtherBlues) == len(ufoMains[1].info.postscriptOtherBlues):
		ufoMains[0].info.postscriptOtherBlues.sort()
		ufoMains[1].info.postscriptOtherBlues.sort()
		tempArray = []
		for i in range(len(ufoMains[0].info.postscriptOtherBlues)):
			tempArray.append(int(round(objectsBase._interpolate(ufoMains[0].info.postscriptOtherBlues[i], ufoMains[1].info.postscriptOtherBlues[i], interpolationFactor))))
		ufoInstance.info.postscriptOtherBlues = tempArray
	# postscriptFamilyBlues
	if len(ufoMains[0].info.postscriptFamilyBlues) == len(ufoMains[1].info.postscriptFamilyBlues):
		ufoMains[0].info.postscriptFamilyBlues.sort()
		ufoMains[1].info.postscriptFamilyBlues.sort()
		tempArray = []
		for i in range(len(ufoMains[0].info.postscriptFamilyBlues)):
			tempArray.append(int(round(objectsBase._interpolate(ufoMains[0].info.postscriptFamilyBlues[i], ufoMains[1].info.postscriptFamilyBlues[i], interpolationFactor))))
		ufoInstance.info.postscriptFamilyBlues = tempArray
	# postscriptFamilyOtherBlues
	if len(ufoMains[0].info.postscriptFamilyOtherBlues) == len(ufoMains[1].info.postscriptFamilyOtherBlues):
		ufoMains[0].info.postscriptFamilyOtherBlues.sort()
		ufoMains[1].info.postscriptFamilyOtherBlues.sort()
		tempArray = []
		for i in range(len(ufoMains[0].info.postscriptFamilyOtherBlues)):
			tempArray.append(int(round(objectsBase._interpolate(ufoMains[0].info.postscriptFamilyOtherBlues[i], ufoMains[1].info.postscriptFamilyOtherBlues[i], interpolationFactor))))
		ufoInstance.info.postscriptFamilyOtherBlues = tempArray
	# postscriptStemSnapH
	if len(ufoMains[0].info.postscriptStemSnapH) == len(ufoMains[1].info.postscriptStemSnapH):
		ufoMains[0].info.postscriptStemSnapH.sort()
		ufoMains[1].info.postscriptStemSnapH.sort()
		tempArray = []
		for i in range(len(ufoMains[0].info.postscriptStemSnapH)):
			tempArray.append(int(round(objectsBase._interpolate(ufoMains[0].info.postscriptStemSnapH[i], ufoMains[1].info.postscriptStemSnapH[i], interpolationFactor))))
		ufoInstance.info.postscriptStemSnapH = tempArray
	# postscriptStemSnapV
	if len(ufoMains[0].info.postscriptStemSnapV) == len(ufoMains[1].info.postscriptStemSnapV):
		ufoMains[0].info.postscriptStemSnapV.sort()
		ufoMains[1].info.postscriptStemSnapV.sort()
		tempArray = []
		for i in range(len(ufoMains[0].info.postscriptStemSnapV)):
			tempArray.append(int(round(objectsBase._interpolate(ufoMains[0].info.postscriptStemSnapV[i], ufoMains[1].info.postscriptStemSnapV[i], interpolationFactor))))
		ufoInstance.info.postscriptStemSnapV = tempArray
	

	faceFolder = makeFaceFolder(outputDirPath, faceName)
	ufoPath = os.path.join(faceFolder, kFontInstanceFileName)

	# Save UFO instance
	if not options.noUFOs:
		print '\tSaving %s file...' % kFontInstanceFileName
	
		# Delete the old UFO file, if it exists
		while os.path.exists(ufoPath):
			shutil.rmtree(ufoPath)
	
		ufoInstance.save(ufoPath)
	
	# Generate 'kern' feature
	if options.genKernFeature:
		print "\tGenerating 'kern' feature..."
		WriteFeaturesKernFDK.KernDataClass(ufoInstance, faceFolder, options.minKern, options.writeTrimmed, options.writeSubtables)

	# Generate 'mark/mkmk' features
	if options.genMarkFeature:
		if options.genMkmkFeature:
			print "\tGenerating 'mark' and 'mkmk' features..."
		else:
			print "\tGenerating 'mark' feature..."
		WriteFeaturesMarkFDK.MarkDataClass(ufoInstance, faceFolder, options.trimCasingTags, options.genMkmkFeature, options.writeClassesFile, options.indianScriptsFormat)
	
	
	# Decompose and remove overlaps (using checkoutlines)
	if options.flatten:
		print '\tFlattening the glyphs...'
		if os.name == "nt":
			coTool = 'checkoutlines.cmd'
		else:
			coTool = 'checkoutlines'
		cmd = '%s -e "%s"' % (coTool, ufoPath)
		popen = Popen(cmd, shell=True, stdout=PIPE)
		popenout, popenerr = popen.communicate()
		if options.verboseMode:
			if popenout:
				print popenout
		if popenerr:
			print popenerr
	
	# Autohint
	if options.autohint:
		print '\tHinting the font...'
		cmd = 'autohint -q "%s"' % ufoPath
		popen = Popen(cmd, shell=True, stdout=PIPE)
		popenout, popenerr = popen.communicate()
		if options.verboseMode:
			if popenout:
				print popenout
		if popenerr:
			print popenerr
	

class Options:
	def __init__(self):
		self.verboseMode = False
		self.genKernFeature = False
		self.genMarkFeature = False
		self.genMkmkFeature = False
		self.writeClassesFile = False
		self.indianScriptsFormat = False
		self.noUFOs = False
		self.minKern = 3
		self.writeTrimmed = False
		self.writeSubtables = False
		self.trimCasingTags = False
		self.autohint = False
		self.flatten = False
		

def getOptions(baseFolderPath):
	options = Options()
	options.inputPath = baseFolderPath
	i = 1
	numOptions = len(sys.argv)

	while i < numOptions:
		arg = sys.argv[i]

		if arg == "-h":
			print __help__
			raise
		elif arg == "-u":
			print __usage__
			raise
		elif arg == "-d":
			print __doc__
			raise
		elif arg == "-v":
			options.verboseMode = True
		elif arg == "-o":
			i += 1
			try:
				outputPath = sys.argv[i]
			except IndexError:
				print >> sys.stderr, "OPTION ERROR: It looks like the output folder was not specified."
				raise
			if outputPath[0] == "-":
				print >> sys.stderr, "OPTION ERROR: It looks like the output folder was not specified."
				raise
			options.outputPath = outputPath
		elif arg == "-min":
			i += 1
			try:
				minimum = sys.argv[i]
			except IndexError:
				print >> sys.stderr, "OPTION ERROR: It looks like the minimum value was not specified."
				raise
			if minimum[0] == "-":
				print >> sys.stderr, "OPTION ERROR: It looks like the minimum value was not specified."
				raise
			try:
				options.minKern = int(minimum)
			except:
				print >> sys.stderr, "OPTION ERROR: It looks like the minimum value is not an integer."
				raise
		elif arg == "-kern":
			options.genKernFeature = True
		elif arg == "-mark":
			options.genMarkFeature = True
		elif arg == "-nufo":
			options.noUFOs = True
		elif arg == "-wtr":
			options.writeTrimmed = True
		elif arg == "-wsb":
			options.writeSubtables = True
		elif arg == "-mkmk":
			options.genMkmkFeature = True
		elif arg == "-clas":
			options.writeClassesFile = True
		elif arg == "-indi":
			options.indianScriptsFormat = True
		elif arg == "-trtg":
			options.trimCasingTags = True
		elif arg == "-hint":
			options.autohint = True
		elif arg == "-flat":
			options.flatten = True
		elif arg[0] == "-":
			print >> sys.stderr, "OPTION ERROR: Unknown option <%s>." %  arg
			raise
		i  += 1

	# To do the 'mkmk' feature, the 'mark' feature must be done as well, therefore enable it
	if options.genMkmkFeature and not options.genMarkFeature:
		options.genMarkFeature = True

	return options


def getFontPaths(path):
	fontsList = []
	instancesFile = None
	for file in os.listdir(path):
		if file[-4:].lower() in [".ufo"]:
			fontsList.append(os.path.join(path, file))
		elif file[-len(kInstancesDataFileName):] == kInstancesDataFileName:
			instancesFile = os.path.join(path, file)
	return fontsList, instancesFile


def run():
	# if an input path is provided
	if len(sys.argv[1:]) and sys.argv[1][0] != '-': # skip if it looks like an option
		baseFolderPath = sys.argv[1]

		if baseFolderPath[-1] == '/':  # remove last slash if present
			baseFolderPath = baseFolderPath[:-1]

		# make sure the path is valid
		if not os.path.isdir(baseFolderPath):
			print >> sys.stderr, "ERROR: Invalid input folder\n\t%s" % baseFolderPath
			return

	# if an input path is not provided, use the current directory
	else:
		baseFolderPath = os.getcwd()

	# Load the options
	try:
		options = getOptions(baseFolderPath)
	except:
		return
	
	# Get paths to fonts and instances file
	fontPathsList, instancesFilePath = getFontPaths(baseFolderPath)
	
	if not len(fontPathsList):
		print >> sys.stderr, "ERROR: No UFO fonts were found in the path below\n\t%s" % baseFolderPath
		return

	# Handle the instances file
	if not instancesFilePath:
		print >> sys.stderr, "ERROR: Could not find the file named '%s' in the path below\n\t%s" % (kInstancesDataFileName, baseFolderPath)
		return
	print "Parsing %s file..." % kInstancesDataFileName
	try:
		instancesList = readInstanceFile(instancesFilePath)
	except:
		print >> sys.stderr, "ERROR: Error parsing file or file is empty."
		return

	# Check the UFO file names
	mainIndexes = []
	for ufoPath in fontPathsList:
		fileNameNoExtension, fileExtension = os.path.splitext(ufoPath)
		mainNumber = fileNameNoExtension.split('_')[-1]
		
		if mainNumber.isdigit():
			mainIndexes.append(int(mainNumber))
	if mainIndexes != range(len(fontPathsList)):
		print >> sys.stderr, "ERROR: The UFO main files are not named properly"
		return
	
	# Check the number of UFOs against the number of axes in the instances file
	axisNum = int(math.log(len(mainIndexes), 2))
	for i in range(len(instancesList)):
		instanceDict = instancesList[i]
		axisVal = instanceDict[kCoordsKey] # Get AxisValues strings
		if axisNum != len(axisVal):
			print 'ERROR:  The %s value for the instance named %s in the %s file is not compatible with the number of axis in the MM source font.' % (kCoordsKey, instanceDict[kFontName], kInstancesDataFileName)
			return

	# Get the path to the output folder
	try:
		outputDirPath = options.outputPath
		if not os.path.isdir(outputDirPath):
			print >> sys.stderr, "ERROR: Invalid output folder\n\t%s" % outputDirPath
			return
	except AttributeError: # use the current folder to output the instances
		outputDirPath = baseFolderPath

	t1 = time.time()

	print "Reading %d UFO files..." % len(fontPathsList)
	ufoMains = [OpenFont(ufoPath) for ufoPath in fontPathsList]	

	totalInstances = len(instancesList)
	print "Generating %d instances..." % totalInstances
	for i in range(totalInstances):
		makeInstance((i+1, totalInstances), ufoMains, instancesList[i], outputDirPath, options)

	t2 = time.time()
	elapsedSeconds = t2-t1
	
	if (elapsedSeconds/60) < 1:
		print 'Completed in %.1f seconds.' % elapsedSeconds
	else:
		print 'Completed in %.1f minutes.' % (elapsedSeconds/60)


if __name__ == "__main__":
	run()
