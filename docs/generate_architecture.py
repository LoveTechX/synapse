import svgwrite

def create_architecture_diagram():
    dwg = svgwrite.Drawing('architecture_diagram.svg', profile='tiny')

    # Define the colors and dimensions
    colors = {'component': '#f0f0f0', 'text': '#000000'}
    width, height = 800, 600

    # Create components
    components = {
        'Data Storage': (100, 100, 200, 100),
        'File Processing': (350, 100, 200, 100),
        'AI Engine': (600, 100, 200, 100),
        'User Interface': (100, 300, 700, 100)
    }

    # Add rectangles and text for components
    for name, (x, y, w, h) in components.items():
        dwg.add(dwg.rect(insert=(x, y), size=(w, h), fill=colors['component'], stroke='#000'))
        dwg.add(dwg.text(name, insert=(x + 10, y + 50), fill=colors['text']))

    # Create connections
    connections = [
        ((200, 150), (350, 150)),  # Data Storage to File Processing
        ((500, 150), (600, 150)),  # File Processing to AI Engine
        ((300, 250), (300, 150)),  # User Interface to File Processing
        ((700, 250), (700, 150)),  # User Interface to AI Engine
    ]

    # Add lines for connections
    for start, end in connections:
        dwg.add(dwg.line(start=start, end=end, stroke=colors['text'], stroke_width=2))

    # Save the SVG file
    dwg.save()

if __name__ == '__main__':
    create_architecture_diagram()