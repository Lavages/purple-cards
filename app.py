from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import io

app = Flask(__name__)

# Events listed 1 per line, Cap On Pen last
EVENTS = [
    "Face-Turning Octahedron (FTO)",
    "Mirror Blocks",
    "Kilominx",
    "Redi Cube",
    "Gear Cube",
    "Ivy Cube",
    "Master Pyraminx",
    "2x2x2 Blindfolded",
    "Clock One-Handed",
    "3x3x3 No Inspection",
    "Team Blindfolded",
    "2-man Mini Guildford",
    "Rubik’s Magic",
    "Master Magic",
    "3x3x3 With Feet",
    "3x3x3 Match The Scramble",
    "3x3x3 Supersolve",
    "3x3x3 Scrambling",
    "4x4x4 One-Handed",
    "2x2x2-4x4x4 Relay",
    "3x3x3 With Oven Mitts",
    "15 Puzzle",
    "Triangular Clock",
    "Pentagonal Clock",
    "Super Pentagonal Clock",
    "Cap On Pen"
]

def format_time_label(seconds_str):
    if not seconds_str or not seconds_str.isdigit():
        return seconds_str
    total_seconds = int(seconds_str)
    if total_seconds > 3600: total_seconds = 3600
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    elif minutes > 0:
        return f"{minutes}:{seconds:02d}"
    else:
        return f"{seconds}.00"

def draw_cutting_guides(c, width, height):
    """Draws light gray dashed lines for perfect 4-way cutting/folding."""
    c.setDash(1, 4)
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.5)
    c.line(width/2, 0, width/2, height)
    c.line(0, height/2, width, height/2)
    c.setDash([])

def draw_card(c, x, y, comp_name, event_name, round_text, format_type, cutoff, limit):
    PURPLE = (0.5, 0.2, 0.8) 
    BLACK = (0, 0, 0)
    
    c.setStrokeColorRGB(*PURPLE)
    c.setLineWidth(1.2)
    
    # Header
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(*BLACK)
    c.drawCentredString(x + 5.25*cm, y + 13.5*cm, comp_name.upper())
    
    # Top Info Boxes
    start_x = x + 0.9*cm 
    c.rect(start_x, y + 11.5*cm, 6.5*cm, 0.8*cm)
    c.rect(start_x + 6.7*cm, y + 11.5*cm, 1.0*cm, 0.8*cm)
    c.rect(start_x + 7.9*cm, y + 11.5*cm, 0.8*cm, 0.8*cm)
    c.drawCentredString(start_x + 8.3*cm, y + 11.8*cm, round_text)
    
    # Event Banner
    c.setFillColorRGB(0.95, 0.9, 1.0) 
    c.rect(start_x, y + 10.3*cm, 8.7*cm, 0.8*cm, fill=1)
    c.setFillColorRGB(0.3, 0.1, 0.5) 
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x + 5.25*cm, y + 10.55*cm, event_name.upper())
    
    # Result Rows Logic
    num_attempts = 3 if format_type == "Mo3" else (1 if format_type == "Bo1" else 5)
    row_height = 1.1*cm
    row_spacing = 0.2*cm
    last_row_y = 0

    for i in range(num_attempts):
        row_y = y + 8.8*cm - (i * (row_height + row_spacing))
        last_row_y = row_y
        
        # DYNAMIC CUTOFF LINE
        # Mo3: Line after attempt 1 (index 0)
        # Ao5: Line after attempt 2 (index 1)
        # Note: We draw the line ABOVE the row that follows the cutoff point
        cutoff_trigger_index = 1 if format_type == "Mo3" else 2
        
        if i == cutoff_trigger_index and cutoff:
            mid_y = row_y + row_height + (row_spacing / 2)
            c.setDash(2, 2)
            c.setLineWidth(0.8)
            c.line(start_x, mid_y, start_x + 8.7*cm, mid_y)
            c.setDash([]) 
            c.setLineWidth(1.2)

        c.setStrokeColorRGB(*PURPLE)
        c.rect(start_x + 0.7*cm, row_y, 5.3*cm, row_height)
        c.rect(start_x + 6.2*cm, row_y, 1.1*cm, row_height)
        c.rect(start_x + 7.5*cm, row_y, 1.2*cm, row_height)
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(*BLACK)
        c.drawString(start_x, row_y + 0.4*cm, str(i + 1))

    # Extra Attempt with "_" on the left
    extra_gap = 0.8*cm
    extra_y = last_row_y - (row_height + extra_gap)
    
    c.setFont("Helvetica-Bold", 8)
    c.setFillColorRGB(*PURPLE)
    c.drawString(start_x, extra_y + 0.4*cm, "_") 
    c.drawString(start_x + 0.7*cm, extra_y + 1.15*cm, "Extra attempt (Delegate initials ____)")
    c.rect(start_x + 0.7*cm, extra_y, 5.3*cm, 1.1*cm)
    c.rect(start_x + 6.2*cm, extra_y, 1.1*cm, 1.1*cm)
    c.rect(start_x + 7.5*cm, extra_y, 1.2*cm, 1.1*cm)

    # Cutoff & Limit Labels
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(*BLACK)
    if cutoff:
        c.drawString(start_x + 0.7*cm, extra_y - 0.5*cm, f"Cutoff: < {format_time_label(cutoff)}")
    if limit:
        c.drawRightString(start_x + 8.7*cm, extra_y - 0.5*cm, f"Time limit: {format_time_label(limit)}")

@app.route('/')
def index():
    return render_template('index.html', events=EVENTS)

@app.route('/generate', methods=['POST'])
def generate():
    comp_name = request.form.get('comp_name', 'Unofficial Comp')
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    card_w, card_h = 10.5 * cm, 14.85 * cm

    for event in EVENTS:
        if request.form.get(f'check_{event}'):
            format_type = request.form.get(f'format_{event}', 'Ao5')
            rounds = int(request.form.get(f'rounds_{event}', 1))
            for r in range(1, rounds + 1):
                round_label = str(r) if r < rounds else "F"
                total_cards = int(request.form.get(f'cards_{event}_r{r}', 0))
                cutoff = request.form.get(f'cutoff_{event}_r{r}', "")
                limit = request.form.get(f'limit_{event}_r{r}', "")
                
                cards_placed = 0
                while cards_placed < total_cards:
                    draw_cutting_guides(c, width, height)
                    for row in range(2): 
                        for col in range(2): 
                            if cards_placed < total_cards:
                                x_pos = col * card_w
                                y_pos = (1 - row) * card_h
                                draw_card(c, x_pos, y_pos, comp_name, event, round_label, format_type, cutoff, limit)
                                cards_placed += 1
                    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{comp_name}_Scorecards.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)