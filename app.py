from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import io

app = Flask(__name__)

# Updated list with new events included
EVENTS = [
    "Face-Turning Octahedron (FTO)", "Mirror Blocks", "Kilominx", "Redi Cube", "Gear Cube", 
    "Ivy Cube", "Master Pyraminx", "2x2x2 Blindfolded", "Clock One-Handed",
    "3x3x3 No Inspection", "Team Blindfolded", "2-man Mini Guildford", 
    "Rubik’s Magic", "Master Magic", "3x3x3 With Feet", "3x3x3 Match The Scramble", 
    "3x3x3 Supersolve", "Cap On Pen", "3x3x3 Scrambling", "4x4x4 One-Handed", "2x2x2-4x4x4 Relay"
]

def draw_card(c, x, y, comp_name, event_name, round_text, format_type):
    # AUTHENTIC PURPLE AESTHETIC
    PURPLE = (0.5, 0.2, 0.8) 
    BLACK = (0, 0, 0)
    
    c.setStrokeColorRGB(*PURPLE)
    c.setLineWidth(1.2)
    
    # Header & Name Boxes
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(*BLACK)
    c.drawCentredString(x + 4.85*cm, y + 11.8*cm, comp_name.upper())
    
    c.rect(x + 0.5*cm, y + 10.2*cm, 6.5*cm, 0.8*cm)   # Name
    c.rect(x + 7.2*cm, y + 10.2*cm, 1.0*cm, 0.8*cm) # Group
    c.rect(x + 8.4*cm, y + 10.2*cm, 0.8*cm, 0.8*cm) # Round
    c.drawCentredString(x + 8.8*cm, y + 10.5*cm, round_text)
    
    # Event Banner with Mistletoe
    c.setFillColorRGB(0.95, 0.9, 1.0) 
    c.rect(x + 0.5*cm, y + 9.0*cm, 8.7*cm, 0.8*cm, fill=1)
    c.setFillColorRGB(0.3, 0.1, 0.5) 
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 0.8*cm, y + 9.25*cm, f"🌿 {event_name.upper()} 🌿")
    
    # Rows Logic: Bo1 = 1, Mo3 = 3, Ao5 = 5
    if format_type == "Bo1":
        num_attempts = 1
    elif format_type == "Mo3":
        num_attempts = 3
    else:
        num_attempts = 5
    
    for i in range(num_attempts):
        row_y = y + 7.3*cm - (i * 1.3*cm)
        c.setStrokeColorRGB(*PURPLE)
        c.rect(x + 1.2*cm, row_y, 5.3*cm, 1.1*cm) # Result
        c.rect(x + 6.7*cm, row_y, 1.1*cm, 1.1*cm) # Judge
        c.rect(x + 8.0*cm, row_y, 1.2*cm, 1.1*cm) # Comp
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(*BLACK)
        c.drawString(x + 0.4*cm, row_y + 0.4*cm, str(i + 1))

    # Extra Attempt positioning
    if format_type == "Bo1":
        extra_y = y + 5.7*cm # High up for Bo1
    elif format_type == "Mo3":
        extra_y = y + 3.1*cm 
    else:
        extra_y = y + 0.5*cm
        
    c.setStrokeColorRGB(*PURPLE)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColorRGB(*PURPLE)
    c.drawString(x + 1.2*cm, extra_y + 1.15*cm, "✧ EXTRA ATTEMPT ✧")
    c.rect(x + 1.2*cm, extra_y, 5.3*cm, 1.1*cm)
    c.rect(x + 6.7*cm, extra_y, 1.1*cm, 1.1*cm)
    c.rect(x + 8.0*cm, extra_y, 1.2*cm, 1.1*cm)

@app.route('/')
def index():
    return render_template('index.html', events=EVENTS)

@app.route('/generate', methods=['POST'])
def generate():
    comp_name = request.form.get('comp_name', 'Unofficial Comp')
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin_x = (width - 19*cm) / 2
    margin_y = (height - 26*cm) / 2

    for event in EVENTS:
        if request.form.get(f'check_{event}'):
            format_type = request.form.get(f'format_{event}', 'Ao5')
            rounds = int(request.form.get(f'rounds_{event}', 1))
            
            for r in range(1, rounds + 1):
                round_label = "F" if r == rounds else str(r)
                try:
                    total_cards = int(request.form.get(f'cards_{event}_r{r}', 0))
                except ValueError:
                    total_cards = 0
                
                cards_placed = 0
                while cards_placed < total_cards:
                    for row in range(2):
                        for col in range(2):
                            if cards_placed < total_cards:
                                x_pos = margin_x + (col * 10*cm)
                                y_pos = height - margin_y - 13*cm - (row * 13.2*cm)
                                draw_card(c, x_pos, y_pos, comp_name, event, round_label, format_type)
                                cards_placed += 1
                    c.showPage()
    
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{comp_name}_Scorecards.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)