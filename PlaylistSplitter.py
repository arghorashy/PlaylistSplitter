import re
import numpy as np
import os
import operator


# Paramaters to be set
path_of_listing = "inputs/listing.txt"
path_of_playlist = "inputs/playlist.mp3"
path_of_mpg123 = "lib/mpg123/Win64/mpg123.exe"
sampling_period = 0.5

# Other parameters
if not os.path.exists('tmp'):
        os.makedirs('tmp')
path_of_wav = "tmp/out.wav"



def convert_mp3_to_wav(mp3path, wavpath, mpg123path):
	import subprocess
	import sys

	try:
	    subprocess.check_call([mpg123path, '-w', wavpath, mp3path])
	except CalledProcessError as e:
	    print(e)
	    sys.exit(1)

# sample_period: what sized piece (in seconds) should the song be divided into?
def get_amp_profile(wavpath, sample_period):
	import wave

	ampprofile = []

	wr = wave.open(wavpath, 'r')
	fr = int(wr.getframerate() * sample_period)	# sampling frequency
	fn = wr.getnframes() 	# get number of frames

	while True:

		stepsize = fr
		if wr.tell() + stepsize > fn:
			stepsize = fn - wr.tell() - 1

		if stepsize <= 0:
			break

		da = np.fromstring(wr.readframes(stepsize), dtype=np.int16)
		left, right = da[0::2], da[1::2]

		ampprofile.append((np.mean(left) + np.mean(right))/2)

	wr.close()
	return ampprofile

def get_silences(ampprofile, sample_period):
	minamp = np.min(ampprofile)
	meanamp = np.mean(ampprofile)
	stdamp = np.std(ampprofile)

	threshold = meanamp - stdamp * 2.5

	silences = []

	in_silence = False
	start_of_curr_silence = 0  
	for i,amp in enumerate(ampprofile):

		if not in_silence:
			if amp < threshold:
				in_silence = True
				start_of_curr_silence = i

		if in_silence:
			if amp > threshold:
				in_silence = False
				duration = i-start_of_curr_silence
				if duration > 0:
					score = 0
					for j in range(start_of_curr_silence,i):
						score += threshold - ampprofile[j]
					score *= (duration) * 3

					time = start_of_curr_silence * sample_period

					silence = {}
					silence['time'] = time
					silence['duration'] = duration
					silence['score'] = score

					silences.append(silence)

	return silences

def secondsToTime(seconds):
	minutes = int(seconds / 60)
	seconds = seconds % 60

	if seconds < 10:
		seconds = str(0) + str(seconds)
	else:
		seconds = str(seconds)

	minutes = str(minutes)

	return minutes + ":" + seconds





# Get list of track names
with open(path_of_listing) as f:
    listing_contents = f.readlines()

for line in listing_contents:
	line = re.sub(r"[0-9]{1,2}:[0-9]{2}[\s]*", "", line)
	line = re.sub(r"\n", "", line)

# Get number of tracks
track_num = len(listing_contents)
print(track_num)

# Convert mp3 file to wav
#convert_mp3_to_wav(path_of_playlist, path_of_wav, path_of_mpg123)

# 
ampprofile = get_amp_profile(path_of_wav, sampling_period)

#
silences = get_silences(ampprofile, sampling_period)

#
silences = sorted(silences, key=operator.itemgetter('score'), reverse=True)

##############################
#
#       Diagnostics
#
##############################
if not os.path.exists('diag'):
        os.makedirs('diag')
path_of_wav = "tmp/out.wav"


# Show best times only
f = open('diag/besttimes.csv', 'w')
f.write("time, score, duration\n")

best_silences = []
for i in range(track_num):
	best_silences.append(silences[i])

best_silences = sorted(best_silences, key=operator.itemgetter('time'), reverse=False)

for silence in best_silences:
	f.write(secondsToTime(silence['time']) + "," + str(silence['score'])+ "," + str(silence['duration']) + "\n")

f.close()


# Show amp profile
f = open('diag/ampprofile.csv', 'w')
f.write('amplitude, time' + "\n")

for i,amp in enumerate(ampprofile):
	f.write(str(amp) + "," + secondsToTime(i*sampling_period) + "\n")

f.close

# Show all detected pauses
f = open('diag/all_silences.csv', 'w')
f.write("time, score, duration" + "\n")

for silence in silences:
	f.write(secondsToTime(silence['time']) + "," + str(silence['score'])+ "," + str(silence['duration']) + "\n")

f.close()


