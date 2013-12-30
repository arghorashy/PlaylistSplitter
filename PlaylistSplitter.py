import re
import numpy as np
import os
import operator


# Paramaters to be set
path_of_listing = "inputs/listing.txt"
path_of_playlist = "inputs/playlist.mp3"
path_of_mpg123 = "lib/mpg123/Win64/mpg123.exe"

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

				score = 0
				for j in range(start_of_curr_silence,i):
					score += meanamp - ampprofile[j]
				score *= (i-start_of_curr_silence) * 3

				time = start_of_curr_silence * sample_period

				silence = {}
				silence['time'] = time
				silence['duration'] = i-start_of_curr_silence
				silence['score'] = score

				silences.append(silence)

	return silences
























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
ampprofile = get_amp_profile(path_of_wav, 0.5)

#
silences = get_silences(ampprofile, 0.5)

#
silences = sorted(silences, key=operator.itemgetter('score'), reverse=True)

#
times = []
for i in range(track_num):
	times.append(silences[i]['time'])

times = sorted(times)

for time in times:
	minutes = time / 60
	seconds = time % 60
	print(str(int(minutes)) + ":" + str(int(seconds)))




