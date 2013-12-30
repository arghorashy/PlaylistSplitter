import re
import numpy as np

# Paramaters to be set
path_of_listing = "inputs/listing.txt"
path_of_playlist = "inputs/playlist.mp3"
path_of_mpg123 = "lib/mpg123/Win64/mpg123.exe"

# Other parameters
path_of_wav = "tmp/out.wav"

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
convert_mp3_to_wav(path_of_playlist, path_of_wav, path_of_mpg123)

# 
ampprofile = get_amp_profile(path_of_wav, 1)

#
silences = get_silences(ampprofile, 1)

#
silences = sorted(silences, key=attrgetter('score'), reverse=True)

#
for i in range(track_num):
	print(silences[i]['time'])
	print("\n")





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
	fr = wr.getframerate() 	# sampling frequency
	fn = wr.getnframes() 	# get number of frames

	while True:

		stepsize = fr
		if tell() + stepsize > fn:
			stepsize = fn - tell() - 1

		if stepsize <= 0:
			break

		da = np.fromstring(wr.readframes(stepsize), dtype=np.int16)
		left, right = da[0::2], da[1::2]

		ampprofile.append((np.mean(left) + np.mean(right))/2)

	wr.close()
	return ampprofile

def get_silences(ampprofile, sample_period):
	minamp = np.minimum(ampprofile)
	meanamp = np.mean(ampprofile)
	stdamp = np.std(ampp)

	threshold = meanamp - stdamp * 2

	silences = []

	in_silence = False
	start_of_curr_silence = 0  
	for i,amp in enumerate(ampprofile):

		if not in_silence:
			if amp < threshold:
				in_silence = True
				start_of_curr_silence = i

		if in_silence:
			if amp > theshold:
				in_silence = False

				score = 0
				for j in range(start_of_curr_silence,i):
					score += meanamp - ampprofile[j]
				score *= (i-start_of_curr_silence)

				time = start_of_curr_silence * sample_period

				silence = {}
				silence['time'] = time
				silence['duration'] = i-start_of_curr_silence
				silence['score'] = score

				silences.append(silence)

	return silences
