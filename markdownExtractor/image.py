import base64
import hashlib
import cairosvg
import cv2
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os
import io
import requests
import pytesseract
import re
import tempfile
from pathlib import Path
import logging


def download_and_extract_image_to_md(
        src: str,
        temp_directory: str,
        alt_text: str = '',
        enhance_level: int = 0,
        include_empty=False) -> str:
    """
    Download an image, extract text and convert to markdown
    :param src: src as it appears in the image tag or a URL, can be a data URL
    :param temp_directory:
    :param alt_text: alt_text as it appears in the image tag
    :param enhance_level:
    :param include_empty:
    :return:
    """
    logging.debug(f"Downloading image: {src}")
    local_path = download_image(src, temp_directory)
    logging.debug(f"Downloaded image to: {local_path}")
    if not local_path:
        logging.error(src + ' failed to download')
        return ''

    if not os.path.isfile(local_path):
        logging.error(f"File not found: {local_path}")
        return ''

    logging.debug(f"Downloaded image to: {local_path}")

    return extract_image_md(src, local_path, alt_text, enhance_level=enhance_level, include_empty=include_empty)


def extract_image_md(src: str, local_path: str, alt_text: str = '', enhance_level: int = 1, include_empty=False) -> str:
    """
    Extract text from a local image and convert to markdown
    :param src:
    :param local_path:
    :param alt_text:
    :param enhance_level:
    :param include_empty:
    :return:
    """
    # Extract text from the image
    extracted_text = extract_image_text(local_path, enhance_level=enhance_level)

    # form the markdown
    return _image_data_to_markdown(src, alt_text, extracted_text, include_empty=include_empty)


def _image_data_to_markdown(src, alt_text, extracted_text, include_empty=False) -> str:
    """
    Convert image information to markdown. If no text was extracted, return an empty string unless include_empty is True
    :param src:
    :param alt_text:
    :param extracted_text:
    :param include_empty:
    :return:
    """
    if not alt_text and not extracted_text:
        # No text was extracted from the image
        if not include_empty:
            return ''
        else:
            return f"![]({src})"

    text_content = ''

    if src.startswith('data:image'):
        # Display these differently as we have no working URL
        if extracted_text:
            extracted_text = extracted_text.replace('"', "'")
            text_content = f"![{alt_text}](local.img \"{extracted_text}\")"
    else:
        text_content = f"![{alt_text}]({src}"
        if extracted_text:
            if len(extracted_text) < 255:
                # convert double quotes to single quotes so that we can put this inline as title
                extracted_text = extracted_text.replace('"', "'")
                text_content += f" \"{extracted_text}\")"
            else:
                # make the extraction a code-block after the image
                # if the extraction contains a code-block wrapper, change it to the alt-format.
                extracted_text = extracted_text.replace('```', '~~~')
                text_content += f")```image-text\n{extracted_text}```"
        else:
            text_content += ')'

    logging.debug(f"Extracted text: {text_content}")

    return text_content


def download_image(src: str, temp_directory: str) -> str:
    """
    Download an image, or extract it from a data URL and save it to a file in the temp_directory
    :param src:
    :param temp_directory:
    :return: The path to the local file
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 '
                      'Safari/537.36'
    }
    # Regular expression to match data URL and extract MIME type
    data_url_pattern = re.compile(r'data:image/(?P<type>png|jpeg|gif|jpg|svg\+xml);base64,(?P<data>.*)')
    match = data_url_pattern.match(src)

    if match:
        logging.debug(f"Found data URL: {src}")
        # It's a data URL, so decode the base64 data
        image_data = base64.b64decode(match.group('data'))
        image_type = match.group('type')

        # Determine the file extension
        if image_type == 'jpeg' or image_type == 'jpg':
            extension = 'jpg'
        elif image_type == 'png':
            extension = 'png'
        elif image_type == 'svg+xml':
            extension = 'svg'
        elif image_type == 'gif':
            extension = 'gif'
        else:
            extension = 'img'  # Default extension or raise an error

        local_path = os.path.join(temp_directory, 'images', f"{hashlib.md5(image_data).hexdigest()}.{extension}")
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, 'wb') as file:
            file.write(image_data)

        return local_path
    elif src.startswith(('http://', 'https://')):
        try:
            logging.debug(f"Downloading image: {src}")
            response = requests.get(src, headers=headers, timeout=2)
            response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful
            # status code
        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to retrieve image: {src}, due to: {e}")
            return ''

        # Generate a file name based on the URL's hash
        file_name = hashlib.md5(src.encode()).hexdigest() + '.' + src.split('.')[-1].split('?')[0]
        local_path = os.path.join(temp_directory, 'images', file_name)
        logging.debug(f" ======  Saving image to: {local_path}")
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        with open(local_path, 'wb') as file:
            logging.debug(f"Writing image to: {local_path}")
            file.write(response.content)  # Write the entire content at once

        return local_path

    else:
        logging.warning(f"Could not download image: {src} - no idea what protocol that IS!")
        return ''


def convert_svg_to_png(svg_path: str, output_width: int = 1000, output_height: int = 1000) -> Image:
    """
    Convert an SVG from a URL to a PNG Image, so that we can OCR
    :param svg_path:
    :param output_width:
    :param output_height:
    :return:
    """
    png_data = cairosvg.svg2png(url=svg_path, output_width=output_width, output_height=output_height)
    return Image.open(io.BytesIO(png_data))


def extract_image_text(local_path: str, enhance_level: int = 1) -> str:
    """
    Extract raw text from an image via OCR
    :param local_path:
    :param enhance_level:
    :return:
    """
    if local_path.endswith('.svg'):
        img = convert_svg_to_png(local_path)
    else:
        with open(local_path, 'rb') as file:
            try:
                img = Image.open(io.BytesIO(file.read()))
            except UnidentifiedImageError:
                logging.error(f"Failed to open image: {local_path}")
                return ''

    if enhance_level > 0:
        # Resize the image
        scale_factor = 6
        new_size = (img.width * scale_factor, img.height * scale_factor)
        img = img.resize(new_size, Image.LANCZOS)
        # img.save("resized_image.png")  # Save the resized image

        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)  # Adjust the factor to suit your needs
        # img.save("contrast_enhanced_image.png")  # Save the contrast-enhanced image

        if enhance_level > 1:
            open_cv_image = np.array(img)
            # Convert RGB to BGR
            if len(open_cv_image.shape) == 3:
                # Image is in color (3D), so reverse color channels
                open_cv_image = open_cv_image[:, :, ::-1].copy()

            # Convert the image to grayscale
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
            # cv2.imwrite("greyscale_image.png", gray)  # Save the blurred image

            # Apply Gaussian Blur
            blur = cv2.GaussianBlur(gray, (3, 3), 0)
            # cv2.imwrite("blurred_image.png", blur)  # Save the blurred image

            # Apply Global Thresholding
            _, thresh = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY)
            # cv2.imwrite("thresholded_image.png", thresh)  # Save the thresholded image

            # Convert back to PIL Image
            img = Image.fromarray(thresh)

        else:
            # Convert to grayscale
            img = img.convert('L')

    custom_config = r'--oem 3 --psm 4'
    # Perform OCR
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=custom_config)
    text = ''

    for i in range(len(data['text'])):
        if int(data['conf'][i]) > 30:  # Confidence level check
            text += data['text'][i] + ' '

    return text.strip()