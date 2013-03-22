"""A utility HTML parser for finding and replacing specific content without 
the need for a document tree"""

# Chump - by Snailwhale LLP
# All code copyright (c) 2010-2012, Snailwhale LLP. All rights reserved.

import re
import hashlib

from chump.fsm import FSM, FSMTransitionError

__version__ = '0.1'
__all__ = ('Region', 'RegionParser', 'RegionParsingError')

# Parsing states
CHAR_OR_TAG_OR_COMMENT = 1;
OPENNING_OR_CLOSING_TAG = 2;
OPENING_TAG = 3;
CLOSING_TAG = 4;
TAG_NAME_OPENING = 5;
TAG_NAME_CLOSING = 6;
TAG_OPENING_SHORT_TAG = 7;
TAG_NAME_MUST_CLOSE = 8;
ATTR_OR_TAG_END = 9;
ATTR_NAME = 10;
ATTR_NAME_MUST_GET_VALUE = 11;
ATTR_DELIM = 12;
ATTR_VALUE_SINGLE_DELIM = 13;
ATTR_VALUE_DOUBLE_DELIM = 14;
ATTR_VALUE_NO_DELIM = 15;
ATTR_ENTITY_NO_DELIM = 16;
ATTR_ENTITY_SINGLE_DELIM = 17;
ATTR_ENTITY_DOUBLE_DELIM = 18;
TAG_OR_COMMENT = 19;
OPENING_COMMENT_BANG = 20;
OPENING_COMMENT_DASH_ONE = 21;
OPENING_COMMENT_DASH_TWO = 22;
INNER_COMMENT = 23;
CLOSING_COMMENT_DASH_ONE = 24;
CLOSING_COMMENT_DASH_TWO = 25;

# Character transitions
ALPHA_CHARS = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz$'
ALPHA_NUMERIC_CHARS = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890_-:'

# Supported short tags
SHORT_TAGS = ['meta', 'link', 'br', 'hr', 'input', 'img']

class RegionParsingError(Exception):
	"""Exception raised by parser if error parsing HTML."""
	pass

class RegionParser(object):
	"""An editable region parser."""
	
	def __init__(self, tags=['div'], classes=[], attributes=[], strict_id=True):
		"""Setup the Parser"""
		
		self.regions = {}
		
		self._region = None
		self._region_tags = tags
		self._region_classes = classes
		self._region_attributes = attributes
		self._region_strict_id = strict_id
		
		self._tag_stack = []
		self._tag_start = 0
		self._tag_name = ''
		self._tag_is_short = False
		self._attribs = {}
		self._attrib_name = ''
		self._attrib_value = ''
		self._buffer = ''
		self._skip_buffer = False
		self._fsm = FSM(CHAR_OR_TAG_OR_COMMENT, self)
		self._head = 0
		self._line_no = 1
		self._column_no = 1
		
		self._build_fsm()
	
	def __str__(self):
		return str(self.__unicode__())
	
	def __unicode__(self):
		# Regions must be in reverse order for replace to ne safe
		regions = self.regions.values()
		regions = sorted(regions, key=lambda region: region.start)
		regions.reverse()
		
		html = self._html
		
		for region in regions:
			head = html[:region.start]
			tail = html[region.end:]
			html = head + unicode(region) + tail
			
		return html
	
	def __iter__(self):
		for key, region in self.regions.items():
			yield region
	
	def parse(self, html):
		"""Parse the html contents"""
		
		self._html = html
		self._parse()
	
	def _build_fsm(self):
	
		def _reset(fsm, parser, c):
			
			# This rule was introduced to allow the contents of script tags 
			# to be ignored by the parser.
			if len(parser._tag_stack) and parser._tag_stack[-1].lower() == 'script':
				return
			
			parser._region = None
			parser._tag_stack = []
			parser._tag_start = 0
			parser._tag_end = 0
			parser._tag_name = ''
			parser._tag_is_short = False
			parser._attribs = {}
			parser._attrib_name = ''
			parser._attrib_value = ''
			parser._buffer = ''
			
		def _head_back(fsm, parser, c):
			parser._skip_buffer = True
			parser._head -= 1
	
		def _tag_start(fsm, parser, c):
			parser._tag_start = parser._head - 1
			_head_back(fsm, parser, c)
			
		def _tag_name(fsm, parser, c):
			parser._tag_name += c
			
		def _tag_is_short(fsm, parser, c):
			parser._tag_is_short = True
			
		def _push_tag(fsm, parser, c):
			# Are we interested in the tag? Only if it's a region or we are
			# parsing inside a region
			tag_name = parser._tag_name.lower()
			attribs = parser._attribs
			
			if tag_name in SHORT_TAGS:
				parser._tag_is_short = True
				parser._tag_name = ''
			
			if parser._region is not None:
				# Inside a region so stack it
				parser._tag_stack.append(tag_name)
				
				if parser._tag_is_short:
					_pop_tag(fsm, parser, c);
					
			elif tag_name in parser._region_tags:
				
				# Check for classes?
				if parser._region_classes:
					classes = attribs.get('class', '').split(' ')
					
					if not len([c for c in classes if c in parser._region_classes]) == 1:
						parser._tag_name = ''
						return
				
				# Check for attributes?
				if parser._region_attributes:
					# NOTE: this checks for attributes existence NOT it's value
					if not [a for a in parser._region_attributes if a in attribs]:
						parser._tag_name = ''
						return
		
				# Check for a valid ID
				id = attribs.get('id', None)
					
				# If there isn't an ID and we are in strict mode we must stop processing here
				if id is None and parser._region_strict_id:
					raise RegionParsingError('Region must have a unique ID! (%s)' % tag_name)
					
				elif id is None:
					# If the id is none and we are not in strict mode - has an id 
					# from its tag and position
					id = hashlib.md5('%s-%s' % (tag_name, parser.line_no)).hexdigest()
					
				else:
					# Remove the ID from attributes as it's assigned it's own property
					del attribs['id']
				
				# Check if id already exists in map
				if id in parser.regions:
					raise RegionParsingError('Region ID must be unique! %s - %s' % (tag_name, id))
						
				# Create a region
				parser._region = Region(id, tag_name, attribs, start=parser._tag_start)
						
				# Stack the tag
				parser._tag_stack.append(tag_name)
				
				parser._buffer = ''
				
			parser._tag_name = ''
			parser._tag_is_short = False
			parser._attribs = {}
		
		def _pop_tag(fsm, parser, c):
			
			# Don't push tags if not in a region
			if parser._region is None:
				parser._tag_name = ''
				return

			if len(parser._tag_stack) == 1:
				# Complete the region
				parser._region.content = parser._buffer.rsplit('<', 1)[0]
				parser._region.end = parser._head + 1
				parser.regions[parser._region.id] = parser._region
			
				parser._region = None
				parser._buffer = ''
			
			parser._tag_stack = parser._tag_stack[:-1]
			parser._tag_name = ''
	
		def _attrib_name(fsm, parser, c):
			parser._attrib_name += c
		
		def _attrib_value(fsm, parser, c):
			parser._attrib_value += c
	
		def _store_attrib(fsm, parser, c):
			parser._attribs[parser._attrib_name] = parser._attrib_value
			parser._attrib_name = ''
			parser._attrib_value = ''
			
		def _short_attrib(fsm, parser, c):
			parser._skip_buffer = True
			parser._head -= 1
			parser._attribs[parser._attrib_name] = parser._attrib_name
			parser._attrib_name = ''
			parser._attrib_value = ''
			
		def _skip_to_gt(fsm, parser, c):
			# This is an optimization meassure, since we know we're only 
			# interested in tags we can skip what's in between.
			try:
				next_gt = parser._html.index('<', parser._head)
				if next_gt > -1:
					parser._buffer += parser._html[parser._head + 1:next_gt]
					parser._head = next_gt - 1
				
			except ValueError, e:
				pass
			
		# Reset if something goes wrong
		self._fsm.set_default_transition(CHAR_OR_TAG_OR_COMMENT, _reset)
		
		# Character, tag, or comment
		self._fsm.add_transition_any(CHAR_OR_TAG_OR_COMMENT, callback=_skip_to_gt)
		self._fsm.add_transition('<', CHAR_OR_TAG_OR_COMMENT, TAG_OR_COMMENT)
		self._fsm.add_transitions(' \t\n', TAG_OR_COMMENT)
		
		# Opening or closing tag
		self._fsm.add_transitions(ALPHA_CHARS + '/', TAG_OR_COMMENT, OPENNING_OR_CLOSING_TAG, _head_back)
		self._fsm.add_transitions(ALPHA_CHARS, OPENNING_OR_CLOSING_TAG, OPENING_TAG, _tag_start)
		self._fsm.add_transition('/', OPENNING_OR_CLOSING_TAG, CLOSING_TAG)
		
		# Opening tag
		self._fsm.add_transitions(' \t\n', OPENING_TAG)
		self._fsm.add_transitions(ALPHA_CHARS, OPENING_TAG, TAG_NAME_OPENING, _head_back)
		
		# Closing tag
		self._fsm.add_transitions(' \t\n', CLOSING_TAG);
		self._fsm.add_transitions(ALPHA_CHARS, CLOSING_TAG, TAG_NAME_CLOSING, _head_back);
		
		# Tag name opening
		self._fsm.add_transitions(ALPHA_NUMERIC_CHARS, TAG_NAME_OPENING, callback=_tag_name)
		self._fsm.add_transitions(' \t\n', TAG_NAME_OPENING, ATTR_OR_TAG_END)
		self._fsm.add_transition('/', TAG_NAME_OPENING, TAG_OPENING_SHORT_TAG, _tag_is_short)
		self._fsm.add_transition('>', TAG_NAME_OPENING, CHAR_OR_TAG_OR_COMMENT, _push_tag)
		self._fsm.add_transitions(' \t\n', TAG_OPENING_SHORT_TAG);
		self._fsm.add_transition('>', TAG_OPENING_SHORT_TAG, CHAR_OR_TAG_OR_COMMENT, _push_tag)
		self._fsm.add_transitions(' \t\n', ATTR_OR_TAG_END);
		self._fsm.add_transition('/', ATTR_OR_TAG_END, TAG_OPENING_SHORT_TAG, _tag_is_short)
		self._fsm.add_transition('>', ATTR_OR_TAG_END, CHAR_OR_TAG_OR_COMMENT, _push_tag)
		self._fsm.add_transitions(ALPHA_CHARS, ATTR_OR_TAG_END, ATTR_NAME, _head_back)
		
		# Tag name closing
		self._fsm.add_transitions(ALPHA_NUMERIC_CHARS, TAG_NAME_CLOSING, callback=_tag_name)
		self._fsm.add_transitions(' \t\n', TAG_NAME_CLOSING, TAG_NAME_MUST_CLOSE)
		self._fsm.add_transition('>', TAG_NAME_CLOSING, CHAR_OR_TAG_OR_COMMENT, _pop_tag)
		self._fsm.add_transitions(' \n', TAG_NAME_MUST_CLOSE)
		self._fsm.add_transition('>', TAG_NAME_MUST_CLOSE, CHAR_OR_TAG_OR_COMMENT, _pop_tag)		
		
		# Attribute name
		self._fsm.add_transitions(ALPHA_NUMERIC_CHARS, ATTR_NAME, callback=_attrib_name)
		self._fsm.add_transitions(' \t\n', ATTR_NAME, ATTR_NAME_MUST_GET_VALUE)
		self._fsm.add_transition('=', ATTR_NAME, ATTR_DELIM)
		self._fsm.add_transitions(' \t\n', ATTR_NAME_MUST_GET_VALUE)
		self._fsm.add_transition('=', ATTR_NAME_MUST_GET_VALUE, ATTR_DELIM)
		self._fsm.add_transition_any(ATTR_NAME, ATTR_OR_TAG_END, _short_attrib)
		self._fsm.add_transition_any(ATTR_NAME_MUST_GET_VALUE, ATTR_OR_TAG_END, _short_attrib)
		
		# Attribute delimiter
		self._fsm.add_transitions(' \t\n', ATTR_DELIM)
		self._fsm.add_transition('\'', ATTR_DELIM, ATTR_VALUE_SINGLE_DELIM)
		self._fsm.add_transition('"', ATTR_DELIM, ATTR_VALUE_DOUBLE_DELIM)
		
		# Attribute value (single delimiter)
		self._fsm.add_transition('\'', ATTR_VALUE_SINGLE_DELIM, ATTR_OR_TAG_END, _store_attrib)
		self._fsm.add_transition_any(ATTR_VALUE_SINGLE_DELIM, callback=_attrib_value)
		
		# Attribute value (single delimiter)
		self._fsm.add_transition('"', ATTR_VALUE_DOUBLE_DELIM, ATTR_OR_TAG_END, _store_attrib)
		self._fsm.add_transition_any(ATTR_VALUE_DOUBLE_DELIM, callback=_attrib_value)
		
		# Opening or closing comment
		self._fsm.add_transitions('!', TAG_OR_COMMENT, OPENING_COMMENT_BANG)
		self._fsm.add_transitions('-', OPENING_COMMENT_BANG, OPENING_COMMENT_DASH_ONE)
		self._fsm.add_transitions('-', OPENING_COMMENT_DASH_ONE, OPENING_COMMENT_DASH_TWO)
		self._fsm.add_transition_any(OPENING_COMMENT_DASH_TWO, INNER_COMMENT)
		
		self._fsm.add_transition('-', INNER_COMMENT, CLOSING_COMMENT_DASH_ONE)
		self._fsm.add_transition_any(INNER_COMMENT)
		
		self._fsm.add_transition('-', CLOSING_COMMENT_DASH_ONE, CLOSING_COMMENT_DASH_TWO)
		self._fsm.add_transition_any(CLOSING_COMMENT_DASH_ONE, INNER_COMMENT)
		
		self._fsm.add_transition('>', CLOSING_COMMENT_DASH_TWO, CHAR_OR_TAG_OR_COMMENT)
		self._fsm.add_transition_any(CLOSING_COMMENT_DASH_TWO, INNER_COMMENT)
		
	def _parse(self):
		# Normalize the line endings
		self._html = self._html.replace('\r\n', '\n').replace('\r', '\n')
		
		# Parse the html
		fsm = self._fsm
		html = self._html
		
		while self._head < len(self._html):
			c = html[self._head]
			
			if self._region is not None and not self._skip_buffer:
				self._buffer += c
			
			self._skip_buffer = False
			
			try:
				fsm.process(c)
			except FSMTransitionError, e:
				raise RegionParsingError(u'[%s, %s] >>> %s' % (
					self.line_no, 
					self.column_no, 
					e
				))
				
			self._head += 1
			self._column_no += 1
			
			if c == '\n':
				self._column_no = 1
				self._line_no += 1
		
	@property
	def line_no(self):
		return self._line_no
		
	@property
	def column_no(self):
		return self._line_no

class Region(object):
	"""An editable region."""
	
	def __init__(self, id, tag, attribs, content='', start=0, end=0):
		self._id = id
		self.start = start
		self.end = end
		self.tag = tag
		self.attribs = attribs
		self.content = content
	
	def __str__(self):
		return str(self.__unicode__())
	
	def __unicode__(self):
		return u'<%(tag)s id="%(id)s" %(attribs)s>%(content)s</%(tag)s>' % {
			'tag': self.tag,
			'id': self.id,
			'attribs': ' '.join(['%s="%s"' % (name, self.attribs[name]) for name in self.attribs]),
			'content': self.content,
		}
	
	def prepend_content(self, prepend_content):
		self._content = prepend_content + self._content
	
	def append_content(self, append_content):
		self._content += append_content
	
	def get_content(self):
		return self._content
	
	def set_content(self, content):
		self._content = content
	
	content = property(get_content, set_content)
	
	@property
	def id(self):
		return self._id
