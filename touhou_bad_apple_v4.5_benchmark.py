import argparse
import cv2
import time
import sys
from PIL import Image
from multiprocessing import Process
import os
import tempfile
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import fpstimer
import moviepy.editor as mp


ASCII_CHARS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", " "]
frame_size = 150
frame_interval = 1.0 / 30.75
benchmark_frame_count = 100

ASCII_LIST = []


def play_audio(path):
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.mixer.init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()


def play_video(total_frames):
    os.system('mode 150, 500')

    timer = fpstimer.FPSTimer(30)
    start_frame = 0

    for frame_number in range(start_frame, total_frames):
        sys.stdout.write("\r" + ASCII_LIST[frame_number])
        timer.sleep()


def extract_transform_generate(video_path, start_frame, number_of_frames=1000):
    capture = cv2.VideoCapture(video_path)
    capture.set(1, start_frame)  # Points cap to target frame
    current_frame = start_frame
    frame_count = 1
    ret, image_frame = capture.read()
    while ret and frame_count <= number_of_frames:
        ret, image_frame = capture.read()
        try:
            image = Image.fromarray(image_frame)
            ascii_characters = pixels_to_ascii(greyscale(resize_image(image)))  # get ascii characters
            pixel_count = len(ascii_characters)
            ascii_image = "\n".join(
                [ascii_characters[index:(index + frame_size)] for index in range(0, pixel_count, frame_size)])

            ASCII_LIST.append(ascii_image)

        except Exception:
            continue

        progress_bar(frame_count, number_of_frames)
        frame_count += 1
        current_frame += 1

    capture.release()


def benchmark_video(video_path, number_of_frames=benchmark_frame_count):
    capture = cv2.VideoCapture(video_path)
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    video_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames_to_process = min(number_of_frames, total_frames)
    processed = 0
    total_chars = 0

    sys.stdout.write(f"Benchmarking {frames_to_process} frames from {video_path}\n")
    sys.stdout.write(f"Video resolution: {video_width}x{video_height}, total frames: {total_frames}\n")

    start_time = time.perf_counter()
    while processed < frames_to_process:
        ret, image_frame = capture.read()
        if not ret:
            break
        try:
            image = Image.fromarray(image_frame)
            ascii_characters = pixels_to_ascii(greyscale(resize_image(image)))
            pixel_count = len(ascii_characters)
            total_chars += pixel_count
            _ = "\n".join(
                [ascii_characters[index:(index + frame_size)] for index in range(0, pixel_count, frame_size)])
        except Exception:
            pass

        processed += 1
        progress_bar(processed, frames_to_process)

    capture.release()
    elapsed = time.perf_counter() - start_time
    avg_chars = (total_chars / processed) if processed else 0
    sys.stdout.write(
        f"\nBenchmark complete:\n"
        f"  Frames processed: {processed}\n"
        f"  Elapsed time: {elapsed:.2f}s\n"
        f"  Average FPS: {(processed / elapsed) if elapsed else 0:.2f}\n"
        f"  Average chars/frame: {avg_chars:.0f}\n"
        f"  Total chars generated: {total_chars}\n"
    )


# Progress bar code is courtesy of StackOverflow user: Aravind Voggu.
# Link to thread: https://stackoverflow.com/questions/6169217/replace-console-output-in-python
def progress_bar(current, total, barLength=25):
    progress = float(current) * 100 / total
    arrow = '#' * int(progress / 100 * barLength - 1)
    spaces = ' ' * (barLength - len(arrow))
    sys.stdout.write('\rProgress: [%s%s] %d%% Frame %d of %d frames' % (arrow, spaces, progress, current, total))


# Resize image
def resize_image(image_frame):
    width, height = image_frame.size
    aspect_ratio = (height / float(width * 2.5))  # 2.5 modifier to offset vertical scaling on console
    new_height = int(aspect_ratio * frame_size)
    resized_image = image_frame.resize((frame_size, new_height))
    return resized_image


# Greyscale
def greyscale(image_frame):
    return image_frame.convert("L")


# Convert pixels to ascii
def pixels_to_ascii(image_frame):
    pixels = image_frame.getdata()
    characters = "".join([ASCII_CHARS[pixel // 25] for pixel in pixels])
    return characters


# Open image => Resize => Greyscale => Convert to ASCII => Store in text file
def ascii_generator(image_path, start_frame, number_of_frames):
    current_frame = start_frame
    while current_frame <= number_of_frames:
        path_to_image = image_path + '/BadApple_' + str(current_frame) + '.jpg'
        image = Image.open(path_to_image)
        ascii_characters = pixels_to_ascii(greyscale(resize_image(image)))  # get ascii characters
        pixel_count = len(ascii_characters)
        ascii_image = "\n".join(
            [ascii_characters[index:(index + frame_size)] for index in range(0, pixel_count, frame_size)])
        file_name = r"TextFiles/" + "bad_apple" + str(current_frame) + ".txt"
        try:
            with open(file_name, "w") as f:
                f.write(ascii_image)
        except FileNotFoundError:
            continue
        current_frame += 1


def preflight_operations(path, extract_audio=True):
    if os.path.exists(path):
        path_to_video = path.strip()
        cap = cv2.VideoCapture(path_to_video)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        audio_path = None
        if extract_audio:
            video = mp.VideoFileClip(path_to_video)
            fd, audio_path = tempfile.mkstemp(suffix='.mp3', prefix='badapple_audio_')
            os.close(fd)
            try:
                video.audio.write_audiofile(audio_path)
            finally:
                video.close()
        else:
            sys.stdout.write('Benchmark mode: skipping audio extraction. Source audio is preserved.\n')

        return total_frames, audio_path

    else:
        sys.stdout.write('Warning file not found!\n')
        return 0


def main():
    parser = argparse.ArgumentParser(description='Play Bad Apple v4.5 as ASCII art in the terminal.')
    parser.add_argument('video_file', nargs='?', help='Optional video file to play directly')
    parser.add_argument('-b', '--benchmark', action='store_true', help='Benchmark frame processing instead of playing back.')
    args = parser.parse_args()

    if args.video_file:
        total_frames, audio_path = preflight_operations(args.video_file, extract_audio=not args.benchmark)
        if total_frames:
            if args.benchmark:
                benchmark_video(args.video_file)
                return

            try:
                if audio_path:
                    play_audio(audio_path)
                extract_transform_generate(args.video_file, 1, total_frames)
                play_video(total_frames=total_frames)
            finally:
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except OSError:
                        pass
        return

    while True:
        sys.stdout.write('==============================================================\n')
        sys.stdout.write('Select option: \n')
        sys.stdout.write('1) Play\n')
        sys.stdout.write('2) Exit\n')
        sys.stdout.write('==============================================================\n')

        user_input = str(input("Your option: "))
        user_input.strip()  # removes trailing whitespaces

        if user_input == '1':
            user_input = str(input("Please enter the video file name (file must be in root!): "))
            total_frames, audio_path = preflight_operations(user_input)
            if total_frames:
                try:
                    if audio_path:
                        play_audio(audio_path)
                    extract_transform_generate(user_input, 1, total_frames)
                    play_video(total_frames=total_frames)
                finally:
                    if audio_path and os.path.exists(audio_path):
                        try:
                            os.remove(audio_path)
                        except OSError:
                            pass
        elif user_input == '2':
            exit()
            continue
        else:
            sys.stdout.write('Unknown input!\n')
            continue


if __name__ == '__main__':
    main()
