import json

with open('assets/coco_annotations.json', 'r') as f:
    data = json.load(f)

# Check all char-related categories and their annotations
for cat_name in ['char_denia', 'char_chisa', 'char_aemeath']:
    cat_id = None
    for cat in data['categories']:
        if cat['name'] == cat_name:
            cat_id = cat['id']
            break
    if cat_id is None:
        print(f'{cat_name}: NOT FOUND in categories')
        continue
    print(f'\n{cat_name} (id={cat_id}):')
    count = 0
    for ann in data['annotations']:
        if ann['category_id'] == cat_id:
            count += 1
            img_info = next((img for img in data['images'] if img['id'] == ann['image_id']), None)
            img_name = img_info['file_name'] if img_info else 'UNKNOWN'
            print(f'  image_id={ann["image_id"]} ({img_name}), bbox={ann["bbox"]}')
    print(f'  Total annotations: {count}')

# Also check images directory
import os
img_dir = 'assets/images'
if os.path.exists(img_dir):
    files = [f for f in os.listdir(img_dir) if f.endswith('.png')]
    print(f'\nTotal template images: {len(files)}')
    for i in [0, 1, 2, 3, 4, 5, 10, 20, 33, 34]:
        fname = f'{i}.png'
        if fname in files:
            size = os.path.getsize(os.path.join(img_dir, fname))
            print(f'  {fname}: {size} bytes')
