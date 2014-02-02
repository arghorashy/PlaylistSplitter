import re
import numpy as np
import os
import operator

##############################
#
#    Parameters to be set by user
#
##############################


path_of_listing = "inputs/listing.txt"
path_of_playlist = "inputs/playlist.mp3"
#path_of_mpg123 = "lib/mpg123/Win64/mpg123.exe"
path_of_mpg123 = "mpg123"


##############################
#
#      Other crap
#
##############################

tmp_dir = "tmp"
diag_dir = "diag"
path_of_wav = tmp_dir + "/out.wav"

# Create directories that may not exist
if not os.path.exists(tmp_dir):
	os.makedirs(tmp_dir)

if not os.path.exists(diag_dir):
        os.makedirs(diag_dir)


##############################
#
#      Silences class
#
##############################

class Silences(object):

	def __init__(self):
		self.silences = []

	def addSilence(self, time, duration, score):
		for silence in self.silences:
			num = silence['instances']
			if abs(silence['time'] - time) < duration + silence['duration'] + 15:
				silence['score'] += score
				silence['time'] = (time + silence['time'] * num)/(num+1.0)
				silence['duration'] = (duration + silence['duration'] * num)/(num+1.0)
				silence['instances'] += 1
				break


		newSilence = {}
		newSilence['time'] = time
		newSilence['duration'] = duration
		newSilence['score'] = score
		newSilence['instances'] = 1
		self.silences.append(newSilence)



##############################
#
#      Functions
#
##############################


def convert_mp3_to_wav(mp3path, wavpath, mpg123path):
	import subprocess
	import sys

	try:
	    subprocess.check_call([mpg123path, '-w', wavpath, mp3path])
	except CalledProcessError as e:
	    print(e)
	    sys.exit(1)

# Returns a list of amplitudes: one amplitude per sample (~44000samples/s) 
def get_amp_profile(wavpath, sample_period):
	import wave

	ampprofile = []

	wr = wave.open(wavpath, 'r')
	sf = wr.getframerate()	# sampling frequency (should be something like 44000Hz)
	stepsize = int(sf * sample_period)
	fn = wr.getnframes() 	# get number of frames in total in file

	while True:

		if wr.tell() + stepsize > fn:  #
			stepsize = fn - wr.tell() - 1

		if stepsize <= 0:
			break

		da = np.fromstring(wr.readframes(stepsize), dtype=np.int16)
		left, right = da[0::2], da[1::2]

		ampprofile.append(np.mean(np.abs(left)) + np.mean(np.abs(right))/2)

	wr.close()
	return ampprofile


# Find and rate all silences
def get_silences(ampprofile, sample_period, std_factor, silences):
	minamp = np.min(ampprofile)
	meanamp = np.mean(ampprofile)
	stdamp = np.std(ampprofile)


	# amplitudes below this threshold are considered to be silent
	threshold = meanamp - stdamp * std_factor
	print("Threshold: " + str(threshold))


	in_silence = False			# Currently in a silence?
	start_of_curr_silence = 0  	# When current silence started
	for i,amp in enumerate(ampprofile):

		if not in_silence:
			if amp < threshold:		# beginning of silence
				in_silence = True
				start_of_curr_silence = i

		if in_silence:
			if amp > threshold:		# end of silence
				in_silence = False
				duration = (i-start_of_curr_silence) * sample_period
				if duration > 2:	# ignore super short silences
					score = 0
					for j in range(start_of_curr_silence,i):
						score += threshold - ampprofile[j]
					score *= (duration) * 1

					time = start_of_curr_silence * sample_period

					# Ignore silences within 10 seconds of the beginning or end of file
					if start_of_curr_silence * sample_period > 10 or i * sample_period < len(ampprofile) * sample_period  - 10:
						silences.addSilence(time, duration, score)


def secondsToTime(seconds):
	minutes = int(seconds / 60)
	seconds = seconds % 60

	if seconds < 10:
		seconds = str(0) + str(seconds)
	else:
		seconds = str(seconds)

	minutes = str(minutes)

	return minutes + ":" + seconds


##############################
#
#      Beginning of main script
#
##############################



# Get list of track names
with open(path_of_listing) as f:
    listing_contents = f.readlines()

for line in listing_contents:
	line = re.sub(r"[0-9]{1,2}:[0-9]{2}[\s-]*", "", line)
	line = re.sub(r"\n", "", line)

# Get number of tracks
track_num = len(listing_contents)
print(track_num)

# Convert mp3 file to wav
convert_mp3_to_wav(path_of_playlist, path_of_wav, path_of_mpg123)

silences = Silences()


for sampling_period in [0.4, 0.5, 0.6]: # map(lambda x: x/5.0, range(1, 11, 1)): #
	for std_factor in [1.6, 1.8, 2.0, 2.2, 2.4, 2.6]: #map(lambda x: x/5.0, range(5,13,1)): 

		# Get amplitude profile
		ampprofile = get_amp_profile(path_of_wav, sampling_period)

		# Get silences
		get_silences(ampprofile, sampling_period, std_factor, silences)

print ("Length: " + str(len(silences.silences)) + "\n")

# Sort silences by score
silences = sorted(silences.silences, key=operator.itemgetter('score'), reverse=True)

##############################
#
#       Diagnostics
#
##############################



# Diagnostic: Show best times only
f = open(diag_dir + '/besttimes.csv', 'w')
f.write("time, score, duration\n")

best_silences = []
for i in range(track_num - 1):  # -1 because we can assume the first song starts at 0:00
	best_silences.append(silences[i])

best_silences = sorted(best_silences, key=operator.itemgetter('time'), reverse=False)

for silence in best_silences:
	f.write(secondsToTime(silence['time']) + "," + str(silence['score'])+ "," + str(silence['duration']) + "\n")

f.close()


# Diagnostic: Show amp profile
f = open(diag_dir + '/ampprofile.csv', 'w')
f.write('amplitude, time' + "\n")

for i,amp in enumerate(ampprofile):
	f.write(str(amp) + "," + secondsToTime(i*sampling_period) + "\n")

f.close

# Diagnostic: Show all detected pauses
f = open(diag_dir + '/all_silences.csv', 'w')
f.write("time, score, duration" + "\n")

for silence in silences:
	f.write(secondsToTime(silence['time']) + "," + str(silence['score'])+ "," + str(silence['duration']) + "\n")

f.close()


