import cv2

def draw_boxes_from_entities(image_path, entities, output='boxed.jpg'):
    img = cv2.imread(image_path)
    
    colors = {
        'supplier_name': (0, 255, 0),
        'line_item': (0, 165, 255),
        'total': (255, 192, 203)
    }
    
    for entity in entities:
        if entity.type_ in colors:
            # Draw box logic here
            pass
    
    cv2.imwrite(output, img)