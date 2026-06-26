import argparse
import cv2
import time
import sys
from PIL import Image
from multiprocessing import Process
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import fpstimer
import moviepy.editor as mp


ASCII_CHARS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", " "]
# Get terminal dimensions for dynamic frame sizing
terminal_size = os.get_terminal_size()
frame_size = terminal_size.columns
terminal_height = terminal_size.lines
# Default frame rate (will be overridden by actual video FPS)
frame_rate = 30.0

ASCII_LIST = []


def play_audio(path):
    """Initialize pygame mixer and play audio file."""
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.mixer.init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()


def stop_audio():
    """Stop any playing audio and quit pygame cleanly."""
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    try:
        pygame.mixer.quit()
    except Exception:
        pass
    try:
        pygame.quit()
    except Exception:
        pass


def play_video(total_frames, fps=30.0):
    """Display ASCII frames in terminal with audio synchronization."""
    try:
        # Refresh terminal size in case it changed
        current_terminal = os.get_terminal_size()
        cols = current_terminal.columns
        rows = current_terminal.lines
        os.system(f'mode {cols}, {rows}')

        # Create timer based on actual video frame rate
        timer = fpstimer.FPSTimer(fps)
        start_frame = 0

        for frame_number in range(start_frame, total_frames):
            sys.stdout.write("\r" + ASCII_LIST[frame_number])
            timer.sleep()
    except KeyboardInterrupt:
        sys.stdout.write('\nPlayback stopped by user.\n')
        stop_audio()


# Extract frames from video and convert to ASCII art
def extract_transform_generate(video_path, start_frame, number_of_frames=1000):
    """Read video frames and convert them to ASCII art for display."""
    capture = cv2.VideoCapture(video_path)
    capture.set(1, start_frame)  # Jump to starting frame
    current_frame = start_frame
    frame_count = 1
    ret, image_frame = capture.read()
    while ret and frame_count <= number_of_frames:
        ret, image_frame = capture.read()
        try:
            image = Image.fromarray(image_frame)
            # Convert frame to ASCII characters
            ascii_characters = pixels_to_ascii(greyscale(resize_image(image)))
            pixel_count = len(ascii_characters)
            # Arrange ASCII characters into lines based on frame width
            ascii_image = "\n".join(
                [ascii_characters[index:(index + frame_size)] for index in range(0, pixel_count, frame_size)])

            ASCII_LIST.append(ascii_image)

        except Exception as error:
            continue

        progress_bar(frame_count, number_of_frames)

        frame_count += 1
        current_frame += 1

    capture.release()


# Display processing progress with a visual bar
def progress_bar(current, total, barLength=25):
    """Show progress bar for frame processing."""
    progress = float(current) * 100 / total
    arrow = '#' * int(progress / 100 * barLength - 1)
    spaces = ' ' * (barLength - len(arrow))
    sys.stdout.write('\rProgress: [%s%s] %d%% Frame %d of %d frames' % (arrow, spaces, progress, current, total))


# Resize image to fit terminal width
def resize_image(image_frame):
    """Resize image to match terminal width while maintaining aspect ratio."""
    width, height = image_frame.size
    # Adjust for console character aspect ratio (characters are taller than wide)
    aspect_ratio = (height / float(width * 2.5))
    new_height = int(aspect_ratio * frame_size)
    resized_image = image_frame.resize((frame_size, new_height))
    return resized_image


# Convert image to greyscale
def greyscale(image_frame):
    """Convert color image to greyscale for ASCII conversion."""
    return image_frame.convert("L")


# Map pixel brightness values to ASCII characters
def pixels_to_ascii(image_frame):
    """Convert pixel brightness values to ASCII characters."""
    pixels = image_frame.getdata()
    characters = "".join([ASCII_CHARS[pixel // 25] for pixel in pixels])
    return characters


# Process images: Resize => Greyscale => Convert to ASCII => Save to file
def ascii_generator(image_path, start_frame, number_of_frames):
    """Convert static images to ASCII art and save to text files."""
    current_frame = start_frame
    while current_frame <= number_of_frames:
        path_to_image = image_path + '/BadApple_' + str(current_frame) + '.jpg'
        image = Image.open(path_to_image)
        # Convert image through pipeline: resize -> greyscale -> ASCII
        ascii_characters = pixels_to_ascii(greyscale(resize_image(image)))
        pixel_count = len(ascii_characters)
        # Arrange ASCII into lines matching terminal width
        ascii_image = "\n".join(
            [ascii_characters[index:(index + frame_size)] for index in range(0, pixel_count, frame_size)])
        file_name = r"TextFiles/" + "bad_apple" + str(current_frame) + ".txt"
        try:
            with open(file_name, "w") as f:
                f.write(ascii_image)
        except FileNotFoundError:
            continue
        current_frame += 1


def preflight_operations(path):
    """Extract video info, audio, and generate ASCII frames."""
    if os.path.exists(path):
        path_to_video = path.strip()
        cap = cv2.VideoCapture(path_to_video)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Get the actual FPS from the video file
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        video = mp.VideoFileClip(path_to_video)
        path_to_audio = 'audio.mp3'
        video.audio.write_audiofile(path_to_audio)

        start_time = time.time()
        sys.stdout.write('Beginning ASCII generation...\n')
        extract_transform_generate(path_to_video, 1, total_frames)
        execution_time = time.time() - start_time
        sys.stdout.write('ASCII generation completed! ASCII generation time: ' + str(execution_time) + '\n')

        return total_frames, video_fps

    else:
        sys.stdout.write('Warning file not found!\n')
        return 0, 30.0


def main():
    """Main menu for user interaction and optional command-line playback."""
    parser = argparse.ArgumentParser(description='Play Bad Apple as ASCII art in the terminal.')
    parser.add_argument('video_file', nargs='?', help='Optional video file to play directly')
    args = parser.parse_args()

    if args.video_file:
        total_frames, video_fps = preflight_operations(args.video_file)
        if total_frames:
            try:
                play_audio('audio.mp3')
                play_video(total_frames=total_frames, fps=video_fps)
            except KeyboardInterrupt:
                stop_audio()
        return

    while True:
        sys.stdout.write('==============================================================\n')
        sys.stdout.write('Bad Apple ASCII Player\n')
        sys.stdout.write('==============================================================\n')
        sys.stdout.write('1) Play\n')
        sys.stdout.write('2) Exit\n')
        sys.stdout.write('==============================================================\n')

        user_input = str(input("Your option: "))
        user_input.strip()

        if user_input == '1':
            user_input = str(input("Please enter the video file name (file must be in root!): "))
            total_frames, video_fps = preflight_operations(user_input)
            if total_frames:
                try:
                    play_audio('audio.mp3')
                    play_video(total_frames=total_frames, fps=video_fps)
                except KeyboardInterrupt:
                    stop_audio()
        elif user_input == '2':
            exit()
            continue
        else:
            sys.stdout.write('Unknown input!\n')
            continue


if __name__ == '__main__':
    main()
