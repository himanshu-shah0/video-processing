import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy import VideoFileClip
from moviepy.video.fx import Crop

# from moviepy.tools import subprocess_call
# from moviepy.config import get_setting


# def ffmpeg_extract_subclip(filename, t1, t2, targetname=None):
#     """ Makes a new video file playing video file ``filename`` between
#     the times ``t1`` and ``t2``. """
#     name, ext = os.path.splitext(filename)
#     if not targetname:
#         T1, T2 = [int(1000*t) for t in [t1, t2]]
#         targetname = "%sSUB%d_%d.%s" % (name, T1, T2, ext)

#     cmd = [get_setting("FFMPEG_BINARY"),"-y",
#            "-ss", "%0.2f"%t1,
#            "-i", filename,
#            "-t", "%0.2f"%(t2-t1),
#            "-vcodec", "copy", "-acodec", "copy", targetname]

#     subprocess_call(cmd)
def read_timestamps(file_path):
    """Reads timestamps from a text file and returns a list of tuples."""
    print(f"📂 Reading timestamps from: {file_path}")

    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        timestamps = []
        for line in lines:
            if '-' in line:
                start, end = line.strip().split('-')
                timestamps.append((start.strip(), end.strip()))
            else:
                print(f"⚠ Skipping invalid line: {line.strip()}")

        print(f"✅ Timestamps read successfully: {timestamps}")
        return timestamps
    except Exception as e:
        print(f"❌ Error reading timestamps file: {e}")
        return []

def time_to_seconds(timestamp):
    """Converts a timestamp (MM:SS or HH:MM:SS) to total seconds."""
    print(f"⏱ Converting timestamp to seconds: {timestamp}")

    try:
        parts = list(map(int, timestamp.split(':')))
        if len(parts) == 2:  # Format: MM:SS
            minutes, seconds = parts
            return minutes * 60 + seconds
        elif len(parts) == 3:  # Format: HH:MM:SS
            hours, minutes, seconds = parts
            return hours * 3600 + minutes * 60 + seconds
    except Exception as e:
        print(f"❌ Error converting timestamp {timestamp}: {e}")
        return None

def extract_and_resize_clips(video_path, timestamps, output_folder):
    """Extracts video segments based on timestamps and resizes them to 1080x1920."""
    print(f"📹 Processing video: {video_path}")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📁 Created output directory: {output_folder}")

    for idx, (start, end) in enumerate(timestamps):
        print(f"🎬 Processing clip {idx + 1}: {start} to {end}")

        start_sec = time_to_seconds(start)
        end_sec = time_to_seconds(end)

        if start_sec is None or end_sec is None:
            print(f"⚠ Skipping invalid timestamps: {start} - {end}")
            continue

        temp_output_path = os.path.join(output_folder, f"temp_clip_{idx + 1}.mp4")

        try:
            print(f"🔪 Extracting subclip: {start_sec}s to {end_sec}s")
            ffmpeg_extract_subclip(video_path, start_sec, end_sec+4, temp_output_path)
            temp_file_size = os.path.getsize(temp_output_path)
            print(f"Temporary file size: {temp_file_size}")

            if temp_file_size == 0:
                print(f"❌ ERROR: Extracted temp clip is empty. FFmpeg extraction failed.")
                continue

            temp_clip_test = VideoFileClip(temp_output_path)
            if temp_clip_test.duration == 0:
                print(f"❌ ERROR: Extracted temp clip has 0 duration, extraction failed")
                temp_clip_test.close()
                os.remove(temp_output_path)
                continue
            temp_clip_test.close()

        except Exception as e:
            print(f"❌ Error extracting subclip: {e}")
            continue

        try:
            print(f"📏 Checking extracted clip {idx + 1}")
            clip = VideoFileClip(temp_output_path)
            fps = clip.fps

            if clip.duration == 0:
                print(f"⚠ Extracted clip {idx + 1} is empty! Skipping...")
                clip.close()
                os.remove(temp_output_path)
                continue

            clip = clip.resized(height=1920)
            cropper = Crop(width=1080, height=1920, x_center=clip.w / 2, y_center=clip.h / 2)
            clip = cropper.apply(clip)

            final_output_path = os.path.join(output_folder, f"clip_{idx + 1}.mp4")
            clip.write_videofile(final_output_path, codec="libx264", fps=fps, audio_codec="aac")
            print(f"✅ Saved clip {idx + 1} at {final_output_path}")

        except Exception as e:
            print(f"❌ Error saving clip {idx + 1}: {e}")
        finally:
            if 'clip' in locals():
                clip.close()

        try:
            os.remove(temp_output_path)
            print(f"🗑 Deleted temporary file: {temp_output_path}")
        except Exception as e:
            print(f"⚠ Error deleting temp file: {e}")

def get_video_duration(video_path):
    """Gets the duration of a video file in seconds."""
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        print(f"❌ Error getting video duration: {e}")
        return 0

def time_to_seconds_to_timestamp(seconds):
    """Converts seconds to a timestamp string (MM:SS)."""
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"

if __name__ == "__main__":
    video_path = "input_files/sample_video.mp4"  # Replace with your video path
    timestamps_file = "input_files/timestamps.txt" # Replace with your timestamps file path
    output_folder = "output_videos"

    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
    elif not os.path.exists(timestamps_file):
        print(f"❌ Timestamps file not found: {timestamps_file}")
    else:
        video_duration = get_video_duration(video_path)
        print("Found the file!!!")
        print(f"ℹ️ Video duration: {video_duration} seconds")

        timestamps = read_timestamps(timestamps_file)

        adjusted_timestamps = []
        for start, end in timestamps:
            start_sec = time_to_seconds(start)
            end_sec = time_to_seconds(end)

            if start_sec is None or end_sec is None:
                print(f"⚠ Skipping invalid timestamps: {start} - {end}")
            elif start_sec >= video_duration:
                print(f"⚠ Start time {start} exceeds video duration. Skipping.")
            elif end_sec > video_duration:
                print(f"⚠ End time {end} exceeds video duration. Adjusting end time.")
                adjusted_timestamps.append((start, time_to_seconds_to_timestamp(video_duration)))
            else:
                adjusted_timestamps.append((start, end))

        extract_and_resize_clips(video_path, adjusted_timestamps, output_folder)
        print("✅ Video processing complete! Clips saved in 'output_videos' folder.")