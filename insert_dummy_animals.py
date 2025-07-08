import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adopt_project.settings')
django.setup()

from adoption.models import Animal, User

# Ambil user shelter (ganti kalau perlu)
admin_user = User.objects.filter(username='admin_shelter').first()

if not admin_user:
    print("Admin shelter user tidak ditemukan!")
    exit()

# Daftar data dummy hewan
animals = [
    {
        'name': 'Brownie',
        'species': 'Dog',
        'breed': 'Mixed',
        'age': 3,
        'gender': 'Male',
        'status': 'available',
        'description': 'Friendly brown dog rescued from the street.'
    },
    {
        'name': 'Luna',
        'species': 'Cat',
        'breed': 'Persian',
        'age': 2,
        'gender': 'Female',
        'status': 'available',
        'description': 'White fluffy cat, very playful.'
    },
    {
        'name': 'Flopsy',
        'species': 'Rabbit',
        'breed': 'Angora',
        'age': 1,
        'gender': 'Female',
        'status': 'available',
        'description': 'Small rabbit with soft fur, rescued from pet abandonment.'
    },
    {
        'name': 'Speedy',
        'species': 'Turtle',
        'breed': 'Red-Eared Slider',
        'age': 5,
        'gender': 'Male',
        'status': 'available',
        'description': 'Slow but curious. Was left at a park.'
    }
]

# Insert data ke database
for data in animals:
    animal = Animal(**data, shelter=admin_user)
    animal.save()
    print(f"✔️ Ditambahkan: {animal.name}")

print("✅ Semua data dummy telah dimasukkan.")
