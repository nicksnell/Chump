"""A Finite State Machine (FSM)."""

__all__ = ('FSM', 'FSMTransitionError')


class FSMTransitionError(Exception):
	"""Exception raised by the FSM on failed transition."""
	pass

class FSM(object):
	"""Finite State Machine."""
	
	def __init__(self, initial_state=None, data=None):
		self._state_transitions = {}
		self._state_transitions_any = {}
		self._default_transition = None
		self._current_state = initial_state
		self._initial_state = initial_state
		self.data = data
	
	def add_transition(self, action, state, next_state=None, callback=None):
		"""Add a transition for a single action"""
		if next_state is None:
			next_state = state
		self._state_transitions[(action, state)] = (callback, next_state)
	
	def add_transitions(self, actions, state, next_state=None, callback=None):
		"""Add a transition for multiple actions"""
		if next_state is None:
			next_state = state
		for action in actions:
			self.add_transition(action, state, next_state, callback)
	
	def add_transition_any(self, state, next_state=None, callback=None):
		"""Set a default transition for a state"""
		if next_state is None:
			next_state = state
		self._state_transitions_any[state] = (callback, next_state)
	
	def set_default_transition(self, state, callback=None):
		"""Set a default transition for the FSM"""
		self._default_transition = (callback, state)
	
	def get_transition(self, action, state):
		"""Get the transition for the specified action and state"""
		if (action, state) in self._state_transitions:
			return self._state_transitions[(action, state)]
		
		elif state in self._state_transitions_any:
			return self._state_transitions_any[state]
		
		elif self._default_transition:
			return self._default_transition
		
		raise FSMTransitionError(u'Undefined tranisition (%s, %s)' % (action, state))
	
	def set_initial_state(self, state):
		"""Set the initial state of the FSM"""
		self._initial_state = state
		if self._current_state is None:
			self.reset()
	
	def get_current_state(self):
		"""Return the current state of the FSM"""
		return self._current_state
	
	def reset(self):
		"""Reset the FSM"""
		self._current_state = self._initial_state
	
	def process(self, action):
		"""Process an action"""
		result = self.get_transition(action, self._current_state)
		if result[0] is not None:
			result[0](self, self.data, action)
		self._current_state = result[1]