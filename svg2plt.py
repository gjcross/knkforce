import xml.dom.minidom
import re
from svg.path import parse_path

class SVG2PLT:
		
	# the plt code to output
	plt = ''
	
	delimiter = 'z'		# path delimiter (mM -> zZ)
	unit = 0.01			# a unit value for the number of pixels per inch

	# factors to transform the SVG as it is read
	scale = 1.0
	x_offset = 0.0
	y_offset = 0.0
	
	divisions = 30.0 	# the number of point divisions on an element
	overcut = 0.2		# how much to overcut the next shape (TODO: units for now as percentage. could be a percentage of the line, could be mm?)
	
	# SVG properties that may be useful
	min_x = 100000
	min_y = 100000
	max_x = 0
	max_y = 0
	width = 0
	height = 0	
	
	def start(self):
		self.plt += 'ST0;\n'
		self.plt += "U"+str(int(self.x_offset))+","+str(int(self.y_offset))+";\n"
		self.plt += 'LED255,64,0;\n'
	
	def end(self):
		self.plt += 'ST0;\n'
		self.plt += "U"+str(int(self.x_offset))+","+str(int(self.y_offset))+";\n"
		self.plt += 'LED128,128,128;\n'
		
	# open a file with name 'filename', extract the path elements, and convert them to PLT code
	def parse_file(self, filename):
		self.start()
		#read the svg doc as a DOM to extract the XML <path> element
		doc = xml.dom.minidom.parse(filename)
		
		svg = doc.getElementsByTagName('svg')[0]
		height = svg.getAttribute('height').replace("in", "")
		width = svg.getAttribute('width').replace("in", "")
		#viewbox = svg.getAttribute('viewBox')
		
		self.unit = (float(height)/212.962 + float(width)/178.819)/2
		
		path_strings = [path.getAttribute('d') for path in doc.getElementsByTagName('path')]
		
		# iterate over each path that is found
		for path_string in path_strings:
			# break up each path shape into the individual lines (mM -> zZ)
			lines = re.split('z|Z', path_string)

			for line in lines:
				if(len(line)>2):
					line += self.delimiter
				path = parse_path(line)		# convert the string to a path using svg.path library
				
				self.parse_path(path)		# parse the path from SVG to PLT
				
				# add overcut to the item
				if(self.overcut and path.closed==True):
					self.plt += self.parse_overcut(path)

		self.end()

	# parse a path (mM -> zZ)
	def parse_path(self, path):
		first = True
		for item in path:
			self.plt += self.parse_item(item, first)
			if(first):
				first = False;
	
	def parse_overcut(self, path):
		item = path[0]
		
		output = ''
		for i in range(0, int(self.divisions*self.overcut)):
			loc = i/self.divisions
			point = item.point(loc)
			output += self.command('D', point.real, point.imag)

		return output

	
	def parse_item(self, item, first):
		output = ''
		
		for i in range(0, int(self.divisions)):
			loc = i/self.divisions
			point = item.point(loc)
			
			if(first and i==0):
				output += self.command('U', point.real, point.imag)
			
			output += self.command('D', point.real, point.imag)
			self.calc_properties(point.real, point.imag)
			
		return output
		
	def command(self, dir, x, y):
		output = dir + str(int(x*self.scale+self.x_offset)) +","+ str(int(y*self.scale+self.y_offset)) +";\n"
		return(output)
		
	def calc_properties(self, x, y):
		if(x<self.min_x):
			self.min_x = x
		if(x>self.max_x):
			self.max_x = x
			
		if(y<self.min_y):
			self.min_y = y
		if(y>self.max_y):
			self.max_y = y
			
		self.width = self.max_x - self.min_x
		self.height = self.max_y - self.min_y