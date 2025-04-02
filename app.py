from flask import Flask, render_template, request
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64, tempfile
from PIL import ImageFont, ImageDraw, Image
from flask import send_file
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from PIL import Image as PILImage
import os


app = Flask(__name__)
generated_images = {}
APP_VERSION = "v1.0.0"

# Utility Functions
def apply_background(canvas, background_type, y_start, bar_height, x_start, x_end):
    for y in range(y_start, y_start + bar_height):
        for x in range(x_start, x_end):
            if background_type == 'PU Hert' and y % 30 < 3:
                canvas[y, x] = [0, 0, 0]
            elif background_type == 'Diamond Type':
                if (x + y) % 50 < 3 or (x - y) % 50 < 3:
                    canvas[y, x] = [0, 0, 0]
            elif background_type == 'S Type':
                wave_length = 60
                wave_height = 15
                wave_offset = x % wave_length
                y_wave = ((wave_offset / (wave_length // 2)) * wave_height) if wave_offset < wave_length // 2 else ((wave_length - wave_offset) / (wave_length // 2)) * wave_height
                if abs(y % wave_height - y_wave) < 2:
                    canvas[y, x] = [0, 0, 0]
            elif background_type == 'T Type':
                diamond_size = 80
                if (x + y) % diamond_size < 3 or (x - y) % diamond_size < 3:
                    canvas[y, x] = [0, 0, 0]
                if (y + diamond_size // 2) % diamond_size < 3:
                    canvas[y, x] = [0, 0, 0]
    return canvas

def draw_horizontal_arrow(draw, x1, x2, y, text, font):
    arrow_size = 10
    text_padding = 10
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
    text_x = (x1 + x2 - text_width) // 2
    text_y = y - 25

    draw.line([(x1, y), (text_x - text_padding, y)], fill="black", width=2)
    draw.line([(text_x + text_width + text_padding, y), (x2, y)], fill="black", width=2)

    draw.polygon([(x1, y), (x1 + arrow_size, y - arrow_size), (x1 + arrow_size, y + arrow_size)], fill="black")
    draw.polygon([(x2, y), (x2 - arrow_size, y - arrow_size), (x2 - arrow_size, y + arrow_size)], fill="black")

    draw.text((text_x, text_y), text, fill="black", font=font)

def draw_vertical_arrow(draw, y1, y2, x, text, font):
    arrow_size = 10
    text_padding = 10
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
    text_y = (y1 + y2 - text_height) // 2
    text_x = x - text_width - 10

    draw.line([(x, y1), (x, text_y - text_padding)], fill="black", width=2)
    draw.line([(x, text_y + text_height + text_padding), (x, y2)], fill="black", width=2)

    draw.polygon([(x, y1), (x - arrow_size, y1 + arrow_size), (x + arrow_size, y1 + arrow_size)], fill="black")
    draw.polygon([(x, y2), (x - arrow_size, y2 - arrow_size), (x + arrow_size, y2 - arrow_size)], fill="black")

    draw.text((text_x, text_y), text, fill="black", font=font)

def generate_image(width, height, background_type, spacing_values, overlap, center_overlap,
                   center_holes, num_center_holes, hole_distances, pu_quantity, additional_message, additional_pu_strip, additional_distances, poly_ridge, hook_number=None, magnified_image=None, pu_sickness_image=None, center_strip_image=None, harp_name=None):
    # Determine expected spacing values count
    if center_overlap == "Yes":
        left_pu_count = pu_quantity // 2
        right_pu_count = pu_quantity - left_pu_count
        expected_spacing_values = left_pu_count + right_pu_count + 2  
    else:
        expected_spacing_values = pu_quantity + 1

    if len(spacing_values) != expected_spacing_values:
        print(f"Warning: Expected {expected_spacing_values} spacing values, got {len(spacing_values)}")
        return None

    # Dimensions
    hook_width = 100
    pu_strip_width = 50
    thin_strip_width = 10
 
    # Set canvas dimensions dynamically
    total_width = max(hook_width + (pu_quantity * pu_strip_width) + sum(spacing_values) + hook_width + 200, width + 700)
    canvas_width = total_width + 1900
    canvas_height = height + 3700 + (100 if overlap == "Yes" else 0)

    if center_overlap == "No":
        canvas_height = max(canvas_height, height + 900)

    # Create a blank white canvas
    canvas = np.ones((canvas_height, canvas_width, 3)) * 255

    # Colors
    hook_color = [104, 104, 104]  
    pu_strip_color = [255, 140, 0]
    overlap_color = [255, 140, 0]
    additional_pu_strip_color = [255, 140, 0]    
    bar_height = height

    # Starting positions
    start_x = (canvas_width - total_width) // 2
    y_start = (canvas_height - bar_height) // 2

    # Initialize positioning variables
    left_dummy = start_x + hook_width
    pos = left_dummy + pu_strip_width
    bar_positions = [left_dummy]
    text_positions = []

    # Handle positioning for center overlap
    if center_overlap == "Yes":
        center_x_start = canvas_width // 2 - (hook_width // 2)
        center_x_end = center_x_start + hook_width
        canvas[y_start:y_start+bar_height, center_x_start:center_x_end] = overlap_color

        left_positions = []
        right_positions = []
        
        # Left side bars
        pos_left = center_x_start - spacing_values[0] - pu_strip_width
        for i in range(left_pu_count):
            left_positions.append(pos_left)
            pos_left -= (pu_strip_width + spacing_values[i + 1])
        left_positions.reverse()  # To make sure left bars are ordered left-to-right

        # Right side bars
        pos_right = center_x_end + spacing_values[left_pu_count]
        for i in range(right_pu_count):
            right_positions.append(pos_right)
            pos_right += (pu_strip_width + spacing_values[left_pu_count + i + 1])
            
            
        # Bar positions list 
        bar_positions = [left_dummy]  
        bar_positions += left_positions
        bar_positions.append(center_x_start) 
        bar_positions += right_positions

    else:
        actual_positions = [pos + sum(spacing_values[:i]) + i * pu_strip_width for i in range(1, pu_quantity + 1)]
        bar_positions += actual_positions

    # Right Pu Strip and last spacing calculation 
    if len(spacing_values) == expected_spacing_values:
        right_dummy = bar_positions[-1] + pu_strip_width + spacing_values[-1]
    else:
        print(f"Warning: Expected {expected_spacing_values} spacing values, got {len(spacing_values)}")
        return None
    
    bar_positions.append(right_dummy)

    canvas = apply_background(canvas, background_type, y_start, bar_height, start_x, right_dummy + pu_strip_width)

    if center_overlap == "Yes":
        canvas[y_start:y_start+bar_height, center_x_start:center_x_end] = overlap_color  

    # Right hook alignment
    right_hook_x = right_dummy + (hook_width // 2)
    print(f"DEBUG: Right Hook X Position: {right_hook_x}, Right Dummy: {right_dummy}, Spacing Values: {spacing_values}")
    print(f"DEBUG: Final text positions: {text_positions}")  

    # Right Pu Strip and hook movement
    if overlap == "Yes":
        overlap_y_start = y_start + bar_height
        pu_strip_start = left_dummy
        pu_strip_end = right_dummy + pu_strip_width
        canvas[overlap_y_start:overlap_y_start+80, pu_strip_start:pu_strip_end] = pu_strip_color 
        
    ridge_strip_height = 40 

    if poly_ridge in ["Top Pu Strip", "To and Bottom Pu Strip"]:
        canvas[y_start - ridge_strip_height : y_start, left_dummy:right_dummy + pu_strip_width] = pu_strip_color

    if poly_ridge in ["Bottom Pu Strip", "To and Bottom Pu Strip"]:
        canvas[y_start + bar_height : y_start + bar_height + ridge_strip_height, left_dummy:right_dummy + pu_strip_width] = pu_strip_color


   # Drawing PU strips at calculated positions excluding center overlap
    for x_pos in bar_positions:
        if center_overlap == "Yes" and (x_pos == center_x_start):
            continue  # Skip drawing the PU strip at center overlap position
        canvas[y_start:y_start+bar_height, x_pos:x_pos+pu_strip_width] = pu_strip_color

    # Explicitly draw center overlap PU strip
    if center_overlap == "Yes":
        canvas[y_start:y_start+bar_height, center_x_start:center_x_end] = overlap_color

    
    # Calculate additional PU strips 
    centered_additional_midpoints = []

    if additional_pu_strip == "Yes" and additional_distances:
        for i in range(len(bar_positions) - 1):
            if i in additional_distances:
                midpoint = (bar_positions[i] + bar_positions[i + 1]) // 2

                if center_overlap == "Yes":
                    # Check index relative to known overlap position index
                    center_idx = bar_positions.index(center_x_start)
                    # Adjust ONLY the PU strip gap next to overlap
                    if i == center_idx - 1:  # left of overlap
                        midpoint -= hook_width // 8
                    elif i == center_idx:  # right of overlap
                        midpoint += hook_width // 4

                centered_midpoint = midpoint - (thin_strip_width // 2)
                centered_additional_midpoints.append(centered_midpoint)

    # Draw the centered thin PU strips
    for midpoint in centered_additional_midpoints:
        centered_x = midpoint - (thin_strip_width // 2) + 2  
        canvas[y_start:y_start+bar_height, centered_x:centered_x+thin_strip_width] = additional_pu_strip_color

                
    print("=== DEBUG INFO ===")
    print("Spacing Values:", spacing_values)
    print("Bar Positions:", bar_positions)
    print("Selected Indices (from form):", additional_distances)
    print("===================")

    
    # Drawing hooks after all adjustments to prevent duplication or misplacing hooks
    canvas[y_start:y_start+bar_height, start_x:start_x+hook_width] = hook_color  # Left hook
    canvas[y_start:y_start+bar_height, right_hook_x:right_hook_x+hook_width] = hook_color  # Right hook
    

    hole_positions = []
    total_y = y_start  # Start from top of PU bar
    
    # Ensuring sum of hole distances matches full height
    if center_holes == "Yes" and num_center_holes > 0:
        total_hole_spacing = sum(hole_distances)
        if total_hole_spacing != height:
            return f"Error: Total hole distances ({total_hole_spacing} mm) do not match the full height ({height} mm)."

        # Hole Placement Logic
        hole_width = 20
        hole_height = 40
        center_x_start = canvas_width // 2 - (hook_width // 2)

        for i in range(num_center_holes):
            # Cumulative Y position based on distance
            total_y += hole_distances[i] 
            hole_y = total_y - (hole_height // 2)
            hole_x = center_x_start + (hook_width // 2) - (hole_width // 2)

            # Allow holes on the full bar height 
            if y_start - 20 <= hole_y <= y_start + bar_height:
                canvas[hole_y:hole_y+hole_height, hole_x:hole_x+hole_width] = [255, 255, 255]
            
            hole_positions.append(total_y) 
            
    # Defining black border properties
    border_color = [0, 0, 0]  
    border_thickness = 2

    # Add black border for PU strips 
    for x_pos in bar_positions:
        if center_overlap == "Yes" and (x_pos == center_x_start):
            continue
        canvas[y_start:y_start+bar_height, x_pos:x_pos+border_thickness] = border_color
        canvas[y_start:y_start+bar_height, x_pos+pu_strip_width-border_thickness:x_pos+pu_strip_width] = border_color
        canvas[y_start:y_start+border_thickness, x_pos:x_pos+pu_strip_width] = border_color
        canvas[y_start+bar_height-border_thickness:y_start+bar_height, x_pos:x_pos+pu_strip_width] = border_color

    # Add border for additional thin PU strips
    for midpoint in centered_additional_midpoints:
        centered_x = midpoint - (thin_strip_width // 2) + 2
        canvas[y_start:y_start+bar_height, centered_x:centered_x+border_thickness] = border_color  # left side
        canvas[y_start:y_start+bar_height, centered_x+thin_strip_width-border_thickness:centered_x+thin_strip_width] = border_color  # right side
        canvas[y_start:y_start+border_thickness, centered_x:centered_x+thin_strip_width] = border_color  # top side
        canvas[y_start+bar_height-border_thickness:y_start+bar_height, centered_x:centered_x+thin_strip_width] = border_color  # bottom side

    # Add border for left and right hooks
    canvas[y_start:y_start+bar_height, start_x:start_x+border_thickness] = border_color  # left hook left side
    canvas[y_start:y_start+bar_height, start_x+hook_width-border_thickness:start_x+hook_width] = border_color  # left hook right side
    canvas[y_start:y_start+border_thickness, start_x:start_x+hook_width] = border_color  # left hook top
    canvas[y_start+bar_height-border_thickness:y_start+bar_height, start_x:start_x+hook_width] = border_color  # left hook bottom

    canvas[y_start:y_start+bar_height, right_hook_x:right_hook_x+border_thickness] = border_color  # right hook left side
    canvas[y_start:y_start+bar_height, right_hook_x+hook_width-border_thickness:right_hook_x+hook_width] = border_color  # right hook right side
    canvas[y_start:y_start+border_thickness, right_hook_x:right_hook_x+hook_width] = border_color  # right hook top
    canvas[y_start+bar_height-border_thickness:y_start+bar_height, right_hook_x:right_hook_x+hook_width] = border_color  # right hook bottom

    # Add border for center PU strip 
    if center_overlap == "Yes":
        canvas[y_start:y_start+bar_height, center_x_start:center_x_start+border_thickness] = border_color
        canvas[y_start:y_start+bar_height, center_x_end-border_thickness:center_x_end] = border_color
        canvas[y_start:y_start+border_thickness, center_x_start:center_x_end] = border_color
        canvas[y_start+bar_height-border_thickness:y_start+bar_height, center_x_start:center_x_end] = border_color

    # Add border for bottom overlap strip
    if overlap == "Yes":
        overlap_y_start = y_start + bar_height
        canvas[overlap_y_start:overlap_y_start+border_thickness, pu_strip_start:pu_strip_end] = border_color  # top
        canvas[overlap_y_start+80-border_thickness:overlap_y_start+80, pu_strip_start:pu_strip_end] = border_color  # bottom
        canvas[overlap_y_start:overlap_y_start+80, pu_strip_start:pu_strip_start+border_thickness] = border_color  # left
        canvas[overlap_y_start:overlap_y_start+80, pu_strip_end-border_thickness:pu_strip_end] = border_color  # right

    # Add border for poly ridge PU strips
    if poly_ridge in ["Top Pu Strip", "To and Bottom Pu Strip"]:
        top_y = y_start - ridge_strip_height
        canvas[top_y:top_y+border_thickness, left_dummy:right_dummy+pu_strip_width] = border_color  # top side
        canvas[y_start-border_thickness:y_start, left_dummy:right_dummy+pu_strip_width] = border_color  # bottom side
        canvas[top_y:y_start, left_dummy:left_dummy+border_thickness] = border_color  # left side
        canvas[top_y:y_start, right_dummy+pu_strip_width-border_thickness:right_dummy+pu_strip_width] = border_color  # right side

    if poly_ridge in ["Bottom Pu Strip", "To and Bottom Pu Strip"]:
        bottom_y = y_start + bar_height
        canvas[bottom_y:bottom_y+border_thickness, left_dummy:right_dummy+pu_strip_width] = border_color  # top side
        canvas[bottom_y+ridge_strip_height-border_thickness:bottom_y+ridge_strip_height, left_dummy:right_dummy+pu_strip_width] = border_color  # bottom side
        canvas[bottom_y:bottom_y+ridge_strip_height, left_dummy:left_dummy+border_thickness] = border_color  # left side
        canvas[bottom_y:bottom_y+ridge_strip_height, right_dummy+pu_strip_width-border_thickness:right_dummy+pu_strip_width] = border_color  # right side

    # Add border for center holes
    if center_holes == "Yes":
        hole_width = 20
        hole_height = 40
        for hole_center_y in hole_positions:
            hole_x = center_x_start + (hook_width // 2) - (hole_width // 2)
            hole_y = hole_center_y - (hole_height // 2)
            # Top border
            canvas[hole_y:hole_y+border_thickness, hole_x:hole_x+hole_width] = border_color
            # Bottom border
            canvas[hole_y+hole_height-border_thickness:hole_y+hole_height, hole_x:hole_x+hole_width] = border_color
            # Left border
            canvas[hole_y:hole_y+hole_height, hole_x:hole_x+border_thickness] = border_color
            # Right border
            canvas[hole_y:hole_y+hole_height, hole_x+hole_width-border_thickness:hole_x+hole_width] = border_color

           
    # Dynamic assignment of text positions based on spacing values
    text_positions = [] 

    for i in range(len(bar_positions) - 1):
        text_x = (bar_positions[i] + bar_positions[i + 1]) // 2
        text_positions.append((text_x, str(spacing_values[i])))

    print(f"DEBUG: ALL text positions (centered): {text_positions}") 
    
    # Convert OpenCV image to PIL for proper text rendering
    canvas_pil = Image.fromarray(canvas.astype('uint8'))

    # Load a Unicode-supported font with a fallback mechanism
    try:
        font_path = "C:/Windows/Fonts/arial.ttf"  # Primary choice: Arial
        font_pil = ImageFont.truetype(font_path, 60)  # Adjust font size if needed
    except IOError:
        try:
            print("⚠️ Arial not found! Trying Segoe UI...")
            font_path = "C:/Windows/Fonts/segoeui.ttf"  # Fallback: Segoe UI
            font_pil = ImageFont.truetype(font_path, 60)
        except IOError:
            try:
                print("⚠️ Segoe UI not found! Trying Verdana...")
                font_path = "C:/Windows/Fonts/verdana.ttf"  # Fallback: Verdana
                font_pil = ImageFont.truetype(font_path, 60)
            except IOError:
                print("⚠️ No valid font found! Using default system font.")
                font_pil = ImageFont.load_default()

    text_color = (0, 0, 0)  # Black color for text
    
    # === Combined image row: Hook, Aperture, PU Sickness, Center Strip ===

    hook_y = canvas_height - 1600  # Adjust vertical position as needed
    current_x = 100  # Start with left margin

    # HOOK image
    if hook_number:
        hook_path = f"static/images/{hook_number}.png"
        try:
            hook_img = Image.open(hook_path).convert("RGBA")
            hook_img = hook_img.resize((800, 600))
            canvas_pil.paste(hook_img, (current_x, hook_y), hook_img)
            current_x += 800 + 100
        except FileNotFoundError:
            print(f"⚠️ Hook image not found: {hook_path}")

    # APERTURE image
    if magnified_image:
        aperture_path = f"static/images/{magnified_image}.png"
        try:
            aperture_img = Image.open(aperture_path).convert("RGBA")
            aperture_img = aperture_img.resize((700, 600))
            canvas_pil.paste(aperture_img, (current_x, hook_y), aperture_img)
            current_x += 700 + 100
        except FileNotFoundError:
            print(f"⚠️ Aperture image not found: {aperture_path}")

    # PU SICKNESS image
    if pu_sickness_image:
        pu_sickness_path = f"static/images/{pu_sickness_image}.png"
        try:
            pu_img = Image.open(pu_sickness_path).convert("RGBA")
            pu_img = pu_img.resize((800, 600))
            canvas_pil.paste(pu_img, (current_x, hook_y), pu_img)
            current_x += 800 + 100
        except FileNotFoundError:
            print(f"⚠️ PU Sickness image not found: {pu_sickness_path}")

    # CENTER STRIP image
    if center_strip_image:
        center_path = f"static/images/{center_strip_image}.png"
        try:
            cs_img = Image.open(center_path).convert("RGBA")
            cs_img = cs_img.resize((800, 600))
            canvas_pil.paste(cs_img, (current_x, hook_y), cs_img)
            current_x += 800 + 100
        except FileNotFoundError:
            print(f"⚠️ Center strip image not found: {center_path}")

            
    
    draw = ImageDraw.Draw(canvas_pil)
    
    # Draw Harp Name inside the canvas
    harp_text = harp_name
    try:
        bold_font_path = "C:/Windows/Fonts/arialbd.ttf"  
        title_font = ImageFont.truetype(bold_font_path, 150)  
    except:
        title_font = font_pil  # Fallback to previously loaded font

    # Get bounding box of the text to compute width/height
    bbox = draw.textbbox((0, 0), harp_text, font=title_font)
    title_width = bbox[2] - bbox[0]

    # Center title horizontally near top of the canvas
    title_x = (canvas_width - title_width) // 2
    title_y = 200  

    draw.text((title_x, title_y), harp_text, fill=text_color, font=title_font)

    
   # Width arrow from left hook to right hook
    if spacing_values:
        left_x = start_x  # Start of the left hook
        right_x = right_hook_x + hook_width  # End of the right hook
        arrow_y = y_start - 180
        draw_horizontal_arrow(draw, left_x, right_x, arrow_y, str(width), font_pil)


    # Spacing arrows
    for i in range(len(bar_positions) - 1):
    # First arrow: from start_x (left hook) to second bar
        if i == 0:
            x1 = start_x
            x2 = bar_positions[1]
        # Last arrow: from last PU strip to end of right hook
        elif i == len(bar_positions) - 2:
            x1 = bar_positions[-2] + pu_strip_width
            x2 = right_hook_x + hook_width
        # All others is a default logic
        else:
            x1 = bar_positions[i] + pu_strip_width
            x2 = bar_positions[i + 1]

        # Skip overlap flip if needed
        if center_overlap == "Yes" and x1 > x2:
            continue

        arrow_y = y_start - 80
        draw_horizontal_arrow(draw, x1, x2, arrow_y, str(spacing_values[i]), font_pil)


    # Height arrow
    height_arrow_x = right_hook_x + hook_width + 160  # adjustable value
    draw_vertical_arrow(draw, y_start, y_start + bar_height, height_arrow_x, str(height), font_pil)


    if center_holes == "Yes" and len(hole_positions) > 0:
        tick_x = start_x - 60
        tick_length = 30
        text_gap = 20

        segments = []

        # From top to first hole
        segments.append((y_start, hole_positions[0], hole_distances[0]))

        # Between holes
        for i in range(1, len(hole_positions)):
            segments.append((hole_positions[i - 1], hole_positions[i], hole_distances[i]))

        # Last hole to bottom
        segments.append((hole_positions[-1], y_start + bar_height, hole_distances[-1]))

        for y1, y2, label in segments:
            mid_y = (y1 + y2) // 2

            # Draw vertical line from y1 to y2
            draw.line([(tick_x + tick_length // 2, y1), (tick_x + tick_length // 2, y2)], fill="black", width=2)

            # Draw horizontal ticks at both ends
            draw.line([(tick_x, y1), (tick_x + tick_length, y1)], fill="black", width=2)
            draw.line([(tick_x, y2), (tick_x + tick_length, y2)], fill="black", width=2)

            # Draw label in the middle
            text_width, text_height = draw.textbbox((0, 0), str(label), font=font_pil)[2:]
            draw.text((tick_x - text_width - text_gap, mid_y - text_height // 2), str(label), font=font_pil, fill="black")
        

    # Formating the additional message for rendering
    additional_message = additional_message.replace('\u00A0', ' ').replace('\r\n', '\n').replace('\r', '\n')

    # Display each line of the additional message at the bottom
    text_position = (50, canvas_height - 800)  
    lines = additional_message.split('\n')
    y_offset = 0
    for line in lines:
        draw.text((text_position[0], text_position[1] + y_offset), line, font=font_pil, fill=text_color)
        y_offset += 70 


    # Convert back to OpenCV format
    canvas = np.array(canvas_pil)

    print(f"DEBUG: Text drawn at positions: {text_positions}")
    
    # Save image in memory and encode as base64
    img_io = BytesIO()
    plt.imsave(img_io, canvas.astype(np.uint8), format='png', dpi=300)
    img_io.seek(0)
    image_data = base64.b64encode(img_io.getvalue()).decode('ascii')
    return image_data

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            width = int(request.form['width'])
            height = int(request.form['height'])
            pu_quantity = int(request.form['pu_quantity'])
            harp_name = request.form['harp_name'].strip()  # Get harp name
            additional_message = request.form['additional_message'].strip() 
        except ValueError:
            return "Invalid numeric input. Please check your entries."

        background_type = request.form['background_type']
        overlap = request.form.get('overlap', 'No')
        center_overlap = request.form.get('center_overlap', 'No')
        poly_ridge = request.form.get('poly_ridge', '')
        center_holes = request.form.get('center_holes', 'No')
        try:
            num_center_holes = int(request.form.get('num_center_holes', '0'))
        except ValueError:
            num_center_holes = 0

        # Process spacing values for non-center overlap
        if center_overlap == "Yes":
            left_list = request.form.getlist('left_spacing')
            right_list = request.form.getlist('right_spacing')
            try:
                left_values = [int(x) for x in left_list if x.strip().isdigit()]
                right_values = [int(x) for x in right_list if x.strip().isdigit()]
            except ValueError:
                return "Invalid spacing values."

            spacing_values = left_values + right_values
        else:
            spacing_list = request.form.getlist('spacing')
            try:
                spacing_values = [int(x) for x in spacing_list if x.strip().isdigit()]
            except ValueError:
                return "Invalid spacing values."
            
        # Validate total spacing against full width
        total_spacing = sum(spacing_values)
        if total_spacing != width:
            return render_template('index.html', error_message=f"Total spacing ({total_spacing} mm) does not match the full width ({width} mm).")    

        # Process hole distances
        hole_distances_str = request.form.get('hole_distances', '')
        if center_holes == "Yes" and num_center_holes > 0:
            try:
                hole_distances = [int(x.strip()) for x in hole_distances_str.split(',') if x.strip() != '']
            except Exception as e:
                return "Invalid hole distances: " + str(e)
        else:
            hole_distances = []

        # Capture Additional PU Strip Data
        additional_pu_strip = request.form.get('additional_pu_strip', 'No')
        additional_distances = []
        if additional_pu_strip == "Yes":
            additional_distances = [int(x) for x in request.form.getlist('additional_distances')]
            
        hook_number = request.form.get('hook_type')
        
        magnified_image = request.form.get('magnified_image')
        
        pu_sickness_image = request.form.get('pu_sickness_image')
        
        center_strip_image = request.form.get('center_strip_image')


        image_data = generate_image(width, height, background_type, spacing_values,
            overlap, center_overlap, center_holes, num_center_holes, hole_distances,
            pu_quantity, additional_message, additional_pu_strip, additional_distances, poly_ridge, hook_number=hook_number, magnified_image=magnified_image, pu_sickness_image=pu_sickness_image,
            center_strip_image=center_strip_image, harp_name=harp_name)
        
        generated_images[harp_name] = image_data


        if image_data is None:
            return "Image generation failed due to missing spacing values."

        return render_template('results.html',
            image_data=image_data,
            harp_name=harp_name,
            additional_pu_strip=additional_pu_strip,
            additional_distances=additional_distances,
            spacing_values=spacing_values,
            hook_number=hook_number,
            magnified_image=magnified_image,
            app_version=APP_VERSION  
        )

    return render_template('index.html')

@app.route('/download-pdf/<harp_name>')
def download_pdf(harp_name):
    image_base64 = generated_images.get(harp_name)

    if not image_base64:
        return "PDF generation failed: No image found for this screen."

    # Decode base64 and save temporarily
    image_data = base64.b64decode(image_base64)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_file:
        img_file.write(image_data)
        img_path = img_file.name

    # Create a PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_file:
        c = pdf_canvas.Canvas(pdf_file.name, pagesize=A4)
        img = PILImage.open(img_path)
        width, height = img.size

        # Fit the image to A4 with margins
        scale = min(A4[0] / width, A4[1] / height) * 0.95
        new_width = width * scale
        new_height = height * scale
        x = (A4[0] - new_width) / 2
        y = (A4[1] - new_height) / 2

        c.drawImage(img_path, x, y, width=new_width, height=new_height)
        c.showPage()
        c.save()

    return send_file(pdf_file.name, as_attachment=True, download_name=f"{harp_name}.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    port = int(os.eviron.get('PORT, 10000'))
    app.run(host='0.0.0.0', port=port)
    #app.run(debug=True)
    

