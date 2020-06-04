#!/usr/bin/env python3
"""Uses ImageMagick to divide scanned batch of photos into individual images.

In order to digitize photographs, it is expedient to scan multiple photos in
batches using a flatbed scanner. The resulting scans typically need further
processing to extract, deskew, and crop the individual photos.

This tool uses ImageMagick `convert` to process such scanned batches of photos.
Scans are required to have a white background.
TODO(shashir): Make robust to transparent background.

Usage:
$ python3 divide_scanned_photos.py image.png output_dir
Found 3 images
Wrote image 0 to output_dir/0_image.png.
Wrote image 1 to output_dir/1_image.png.
Wrote image 2 to output_dir/2_image.png.

If output_dir is not provided, the constituent images are written to the same
directory as the input image.
"""

import argparse
import collections
import logging
import os
import subprocess
import shutil
import sys
import tempfile


# ImageMagick constants.
# TODO(shashir): Expose some of these as flags.
BLACK_WHITE_THRESHOLD_PERC = 90  # convert -threshold
CONNECTED_COMPONENTS = 4  # convert -connected-components
DESKEW_PERC = 40  # convert -deskew
FUZZ_PERC = 10  # convert -fuzz

# Other constants
# All images are required to have area >= this fraction of the
# largest image's area. This helps filter out noise and specks.
FRACTION_OF_LARGEST_AREA = 0.1


# Connected components parsed from ImageMagick output.
ConnectedComponent = collections.namedtuple(
    'ConnectedComponent', ['region', 'area', 'mean_color'])


def run_command(cmd):
  """Run command and return stdout."""
  logging.info(f"run: {cmd}")
  process = subprocess.Popen(
      cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, stderr = (x.decode("utf-8").strip() for x in process.communicate())
  logging.info(f"stdout: {stdout}")
  if stderr:
    logging.warning(f"stderr: {stderr}")
  assert process.returncode == 0, f"Command: '{cmd}' failed with '{stderr}'."
  return stdout


def get_photo_regions(input_path):
  """Determine regions containing photos."""
  # Find connected components.
  components = list()
  max_area = 1  # Area of the largest component, not including the whole image.
  with tempfile.NamedTemporaryFile() as tmpfile:
    cmd = (
        f"convert {input_path} -threshold {BLACK_WHITE_THRESHOLD_PERC}% "
        f"-define connected-components:verbose=true "
        f"-connected-components {CONNECTED_COMPONENTS} "
        f"{tmpfile.name}")
    stdout_lines = run_command(cmd).split("\n")[1:]
    for line in stdout_lines:
      tokens = line.split(" ")
      if len(tokens) != 7:
        continue
      component = ConnectedComponent(tokens[3], int(tokens[5]), tokens[6])
      # Filter out blank regions.
      if (component.mean_color == "srgb(0,0,0)" or \
          component.mean_color.startswith("srgba(0,0,0")):
        max_area = max(max_area, component.area)
        components.append(component)
  logging.info(f"Found {len(components)} total connected components.")
        
  # Filter out small connected components.
  filtered_components = list()
  for component in components:
    if component.area >= FRACTION_OF_LARGEST_AREA * max_area:
      filtered_components.append(component)
  print(f"Found {len(filtered_components)} images.")
  return filtered_components


def crop_photo_region(input_path, region, output_path):
  """Cut specified region from input image and write to output."""
  cmd = f"convert {input_path} -crop {region} +repage {output_path}"
  return run_command(cmd)


def straighen_image(input_path, output_path):
  """Straighten a skewed input image and write to output."""
  cmd = (
      f"convert {input_path} -deskew {DESKEW_PERC}% -fuzz {FUZZ_PERC}% "
      f"-trim +repage {output_path}")
  return run_command(cmd)


def divide_crop_and_straighten(input_path, output_dir):
  """Divides input image into parts and write them to the output dir."""
  photo_regions = get_photo_regions(input_path)
  input_filename = os.path.basename(input_path)
  with tempfile.NamedTemporaryFile() as tmpfile:
    counter = 0
    for photo_region in photo_regions:
      crop_photo_region(input_path, photo_region.region, tmpfile.name)
      output_path = os.path.join(output_dir, f"{counter}_{input_filename}")
      straighen_image(tmpfile.name, output_path)
      print(f"Wrote image {counter} to {output_path}.")
      counter += 1
 

def main(args):
  if args.log == "warning":
    logging.basicConfig(level=logging.WARNING)
  else:
    logging.basicConfig(level=logging.INFO)
  input_dir = os.path.dirname(args.input)
  output_dir = args.output_dir if args.output_dir else input_dir
  divide_crop_and_straighten(args.input, output_dir)


if __name__ == "__main__":
  assert shutil.which("convert"), (
      "Did not find `convert` tool in the path. Please install ImageMagick.")
  parser = argparse.ArgumentParser()
  parser.add_argument("input", type=str, help="Path to input image.")
  parser.add_argument(
      "output_dir", type=str, default="", nargs="?",
      help=("Path to output directory. If empty, output images will be "
            "written to the same directory as the input image."))
  parser.add_argument(
      "-log", "--log", type=str, default="warning",
      choices=["warning", "info"],
      help="Log level: warning, info")
  main(parser.parse_args())


