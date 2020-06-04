# Uses ImageMagick to divide scanned batch of photos into individual images.

In order to digitize photographs, it is expedient to scan multiple photos in
batches using a flatbed scanner. The resulting scans typically need further
processing to extract, deskew, and crop the individual photos.

This tool uses ImageMagick `convert` to process such scanned batches of photos.
Scans are required to have a white background.
TODO(shashir): Make robust to transparent background.

Usage:
```
$ python3 divide_scanned_photos.py image.png output_dir
Found 3 images
Wrote image 0 to output_dir/0_image.png.
Wrote image 1 to output_dir/1_image.png.
Wrote image 2 to output_dir/2_image.png.
```

If output_dir is not provided, the constituent images are written to the same
directory as the input image.
