
# Silences merely contains an array of hashes.  Each hash contains the information 
# pertaining to a single silence that was found.  

class Silences(object):

	def __init__(self):
		self.silences = []

	# Everytime a silence is found, this function is called.  It determines whether
	# the newest sileence is the same as a previously found silence and takes care
	# of the book-keeping in either case.
	def addSilence(self, time, duration, score):
		for silence in self.silences:
			num = silence['instances']
			if abs(silence['time'] - time) < duration + silence['duration'] + 15:
				silence['score'] += score
				silence['time'] = (time + silence['time'] * num)/(num+1.0)
				silence['duration'] = (duration + silence['duration'] * num)/(num+1.0)
				silence['instances'] += 1
				return


		newSilence = {}
		newSilence['time'] = time
		newSilence['duration'] = duration
		newSilence['score'] = score
		newSilence['instances'] = 1
		self.silences.append(newSilence)